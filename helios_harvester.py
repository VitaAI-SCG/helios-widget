# helios_harvester.py (v3.0 - Legendary Edition)
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
BINANCE_API_URL = "https://fapi.binance.com/fapi/v1"
BYBIT_API_URL = "https://api.bybit.com/v5/market"

# --- LEGENDARY "CHRONOS" AI ENGINE ---
def generate_narrative_vector(current_data, previous_data):
    """
    The Legendary Chronos Engine.
    It analyzes the interplay between vectors and the rate of change
    to generate deep, context-aware insights.
    """
    try:
        # --- Extract all current and previous data points safely ---
        current_price = current_data.get("market_vector", {}).get("price_usd", 0)
        spec_vector = current_data.get("speculative_vector", {})
        current_funding = spec_vector.get("funding_rate", 0)
        current_oi = spec_vector.get("open_interest", 0)
        
        mining_vector = current_data.get("mining_vector", {})
        current_diff_change = mining_vector.get("difficulty_change_percent", 0)
        
        monetary_vector = current_data.get("monetary_vector", {})
        blocks_to_halving = monetary_vector.get("blocks_until_next_halving", 210000)
        blocks_to_retarget = mining_vector.get("next_retarget_blocks", 2016)

        # --- Priority 1: High-Significance Network Events ---
        if blocks_to_halving <= 144: # Less than a day
            return {"insight": "HALVING IMMINENT: A fundamental shift in supply issuance is underway."}
        if blocks_to_halving <= 10000:
            return {"insight": "Supply shock incoming. The network is preparing for the halving event."}
        if blocks_to_retarget <= 144: # Less than a day
            return {"insight": f"DIFFICULTY RETARGET IMMINENT: Expecting a {current_diff_change:.2f}% adjustment to network security."}

        # --- Priority 2: Trend & Interplay Analysis (requires previous data) ---
        if previous_data:
            prev_price = previous_data.get("market_vector", {}).get("price_usd", 0)
            prev_spec_vector = previous_data.get("speculative_vector", {})
            prev_oi = prev_spec_vector.get("open_interest", 0) if prev_spec_vector else 0
            
            price_change_percent = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
            oi_change_percent = ((current_oi - prev_oi) / prev_oi) * 100 if prev_oi else 0

            # --- Analyze High Volatility Events ---
            if abs(price_change_percent) > 0.5:
                price_direction = "expanding rapidly" if price_change_percent > 0 else "contracting sharply"
                
                # If Open Interest is also moving, it's a leverage-driven move.
                if abs(oi_change_percent) > 0.5:
                    oi_direction = "surging" if oi_change_percent > 0 else "unwinding"
                    return {"insight": f"Financial energy is {price_direction} as speculative leverage is {oi_direction}."}
                
                # If OI is flat but price is moving, it's spot-driven.
                else:
                    return {"insight": f"A spot-driven move is underway as financial energy is {price_direction} on low speculative volume."}

            # --- Analyze Speculative Divergences ---
            if current_funding > 0.0003 and price_change_percent < -0.1:
                return {"insight": "A leverage flush may be imminent as longs pay high funding amidst falling price."}
            if current_funding < -0.0001 and price_change_percent > 0.1:
                return {"insight": "A potential short squeeze is forming as price rises against negative sentiment."}

        # --- Priority 3: General State (if no major events or trends) ---
        if current_diff_change > 2:
            return {"insight": "The network security posture is hardening during a period of price consolidation."}
        elif current_diff_change < -2:
            return {"insight": "The network is optimizing for efficiency while market energy remains stable."}
        else:
            return {"insight": "A quiet equilibrium persists between network fundamentals and market energy."}

    except Exception as e:
        print(f"[WARN] Legendary Chronos Engine encountered an error: {e}")
        return {"insight": "Data stream nominal. Awaiting deeper analysis."}

