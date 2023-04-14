import ccxt
import pandas as pd
import numpy as np
import tensorflow as tf

# Initialize Binance exchange
exchange = ccxt.binanceus({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
})

# Define currency pair and time interval
symbol = 'BTC/USD'
interval = '1d'

# Define initial balance and position size
initial_balance = 1000
position_size = 0.01

# Retrieve historical price data
ohlcv = exchange.fetch_ohlcv(symbol, interval)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Calculate simple moving average (SMA)
sma_window = 10
df['sma'] = df['close'].rolling(sma_window).mean()
df.dropna(inplace=True)

# Define features and labels
X = np.array(df[['close', 'sma']])
y = np.where(df['close'].shift(-1) > df['close'], 1, -1)[:-1]

# Split data into train and test sets
split_ratio = 0.8
split_index = int(len(X) * split_ratio)
X_train, X_test = X[:split_index], X[split_index:]
y_train, y_test = y[:split_index], y[split_index:]

# Define neural network model
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(1, input_shape=(2,), activation='linear')
])

# Compile model
model.compile(optimizer='adam', loss='mse')

# Train model
model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)

# Evaluate model
test_loss = model.evaluate(X_test, y_test, verbose=0)
print(f'Test loss: {test_loss:.4f}')

# Define buy and sell functions
def buy(balance, price):
    # Calculate position size based on balance
    position = balance * position_size / price
    # Buy position
    exchange.create_market_buy_order(symbol, position)

def sell(position):
    # Sell entire position
    exchange.create_market_sell_order(symbol, position)

# Define current balance and position
balance = initial_balance
position = 0

# Loop through real-time price data
for i in exchange.fetch_ohlcv(symbol, interval):
    # Calculate current price
    price = i[4]
    # Calculate features
    features = np.array([[price, df['sma'].iloc[-1]]])
    # Predict label
    label = model.predict(features)
    # Buy if label is positive and position is zero
    if label > 0 and position == 0:
        buy(balance, price)
        position = balance / price
        balance = 0
    # Sell if label is negative and position is nonzero
    elif label < 0 and position != 0:
        sell(position)
        balance = position * price
        position = 0
