import ccxt
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
from tensorflow.keras.optimizers import Adam

# Define API credentials and symbol to retrieve data for
exchange = ccxt.bybit()
exchange.apiKey = 'YOUR_API_KEY'
exchange.secret = 'YOUR_SECRET_KEY'
symbol = 'BTC/USD'

# Retrieve historical data from the exchange
ohlcv = exchange.fetch_ohlcv(symbol, '1d')
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# Calculate the Money Flow Index (MFI)
typical_price = (df['high'] + df['low'] + df['close']) / 3
raw_money_flow = typical_price * df['volume']
positive_money_flow = np.where(typical_price > typical_price.shift(1), raw_money_flow, 0)
negative_money_flow = np.where(typical_price < typical_price.shift(1), raw_money_flow, 0)
positive_money_flow_sum = positive_money_flow.rolling(window=14).sum()
negative_money_flow_sum = negative_money_flow.rolling(window=14).sum()
money_ratio = positive_money_flow_sum / negative_money_flow_sum
df['mfi'] = 100 - (100 / (1 + money_ratio))

# Normalize the data using MinMaxScaler
scaler = MinMaxScaler()
data = scaler.fit_transform(df[['open', 'high', 'low', 'close', 'volume', 'mfi']])

# Split the data into training and testing sets
train_size = int(len(data) * 0.8)
train_data = data[:train_size]
test_data = data[train_size:]

# Define the number of time steps and features for the LSTM model
n_steps = 30
n_features = 6

# Create a function to prepare the data for training the LSTM model
def prepare_data(data, n_steps):
    X, y = [], []
    for i in range(n_steps, len(data)):
        X.append(data[i-n_steps:i])
        y.append(data[i, 0])
    X, y = np.array(X), np.array(y)
    return X, y

# Prepare the data for training the LSTM model
X_train, y_train = prepare_data(train_data, n_steps)
X_test, y_test = prepare_data(test_data, n_steps)

# Define and compile the LSTM model
model = Sequential([
    LSTM(128, input_shape=(n_steps, n_features), return_sequences=True),
    Dropout(0.2),
    LSTM(128, return_sequences=True),
    Dropout(0.2),
    LSTM(128),
    Dropout(0.2),
    Dense(1)
])
model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

# Train the LSTM model
model.fit(X_train, y_train, epochs=100, batch_size=32)

# Make predictions on the test data
y_pred = model.predict(X_test)

# Evaluate the performance of the model
mse = model.evaluate(X_test, y_test)
print('MSE: ', mse)

# Make a binary prediction based on whether the price increased or decreased
y_pred_binary = np.where(y_pred > y_test, 1, 0)

# Calculate the accuracy of the binary prediction
accuracy = np.mean(y_pred_binary == y_test)
print('Accuracy: ', accuracy)
