# helios_harvester.py (v1.5 - Oracle Engine)
import requests
import json
import urllib.request
from datetime import datetime, timezone, timedelta

# --- CONFIGURATION ---
OUTPUT_FILE = "data.json"

# --- DATA SOURCES ---
KRAKEN_API_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
MEMPOOL_API_URL = "https://mempool.space/api"

# --- AI ORACLE LOGIC ---
def generate_narrative_vector(mining_vector, monetary_vector):
    """
    Generates a qualitative insight based on quantitative data.
    """
    try:
        difficulty_change = mining_vector.get('difficulty_change_percent', 0)
        blocks_to_retarget = mining_vector.get('next_retarget_blocks', 2016)
        blocks_to_halving = monetary_vector.get('blocks_until_next_halving', 210000)

        # Priority 1: Halving Event
        if blocks_to_halving <= 10000:
            narrative = "A supply shock is imminent. "
            if difficulty_change > 1:
                narrative += "Network security is hardening in anticipation."
            elif difficulty_change < -1:
                narrative += "Network efficiency is recalibrating ahead of the event."
            else:
                narrative += "Network security remains stable pre-halving."
            return {"insight": narrative}

        # Priority 2: Difficulty Adjustment Event
        if blocks_to_retarget <= 144: # Less than a day away
            narrative = "A difficulty adjustment is imminent. "
            if difficulty_change > 2:
                narrative += "A significant security increase is expected."
            elif difficulty_change < -2:
                narrative += "A significant efficiency gain is expected."
            else:
                narrative += "A minor recalibration is expected."
            return {"insight": narrative}
            
        # Priority 3: General State
        if difficulty_change > 2.5:
            return {"insight": "Financial energy is consolidating as network security hardens significantly."}
        elif difficulty_change < -2.5:
            return {"insight": "Financial energy is consolidating as network efficiency increases."}
        else:
            return {"insight": "Financial energy is consolidating while the network maintains a stable security posture."}

    except Exception as e:
        print(f"[WARN] Failed to generate Narrative Vector: {e}")
        return {"insight": "Data stream nominal. Awaiting deeper analysis."}

# --- CORE LOGIC ---
# (fetch_market_vector, fetch_mining_vector, calculate_monetary_vector remain the same as v1.4)
def fetch_market_vector():
    try:
        response = requests.get(KRAKEN_API_URL, headers={"User-Agent": "Helios/1.0"})
        response.raise_for_status()
        data = response.json()
        if data.get("error"): return None
        result = data.get("result", {}).get("XXBTZUSD", {})
        if result: return {"price_usd": float(result.get('c', [0])[0])}
        return None
    except Exception as e:
        print(f"[ERROR] Failed to fetch Market Vector: {e}")
        return None

def fetch_mining_vector():
    try:
        difficulty_url = "https://mempool.space/api/v1/difficulty-adjustment"
        req = urllib.request.Request(difficulty_url, headers={"User-Agent": "Helios/1.0"})
        with urllib.request.urlopen(req) as response:
            if response.status != 200: return None
            raw_data = response.read().decode('utf-8')
            difficulty_data = json.loads(raw_data)
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
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core with Oracle...")
    market_vector = fetch_market_vector()
    mining_vector = fetch_mining_vector()
    monetary_vector = calculate_monetary_vector()

    if not all([market_vector, mining_vector, monetary_vector]):
        print("[ERROR] Failed to forge one or more primary vectors. Aborting.")
        return

    narrative_vector = generate_narrative_vector(mining_vector, monetary_vector)

    helios_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "market_vector": market_vector,
        "mining_vector": mining_vector,
        "monetary_vector": monetary_vector,
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