# --- DATA FETCHING (No changes needed) ---
def fetch_market_vector():
    try:
        response = requests.get(KRAKEN_API_URL, headers={"User-Agent": "Helios/3.0"})
        response.raise_for_status(); data = response.json()
        if data.get("error"): return None
        result = data.get("result", {}).get("XXBTZUSD", {})
        return {"price_usd": float(result.get('c', [0])[0])} if result else None
    except Exception as e:
        print(f"[ERROR] Failed to fetch Market Vector: {e}"); return None

def fetch_mining_vector():
    try:
        req = urllib.request.Request(f"{MEMPOOL_API_URL}/v1/difficulty-adjustment", headers={"User-Agent": "Helios/3.0"})
        with urllib.request.urlopen(req) as response:
            if response.status != 200: return None
            data = json.loads(response.read().decode('utf-8'))
        retarget_date = datetime.fromtimestamp(data.get('estimatedRetargetDate', 0) / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
        return {"difficulty_change_percent": data.get('difficultyChange'), "next_retarget_blocks": data.get('remainingBlocks'), "estimated_retarget_date": retarget_date}
    except Exception as e:
        print(f"[ERROR] Failed to fetch Mining Vector: {e}"); return None

def calculate_monetary_vector():
    try:
        response = requests.get(f"{MEMPOOL_API_URL}/blocks/tip/height", headers={"User-Agent": "Helios/3.0"})
        response.raise_for_status(); current_block = int(response.text)
        halvings = current_block // 210000
        total_supply = sum(min(max(0, current_block - i * 210000), 210000) * (50 / (2**i)) for i in range(halvings + 1))
        blocks_until_halving = 210000 - (current_block % 210000)
        return {"circulating_supply": total_supply, "current_block_reward": 50 / (2 ** halvings), "blocks_until_next_halving": blocks_until_halving, "next_halving_estimated_date": (datetime.now(timezone.utc) + timedelta(minutes=10 * blocks_until_halving)).strftime('%Y-%m-%d')}
    except Exception as e:
        print(f"[ERROR] Failed to calculate Monetary Vector: {e}"); return None

def fetch_speculative_vector():
    try:
        oi_response = requests.get(f"{BYBIT_API_URL}/open-interest?category=linear&symbol=BTCUSDT", headers={"User-Agent": "Helios/3.0"})
        oi_response.raise_for_status()
        open_interest = float(oi_response.json().get("result", {}).get("list", [{}])[0].get("openInterest", 0))

        funding_response = requests.get(f"{BINANCE_API_URL}/premiumIndex?symbol=BTCUSDT", headers={"User-Agent": "Helios/3.0"})
        funding_response.raise_for_status()
        funding_rate = float(funding_response.json().get("lastFundingRate", 0))
        
        return {"open_interest": open_interest, "funding_rate": funding_rate}
    except Exception as e:
        print(f"[WARN] Could not fetch Speculative Vector: {e}. Proceeding without it.")
        return {"open_interest": 0, "funding_rate": 0, "error": True}

# --- MAIN EXECUTION (No changes needed) ---
def main():
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core with Legendary Chronos Engine...")
    previous_data = None
    if os.path.exists(PREVIOUS_DATA_FILE):
        with open(PREVIOUS_DATA_FILE, 'r') as f:
            previous_data = json.load(f)
    market_vector = fetch_market_vector()
    mining_vector = fetch_mining_vector()
    monetary_vector = calculate_monetary_vector()
    if not all([market_vector, mining_vector, monetary_vector]):
        print("[ERROR] Failed to forge one or more CORE vectors. Aborting."); return
    speculative_vector = fetch_speculative_vector()
    current_data = {"market_vector": market_vector, "mining_vector": mining_vector, "monetary_vector": monetary_vector, "speculative_vector": speculative_vector}
    narrative_vector = generate_narrative_vector(current_data, previous_data)
    helios_data = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **current_data, "narrative_vector": narrative_vector}
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(helios_data, f, indent=4)
        print(f"[SUCCESS] Helios Data Core successfully forged to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write data to file: {e}")

if __name__ == "__main__":
    main()