# helios_harvester.py (v6.0 - Echo Engine)
import requests
import json
import urllib.request
from datetime import datetime, timezone, timedelta
import os
import math

# --- CONFIGURATION & DATA SOURCES ---
OUTPUT_FILE = "data.json"; PREVIOUS_DATA_FILE = "data_previous.json"
KRAKEN_API_URL = "https://api.kraken.com/0/public"; MEMPOOL_API_URL = "https://mempool.space/api"
BLOCKSTREAM_API_URL = "https://blockstream.info/api"; BINANCE_API_URL = "https://fapi.binance.com/fapi/v1"
BYBIT_API_URL = "https://api.bybit.com/v5/market"

# --- HELIOS ECHO - HISTORICAL ARCHETYPES ---
# A curated memory of significant market structures.
# Each archetype has a representative RSI and Funding Rate.
HISTORICAL_ARCHETYPES = {
    "2021 Bull Peak": {"rsi": 85, "funding": 0.0005, "insight": "Current structure echoes the euphoric '2021 Bull Peak.' Extreme caution is advised."},
    "2022 Bear Bottom": {"rsi": 25, "funding": -0.0002, "insight": "Current structure shows a pattern match to the '2022 Bear Market Bottom.' Maximum opportunity may be present."},
    "Pre-Halving Lull": {"rsi": 55, "funding": 0.0001, "insight": "Current structure mirrors the 'Pre-Halving Lull.' A period of consolidation may precede a supply shock."},
    "COVID Crash": {"rsi": 20, "funding": -0.0005, "insight": "Current structure mirrors the 'COVID Crash' of March 2020. Extreme fear is palpable."}
}

# --- ENGINES ---
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains, losses = [], [];
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

def calculate_singularity_score(data):
    try:
        rsi_score = data.get("trend_vector", {}).get("rsi_14d", 50)
        price_change = data.get("trend_vector", {}).get("price_change_percent", 0)
        price_score = max(0, min(100, 50 + (price_change * 10)))
        funding_rate = data.get("speculative_vector", {}).get("funding_rate", 0)
        funding_score = max(0, min(100, 50 + (funding_rate * 50000)))
        diff_change = data.get("mining_vector", {}).get("difficulty_change_percent", 0)
        diff_score = max(0, min(100, 50 + (diff_change * 5)))
        total_score = (rsi_score * 0.40) + (price_score * 0.30) + (funding_score * 0.20) + (diff_score * 0.10)
        return int(total_score)
    except Exception: return 50

def generate_narrative_vector(data, previous_data):
    try:
        rsi = data.get("trend_vector", {}).get("rsi_14d", 50)
        funding = data.get("speculative_vector", {}).get("funding_rate", 0)
        
        # --- Helios Echo Pattern Matching ---
        for name, archetype in HISTORICAL_ARCHETYPES.items():
            rsi_dist = (rsi - archetype["rsi"])**2
            funding_dist = (funding*1000 - archetype["funding"]*1000)**2 # Scale funding for similar weight
            distance = math.sqrt(rsi_dist + funding_dist)
            if distance < 10: # If a close match is found
                return {"primary": f"ECHO DETECTED: {archetype['insight']}"}

        # --- Standard ALPHA Analyst Briefing (if no echo) ---
        primary_insight = "The objective remains unchanged. Awaiting a new catalyst."
        if rsi > 70: primary_insight = f"Market sentiment is overheated (RSI: {rsi:.0f}). A correction is probable."
        elif rsi < 30: primary_insight = f"Market sentiment is capitulatory (RSI: {rsi:.0f}). An opportunity may be forming."
        return {"primary": primary_insight}
    except Exception as e:
        print(f"[WARN] ALPHA Analyst Engine error: {e}")
        return {"primary": "Mission parameters unclear. Re-evaluating."}

# --- DATA FETCHING (Unchanged from v5.1) ---
def fetch_market_vector():
    try:
        response = requests.get(f"{KRAKEN_API_URL}/Ticker?pair=XBTUSD", headers={"User-Agent": "Helios/6.0"})
        response.raise_for_status(); data = response.json()
        result = data.get("result", {}).get("XXBTZUSD", {})
        return {"price_usd": float(result.get('c', [0])[0])} if result else None
    except Exception as e: print(f"[ERROR] Market Vector: {e}"); return None
