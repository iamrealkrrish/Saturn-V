import time
import ccxt
from datetime import datetime

# ================= CONFIGURATION =================
# 1. Choose Exchange (e.g., 'binance', 'kucoin', 'kraken', 'coinbase')
EXCHANGE_NAME = "kucoin"

# 2. Choose Trading Mode (True = Paper/Sandbox Trading, False = Live Trading)
IS_PAPER_TRADING = True

# 3. API Credentials (Use sandbox keys if Paper Trading is True)
API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"
API_PASSWORD = "your_api_password_if_required"  # Required for KuCoin/Coinbase, leave empty ("") if not needed

# 4. Market & Order Settings
SYMBOL = "KCS/USDT"
TRADE_AMOUNT = 1.0          # Amount of base asset to trade per order
CHECK_INTERVAL_SECONDS = 60  

# 5. Strategy Risk Parameters
PROFIT_TARGET_PERCENT = 0.5   # +0.50% profit target to take profit
REBUY_DROP_PERCENT = 4.0      # -4.0% price drop to trigger a DCA rebuy
STOP_LOSS_PERCENT = 8.0       # -8.0% hard stop-loss to abort and cut losses
# =================================================

# Dynamic Exchange Initialization via CCXT
try:
    exchange_class = getattr(ccxt, EXCHANGE_NAME)
except AttributeError:
    raise ValueError(f"Exchange '{EXCHANGE_NAME}' is not supported by CCXT.")

exchange_config = {
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'timeout': 30000,
    'options': {
        'defaultType': 'spot',
    }
}

if API_PASSWORD:
    exchange_config['password'] = API_PASSWORD

exchange = exchange_class(exchange_config)

# Enable Sandbox/Paper Trading Mode if supported by the exchange
if IS_PAPER_TRADING:
    try:
        exchange.set_sandbox_mode(True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PAPER TRADING MODE ENABLED (Sandbox)")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Notice: Sandbox mode not natively supported via CCXT for {EXCHANGE_NAME}: {e}")

# State Variables
entry_price = None
rebuy_count = 0
last_buy_time = 0

def get_base_quote_currencies(symbol):
    """Safely extract base and quote currencies from symbol (e.g., KCS/USDT -> KCS, USDT)."""
    parts = symbol.split('/')
    return parts[0], parts[1]

def get_balances():
    """Fetch free balances for quote and base currencies safely."""
    try:
        base_curr, quote_curr = get_base_quote_currencies(SYMBOL)
        balance = exchange.fetch_balance()
        quote_free = balance['free'].get(quote_curr, 0.0)
        base_free = balance['free'].get(base_curr, 0.0)
        return quote_free, base_free
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error fetching balances: {e}")
        return 0.0, 0.0

def run_bot():
    global entry_price, rebuy_count, last_buy_time
    
    base_curr, quote_curr = get_base_quote_currencies(SYMBOL)
    mode_str = "PAPER TRADING" if IS_PAPER_TRADING else "LIVE TRADING"
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Saturn-V Bot ({mode_str}) on {EXCHANGE_NAME.upper()} for {SYMBOL}...")
    
    try:
        exchange.load_markets()
    except Exception as e:
        print(f"Warning: Initial market load failed, will retry in loop: {e}")

    while True:
        try:
            current_time = time.time()
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. Fetch latest market ticker price
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']
            
            # 2. Get current account balances
            quote_balance, base_balance = get_balances()
            
            base_value_quote = base_balance * current_price
            holding_base = base_balance > 0.01  
            
            action_logged = "HOLD"
            
            # --- STRATEGY LOGIC ---
            
            # Condition 1: Initial Buy
            if quote_balance >= 1.0 and not holding_base and entry_price is None:
                exchange.create_market_buy_order(SYMBOL, TRADE_AMOUNT)
                entry_price = current_price
                rebuy_count = 0
                last_buy_time = current_time
                action_logged = "INITIAL BUY"
                print(f"[{timestamp_str}] [BUY] Executed Initial Buy at {current_price}. Entry Price set to {entry_price}")

            # Condition 2: Sell Condition (Profit Target Hit)
            elif holding_base and entry_price is not None and current_price >= (entry_price * (1 + PROFIT_TARGET_PERCENT / 100)):
                if base_value_quote >= 1.0:
                    exchange.create_market_sell_order(SYMBOL, base_balance)
                    print(f"[{timestamp_str}] [SELL] Target +{PROFIT_TARGET_PERCENT}% hit. Sold at {current_price} (Entry was {entry_price})")
                    entry_price = None
                    rebuy_count = 0
                    action_logged = "SELL (Profit)"
                else:
                    action_logged = f"HOLD ({base_curr} value too low to sell)"

            # Condition 3: Stop-Loss Condition (Hard Stop-Loss Triggered)
            elif holding_base and entry_price is not None and current_price <= (entry_price * (1 - STOP_LOSS_PERCENT / 100)):
                if base_value_quote >= 1.0:
                    exchange.create_market_sell_order(SYMBOL, base_balance)
                    print(f"[{timestamp_str}] [STOP-LOSS] Drop -{STOP_LOSS_PERCENT}% hit. Emergency sell at {current_price} (Entry was {entry_price})")
                    entry_price = None
                    rebuy_count = 0
                    action_logged = "SELL (Stop-Loss)"
                else:
                    action_logged = "HOLD (Stop-loss hit, but asset value too low to sell)"

            # Condition 4: Rebuy Condition (DCA Drop Triggered)
            elif holding_base and entry_price is not None and current_price <= (entry_price * (1 - REBUY_DROP_PERCENT / 100)):
                if quote_balance >= 1.0:
                    if rebuy_count == 0:
                        # First rebuy: Immediate execution on dip
                        exchange.create_market_buy_order(SYMBOL, TRADE_AMOUNT)
                        entry_price = current_price
                        rebuy_count = 1
                        last_buy_time = current_time
                        action_logged = "REBUY (1st)"
                        print(f"[{timestamp_str}] [REBUY 1] Drop -{REBUY_DROP_PERCENT}% hit. Bought at {current_price}")
                    else:
                        # Subsequent rebuys: Progressive cooldown check (7 mins per count)
                        cooldown = rebuy_count * 7 * 60  
                        time_elapsed = current_time - last_buy_time
                        
                        if time_elapsed >= cooldown:
                            exchange.create_market_buy_order(SYMBOL, TRADE_AMOUNT)
                            entry_price = current_price
                            rebuy_count += 1
                            last_buy_time = current_time
                            action_logged = f"REBUY ({rebuy_count}th)"
                            print(f"[{timestamp_str}] [REBUY {rebuy_count}] Cooldown passed ({int(time_elapsed)}s). Bought at {current_price}")
                        else:
                            action_logged = f"HOLD (Rebuy cooldown active: {int(cooldown - time_elapsed)}s remaining)"
                else:
                    action_logged = f"HOLD (Insufficient {quote_curr} balance for rebuy)"

            # Condition 5: Hold Condition
            else:
                action_logged = "HOLD"

            print(f"[{timestamp_str}] Action: {action_logged} | Price: {current_price} | Entry: {entry_price} | Rebuys: {rebuy_count} | {quote_curr} Bal: {quote_balance:.2f} | {base_curr} Bal: {base_balance:.4f}")

        except ccxt.NetworkError as ne:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Network/Timeout Error: {ne}. Retrying in 10s...")
            time.sleep(10)
            continue
        except ccxt.ExchangeError as ee:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Exchange Error: {ee}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unexpected error: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_bot()
