import ccxt
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

# set up ccxt exchange clients
exchange_names = ['binance', 'bybit', 'coinbase', 'kraken']
exchanges = {}
for exchange_name in exchange_names:
    exchange = getattr(ccxt, exchange_name)()
    exchange.load_markets()
    exchanges[exchange_name] = exchange

# set up model
model = Sequential()
model.add(Dense(32, activation='relu', input_shape=(3,)))
model.add(Dense(1, activation='sigmoid'))
model.compile(optimizer=Adam(lr=0.001), loss='binary_crossentropy', metrics=['accuracy'])

# function to get data from multiple exchanges
def get_data(exchanges):
    X = []
    y = []
    for exchange_name, exchange in exchanges.items():
        symbol = 'BTC/USDT'
        timeframe = '5m'
        limit = 100
        ohlcvs = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        ohlcvs = np.array(ohlcvs)
        if len(ohlcvs) > 0:
            closes = ohlcvs[:, 4]
            mfis = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params={'indicator': 'mfi'})
            mfis = np.array(mfis)[:, 5]
            ema = pd.Series(closes).ewm(span=89).mean().values
            X_exchange = np.column_stack((closes, mfis, ema))
            y_exchange = np.where(np.diff(closes) > 0, 1, 0)
            X.append(X_exchange)
            y.append(y_exchange)
    X = np.concatenate(X, axis=0)
    y = np.concatenate(y, axis=0)
    return X, y

# train the model
for i in range(10):
    X_train, y_train = get_data(exchanges)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    model.fit(X_train, y_train, epochs=10, batch_size=32)

# continuously pull data and make predictions
while True:
    X_test, _ = get_data(exchanges)
    X_test = scaler.transform(X_test)
    y_pred = model.predict(X_test)
    print('Predicted price change: {:.2f}%, weight: {:.2f}'.format(y_pred[0][0] * 100, np.abs(y_pred[0][0] - 0.5) * 2))
    sleep(2)
