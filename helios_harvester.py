# helios_harvester.py (v1.4 - Final)
import requests
import json
import urllib.request
from datetime import datetime, timezone, timedelta

# --- CONFIGURATION ---
OUTPUT_FILE = "data.json"

# --- DATA SOURCES ---
KRAKEN_API_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
MEMPOOL_API_URL = "https://mempool.space/api"

# --- CORE LOGIC ---

def fetch_market_vector():
    """
    Fetches the Financial Energy vector: real-time price.
    """
    try:
        response = requests.get(KRAKEN_API_URL, headers={"User-Agent": "Helios/1.0"})
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            print(f"[WARN] Kraken API returned an error: {data['error']}")
            return None
        result = data.get("result", {}).get("XXBTZUSD", {})
        if result:
            return {"price_usd": float(result.get('c', [0])[0])}
        return None
    except Exception as e:
        print(f"[ERROR] Failed to fetch Market Vector: {e}")
        return None

def fetch_mining_vector():
    """
    Fetches the Kinetic Energy vector.
    """
    try:
        difficulty_url = "https://mempool.space/api/v1/difficulty-adjustment"
        req = urllib.request.Request(difficulty_url, headers={"User-Agent": "Helios/1.0"})
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"[ERROR] Mining Vector fetch failed with status code: {response.status}")
                return None
            raw_data = response.read().decode('utf-8')
            difficulty_data = json.loads(raw_data)
        
        # DEFINITIVE FIX: Convert timestamp from milliseconds to seconds
        retarget_timestamp_ms = difficulty_data.get('estimatedRetargetDate', 0)
        retarget_date = datetime.fromtimestamp(retarget_timestamp_ms / 1000, tz=timezone.utc).strftime('%Y-%m-%d')

        return {
            "difficulty_change_percent": difficulty_data.get('difficultyChange'),
            "next_retarget_blocks": difficulty_data.get('remainingBlocks'),
            "estimated_retarget_date": retarget_date
        }
    except Exception as e:
        print(f"[ERROR] Failed to fetch Mining Vector: {e}")
        return None

def calculate_monetary_vector():
    """
    Calculates the Potential Energy vector: scarcity and issuance schedule.
    """
    try:
        INITIAL_BLOCK_REWARD = 50.0
        HALVING_INTERVAL_BLOCKS = 210000

        height_url = f"{MEMPOOL_API_URL}/blocks/tip/height"
        response = requests.get(height_url, headers={"User-Agent": "Helios/1.0"})
        response.raise_for_status()
        current_block = int(response.text)

        halvings = current_block // HALVING_INTERVAL_BLOCKS
        blocks_since_last_halving = current_block % HALVING_INTERVAL_BLOCKS
        
        current_reward = INITIAL_BLOCK_REWARD / (2 ** halvings)
        blocks_until_next_halving = HALVING_INTERVAL_BLOCKS - blocks_since_last_halving

        total_supply = 0
        reward = 50.0
        blocks_remaining_calc = current_block
        while blocks_remaining_calc > 0:
            blocks_in_epoch = min(blocks_remaining_calc, HALVING_INTERVAL_BLOCKS)
            total_supply += blocks_in_epoch * reward
            blocks_remaining_calc -= blocks_in_epoch
            reward /= 2

        return {
            "circulating_supply": total_supply,
            "current_block_reward": current_reward,
            "blocks_until_next_halving": blocks_until_next_halving,
            "next_halving_estimated_date": (datetime.now(timezone.utc) + timedelta(minutes=10 * blocks_until_next_halving)).strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"[ERROR] Failed to calculate Monetary Vector: {e}")
        return None

def main():
    """
    The main execution function. Fetches all vectors and writes to a file.
    """
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core...")

    market_vector = fetch_market_vector()
    mining_vector = fetch_mining_vector()
    monetary_vector = calculate_monetary_vector()

    if not all([market_vector, mining_vector, monetary_vector]):
        print("[ERROR] Failed to forge one or more vectors. Aborting file write.")
        return

    helios_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "market_vector": market_vector,
        "mining_vector": mining_vector,
        "monetary_vector": monetary_vector
    }

    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(helios_data, f, indent=4)
        print(f"[SUCCESS] Helios Data Core successfully forged to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write data to file: {e}")

if __name__ == "__main__":
    main()