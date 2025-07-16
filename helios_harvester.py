# helios_harvester.py (v2.0 - Chronos Engine)
import requests
import json
import urllib.request
from datetime import datetime, timezone, timedelta
import os

# --- CONFIGURATION ---
OUTPUT_FILE = "data.json"
PREVIOUS_DATA_FILE = "data_previous.json"

# --- DATA SOURCES ---
KRAKEN_API_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
MEMPOOL_API_URL = "https://mempool.space/api"
# New data source for Speculative Energy Vector
BINANCE_FUTURES_API_URL = "https://fapi.binance.com/fapi/v1"


# --- AI "CHRONOS" ENGINE ---
def generate_narrative_vector(current_data, previous_data):
    """
    The Chronos Engine: Generates qualitative insight by comparing
    the current state to the previous state.
    """
    insight = "Financial energy is consolidating while the network maintains a stable security posture." # Default
    
    try:
        # --- Extract current data points ---
        current_price = current_data.get("market_vector", {}).get("price_usd", 0)
        current_funding_rate = current_data.get("speculative_vector", {}).get("funding_rate", 0)
        current_open_interest = current_data.get("speculative_vector", {}).get("open_interest", 0)
        current_diff_change = current_data.get("mining_vector", {}).get("difficulty_change_percent", 0)

        # --- If previous data exists, analyze the trend ---
        if previous_data:
            previous_price = previous_data.get("market_vector", {}).get("price_usd", 0)
            price_change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price else 0

            # --- Trend-based Narrative Logic ---
            if abs(price_change_percent) > 0.1: # Significant price movement
                direction = "surging" if price_change_percent > 0 else "receding"
                if current_funding_rate > 0.0002: # High funding
                    insight = f"Financial energy is {direction}, fueled by aggressive speculative sentiment."
                elif current_funding_rate < 0: # Negative funding
                    insight = f"Financial energy is {direction} against prevailing bearish sentiment."
                else:
                    insight = f"Financial energy is {direction} with moderate speculative interest."
            else: # Price is consolidating
                if current_diff_change > 2:
                    insight = "Price is consolidating as network security hardens significantly."
                elif current_diff_change < -2:
                    insight = "Price is consolidating as the network recalibrates for greater efficiency."
                else:
                    insight = "The network is in a state of equilibrium, awaiting a new catalyst."

        # Override with imminent, high-priority events
        blocks_to_halving = current_data.get("monetary_vector", {}).get("blocks_until_next_halving", 210000)
        if blocks_to_halving <= 10000:
            insight = "A supply shock is imminent. Network preparing for the halving event."
            
    except Exception as e:
        print(f"[WARN] Chronos Engine encountered an error: {e}")
        insight = "Data stream nominal. Awaiting deeper analysis."
        
    return {"insight": insight}


# --- DATA FETCHING ---
def fetch_market_vector():
    """Fetches real-time price from Kraken."""
    try:
        response = requests.get(KRAKEN_API_URL, headers={"User-Agent": "Helios/2.0"})
        response.raise_for_status()
        data = response.json()
        if data.get("error"): return None
        result = data.get("result", {}).get("XXBTZUSD", {})
        return {"price_usd": float(result.get('c', [0])[0])} if result else None
    except Exception as e:
        print(f"[ERROR] Failed to fetch Market Vector: {e}")
        return None

def fetch_mining_vector():
    """Fetches network difficulty and retarget data."""
    try:
        difficulty_url = f"{MEMPOOL_API_URL}/v1/difficulty-adjustment"
        req = urllib.request.Request(difficulty_url, headers={"User-Agent": "Helios/2.0"})
        with urllib.request.urlopen(req) as response:
            if response.status != 200: return None
            data = json.loads(response.read().decode('utf-8'))
        retarget_date = datetime.fromtimestamp(data.get('estimatedRetargetDate', 0) / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
        return {
            "difficulty_change_percent": data.get('difficultyChange'),
            "next_retarget_blocks": data.get('remainingBlocks'),
            "estimated_retarget_date": retarget_date
        }
    except Exception as e:
        print(f"[ERROR] Failed to fetch Mining Vector: {e}")
        return None

def calculate_monetary_vector():
    """Calculates supply and halving data."""
    try:
        height_url = f"{MEMPOOL_API_URL}/blocks/tip/height"
        response = requests.get(height_url, headers={"User-Agent": "Helios/2.0"})
        response.raise_for_status()
        current_block = int(response.text)
        
        halvings = current_block // 210000
        total_supply = sum(min(max(0, current_block - i * 210000), 210000) * (50 / (2**i)) for i in range(halvings + 1))
        
        return {
            "circulating_supply": total_supply,
            "current_block_reward": 50 / (2 ** halvings),
            "blocks_until_next_halving": 210000 - (current_block % 210000),
            "next_halving_estimated_date": (datetime.now(timezone.utc) + timedelta(minutes=10 * (210000 - (current_block % 210000)))).strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"[ERROR] Failed to calculate Monetary Vector: {e}")
        return None

def fetch_speculative_vector():
    """Fetches Open Interest and Funding Rate from Binance."""
    try:
        # Fetch Open Interest
        oi_response = requests.get(f"{BINANCE_FUTURES_API_URL}/openInterest?symbol=BTCUSDT", headers={"User-Agent": "Helios/2.0"})
        oi_response.raise_for_status()
        open_interest = float(oi_response.json().get("openInterest", 0))

        # Fetch Funding Rate
        funding_response = requests.get(f"{BINANCE_FUTURES_API_URL}/premiumIndex?symbol=BTCUSDT", headers={"User-Agent": "Helios/2.0"})
        funding_response.raise_for_status()
        funding_rate = float(funding_response.json().get("lastFundingRate", 0))

        return {
            "open_interest": open_interest,
            "funding_rate": funding_rate
        }
    except Exception as e:
        print(f"[ERROR] Failed to fetch Speculative Vector: {e}")
        return None

# --- MAIN EXECUTION ---
def main():
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core with Chronos Engine...")

    # Load previous data for trend analysis
    previous_data = None
    if os.path.exists(PREVIOUS_DATA_FILE):
        with open(PREVIOUS_DATA_FILE, 'r') as f:
            previous_data = json.load(f)

    # Fetch all current data vectors
    market_vector = fetch_market_vector()
    mining_vector = fetch_mining_vector()
    monetary_vector = calculate_monetary_vector()
    speculative_vector = fetch_speculative_vector()

    if not all([market_vector, mining_vector, monetary_vector, speculative_vector]):
        print("[ERROR] Failed to forge one or more primary vectors. Aborting.")
        return

    # Combine current data for the AI
    current_data = {
        "market_vector": market_vector,
        "mining_vector": mining_vector,
        "monetary_vector": monetary_vector,
        "speculative_vector": speculative_vector
    }

    # Generate the AI narrative
    narrative_vector = generate_narrative_vector(current_data, previous_data)

    # Assemble the final data object
    helios_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **current_data,
        "narrative_vector": narrative_vector
    }

    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(helios_data, f, indent=4)
        print(f"[SUCCESS] Helios Data Core successfully forged to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write data to file: {e}")

if __name__ == "__main__":
    main()