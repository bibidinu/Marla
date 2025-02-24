import pandas as pd
from strategy import calculate_trading_signal

def backtest_strategy(historical_data):
    """
    Esegue il backtest della strategia sui dati storici forniti.
    """
    wins, losses = 0, 0
    for index in range(50, len(historical_data)):
        df_slice = historical_data.iloc[:index]
        signal = calculate_trading_signal(df_slice)
        if signal == "BUY" or signal == "SELL":
            entry_price = df_slice.iloc[-1]["close"]
            exit_price = historical_data.iloc[index]["close"]
            if (signal == "BUY" and exit_price > entry_price) or (signal == "SELL" and exit_price < entry_price):
                wins += 1
            else:
                losses += 1
    
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    print(f"📊 Backtest completato - Win Rate: {win_rate:.2f}% ({wins} vinti / {losses} persi)")
    return win_rate
