import time
import ccxt
from datetime import datetime

def get_user_config():
    """Interactive command-line setup menu."""
    print("=========================================")
    print("       SATURN-V BOT CONFIGURATION        ")
    print("=========================================")
    
    exchange_name = input("Exchange Name [default: kucoin]: ").strip().lower() or "kucoin"
    
    paper_input = input("Use Paper/Sandbox Trading? (y/n) [default: y]: ").strip().lower()
    is_paper_trading = False if paper_input == 'n' else True
    
    print("\n--- API Credentials ---")
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    api_password = input("API Password / Passphrase (press Enter if none): ").strip()
    
    print("\n--- Trading Strategy Settings ---")
    symbol = input("Trading Symbol [default: KCS/USDT]: ").strip().upper() or "KCS/USDT"
    trade_amount = float(input("Trade Amount per order [default: 1.0]: ") or 1.0)
    
    profit_target = float(input("Profit Target % [default: 0.5]: ") or 0.5)
    rebuy_drop = float(input("Rebuy Drop % [default: 4.0]: ") or 4.0)
    stop_loss = float(input("Stop Loss % [default: 8.0]: ") or 8.0)
    
    print("=========================================\n")
    
    return {
        "EXCHANGE_NAME": exchange_name,
        "IS_PAPER_TRADING": is_paper_trading,
        "API_KEY": api_key,
        "API_SECRET": api_secret,
        "API_PASSWORD": api_password,
        "SYMBOL": symbol,
        "TRADE_AMOUNT": trade_amount,
        "PROFIT_TARGET_PERCENT": profit_target,
        "REBUY_DROP_PERCENT": rebuy_drop,
        "STOP_LOSS_PERCENT": stop_loss,
        "CHECK_INTERVAL_SECONDS": 60
    }

def get_base_quote_currencies(symbol):
    """Safely extract base and quote currencies from symbol (e.g., KCS/USDT -> KCS, USDT)."""
    parts = symbol.split('/')
    return parts[0], parts[1]

def run_bot(config):
    # Unpack config
    EXCHANGE_NAME = config["EXCHANGE_NAME"]
    IS_PAPER_TRADING = config["IS_PAPER_TRADING"]
    SYMBOL = config["SYMBOL"]
    TRADE_AMOUNT = config["TRADE_AMOUNT"]
    PROFIT_TARGET_PERCENT = config["PROFIT_TARGET_PERCENT"]
    REBUY_DROP_PERCENT = config["REBUY_DROP_PERCENT"]
    STOP_LOSS_PERCENT = config["STOP_LOSS_PERCENT"]
    CHECK_INTERVAL_SECONDS = config["CHECK_INTERVAL_SECONDS"]

    # Dynamic Exchange Initialization via CCXT
    try:
        exchange_class = getattr(ccxt, EXCHANGE_NAME)
    except AttributeError:
        raise ValueError(f"Exchange '{EXCHANGE_NAME}' is not supported by CCXT.")

    exchange_config = {
        'apiKey': config["API_KEY"],
        'secret': config["API_SECRET"],
        'enableRateLimit': True,
        'timeout': 30000,
        'options': {'defaultType': 'spot'},
    }

    if config["API_PASSWORD"]:
        exchange_config['password'] = config["API_PASSWORD"]

    exchange = exchange_class(exchange_config)

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

    def get_balances():
        try:
            base_curr, quote_curr = get_base_quote_currencies(SYMBOL)
            balance = exchange.fetch_balance()
            quote_free = balance['free'].get(quote_curr, 0.0)
            base_free = balance['free'].get(base_curr, 0.0)
            return quote_free, base_free
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error fetching balances: {e}")
            return 0.0, 0.0

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
            
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']
            
            quote_balance, base_balance = get_balances()
            base_value_quote = base_balance * current_price
            holding_base = base_balance > 0.01  
            
            action_logged = "HOLD"
            
            # --- STRATEGY LOGIC ---
            if quote_balance >= 1.0 and not holding_base and entry_price is None:
                exchange.create_market_buy_order(SYMBOL, TRADE_AMOUNT)
                entry_price = current_price
                rebuy_count = 0
                last_buy_time = current_time
                action_logged = "INITIAL BUY"
                print(f"[{timestamp_str}] [BUY] Executed Initial Buy at {current_price}. Entry Price set to {entry_price}")

            elif holding_base and entry_price is not None and current_price >= (entry_price * (1 + PROFIT_TARGET_PERCENT / 100)):
                if base_value_quote >= 1.0:
                    exchange.create_market_sell_order(SYMBOL, base_balance)
                    print(f"[{timestamp_str}] [SELL] Target +{PROFIT_TARGET_PERCENT}% hit. Sold at {current_price} (Entry was {entry_price})")
                    entry_price = None
                    rebuy_count = 0
                    action_logged = "SELL (Profit)"
                else:
                    action_logged = f"HOLD ({base_curr} value too low to sell)"

            elif holding_base and entry_price is not None and current_price <= (entry_price * (1 - STOP_LOSS_PERCENT / 100)):
                if base_value_quote >= 1.0:
                    exchange.create_market_sell_order(SYMBOL, base_balance)
                    print(f"[{timestamp_str}] [STOP-LOSS] Drop -{STOP_LOSS_PERCENT}% hit. Emergency sell at {current_price} (Entry was {entry_price})")
                    entry_price = None
                    rebuy_count = 0
                    action_logged = "SELL (Stop-Loss)"
                else:
                    action_logged = "HOLD (Stop-loss hit, but asset value too low to sell)"

            elif holding_base and entry_price is not None and current_price <= (entry_price * (1 - REBUY_DROP_PERCENT / 100)):
                if quote_balance >= 1.0:
                    if rebuy_count == 0:
                        exchange.create_market_buy_order(SYMBOL, TRADE_AMOUNT)
                        entry_price = current_price
                        rebuy_count = 1
                        last_buy_time = current_time
                        action_logged = "REBUY (1st)"
                        print(f"[{timestamp_str}] [REBUY 1] Drop -{REBUY_DROP_PERCENT}% hit. Bought at {current_price}")
                    else:
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
    config = get_user_config()
    run_bot(config)
