import requests
import time
import hmac
import hashlib
import logging
import pandas as pd
import config  # ✅ Usa config.py invece di config.json

# ✅ Configurazione API
API_KEY = config.API_KEY
API_SECRET = config.API_SECRET
BASE_URL = config.BASE_URL
MAX_RETRIES = 3  # Numero massimo di tentativi in caso di errore

print(f"🔑 API_KEY: {API_KEY[:5]}****")  # Mostra solo le prime cifre
print(f"🔐 API_SECRET: {API_SECRET[:5]}****")
print(f"🌍 BASE_URL: {BASE_URL}")

# 📌 Funzione per generare firma API v5
def generate_signature(params, secret):
    """ Genera la firma richiesta per l'autenticazione API di Bybit v5. """
    sorted_params = sorted(params.items())
    query_string = "&".join(f"{key}={value}" for key, value in sorted_params)
    return hmac.new(bytes(secret, "utf-8"), bytes(query_string, "utf-8"), hashlib.sha256).hexdigest()

# 📌 Funzione per eseguire richieste API con firma HMAC per autenticazione
def make_request(endpoint, params=None, method="GET", requires_auth=False):
    """ Esegue richieste API a Bybit con gestione degli errori e firma quando necessaria. """
    if params is None:
        params = {}

    headers = {"Content-Type": "application/json"}

    if requires_auth:
        params["apiKey"] = API_KEY
        params["timestamp"] = str(int(time.time() * 1000))
        params["sign"] = generate_signature(params, API_SECRET)
        headers["X-BYBIT-API-KEY"] = API_KEY

    url = f"{BASE_URL}{endpoint}"

    for attempt in range(MAX_RETRIES):
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=params, headers=headers, timeout=10)

            if response.status_code == 401:
                print(f"🚫 Errore 401: API Key non valida o permessi insufficienti su {endpoint}")
                return None

            if response.status_code != 200:
                print(f"⚠️ Errore API {endpoint}: {response.status_code} - {response.text}")
                time.sleep(2)
                continue  # Riprova la richiesta

            data = response.json()
            if "retCode" in data and data["retCode"] != 0:
                print(f"⚠️ Errore API Bybit: {data['retMsg']}")
                return None

            return data

        except requests.exceptions.Timeout:
            print(f"⏳ Timeout nella richiesta a {url}, tentativo {attempt + 1} di {MAX_RETRIES}")
        except requests.exceptions.ConnectionError:
            print(f"🚫 Errore di connessione a {url}, tentativo {attempt + 1} di {MAX_RETRIES}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore generico: {e}")
            return None

    print(f"❌ Errore API non risolto dopo {MAX_RETRIES} tentativi. Skipping request.")
    return None

# 📌 Recupera il saldo disponibile in USDT
def get_balance():
    """ Recupera il saldo disponibile in USDT per calcolare il rischio per operazione. """
    endpoint = "/v5/account/wallet-balance"
    params = {"accountType": "UNIFIED"}
    response = make_request(endpoint, params, requires_auth=True)

    if response and "result" in response and "list" in response["result"]:
        for asset in response["result"]["list"][0]["coin"]:
            if asset["coin"] == "USDT":
                balance = float(asset["walletBalance"])
                print(f"💰 Saldo USDT disponibile: {balance}")
                return balance

    print("⚠️ Errore: Impossibile ottenere il saldo. Controlla le API Key e i permessi.")
    return 0.0

# 📌 Recupera le coppie future disponibili su Bybit
def get_filtered_pairs():
    """ Recupera tutte le coppie future disponibili e le filtra per volume alto. """
    endpoint = "/v5/market/tickers"
    params = {"category": "linear"}

    response = make_request(endpoint, params)

    if not response or "result" not in response or "list" not in response["result"]:
        print("⚠️ Nessun dato ricevuto per le coppie future.")
        return []

    print(f"🔍 Debug API Bybit (Prime 5 coppie): {response['result']['list'][:5]}")

    pairs = []
    for item in response["result"]["list"]:
        try:
            volume = float(item.get("turnover24h", item.get("volume24h", 0)))  
            if volume > 1000000:  
                pairs.append(item["symbol"])
        except KeyError as e:
            print(f"⚠️ Errore: Chiave mancante nella risposta API {e}")

    print(f"✅ Coppie selezionate dopo il filtro: {pairs}")
    return pairs

# 📌 Recupera dati storici per un simbolo
def get_historical_data(symbol, timeframe="5"):
    """ Recupera i dati storici di un simbolo per il trading e l'AI. """
    endpoint = "/v5/market/kline"
    params = {
        "symbol": symbol,
        "interval": timeframe,
        "category": "linear",
        "limit": 200  
    }

    response = make_request(endpoint, params)

    if not response or "result" not in response or "list" not in response["result"]:
        print(f"⚠️ Nessun dato trovato per {symbol} nel timeframe {timeframe}.")
        return None

    print(f"🔍 Debug API Bybit {symbol}: {response['result']['list'][:3]}")

    df = pd.DataFrame(response["result"]["list"], columns=[
        "open_time", "open", "high", "low", "close", "volume", "turnover"
    ])

    df["open_time"] = pd.to_datetime(df["open_time"].astype(float), unit="ms")
    df[["open", "high", "low", "close", "volume", "turnover"]] = df[[
        "open", "high", "low", "close", "volume", "turnover"
    ]].astype(float)

    return df

# 📌 Recupera dati live di una coppia
def get_live_data(symbol):
    """ Recupera i dati di mercato più recenti per una determinata coppia. """
    endpoint = "/v5/market/tickers"
    params = {"symbol": symbol, "category": "linear"}

    response = make_request(endpoint, params)

    if not response or "result" not in response or "list" not in response["result"]:
        print(f"⚠️ Nessun dato live ricevuto per {symbol}. Verifica se il simbolo è corretto e disponibile.")
        return None

    latest = response["result"]["list"][0]

    return {
        "open": float(latest["prevPrice24h"]),
        "high": float(latest["highPrice24h"]),
        "low": float(latest["lowPrice24h"]),
        "close": float(latest["lastPrice"]),
        "volume": float(latest["volume24h"]),
        "turnover": float(latest["turnover24h"])
    }

# 📌 Recupera il numero di posizioni aperte
def get_open_trades():
    """
    Ottiene l'elenco delle posizioni aperte per limitare il numero massimo di trade.
    """
    endpoint = "/v5/position/list"
    params = {
        "category": "linear",
        "accountType": "UNIFIED"  # ✅ FIX: Aggiunto accountType per Unified Trading Account
    }

    response = make_request(endpoint, params, method="GET")

    if not response or "result" not in response:
        print("🚫 Errore 401: API Key non valida o permessi insufficienti su /v5/position/list")
        return 0

    open_positions = response["result"].get("list", [])
    return len(open_positions)  # ✅ Restituisce il numero di trade aperti
