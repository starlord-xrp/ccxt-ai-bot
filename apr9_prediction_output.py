import ccxt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model

# Load the trained LSTM model
model = load_model('my_model.h5')

# Connect to Bybit
exchange = ccxt.bybit()
symbol = 'BTC/USD'

# Define the length of the historical data to use for each prediction
lookback = 30

# Define the threshold for converting the continuous output to a binary classification
threshold = 0.5

# Define the weight of the prediction
weight = 0.0

while True:
    # Get the most recent historical price data
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=lookback)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Calculate the Money Flow Index (MFI)
    tp = (df['high'] + df['low'] + df['close']) / 3.0
    mf = tp * df['volume']
    mfr = mf / (tp * lookback)
    mfi = 100 - (100 / (1 + mfr))

    # Normalize the data using the MinMaxScaler
    scaler = MinMaxScaler()
    df['mfi'] = scaler.fit_transform(mfi.values.reshape(-1, 1))
    df['close_norm'] = scaler.fit_transform(df['close'].values.reshape(-1, 1))

    # Prepare the data for prediction
    X = np.array(df[['mfi', 'close_norm']])
    X = np.reshape(X, (1, X.shape[0], X.shape[1]))

    # Make the prediction using the LSTM model
    y_pred = model.predict(X)
    y_pred_bin = 1 if y_pred > threshold else 0
    weight = 0.9 * weight + 0.1 * y_pred_bin

    # Print the predicted price movement and weight of the prediction
    if y_pred_bin == 1:
        print('Prediction: up ({:.2f})'.format(weight))
    else:
        print('Prediction: down ({:.2f})'.format(1.0 - weight))
