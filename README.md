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
------------------------------------------------------------------
STEP 1: Install Python
------------------------------------------------------------------
Ensure Python (version 3.8 or higher) is installed on your system. 
- Windows / macOS: Download from the official Python Downloads Page. (On Windows, make sure to check the box that says "Add Python to PATH").
- Linux: Run the following command in your terminal:
  
  ```
  sudo apt update && sudo apt install python python-pip

Verify your installation by running:
  ```
  python --version
  pip --version
  ```         

------------------------------------------------------------------
## STEP 2: Clone the Project Repository
------------------------------------------------------------------
Open your terminal and clone the repository to your local computer, then navigate into the project folder:
( Go to the folder you need to put bot files in / do mkdir saturn to make a folder )

```
  git clone https://github.com/iamrealkrrish/saturn-v.git
  chmod +x *
  cd saturn-v
```
(Alternatively, if you aren't using Git, create a new folder named "saturn-v" manually and place your "saturn.py" and "requirements.txt" files inside it).


------------------------------------------------------------------
STEP 3: Install Project Dependencies
------------------------------------------------------------------
install the required dependencies using pip:

```
  pip install -r requirements.txt
```
if pip didn't work then:

```
  python -m pip install -r requirements.txt
```

------------------------------------------------------------------
STEP 4: Launch and Configure the Bot
------------------------------------------------------------------
Run the script from your terminal:

```
  python saturn.py
```
Follow the interactive configuration prompt to input your exchange settings, API keys, and strategy margins directly on the fly.


------------------------------------------------------------------
PROJECT DESCRIPTION & DISCLAIMER
------------------------------------------------------------------
Saturn-V is your lightweight, interactive launch vehicle for automated crypto spot trading. It features an interactive terminal setup wizard that lets you configure your exchange, API credentials, trading pairs, and risk parameters on the fly without editing source code. 

Disclaimer: Cryptocurrency trading carries a high level of risk and may not be suitable for all investors. Saturn-V is provided strictly for educational and experimental purposes. Always test your strategies extensively using sandbox or paper trading modes before deploying real capital. Use at your own risk.
