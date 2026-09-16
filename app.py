from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector


from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

users = {}




# Load the pre-trained stock prediction model
MODEL_PATH = "lstm_model.keras"
model = tf.keras.models.load_model(MODEL_PATH, compile=False)

# Function to fetch real stock data
def fetch_stock_data(symbol, days=60):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=f"{days}d")
        return data["Close"].values if not data.empty else None
    except:
        return None

# Function to make stock price predictions
def predict_stock_price(symbol, future_days=30):
    stock_data = fetch_stock_data(symbol)
    if stock_data is None:
        return {"error": "Invalid stock symbol or no data available."}

    # Normalize the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    stock_data_scaled = scaler.fit_transform(stock_data.reshape(-1, 1))

    # Prepare input for the model (last 60 days)
    input_data = np.array(stock_data_scaled[-60:]).reshape(1, 60, 1)

    # Predict next 30 days
    predictions = []
    current_input = input_data

    for _ in range(future_days):
        pred = model.predict(current_input)[0, 0]
        predictions.append(pred)
        current_input = np.append(current_input[:, 1:, :], [[[pred]]], axis=1)

    # Convert back to original scale
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

    # Generate date-wise predictions
    today = datetime.today()
    prediction_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, future_days + 1)]

    return {"predictions": [{"date": d, "price": float(p)} for d, p in zip(prediction_dates, predictions)]}

# -----------------------------------------------------------------------------

# ---------------- LOGIN REQUIRED ----------------
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("dashboard.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return "User already exists!"

        hashed_password = generate_password_hash(password)
        users[username] = hashed_password

        return redirect(url_for('login'))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid username or password!"

    return render_template("login.html")

# ---------------- INDEX (PROTECTED) ----------------
@app.route("/index")
@login_required
def index():
    return render_template("index.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))




# API route for stock prediction
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    stock_symbol = data.get("stockSymbol", "").upper()
    if not stock_symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    prediction_result = predict_stock_price(stock_symbol)
    return jsonify(prediction_result)

if __name__ == "__main__":
    app.run(debug=True)
