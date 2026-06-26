import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# Page config
st.set_page_config(page_title="QuantEdge Predictive Engine", layout="wide")

# Persistent Memory
if "cash" not in st.session_state: st.session_state.cash = 10000.00
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "engine_executed" not in st.session_state: st.session_state.engine_executed = False
if "current_market_data" not in st.session_state: st.session_state.current_market_data = None
if "last_analyzed_ticker" not in st.session_state: st.session_state.last_analyzed_ticker = None
if "live_price" not in st.session_state: st.session_state.live_price = 0.0

ASSET_CLASSES = {
    "Equities": {"Apple": "AAPL", "Tesla": "TSLA", "Nvidia": "NVDA", "S&P 500": "SPY"},
    "Crypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Forex": {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X"},
    "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F"}
}

# Sidebar Controls
st.sidebar.header("🕹️ Terminal Controls")
asset_type = st.sidebar.selectbox("Asset Class", list(ASSET_CLASSES.keys()))
asset_name = st.sidebar.selectbox("Select Ticker", list(ASSET_CLASSES[asset_type].keys()))
ticker = ASSET_CLASSES[asset_type][asset_name]
timeframe = st.sidebar.selectbox("Interval", ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour"])
auto_refresh = st.sidebar.toggle("Enable Fast-Sync Loop", value=False)

# Execution Logic
if st.sidebar.button("🔄 Sync Market Data"):
    interval_map = {"1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m", "1 Hour": "1h"}
    period_map = {"1 Minute": "1d", "5 Minutes": "5d", "15 Minutes": "5d", "1 Hour": "60d"}
    
    df = yf.download(ticker, period=period_map[timeframe], interval=interval_map[timeframe], progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        
        # Native Math (Replacement for pandas-ta)
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (df['Close'].diff().clip(lower=0).rolling(14).mean() / -df['Close'].diff().clip(upper=0).rolling(14).mean())))
        
        # Bollinger Bands
        sma = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        df['BBU'] = sma + (std * 2)
        df['BBL'] = sma - (std * 2)
        
        st.session_state.current_market_data = df
        st.session_state.live_price = float(df['Close'].iloc[-1])
        st.session_state.engine_executed = True
        st.session_state.last_analyzed_ticker = ticker

# UI Rendering
if st.session_state.engine_executed and st.session_state.current_market_data is not None:
    df = st.session_state.current_market_data
    curr_p = st.session_state.live_price
    
    st.metric("Live Price", f"${curr_p:,.4f}")
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_9'], name="EMA 9", line=dict(color='yellow')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['BBU'], line=dict(color='gray', dash='dot'), name="Upper Band"))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['BBL'], line=dict(color='gray', dash='dot'), name="Lower Band"))
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Trade Form
    with st.form("trade"):
        qty = st.number_input("Quantity", value=1.0)
        if st.form_submit_button("Buy"):
            st.session_state.portfolio[ticker] = st.session_state.portfolio.get(ticker, 0) + qty
            st.success("Trade Executed")

if auto_refresh:
    time.sleep(5)
    st.rerun()
