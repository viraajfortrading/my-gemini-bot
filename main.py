import os
import json
from google import genai
from google.genai import types
import alpaca_trade_api as tradeapi

# Connect to the tools using the secret codes we will set up in Render
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = 'https://alpaca.markets' 

# Initialize the brains and bank accounts
ai_client = genai.Client(api_key=GEMINI_API_KEY)
alpaca = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

TICKER = "AAPL" # The bot will track Apple stock. You can change this later.

def run_bot():
    print("Step 1: Fetching stock price data from Alpaca...")
    bars = alpaca.get_bars(TICKER, tradeapi.TimeFrame.Day, limit=5).df
    
    market_data = ""
    for index, row in bars.iterrows():
        market_data += f"Date: {index.date()}, Close Price: ${row['close']}, Volume: {row['volume']}\n"
        
    print("Step 2: Sending data to Gemini for analysis...")
    prompt = f"Analyze this recent stock data for {TICKER}:\n{market_data}\nDecide to BUY, SELL, or HOLD. Respond strictly in this JSON format: {{'action': 'BUY' or 'SELL' or 'hold', 'reasoning': 'why'}}"
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    
    decision = json.loads(response.text)
    action = decision.get("action").upper()
    print(f"Gemini Decision: {action} because {decision.get('reasoning')}")
    
    print("Step 3: Executing order at the brokerage...")
    if "BUY" in action:
        alpaca.submit_order(symbol=TICKER, qty=1, side='buy', type='market', time_in_force='gtc')
        print("Success: Bought 1 share.")
    elif "SELL" in action:
        try:
            alpaca.get_position(TICKER)
            alpaca.submit_order(symbol=TICKER, qty=1, side='sell', type='market', time_in_force='gtc')
            print("Success: Sold 1 share.")
        except:
            print("Gemini said SELL, but you don't own any shares right now. Doing nothing.")
    else:
        print("Gemini said HOLD. No trades made today.")

if __name__ == "__main__":
    run_bot()
