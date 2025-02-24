import logging

def calculate_position_size(balance, risk_percent, entry_price):
    """
    Calcola la dimensione della posizione in base al saldo disponibile e al rischio percentuale.
    """
    risk_amount = balance * (risk_percent / 100)
    position_size = risk_amount / entry_price
    logging.info(f"💰 Calcolata posizione: {position_size} con rischio {risk_percent}% del saldo")
    return position_size

def adjust_risk_based_on_volatility(volatility_index, base_risk_percent):
    """
    Adatta il rischio percentuale in base alla volatilità del mercato.
    """
    adjusted_risk = base_risk_percent * (1 + volatility_index)
    adjusted_risk = min(adjusted_risk, 5)  # Limite massimo del 5%
    logging.info(f"⚖️ Rischio adattato: {adjusted_risk}% basato sulla volatilità {volatility_index}")
    return adjusted_risk