def fetch_trend_vector(previous_price):
    try:
        response = requests.get(f"{KRAKEN_API_URL}/OHLC?pair=XBTUSD&interval=1440", headers={"User-Agent": "Helios/6.0"})
        response.raise_for_status(); data = response.json()
        result = data.get("result", {}).get("XXBTZUSD", [])
        closing_prices = [float(item[4]) for item in result]
        if not closing_prices: return None
        rsi_14d = calculate_rsi(closing_prices)
        price_change_percent = ((closing_prices[-1] - previous_price) / previous_price) * 100 if previous_price else 0
        return {"rsi_14d": rsi_14d, "historical_prices": closing_prices[-20:], "price_change_percent": price_change_percent}
    except Exception as e: print(f"[WARN] Trend Vector: {e}"); return {"rsi_14d": None, "error": True}
def fetch_mining_vector():
    try:
        req = urllib.request.Request(f"{MEMPOOL_API_URL}/v1/difficulty-adjustment", headers={"User-Agent": "Helios/6.0"})
        with urllib.request.urlopen(req) as r: data = json.loads(r.read().decode('utf-8'))
        return {"difficulty_change_percent": data.get('difficultyChange'), "next_retarget_blocks": data.get('remainingBlocks')}
    except Exception as e:
        print(f"[WARN] Primary mining source failed: {e}. Trying fallback.")
        try:
            req = urllib.request.Request(f"{BLOCKSTREAM_API_URL}/difficulty-adjustment", headers={"User-Agent": "Helios/6.0"})
            with urllib.request.urlopen(req) as r: data = json.loads(r.read().decode('utf-8'))
            return {"difficulty_change_percent": data.get('difficultyChange'), "next_retarget_blocks": data.get('remainingBlocks')}
        except Exception as e2: print(f"[ERROR] Mining Vector (fallback failed): {e2}"); return None
def calculate_monetary_vector():
    try:
        response = requests.get(f"{MEMPOOL_API_URL}/blocks/tip/height", headers={"User-Agent": "Helios/6.0"})
        response.raise_for_status(); current_block = int(response.text)
    except Exception as e:
        print(f"[WARN] Primary monetary source failed: {e}. Trying fallback.")
        try:
            response = requests.get(f"{BLOCKSTREAM_API_URL}/blocks/tip/height", headers={"User-Agent": "Helios/6.0"})
            response.raise_for_status(); current_block = int(response.text)
        except Exception as e2: print(f"[ERROR] Monetary Vector (fallback failed): {e2}"); return None
    halvings = current_block // 210000; blocks_until_halving = 210000 - (current_block % 210000)
    total_supply = sum(min(max(0, current_block - i * 210000), 210000) * (50 / (2**i)) for i in range(halvings + 1))
    return {"circulating_supply": total_supply, "current_block_reward": 50 / (2 ** halvings), "blocks_until_next_halving": blocks_until_halving}
def fetch_speculative_vector():
    try:
        oi_response = requests.get(f"{BYBIT_API_URL}/open-interest?category=linear&symbol=BTCUSDT", headers={"User-Agent": "Helios/6.0"})
        oi_response.raise_for_status()
        open_interest = float(oi_response.json().get("result", {}).get("list", [{}])[0].get("openInterest", 0))
        funding_response = requests.get(f"{BINANCE_API_URL}/premiumIndex?symbol=BTCUSDT", headers={"User-Agent": "Helios/6.0"})
        funding_response.raise_for_status(); funding_rate = float(funding_response.json().get("lastFundingRate", 0))
        return {"open_interest": open_interest, "funding_rate": funding_rate}
    except Exception as e: print(f"[WARN] Speculative Vector: {e}"); return {"open_interest": 0, "funding_rate": 0, "error": True}
def main():
    print(f"[{datetime.now().isoformat()}] Forging Helios Data Core with Echo Engine...")
    previous_data = None;
    if os.path.exists(PREVIOUS_DATA_FILE):
        with open(PREVIOUS_DATA_FILE, 'r') as f: previous_data = json.load(f)
    vectors = {"market_vector": fetch_market_vector(), "mining_vector": fetch_mining_vector(), "monetary_vector": calculate_monetary_vector(), "speculative_vector": fetch_speculative_vector()}
    if not all([vectors["market_vector"], vectors["mining_vector"], vectors["monetary_vector"]]): print("[ERROR] Failed to forge one or more CORE vectors. Aborting."); return
    previous_price = previous_data.get("market_vector", {}).get("price_usd") if previous_data else None
    vectors["trend_vector"] = fetch_trend_vector(previous_price)
    vectors["singularity_score"] = calculate_singularity_score(vectors)
    vectors["narrative_vector"] = generate_narrative_vector(vectors, previous_data)
    helios_data = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **vectors}
    try:
        with open(OUTPUT_FILE, 'w') as f: json.dump(helios_data, f, indent=4)
        print(f"[SUCCESS] Helios Data Core successfully forged to {OUTPUT_FILE}")
    except Exception as e: print(f"[ERROR] Failed to write data to file: {e}")
if __name__ == "__main__": main()