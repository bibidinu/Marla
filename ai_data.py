import pandas as pd
import numpy as np
from api import get_historical_data
from strategy import (
    compute_rsi, compute_atr, compute_macd, compute_bollinger_bands, compute_vwap, 
    compute_adx, compute_supertrend, compute_ema, compute_trend, compute_mfi, compute_cci,
    compute_stochastic_oscillator, compute_williams_r
)

def compute_target(df):
    """Definisce il target come 1 (profitto) o 0 (perdita), basato sulla chiusura futura."""
    df["target"] = np.where(df["close"].shift(-3) > df["close"], 1, 0)
    return df

def collect_data(symbols, timeframes=["5", "15", "30", "60", "120", "240", "D", "W"]):
    """Raccoglie i dati storici e li salva in un file CSV per l'addestramento AI."""
    print("🚀 Avvio della raccolta dati AI...")
    all_data = []

    for symbol in symbols:
        for timeframe in timeframes:
            print(f"📡 Raccolta dati per {symbol} (TF: {timeframe})...")

            df = get_historical_data(symbol, timeframe)
            if df is None or df.empty:
                print(f"⚠️ Nessun dato ricevuto per {symbol}, saltato.")
                continue

            # ✅ Calcola tutti gli indicatori
            df = compute_rsi(df)
            df = compute_atr(df)
            df = compute_macd(df)
            df = compute_bollinger_bands(df)
            df = compute_vwap(df)
            df = compute_adx(df)
            df = compute_supertrend(df)
            df = compute_ema(df, 50)
            df = compute_ema(df, 200)
            df = compute_trend(df)
            df = compute_mfi(df)
            df = compute_cci(df)
            df = compute_stochastic_oscillator(df)
            df = compute_williams_r(df)
            df = compute_target(df)

            # ✅ Riempie i NaN con valori predefiniti
            df.fillna({
                "RSI": 50, "ATR": df["ATR"].median(), "MACD": 0, "MACD_Signal": 0,
                "BB_Upper": df["close"], "BB_Lower": df["close"], "VWAP": df["close"],
                "ADX": 20, "SuperTrend": df["close"], "EMA_50": df["close"], "EMA_200": df["close"],
                "trend": 0, "MFI": 50, "CCI": 0, "Stoch": 50, "WilliamsR": -50
            }, inplace=True)

            all_data.append(df)

    if not all_data:
        print("⚠️ Nessun dato disponibile per l'addestramento AI.")
        return

    dataset = pd.concat(all_data)
    print(f"🔍 Anteprima dataset:\n{dataset.head()}")
    dataset.to_csv("training_data.csv", index=False)
    print("✅ Dataset di training salvato come training_data.csv")

if __name__ == "__main__":
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "SUIUSDT", "LTCUSDT", "TRXUSDT", "LINKUSDT"]
    collect_data(symbols)
