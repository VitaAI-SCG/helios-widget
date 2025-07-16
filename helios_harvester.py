# helios_harvester.py (v5.0 - Singularity Edition)
import requests
import json
import urllib.request
from datetime import datetime, timezone, timedelta
import os

# --- CONFIGURATION & DATA SOURCES ---
OUTPUT_FILE = "data.json"
PREVIOUS_DATA_FILE = "data_previous.json"
KRAKEN_API_URL = "https://api.kraken.com/0/public"
# --- HYDRA ENGINE: Primary and Fallback on-chain sources ---
MEMPOOL_API_URL = "https://mempool.space/api"
BLOCKSTREAM_API_URL = "https://blockstream.info/api"
# ---
BINANCE_API_URL = "https://fapi.binance.com/fapi/v1"
BYBIT_API_URL = "https://api.bybit.com/v5/market"

# --- TECHNICAL ANALYSIS ENGINE ---
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(change if change > 0 else 0)
        losses.append(abs(change) if change < 0 else 0)
    avg_gain = sum(gains[:period]) / period; avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# --- LEGENDARY "CHRONOS" AI & SINGULARITY SCORE ---
def calculate_singularity_score(data):
    """Calculates a single 0-100 score for overall network momentum."""
    try:
        # RSI Component (40% weight) - measures momentum
        rsi = data.get("trend_vector", {}).get("rsi_14d", 50)
        rsi_score = rsi if rsi else 50 # Default to 50 if RSI is unavailable

        # Price Trend Component (30% weight) - measures short-term direction
        price_change = data.get("trend_vector", {}).get("price_change_percent", 0)
        # Scale price change to a -10 to +10 range and shift to a 0-100 scale
        price_score = max(0, min(100, 50 + (price_change * 10)))

        # Funding Rate Component (20% weight) - measures speculative sentiment
        funding_rate = data.get("speculative_vector", {}).get("funding_rate", 0)
        # Scale funding rate to a -25 to +25 range and shift to a 0-100 scale
        funding_score = max(0, min(100, 50 + (funding_rate * 50000)))
        
        # Difficulty Change Component (10% weight) - measures long-term network health
        diff_change = data.get("mining_vector", {}).get("difficulty_change_percent", 0)
        diff_score = max(0, min(100, 50 + (diff_change * 5)))

        # Calculate weighted average
        total_score = (rsi_score * 0.40) + (price_score * 0.30) + (funding_score * 0.20) + (diff_score * 0.10)
        return int(total_score)
    except Exception:
        return 50 # Return neutral score on error

def generate_narrative_vector(data, previous_data):
    """Generates the AI insight based on all available data."""
    try:
        rsi = data.get("trend_vector", {}).get("rsi_14d", 50)
        if rsi > 70: return {"insight": f"Market is OVERBOUGHT (RSI: {rsi:.0f}), suggesting downward pressure may build."}
        if rsi < 30: return {"insight": f"Market is OVERSOLD (RSI: {rsi:.0f}), suggesting a potential relief rally."}
        
        price_change = data.get("trend_vector", {}).get("price_change_percent", 0)
        if abs(price_change) > 0.5:
            direction = "surging" if price_change > 0 else "receding"
            return {"insight": f"Financial energy is {direction} with spot-driven volume."}

        return {"insight": "The network is in a state of equilibrium, awaiting a new catalyst."}
    except Exception:
        return {"insight": "Data stream nominal. Awaiting deeper analysis."}

# --- DATA FETCHING ---
def fetch_market_vector():
    try:
        response = requests.get(f"{KRAKEN_API_URL}/Ticker?pair=XBTUSD", headers={"User-Agent": "Helios/5.0"})
        response.raise_for_status(); data = response.json()
        result = data.get("result", {}).get("XXBTZUSD", {})
        return {"price_usd": float(result.get('c', [0])[0])} if result else None
    except Exception as e:
        print(f"[ERROR] Market Vector: {e}"); return None

def fetch_trend_vector(previous_price):
    try:
        response = requests.get(f"{KRAKEN_API_URL}/OHLC?pair=XBTUSD&interval=1440", headers={"User-Agent": "Helios/5.0"})
        response.raise_for_status(); data = response.json()
        result = data.get("result", {}).get("XXBTZUSD", [])
        closing_prices = [float(item[4]) for item in result]
        if not closing_prices: return None
        rsi_14d = calculate_rsi(closing_prices)
        price_change_percent = ((closing_prices[-1] - previous_price) / previous_price) * 100 if previous_price else 0
        return {"rsi_14d": rsi_14d, "historical_prices": closing_prices[-20:], "price_change_percent": price_change_percent}
    except Exception as e:
        print(f"[WARN] Trend Vector: {e}"); return {"rsi_14d": None, "error": True}

