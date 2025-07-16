# helios_harvester.py (v4.0 - Legendary Edition)
import requests
import json
import urllib.request
from datetime import datetime, timezone, timedelta
import os

# --- CONFIGURATION & DATA SOURCES ---
OUTPUT_FILE = "data.json"
PREVIOUS_DATA_FILE = "data_previous.json"
KRAKEN_API_URL = "https://api.kraken.com/0/public"
MEMPOOL_API_URL = "https://mempool.space/api"
BINANCE_API_URL = "https://fapi.binance.com/fapi/v1"
BYBIT_API_URL = "https://api.bybit.com/v5/market"

# --- TECHNICAL ANALYSIS ENGINE ---
def calculate_rsi(prices, period=14):
    """Calculates the Relative Strength Index (RSI) from a list of prices."""
    if len(prices) < period + 1:
        return None # Not enough data
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100 # RSI is 100 if there are no losses
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- LEGENDARY "CHRONOS" AI ENGINE ---
def generate_narrative_vector(current_data, previous_data):
    """The Legendary Chronos Engine, now with RSI trend awareness."""
    try:
        # Extract all current data points
        current_price = current_data.get("market_vector", {}).get("price_usd", 0)
        rsi = current_data.get("trend_vector", {}).get("rsi_14d", 50)
        
        # --- Priority 1: RSI Divergences & Extremes (requires previous data) ---
        if previous_data:
            prev_price = previous_data.get("market_vector", {}).get("price_usd", 0)
            price_change_percent = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
            
            if rsi > 75 and price_change_percent < 0.1:
                return {"insight": "BEARISH DIVERGENCE: Upward momentum is exhausted as price stagnates."}
            if rsi < 25 and price_change_percent > -0.1:
                return {"insight": "BULLISH DIVERGENCE: Downward momentum is exhausted as price finds a floor."}

        # --- Priority 2: RSI Extreme Conditions ---
        if rsi > 70:
            return {"insight": f"Market is approaching OVERBOUGHT conditions (RSI: {rsi:.0f}), suggesting caution."}
        if rsi < 30:
            return {"insight": f"Market is entering OVERSOLD territory (RSI: {rsi:.0f}), suggesting potential opportunity."}

        # --- Priority 3: Other High-Significance Events ---
        blocks_to_halving = current_data.get("monetary_vector", {}).get("blocks_until_next_halving", 210000)
        if blocks_to_halving <= 10000:
            return {"insight": "Supply shock incoming. The network is preparing for the halving event."}

        # --- Priority 4: Default State ---
        return {"insight": "The network is in a state of equilibrium, awaiting a new catalyst."}

    except Exception as e:
        print(f"[WARN] Legendary Chronos Engine encountered an error: {e}")
        return {"insight": "Data stream nominal. Awaiting deeper analysis."}

# --- DATA FETCHING ---
def fetch_market_vector():
    try:
        response = requests.get(f"{KRAKEN_API_URL}/Ticker?pair=XBTUSD", headers={"User-Agent": "Helios/4.0"})
        response.raise_for_status(); data = response.json()
        result = data.get("result", {}).get("XXBTZUSD", {})
        return {"price_usd": float(result.get('c', [0])[0])} if result else None
    except Exception as e:
        print(f"[ERROR] Market Vector: {e}"); return None

def fetch_trend_vector():
    """Fetches historical data from Kraken and calculates RSI."""
    try:
        # Fetch last 20 days of price data (1440 minute interval = 1 day)
        response = requests.get(f"{KRAKEN_API_URL}/OHLC?pair=XBTUSD&interval=1440", headers={"User-Agent": "Helios/4.0"})
        response.raise_for_status(); data = response.json()
        result = data.get("result", {}).get("XXBTZUSD", [])
        
        # Extract closing prices
        closing_prices = [float(item[4]) for item in result]
        
        if not closing_prices: return None

        # Calculate 14-day RSI
        rsi_14d = calculate_rsi(closing_prices)
        
        return {"rsi_14d": rsi_14d}
    except Exception as e:
        print(f"[WARN] Trend Vector: {e}"); return {"rsi_14d": None, "error": True}


def fetch_mining_vector():
    try:
        req = urllib.request.Request(f"{MEMPOOL_API_URL}/v1/difficulty-adjustment", headers={"User-Agent": "Helios/4.0"})
        with urllib.request.urlopen(req) as response:
            if response.status != 200: return None
            data = json.loads(response.read().decode('utf-8'))
        retarget_date = datetime.fromtimestamp(data.get('estimatedRetargetDate', 0) / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
        return {"difficulty_change_percent": data.get('difficultyChange'), "next_retarget_blocks": data.get('remainingBlocks'), "estimated_retarget_date": retarget_date}
    except Exception as e:
        print(f"[ERROR] Mining Vector: {e}"); return None

def calculate_monetary_vector():
    try:
        response = requests.get(f"{MEMPOOL_API_URL}/blocks/tip/height", headers={"User-Agent": "Helios/4.0"})
        response.raise_for_status(); current_block = int(response.text)
        halvings = current_block // 210000
        total_supply = sum(min(max(0, current_block - i * 210000), 210000) * (50 / (2**i)) for i in range(halvings + 1))
        blocks_until_halving = 210000 - (current_block % 210000)
        return {"circulating_supply": total_supply, "current_block_reward": 50 / (2 ** halvings), "blocks_until_next_halving": blocks_until_halving, "next_halving_estimated_date": (datetime.now(timezone.utc) + timedelta(minutes=10 * blocks_until_halving)).strftime('%Y-%m-%d')}
    except Exception as e:
        print(f"[ERROR] Monetary Vector: {e}"); return None

def fetch_speculative_vector():
    try:
        oi_response = requests.get(f"{BYBIT_API_URL}/open-interest?category=linear&symbol=BTCUSDT", headers={"User-Agent": "Helios/4.0"})
        oi_response.raise_for_status()
        open_interest = float(oi_response.json().get("result", {}).get("list", [{}])[0].get("openInterest", 0))
        funding_response = requests.get(f"{BINANCE_API_URL}/premiumIndex?symbol=BTCUSDT", headers={"User-Agent": "Helios/4.0"})
        funding_response.raise_for_status()
        funding_rate = float(funding_response.json().get("lastFundingRate", 0))
        return {"open_interest": open_interest, "funding_rate": funding_rate}
    except Exception as e:
        print(f"[WARN] Speculative Vector: {e}"); return {"open_interest": 0, "funding_rate": 0, "error": True}

# --- MAIN EXECUTION ---
def main():
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core with Legendary Chronos Engine...")
    previous_data = None
    if os.path.exists(PREVIOUS_DATA_FILE):
        with open(PREVIOUS_DATA_FILE, 'r') as f: previous_data = json.load(f)

    vectors = {
        "market_vector": fetch_market_vector(),
        "mining_vector": fetch_mining_vector(),
        "monetary_vector": calculate_monetary_vector(),
        "speculative_vector": fetch_speculative_vector(),
        "trend_vector": fetch_trend_vector()
    }

    if not all([vectors["market_vector"], vectors["mining_vector"], vectors["monetary_vector"]]):
        print("[ERROR] Failed to forge one or more CORE vectors. Aborting."); return

    vectors["narrative_vector"] = generate_narrative_vector(vectors, previous_data)
    helios_data = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **vectors}

    try:
        with open(OUTPUT_FILE, 'w') as f: json.dump(helios_data, f, indent=4)
        print(f"[SUCCESS] Helios Data Core successfully forged to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write data to file: {e}")

if __name__ == "__main__":
    main()