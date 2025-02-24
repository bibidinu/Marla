import joblib
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor
from api import get_live_data, get_filtered_pairs, get_open_trades
from orders import place_order

# ✅ Caricamento AI e scaler
model = joblib.load("ai_model.pkl")
scaler = joblib.load("scaler.pkl")

MAX_OPEN_TRADES = 10  # 🔥 Limite massimo di trade aperti contemporaneamente
CHECK_INTERVAL = 60  # 🔄 Controlla il mercato ogni 60 secondi

def make_trade_decision(symbol):
    """Analizza i dati live e decide se aprire un trade."""
    # 🔥 Controlla il numero di trade aperti PRIMA di continuare
    open_trades = get_open_trades()
    if open_trades >= MAX_OPEN_TRADES:
        print(f"⚠️ Limite massimo di {MAX_OPEN_TRADES} trade aperti raggiunto. Skipping {symbol}.")
        return

    data = get_live_data(symbol)
    if data is None:
        print(f"⚠️ Nessun dato live per {symbol}, saltato.")
        return

    try:
        X_live = np.array([[data["open"], data["high"], data["low"], data["close"], data["volume"], data["turnover"]]])
        X_live_scaled = scaler.transform(X_live)

        # ✅ Predizione AI e probabilità
        prob = model.predict_proba(X_live_scaled)[:, 1][0]  # 🔥 FIX: Preleva singolo valore
        signal = model.predict(X_live_scaled)[0]

        if prob < 0.6:
            print(f"⚠️ AI insicura ({prob:.2f}), nessun trade per {symbol}.")
            return

        print(f"✅ AI conferma il segnale ({prob:.2f}), eseguo ordine per {symbol}!")
        place_order(symbol, "BUY" if signal == 1 else "SELL", 100, data["close"])

    except Exception as e:
        print(f"❌ Errore nell'analisi AI per {symbol}: {e}")

def scan_and_trade():
    """Scansiona le coppie di trading disponibili e prende decisioni di trading."""
    while True:
        print("🔍 Scansione delle coppie disponibili...")
        pairs = get_filtered_pairs()

        if not pairs:
            print("⚠️ Nessuna coppia trovata. Attendo il prossimo ciclo...")
            time.sleep(CHECK_INTERVAL)
            continue

        open_trades = get_open_trades()  # ✅ Verifica il numero di trade aperti
        print(f"📊 Trade attualmente aperti: {open_trades}/{MAX_OPEN_TRADES}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            for symbol in pairs:
                if open_trades >= MAX_OPEN_TRADES:
                    print(f"⚠️ Limite raggiunto. Stop trading per ora.")
                    break

                futures.append(executor.submit(make_trade_decision, symbol))
                open_trades += 1  # ✅ Aggiorna il conteggio in memoria
                time.sleep(1)  # 🔄 Ritardo per evitare limiti API

            for future in futures:
                future.result()  # ✅ Attende il completamento di tutti i thread

        print(f"⏳ Attesa {CHECK_INTERVAL} secondi prima della prossima scansione...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    print("🚀 Bot avviato! Inizio scansione delle coppie future...")
    scan_and_trade()
