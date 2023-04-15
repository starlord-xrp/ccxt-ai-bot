import websocket
import json
import keys
import time
import ccxt
import math

#global veriables
ws = None
last_buy_price = 0

# Set up Binance US API key and secret
api_key = keys.binance_api_key
api_secret = keys.binance_api_secret

# Set up Binance US WebSocket endpoint
websocket_endpoint = "wss://stream.binance.us:9443/ws/ethusd@ticker"
symbol = 'ETHUSD'
exchange = ccxt.binanceus({'apiKey': api_key,'secret': api_secret, 'enableRateLimit': True})
print(f'Connected to {exchange}')
#--------------------------------------------------------------------------------------

async def cancel_order(order_id):
    try:
        canceled = await exchange.cancelOrder(sell_order_id)
        if canceled['status']=='canceled':
            return 'canceled'
        elif canceled['status']=='closed':
            return 'closed'
    except Exception as e:
        print('Error caneling order order:', e)
        return 'error'
#--------------------------------------------------------------------------------------

async def open_order (type, side, quantity, price):
    global symbol
    try:
        order = await exchange.create_order(symbol, type, side, quantity, price)
        return order
    except Exception as e:
        print('Error creating buy order:', e)
        return None
#--------------------------------------------------------------------------------------

async def pull_orders ():
    open_orders = await exchange.fetchOpenOrders()
    return open_orders
#--------------------------------------------------------------------------------------

def check_for_open_buy(open_orders):
    for order in open_orders:
        if order['side'] == 'buy':
            return order
    return None
    
#--------------------------------------------------------------------------------------

def check_for_open_sell (open_orders):
    for order in open_orders:
        if order['side'] == 'sell':
            return order
    return None
    
#--------------------------------------------------------------------------------------

async def check_if_filled (order_id):
    order = await exchange.fetch_order(order_id)
    if order['status'] == 'closed':
        return True
    else:
        return False
        
#--------------------------------------------------------------------------------------  

async def check_filled_price(order_id):
    order = await exchange.fetch_order(order_id)
    if order['status'] == 'closed' and order['filled'] > 0:
        return order['average']
    else:
        return None
        
#--------------------------------------------------------------------------------------

def calculate_buy (ask):
    return round(bid+0.01, 2)
    
#--------------------------------------------------------------------------------------

def calculate_stoploss(filled_price):
    stoploss = filled_price-0.01
    return math.floor(stoploss*100)/100
    
#--------------------------------------------------------------------------------------

def calculate_sell (ask):
    return round(ask-0.01, 2)
    
#--------------------------------------------------------------------------------------

def calculate_quantity(free_balance, buy_price):
    quantity = free_balance/buy_price
    return math.floor(quantity*10000)/10000
    
#-------------------------------------------------------------------------------------- 

async def get_account_balance():
    # Load your account balance
    await balance = exchange.fetch_balance()
    return balance['total']['USD']
    
#--------------------------------------------------------------------------------------

async def check_last_trade():
    global symbol
    my_trades = await exchange.fetch_my_trades(symbol)
    # Check if the last trade was a filled buy
    last_trade = my_trades[-1]
    return last_trade

#---------------------------------------------------------------------------------------
# Define function to handle WebSocket messages
def on_message(ws, message):
    global last_buy_price
    #parse the message:
    data = json.loads(message)
    bid_price = float(data["b"])
    ask_price = float(data["a"])
    
    #calculate values
    spread = ask_price - bid_price
    buy_price = calculate_buy(bid_price)
    sell_price = calculate_sell(ask_price)
    stoploss = calculate_stoploss(last_buy_price)
    free_balance = get_account_balance()
    quantity = calculate_quantity(free_balance, buy_price)
    #print full status
    print(f"Bid: {bid_price} Ask: {ask_price} Spread: {spread} Buy: {buy_price} Sell: {sell_price} Stoploss {stoploss} LastBuy: {last_buy_price}", end="/r")
    
    #pull open orders
    all_orders = pull_orders()
    
    #check if there are any open orders
    if all_orders:
        #check for sells
        open_sell = check_for_open_sell(all_orders)
        if open_sell:
            if ask_price<stoploss:
                status = cancel_order(open_sell['id'])
                if status=='canceled':
                    eject_order = open_order('market', 'sell', open_sell['amount'], sell_price)
                    print(f"Sell order dumped at {eject_order['price']}")
                else:
                    return
            elif sell_price<open_sell['price'] and sell_price>last_buy_price:
                status = cancel_order(open_sell['id'])
                if status == 'canceled':
                    new_sell = open_order('limit', 'sell', open_sell['amount'], sell_price)
                    print (f"New sell order plced at {new_sell['price']} due to downtrend.")
                    return
                else:
                    print("Error canceling sell order")
                    return
            else:
                print(f"Open sell order detected at {open_sell['price']} - No action")
                return
        #check for buys
        open_buy = check_for_open_buy(all_orders)
        if open_buy:
            status = cancel_order(open_buy['id'])
            if status == 'canceled':
                new_buy = open_order('limit', 'buy', quantity, buy_price)
                print(f"Buy order placed at {new_buy['price']}")
                if new_buy['status']=='closed':
                    new_sell = open_order('limit', 'sell', new_buy['amount'], sell_price)
                    print("Instant fill, sell order placed")
                    return
                return
            else:
                print("Error canceling buy order")
                return
    #there are no open orders
    else:
        #lets see if one got filled
        last_trade = check_last_trade()
        if last_trade['side'] == 'buy' and last_trade['status'] == 'closed':
            last_buy_price = last_trade['average']
            new_sell = open_order('limit', 'sell', last_trade['amount'], sell_price)
            print(f"Buy order filled at {last_trade['price']} - Sell order placed at {sell_price}")
            return
        #no open trades, no filled trades. Time for a new trade
        else:
            if sell_price > buy_price and quantity>0: #make sure the spread is wide enough to go in
                new_buy = open_order('limit', 'buy', quantity, sell_price)
                return
            else:
                print('Spread invalid or insufficient balance')
                return
#--------------------------------------------------------------------------------------
# Define function to handle WebSocket errors
def on_error(ws, error):
    print(error)
#--------------------------------------------------------------------------------------
# Define function to handle WebSocket close
def on_close(ws):
    print("WebSocket closed")
    ws = None
#--------------------------------------------------------------------------------------
# Define function to handle WebSocket open
def on_open(ws):
    print("WebSocket opened")
#--------------------------------------------------------------------------------------
def main():
    global ws
    while True:
        if ws is None:
            # Create WebSocket connection and subscribe to bookTicker stream
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(websocket_endpoint, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
        else:
            # WebSocket connection already exists, so wait for messages
            pass
#--------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
