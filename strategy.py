import pandas as pd
import ta
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging

# ✅ Configurazione logging
logging.basicConfig(filename="strategy_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# 📌 Calcolo degli indicatori tecnici
def compute_rsi(df, window=14):
    """Calcola RSI (Relative Strength Index)."""
    df["RSI"] = ta.momentum.RSIIndicator(df["close"], window=window).rsi()
    return df

def compute_atr(df, window=14):
    """Calcola ATR (Average True Range)."""
    df["ATR"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=window).average_true_range()
    return df

def compute_macd(df):
    """Calcola MACD e la linea di segnale."""
    macd = ta.trend.MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    return df

def compute_bollinger_bands(df):
    """Calcola Bollinger Bands."""
    bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Lower"] = bb.bollinger_lband()
    return df

def compute_vwap(df):
    """Calcola VWAP (Volume Weighted Average Price)."""
    df["VWAP"] = ta.volume.VolumeWeightedAveragePrice(df["high"], df["low"], df["close"], df["volume"]).volume_weighted_average_price()
    return df

def compute_adx(df):
    """Calcola ADX (Average Directional Index)."""
    df["ADX"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
    return df

def compute_supertrend(df, period=10, multiplier=3):
    """Calcola il SuperTrend per identificare trend e segnali di inversione."""
    atr = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=period).average_true_range()
    hl2 = (df["high"] + df["low"]) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    df["SuperTrend"] = np.where(df["close"] > upper_band.shift(1), lower_band, upper_band)
    return df

def compute_ema(df, window=50):
    """Calcola l'EMA (Exponential Moving Average) per il trend."""
    df[f"EMA_{window}"] = df["close"].ewm(span=window, adjust=False).mean()
    return df

def compute_trend(df):
    """Determina il trend basandosi sulla posizione del prezzo rispetto a EMA_50."""
    df["trend"] = np.where(df["close"] > df["EMA_50"], 1, 0)  # 1 = uptrend, 0 = downtrend
    return df

def compute_mfi(df):
    """Calcola il Money Flow Index (MFI)."""
    df["MFI"] = ta.volume.MFIIndicator(df["high"], df["low"], df["close"], df["volume"], window=14).money_flow_index()
    return df

def compute_cci(df):
    """Calcola il Commodity Channel Index (CCI)."""
    df["CCI"] = ta.trend.CCIIndicator(df["high"], df["low"], df["close"], window=20).cci()
    return df

def compute_stochastic_oscillator(df):
    """Calcola lo Stochastic Oscillator."""
    df["Stoch"] = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"], window=14).stoch()
    return df

def compute_williams_r(df):
    """Calcola il Williams %R."""
    df["WilliamsR"] = ta.momentum.WilliamsRIndicator(df["high"], df["low"], df["close"], lbp=14).williams_r()
    return df

# 📌 Analisi completa degli indicatori
def analyze_indicators(df):
    """Analizza RSI, MACD, Bollinger Bands, VWAP, ADX, SuperTrend e altri indicatori avanzati."""
    df = compute_rsi(df)
    df = compute_atr(df)
    df = compute_macd(df)
    df = compute_bollinger_bands(df)
    df = compute_vwap(df)
    df = compute_adx(df)
    df = compute_supertrend(df)
    df = compute_ema(df)
    df = compute_trend(df)
    df = compute_mfi(df)
    df = compute_cci(df)
    df = compute_stochastic_oscillator(df)
    df = compute_williams_r(df)
    return df

# 📌 Generazione dei segnali di trading
def generate_trade_signal(df):
    """Genera segnali di trading usando indicatori e Machine Learning."""
    latest = df.iloc[-1]

    long_condition = (
        latest["RSI"] > 50 and
        latest["MACD"] > latest["MACD_Signal"] and
        latest["close"] > latest["VWAP"] and
        latest["SuperTrend"] > 0 and
        latest["ADX"] > 25
    )

    short_condition = (
        latest["RSI"] < 50 and
        latest["MACD"] < latest["MACD_Signal"] and
        latest["close"] < latest["VWAP"] and
        latest["SuperTrend"] < 0 and
        latest["ADX"] > 25
    )

    if long_condition:
        return "Buy"
    elif short_condition:
        return "Sell"
    else:
        return "NO_TRADE"

# 📌 Calcolo dei livelli di Take Profit, Stop Loss e Trailing Stop
def calculate_trade_levels(entry_price, side):
    """Calcola TP, SL e Trailing Stop con ATR dinamico."""
    atr = entry_price * 0.005  # ATR basato sul prezzo

    if side == "Buy":
        tp1 = entry_price * 1.006
        tp2 = entry_price * 1.012
        tp3 = entry_price * 1.018
        sl = entry_price - atr
    else:
        tp1 = entry_price * 0.994
        tp2 = entry_price * 0.988
        tp3 = entry_price * 0.982
        sl = entry_price + atr

    trailing_stop = atr * 0.5

    return {
        "tp1": round(tp1, 6),
        "tp2": round(tp2, 6),
        "tp3": round(tp3, 6),
        "sl": round(sl, 6),
        "trailing_stop": round(trailing_stop, 6)
    }
