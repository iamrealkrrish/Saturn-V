
import time
import json
import os
import ccxt
from datetime import datetime

CONFIG_FILE = "bot_config.json"

def load_saved_config():
    """Load configuration from local file if it exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_config(config):
    """Save configuration to local file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Notice: Could not save configuration file: {e}")

def get_user_config():
    """Interactive command-line setup menu with persistent memory check."""
    saved_config = load_saved_config()
    
    if saved_config:
        print("=========================================")
        print("       SATURN-V BOT CONFIGURATION        ")
        print("=========================================")
        print("Found an existing saved configuration:")
        print(f" - Exchange: {saved_config.get('EXCHANGE_NAME')}")
        print(f" - Symbol: {saved_config.get('SYMBOL')}")
        print(f" - Paper Trading: {saved_config.get('IS_PAPER_TRADING')}")
        print(f" - Trade Budget (USDT): {saved_config.get('SPEND_AMOUNT')}")
        print("=========================================")
        
        choice = input("Do you want to use this saved configuration and API details? (y/n) [default: y]: ").strip().lower()
        if choice != 'n':
            print("Using saved configuration...\n")
            return saved_config

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
    
    spend_amount = float(input("Amount to spend per trade in USDT (Quote Currency) [default: 10.0]: ") or 10.0)
    
    profit_target = float(input("Profit Target % [default: 0.5]: ") or 0.5)
    rebuy_drop = float(input("Rebuy Drop % [default: 4.0]: ") or 4.0)
    stop_loss = float(input("Stop Loss % [default: 8.0]: ") or 8.0)
    
    print("=========================================\n")
    
    config = {
        "EXCHANGE_NAME": exchange_name,
        "IS_PAPER_TRADING": is_paper_trading,
        "API_KEY": api_key,
        "API_SECRET": api_secret,
        "API_PASSWORD": api_password,
        "SYMBOL": symbol,
        "SPEND_AMOUNT": spend_amount,
        "PROFIT_TARGET_PERCENT": profit_target,
        "REBUY_DROP_PERCENT": rebuy_drop,
        "STOP_LOSS_PERCENT": stop_loss,
        "CHECK_INTERVAL_SECONDS": 15
    }
    
    save_config(config)
    return config

def get_base_quote_currencies(symbol):
    """Safely extract base and quote currencies from symbol (e.g., KCS/USDT -> KCS, USDT)."""
    parts = symbol.split('/')
    return parts[0], parts[1]

