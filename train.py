import numpy as np
import pandas as pd
import yfinance as yf
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
import os

# Define future prediction days
FUTURE_DAYS = 30  # Predict next 30 days

# Download stock data
def get_stock_data(stock_symbol, period="5y", interval="1d"):
    df = yf.download(stock_symbol, period=period, interval=interval)
    return df


# Preprocess data
def preprocess_data(df):
    scaler = MinMaxScaler(feature_range=(0, 1))
    df_close = df['Close'].values.reshape(-1, 1)
    df_scaled = scaler.fit_transform(df_close)
    return df_scaled, scaler


# Create sequences for LSTM
def create_sequences(data, time_step=60, future_days=FUTURE_DAYS):
    X, y = [], []
    for i in range(len(data) - time_step - future_days):
        X.append(data[i: i + time_step])
        y.append(data[i + time_step: i + time_step + future_days])
    return np.array(X), np.array(y)


# Train LSTM model
def train_lstm(X_train, y_train, epochs=50, batch_size=32):
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
        tf.keras.layers.LSTM(50, return_sequences=False),
        tf.keras.layers.Dense(25),
        tf.keras.layers.Dense(FUTURE_DAYS)  # Predict 30 days
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
    return model

if __name__ == "__main__":
    stock_symbol = "AAPL"  # Change to desired stock
    df = get_stock_data(stock_symbol)
    scaled_data, scaler = preprocess_data(df)
    
    X, y = create_sequences(scaled_data)
    train_size = int(len(X) * 0.8)
    X_train, y_train = X[:train_size], y[:train_size]
    
    model = train_lstm(X_train, y_train)
    model.save("lstm_model.keras")
    print("Model trained and saved as lstm_model.keras")
