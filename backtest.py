import yfinance as yf
import pandas as pd
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def run_backtest():
    logger.info("Downloading historical data for GC=F (15m interval, last 60 days)...")
    ticker = yf.Ticker("GC=F")
    
    # 60 days is the max for 15m interval on yfinance
    df = ticker.history(period="60d", interval="15m")
    
    if df.empty:
        logger.error("No data fetched.")
        return
        
    logger.info(f"Fetched {len(df)} candles.")
    
    # Calculate basic indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['RSI_14'] = calculate_rsi(df, period=14)
    
    # Calculate rolling Swing High/Low for the previous 20 candles
    df['Swing_High'] = df['High'].shift(1).rolling(window=20).max()
    df['Swing_Low'] = df['Low'].shift(1).rolling(window=20).min()
    
    # Drop NaNs
    df.dropna(inplace=True)
    
    # Simulation variables
    in_trade = False
    entry_price = 0.0
    trade_type = None # "BUY" or "SELL"
    tp = 0.0
    sl = 0.0
    
    win = 0
    loss = 0
    
    # Backtest Loop using SNIPER Rules
    # BUY: Price near Swing Low AND RSI < 40
    # SELL: Price near Swing High AND RSI > 60
    logger.info("Starting simulation...")
    
    for index, row in df.iterrows():
        current_price = row['Close']
        
        # Check if we hit SL or TP
        if in_trade:
            if trade_type == "BUY":
                if row['Low'] <= sl:
                    loss += 1
                    in_trade = False
                elif row['High'] >= tp:
                    win += 1
                    in_trade = False
            elif trade_type == "SELL":
                if row['High'] >= sl:
                    loss += 1
                    in_trade = False
                elif row['Low'] <= tp:
                    win += 1
                    in_trade = False
            continue # wait until next candle if still in trade
        
        # Look for Entry
        swing_low = row['Swing_Low']
        swing_high = row['Swing_High']
        rsi = row['RSI_14']
        
        # Tolerance for "near" (e.g., within 2 dollars)
        near_tolerance = 2.0 
        
        # BUY Condition
        if (current_price - swing_low) <= near_tolerance and rsi < 40:
            in_trade = True
            trade_type = "BUY"
            entry_price = current_price
            sl = swing_low - 2.0 # SL slightly below swing low
            tp = entry_price + (entry_price - sl) * 1.5 # 1:1.5 RR
            # logger.info(f"[{index}] BUY at {entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
            
        # SELL Condition
        elif (swing_high - current_price) <= near_tolerance and rsi > 60:
            in_trade = True
            trade_type = "SELL"
            entry_price = current_price
            sl = swing_high + 2.0 # SL slightly above swing high
            tp = entry_price - (sl - entry_price) * 1.5 # 1:1.5 RR
            # logger.info(f"[{index}] SELL at {entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")

    total_trades = win + loss
    win_rate = (win / total_trades * 100) if total_trades > 0 else 0.0
    
    logger.info("=== BACKTEST RESULTS ===")
    logger.info(f"Total Trades: {total_trades}")
    logger.info(f"Wins: {win} | Losses: {loss}")
    logger.info(f"Win Rate: {win_rate:.2f}%")

if __name__ == "__main__":
    run_backtest()
