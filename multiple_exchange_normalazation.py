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
model.add(Dense(32, activation='relu', input_shape=(2,)))
model.add(Dense(1, activation='sigmoid'))
model.compile(optimizer=Adam(lr=0.001), loss='binary_crossentropy', metrics=['accuracy'])

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
