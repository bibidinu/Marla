import time
import logging
from concurrent.futures import ThreadPoolExecutor
from api import get_filtered_pairs, get_balance, make_request, get_historical_data
from strategy import calculate_trade_levels

# Configurazione del logging
logging.basicConfig(filename="trading_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

MAX_WORKERS = 5  # Numero massimo di processi paralleli
MAX_OPEN_TRADES = 10  # Limite massimo di trade aperti contemporaneamente
SCAN_INTERVAL = 60  # Intervallo tra le scansioni in secondi (es. ogni 60 sec)

open_trades = {}  # Dizionario per tracciare gli ordini attivi

from api import make_request

def get_open_trades():
    """Ottiene le posizioni aperte per determinare se possiamo aprire nuovi trade."""
    endpoint = "/v5/position/list"
    params = {"category": "linear"}  # ✅ Assicurati che la categoria sia impostata correttamente
    response = make_request(endpoint, params)

    if response and "result" in response and "list" in response["result"]:
        positions = response["result"]["list"]
        open_trades = [pos["symbol"] for pos in positions if float(pos["size"]) > 0]
        print(f"📌 Posizioni aperte: {open_trades}")
        return open_trades

    print("⚠️ Nessuna posizione aperta trovata o errore nella richiesta API.")
    return []

def place_order(symbol, side, qty, entry_price):
    """
    Esegue un ordine con TP, SL e trailing stop e lo registra nei trade aperti.
    """
    trade_levels = calculate_trade_levels(entry_price, side)

    if trade_levels is None:
        print(f"⚠️ Errore nel calcolo dei livelli di trade per {symbol}. Skipping...")
        return

    params = {
        "category": "linear",
        "symbol": symbol,
        "side": side,
        "orderType": "Market",
        "qty": str(qty),
        "takeProfit": str(trade_levels["tp1"]),
        "stopLoss": str(trade_levels["sl"]),
        "trailingStop": str(trade_levels["trailing_stop"]),
        "timeInForce": "GoodTillCancel"
    }

    response = make_request("/v5/order/create", params, method="POST")

    if response:
        order_id = response.get("result", {}).get("orderId", None)
        if order_id:
            open_trades[symbol] = order_id  # Registra l'ordine attivo
            print(f"✅ Ordine {side} aperto su {symbol}: QTY {qty}, TP1 {trade_levels['tp1']}, TP2 {trade_levels['tp2']}, TP3 {trade_levels['tp3']}, SL {trade_levels['sl']}, Trailing Stop {trade_levels['trailing_stop']}")
            logging.info(f"Ordine aperto: {symbol} {side} QTY: {qty}, TP1: {trade_levels['tp1']}, TP2: {trade_levels['tp2']}, TP3: {trade_levels['tp3']}, SL: {trade_levels['sl']}, Trailing Stop: {trade_levels['trailing_stop']}")
        else:
            print(f"⚠️ Ordine aperto, ma nessun ID restituito per {symbol}.")
    else:
        print(f"❌ Errore nell'apertura dell'ordine per {symbol}")

    return response

def move_stop_loss(symbol, order_id, new_sl):
    """
    Aggiorna lo Stop Loss all'entrata dopo il primo Take Profit (TP1).
    """
    params = {
        "category": "linear",
        "symbol": symbol,
        "orderId": order_id,
        "stopLoss": str(new_sl)
    }
    
    response = make_request("/v5/order/amend", params, method="POST")
    
    if response:
        print(f"🔄 Stop Loss aggiornato per {symbol} a {new_sl}")
        logging.info(f"Stop Loss aggiornato per {symbol} a {new_sl}")
    else:
        print(f"⚠️ Errore nell'aggiornamento dello Stop Loss per {symbol}")
    
    return response

def scan_and_trade(symbol):
    """
    Scansiona una singola coppia e apre un trade se soddisfa i criteri.
    """
    print(f"📡 Analizzando {symbol}...")

    # Controlla quanti trade sono aperti prima di procedere
    current_open_trades = get_open_trades()
    if current_open_trades >= MAX_OPEN_TRADES:
        print(f"⚠️ Limite massimo di {MAX_OPEN_TRADES} trade aperti raggiunto, skipping {symbol}...")
        return

    df = get_historical_data(symbol)

    if df is None:
        print(f"⚠️ Nessun dato storico per {symbol}. Skipping...")
        return

    entry_price = df["close"].iloc[-1]
    side = "Buy" if df["RSI"].iloc[-1] > 55 else "Sell"

    trade_levels = calculate_trade_levels(entry_price, side)
    if trade_levels is None:
        print(f"⏭️ Nessun setup valido per {symbol}. Skipping...")
        return

    balance = get_balance()
    risk_per_trade = 0.02  # 2% del capitale per trade
    position_size = balance * risk_per_trade / entry_price

    place_order(symbol, side, position_size, entry_price)

def scan_and_trade_parallel():
    """
    Mantiene il bot attivo in un ciclo infinito, scansionando periodicamente le coppie.
    """
    while True:
        pairs = get_filtered_pairs()

        if not pairs:
            print("⚠️ Nessuna coppia valida trovata. Attendo prima della prossima scansione...")
        else:
            print(f"🔍 Scansione di {len(pairs)} coppie in parallelo...")

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                executor.map(scan_and_trade, pairs)

        print(f"⏳ Attesa {SCAN_INTERVAL} secondi prima della prossima scansione...")
        time.sleep(SCAN_INTERVAL)  # Attesa tra una scansione e l'altra
