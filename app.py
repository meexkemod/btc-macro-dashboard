import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Terminal HF - BTC Macro Dashboard")

# ===================== FUNGSI AMBIL DATA ===================== #

@st.cache_data(ttl=300)
def get_candles():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "Time", "Open", "High", "Low", "Close", "Volume",
        "CloseTime", "QuoteAssetVolume", "NumberOfTrades",
        "TakerBuyBaseVol", "TakerBuyQuoteVol", "Ignore"
    ])
    df["Time"] = pd.to_datetime(df["Time"], unit="ms")
    df[["Open", "High", "Low", "Close", "Volume"]] = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    df["deltaVol"] = df["Volume"].diff().fillna(0)
    df["CVD"] = df["deltaVol"].cumsum()
    return df

@st.cache_data(ttl=300)
def get_oi():
    url = "https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=100"
    data = requests.get(url).json()
    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["sumOpenInterest"] = df["sumOpenInterest"].astype(float)
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_funding():
    url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=100"
    data = requests.get(url).json()
    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        df["fundingTime"] = pd.to_datetime(df["fundingTime"], unit="ms")
        df["fundingRate"] = df["fundingRate"].astype(float)
        return df
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_depth():
    url = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=100"
    data = requests.get(url).json()
    if "bids" in data and "asks" in data:
        bids = pd.DataFrame(data["bids"], columns=["price", "quantity"], dtype=float)
        asks = pd.DataFrame(data["asks"], columns=["price", "quantity"], dtype=float)
        return bids, asks
    return pd.DataFrame(), pd.DataFrame()

# ===================== TARIK DATA ===================== #

st.title("📊 Terminal HF: BTC Macro Dashboard")
st.caption("Live data from Binance | Built by Mee & Kemod 💼")

df_k = get_candles()
df_oi = get_oi()
df_f = get_funding()
bids, asks = get_depth()

# ===================== PLOT ===================== #
fig, axs = plt.subplots(3, 2, figsize=(15, 12))

# 1. Candlestick Close
if not df_k.empty:
    axs[0, 0].plot(df_k["Time"], df_k["Close"], color="black")
axs[0, 0].set_title("BTCUSDT 1H Close Price")
axs[0, 0].grid(True)

# 2. Open Interest
if not df_oi.empty:
    axs[0, 1].plot(df_oi["timestamp"], df_oi["sumOpenInterest"], color="orange")
axs[0, 1].set_title("Open Interest (5m)")
axs[0, 1].grid(True)

# 3. Funding Rate
if not df_f.empty:
    axs[1, 0].plot(df_f["fundingTime"], df_f["fundingRate"], color="blue")
axs[1, 0].set_title("Funding Rate (8h)")
axs[1, 0].grid(True)

# 4. Order Book Depth
if not bids.empty and not asks.empty:
    axs[1, 1].plot(bids["price"], bids["quantity"], label="Bids", color="green")
    axs[1, 1].plot(asks["price"], asks["quantity"], label="Asks", color="red")
    axs[1, 1].legend()
axs[1, 1].set_title("Order Book Depth")
axs[1, 1].grid(True)

# 5. CVD
if not df_k.empty and "CVD" in df_k:
    axs[2, 0].plot(df_k["Time"], df_k["CVD"], color="purple")
axs[2, 0].set_title("CVD (Delta Volume)")
axs[2, 0].grid(True)

# 6. Kosongin slot terakhir
axs[2, 1].axis("off")

plt.tight_layout()
st.pyplot(fig)
