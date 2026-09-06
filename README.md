# Saturn-V 🚀

Your multi-stage launch vehicle for automated crypto spot trading. 

---

## Overview

**Saturn-V** is a lightweight, interactive automated spot trading bot built with Python and CCXT. Designed for simplicity and control, it features an interactive terminal setup wizard that lets you configure your exchange, API credentials, trading pairs, and risk parameters on the fly without ever editing the source code.

Whether you're executing small test hops in sandbox mode or aiming for escape velocity in live markets, Saturn-V handles continuous market monitoring, target profit-taking, strict stop-loss measures, and a smart DCA rebuy loop.

---

## Key Features

* **Interactive Setup Wizard:** Configurable directly from your terminal upon launch with smart defaults.
* **Multi-Exchange Support:** Plugs into any exchange supported by CCXT (e.g., Binance, KuCoin, Kraken, Coinbase).
* **Paper / Live Trading Modes:** Test your strategies safely using exchange sandbox/paper trading modes before risking real capital.
* **Advanced Risk Management:** Built-in target profit limits, hard stop-losses, and progressive cooldown DCA rebuys for dip accumulation.

---

## Step-by-Step Setup & Installation

### Step 1: Install Python
Ensure Python (version 3.8 or higher) is installed on your system. 
* **Windows / macOS:** Download from the [Python Downloads Page](https://www.python.org/downloads/). *(On Windows, check "Add Python to PATH").*
* **Linux:** Run `sudo apt update && sudo apt install python3 python3-pip`

Verify installation:
```bash
python --version
pip --version





### Step 2: Clone the Project Repository
