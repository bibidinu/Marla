import logging

# Configurazione logging
def setup_logging():
    logging.basicConfig(
        filename="trade_performance.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("📜 Logger avviato con successo")

def log_trade(symbol, side, qty, entry_price, tp1, tp2, tp3, sl, trailing_stop):
    """
    Registra le operazioni effettuate nel file di log.
    """
    trade_log = (f"📝 Trade registrato: {symbol} {side} - QTY: {qty}, Entry: {entry_price}, "
                 f"TP1: {tp1}, TP2: {tp2}, TP3: {tp3}, SL: {sl}, Trailing Stop: {trailing_stop}")
    logging.info(trade_log)
    print(trade_log)

def log_error(error_message):
    """
    Registra errori nel file di log.
    """
    logging.error(f"❌ Errore: {error_message}")
    print(f"❌ {error_message}")
