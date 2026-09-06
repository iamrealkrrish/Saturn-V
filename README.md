# Saturn-V 🚀 Complete Setup & Installation Guide

------------------------------------------------------------------
STEP 1: Install Python
------------------------------------------------------------------
Ensure Python (version 3.8 or higher) is installed on your system. 
- Windows / macOS: Download from the official Python Downloads Page. (On Windows, make sure to check the box that says "Add Python to PATH").
- Linux: Run the following command in your terminal:
  sudo apt update && sudo apt install python3 python3-pip

Verify your installation by running:
python --version
pip --version


------------------------------------------------------------------
STEP 2: Clone the Project Repository
------------------------------------------------------------------
Open your terminal and clone the repository to your local computer, then navigate into the project folder:
git clone https://github.com/your-username/saturn-v.git
cd saturn-v

(Alternatively, if you aren't using Git, create a new folder named "saturn-v" manually and place your "main.py" and "requirements.txt" files inside it).


------------------------------------------------------------------
STEP 3: Install Project Dependencies
------------------------------------------------------------------
Create a file named `requirements.txt` and add:
ccxt>=4.0.0

Then install the required dependencies using pip:
pip install -r requirements.txt


------------------------------------------------------------------
STEP 4: Launch and Configure the Bot
------------------------------------------------------------------
Run the script from your terminal:
python main.py

Follow the interactive configuration prompt to input your exchange settings, API keys, and strategy margins directly on the fly.


------------------------------------------------------------------
PROJECT DESCRIPTION & DISCLAIMER
------------------------------------------------------------------
Saturn-V is your lightweight, interactive launch vehicle for automated crypto spot trading. It features an interactive terminal setup wizard that lets you configure your exchange, API credentials, trading pairs, and risk parameters on the fly without editing source code. 

Disclaimer: Cryptocurrency trading carries a high level of risk and may not be suitable for all investors. Saturn-V is provided strictly for educational and experimental purposes. Always test your strategies extensively using sandbox or paper trading modes before deploying real capital. Use at your own risk.