def fetch_mining_vector(): # HYDRA ENGINE
    try: # Try primary source first (Mempool)
        req = urllib.request.Request(f"{MEMPOOL_API_URL}/v1/difficulty-adjustment", headers={"User-Agent": "Helios/5.0"})
        with urllib.request.urlopen(req) as r: data = json.loads(r.read().decode('utf-8'))
        return {"difficulty_change_percent": data.get('difficultyChange'), "next_retarget_blocks": data.get('remainingBlocks')}
    except Exception as e:
        print(f"[WARN] Primary mining source failed: {e}. Trying fallback.")
        try: # Try fallback source (Blockstream)
            req = urllib.request.Request(f"{BLOCKSTREAM_API_URL}/difficulty-adjustment", headers={"User-Agent": "Helios/5.0"})
            with urllib.request.urlopen(req) as r: data = json.loads(r.read().decode('utf-8'))
            return {"difficulty_change_percent": data.get('difficultyChange'), "next_retarget_blocks": data.get('remainingBlocks')}
        except Exception as e2:
            print(f"[ERROR] Mining Vector (fallback failed): {e2}"); return None

def calculate_monetary_vector(): # HYDRA ENGINE
    try: # Try primary source first (Mempool)
        response = requests.get(f"{MEMPOOL_API_URL}/blocks/tip/height", headers={"User-Agent": "Helios/5.0"})
        response.raise_for_status(); current_block = int(response.text)
    except Exception as e:
        print(f"[WARN] Primary monetary source failed: {e}. Trying fallback.")
        try: # Try fallback source (Blockstream)
            response = requests.get(f"{BLOCKSTREAM_API_URL}/blocks/tip/height", headers={"User-Agent": "Helios/5.0"})
            response.raise_for_status(); current_block = int(response.text)
        except Exception as e2:
            print(f"[ERROR] Monetary Vector (fallback failed): {e2}"); return None
    
    halvings = current_block // 210000
    total_supply = sum(min(max(0, current_block - i * 210000), 210000) * (50 / (2**i)) for i in range(halvings + 1))
    blocks_until_halving = 210000 - (current_block % 210000)
    return {"circulating_supply": total_supply, "current_block_reward": 50 / (2 ** halvings), "blocks_until_next_halving": blocks_until_halving}

def fetch_speculative_vector():
    try:
        oi_response = requests.get(f"{BYBIT_API_URL}/open-interest?category=linear&symbol=BTCUSDT", headers={"User-Agent": "Helios/5.0"})
        oi_response.raise_for_status()
        open_interest = float(oi_response.json().get("result", {}).get("list", [{}])[0].get("openInterest", 0))
        funding_response = requests.get(f"{BINANCE_API_URL}/premiumIndex?symbol=BTCUSDT", headers={"User-Agent": "Helios/5.0"})
        funding_response.raise_for_status()
        funding_rate = float(funding_response.json().get("lastFundingRate", 0))
        return {"open_interest": open_interest, "funding_rate": funding_rate}
    except Exception as e:
        print(f"[WARN] Speculative Vector: {e}"); return {"open_interest": 0, "funding_rate": 0, "error": True}

def main():
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core with Singularity Engine...")
    previous_data = None
    if os.path.exists(PREVIOUS_DATA_FILE):
        with open(PREVIOUS_DATA_FILE, 'r') as f: previous_data = json.load(f)

    vectors = {
        "market_vector": fetch_market_vector(),
        "mining_vector": fetch_mining_vector(),
        "monetary_vector": calculate_monetary_vector(),
        "speculative_vector": fetch_speculative_vector(),
    }
    
    if not all([vectors["market_vector"], vectors["mining_vector"], vectors["monetary_vector"]]):
        print("[ERROR] Failed to forge one or more CORE vectors. Aborting."); return

    previous_price = previous_data.get("market_vector", {}).get("price_usd") if previous_data else None
    vectors["trend_vector"] = fetch_trend_vector(previous_price)
    vectors["singularity_score"] = calculate_singularity_score(vectors)
    vectors["narrative_vector"] = generate_narrative_vector(vectors, previous_data)
    
    helios_data = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **vectors}
    try:
        with open(OUTPUT_FILE, 'w') as f: json.dump(helios_data, f, indent=4)
        print(f"[SUCCESS] Helios Data Core successfully forged to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write data to file: {e}")

if __name__ == "__main__":
    main()