def run_bot(config):
    EXCHANGE_NAME = config["EXCHANGE_NAME"]
    IS_PAPER_TRADING = config["IS_PAPER_TRADING"]
    SYMBOL = config["SYMBOL"]
    SPEND_AMOUNT = config["SPEND_AMOUNT"]
    PROFIT_TARGET_PERCENT = config["PROFIT_TARGET_PERCENT"]
    REBUY_DROP_PERCENT = config["REBUY_DROP_PERCENT"]
    STOP_LOSS_PERCENT = config["STOP_LOSS_PERCENT"]
    CHECK_INTERVAL_SECONDS = 15

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
        if exchange.has.get('sandbox', False):
            try:
                exchange.set_sandbox_mode(True)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PAPER TRADING MODE ENABLED (Sandbox)")
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Notice: Failed to activate sandbox mode: {e}")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WARNING: {EXCHANGE_NAME.upper()} does NOT natively support Sandbox/Paper trading mode via CCXT.")

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
            holding_base = base_balance * current_price > 1.0  
            
            action_logged = "HOLD"
            
            calculated_trade_amount = SPEND_AMOUNT / current_price

            if quote_balance >= SPEND_AMOUNT and not holding_base and entry_price is None:
                try:
                    exchange.create_market_buy_order(SYMBOL, calculated_trade_amount)
                    entry_price = current_price
                    rebuy_count = 0
                    last_buy_time = current_time
                    action_logged = "INITIAL BUY"
                    print(f"[{timestamp_str}] [BUY] Spent ~{SPEND_AMOUNT} {quote_curr} to buy {calculated_trade_amount:.4f} {base_curr} at {current_price}.")
                except ccxt.ExchangeError as ee:
                    print(f"[{timestamp_str}] [ERROR] Exchange rejected order constraint: {ee}")
                    print(f"[{timestamp_str}] [HALT] {EXCHANGE_NAME.upper()} requires a minimum order size or budget for {SYMBOL} greater than {SPEND_AMOUNT} {quote_curr}. Please increase your spend amount.")
                    break

            elif holding_base and entry_price is not None and current_price >= (entry_price * (1 + PROFIT_TARGET_PERCENT / 100)):
                if base_value_quote >= 1.0:
                    try:
                        exchange.create_market_sell_order(SYMBOL, base_balance)
                        print(f"[{timestamp_str}] [SELL] Target +{PROFIT_TARGET_PERCENT}% hit. Sold at {current_price} (Entry was {entry_price})")
                        entry_price = None
                        rebuy_count = 0
                        action_logged = "SELL (Profit)"
                    except ccxt.ExchangeError as ee:
                        print(f"[{timestamp_str}] [ERROR] Exchange rejected sell order: {ee}")
                else:
                    action_logged = f"HOLD ({base_curr} value too low to sell)"

            elif holding_base and entry_price is not None and current_price <= (entry_price * (1 - STOP_LOSS_PERCENT / 100)):
                if base_value_quote >= 1.0:
                    try:
                        exchange.create_market_sell_order(SYMBOL, base_balance)
                        print(f"[{timestamp_str}] [STOP-LOSS] Drop -{STOP_LOSS_PERCENT}% hit. Emergency sell at {current_price} (Entry was {entry_price})")
                        entry_price = None
                        rebuy_count = 0
                        action_logged = "SELL (Stop-Loss)"
                    except ccxt.ExchangeError as ee:
                        print(f"[{timestamp_str}] [ERROR] Exchange rejected stop-loss order: {ee}")
                else:
                    action_logged = "HOLD (Stop-loss hit, but asset value too low to sell)"

            elif holding_base and entry_price is not None and current_price <= (entry_price * (1 - REBUY_DROP_PERCENT / 100)):
                if quote_balance >= SPEND_AMOUNT:
                    if rebuy_count == 0:
                        try:
                            exchange.create_market_buy_order(SYMBOL, calculated_trade_amount)
                            entry_price = current_price
                            rebuy_count = 1
                            last_buy_time = current_time
                            action_logged = "REBUY (1st)"
                            print(f"[{timestamp_str}] [REBUY 1] Drop -{REBUY_DROP_PERCENT}% hit. Spent ~{SPEND_AMOUNT} {quote_curr} at {current_price}")
                        except ccxt.ExchangeError as ee:
                            print(f"[{timestamp_str}] [ERROR] Exchange rejected rebuy order constraint: {ee}")
                            print(f"[{timestamp_str}] [HALT] Check minimum limits or required funds for {SYMBOL} on {EXCHANGE_NAME.upper()}.")
                            break
                    else:
                        cooldown = rebuy_count * 7 * 60  
                        time_elapsed = current_time - last_buy_time
                        
                        if time_elapsed >= cooldown:
                            try:
                                exchange.create_market_buy_order(SYMBOL, calculated_trade_amount)
                                entry_price = current_price
                                rebuy_count += 1
                                last_buy_time = current_time
                                action_logged = f"REBUY ({rebuy_count}th)"
                                print(f"[{timestamp_str}] [REBUY {rebuy_count}] Cooldown passed ({int(time_elapsed)}s). Spent ~{SPEND_AMOUNT} {quote_curr} at {current_price}")
                            except ccxt.ExchangeError as ee:
                                print(f"[{timestamp_str}] [ERROR] Exchange rejected progressive rebuy order: {ee}")
                                break
                        else:
                            action_logged = f"HOLD (Rebuy cooldown active: {int(cooldown - time_elapsed)}s remaining)"
                else:
                    action_logged = f"HOLD (Available {quote_curr} is below allocated spend amount of {SPEND_AMOUNT})"

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
