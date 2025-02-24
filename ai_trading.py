import joblib
import pandas as pd
from strategy import compute_rsi, compute_atr

# Caricare il modello AI
model = joblib.load("ai_trading_model.pkl")

def predict_trade(symbol, df):
    """ Utilizza il modello AI per prevedere la probabilità di successo di un trade. """
    df["RSI"] = compute_rsi(df["close"])
    df["ATR"] = compute_atr(df)
    df["EMA_50"] = df["close"].ewm(span=50).mean()
    df["EMA_200"] = df["close"].ewm(span=200).mean()
    df["trend"] = (df["EMA_50"] > df["EMA_200"]).astype(int)

    latest_data = df.iloc[-1][["RSI", "ATR", "EMA_50", "EMA_200", "trend"]].values.reshape(1, -1)
    
    prediction = model.predict(latest_data)
    probability = model.predict_proba(latest_data)[0][1]  # Probabilità che sia vincente

    print(f"📊 AI Prediction per {symbol}: {'BUY' if prediction[0] == 1 else 'SELL'} con probabilità {probability:.2%}")
    return prediction[0], probability
