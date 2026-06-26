import streamlit as str
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

# Page configuration
str.set_page_config(page_title="Institutional Verdict Engine", layout="wide")

# 1. Navigation Tabs for a Clean User Experience
tab1, tab2, tab3 = str.tabs(["📖 How to Use", "⚡ Live Verdict Engine", "⚠️ Legal Disclaimer"])

# ==========================================
# TAB 1: HOW TO USE
# ==========================================
with tab1:
    str.header("Welcome to the Multi-Asset Verdict Engine")
    str.write("""
    This application functions as a technical consensus engine, aggregating mathematical indicators 
    across ultra-short timeframes to determine statistical momentum for Forex, Crypto, and Commodities.
    """)
    
    str.subheader("Getting Started in 3 Steps:")
    str.markdown("""
    1. **Navigate to the Live Engine:** Click on the **Live Verdict Engine** tab above.
    2. **Configure Your Market:** Use the sidebar to select your asset class (e.g., Cryptocurrency) and specific ticker symbol.
    3. **Select Your Timeframe:** Choose an interval (e.g., 1 Minute or 5 Minutes). The system will pull the last 50-100 data points to run calculations.
    """)
    
    str.subheader("Understanding the Consensus Metric:")
    str.write("""
    The system cross-references three distinct trading methodologies:
    * **Moving Average Convergence Divergence (MACD):** Measures asset velocity and trend direction.
    * **Relative Strength Index (RSI):** Evaluates if an asset is being overbought (potential drop) or oversold (potential bounce).
    * **Simple Moving Average Cross (SMA):** Identifies short-term structural support.
    """)

# ==========================================
# TAB 3: DISCLAIMER (Placed structurally before logic)
# ==========================================
with tab3:
    str.header("Risk Disclosure & Disclaimer")
    str.warning("""
    **IMPORTANT NOTICE PLEASE READ CAREFULLY:**
    
    The trading of financial instruments, including foreign exchange (Forex), cryptocurrencies, and commodities, involves high risk and may not be suitable for all investors. 
    
    * **Not Financial Advice:** The information, mathematical models, consensus scores, and individual tool directions presented within this application are for educational and informational purposes only. They do not constitute financial, investment, or trading advice.
    * **Data Lag:** Intraday data pulled via public endpoints is subject to provider delays and network latency. Never execute real-time trades based strictly on delayed tracking software.
    * **No Accuracy Guarantees:** Past performance is zero guarantee of future market results. High-frequency market fluctuations are highly volatile and inherently unpredictable. The developer assumes no liability for financial losses incurred.
    """)

# ==========================================
# TAB 2: LIVE VERDICT ENGINE
# ==========================================
with tab2:
    # Asset Configuration Dictionary
    ASSET_CLASSES = {
        "Cryptocurrency": {"Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD"},
        "Forex": {"EUR / USD": "EURUSD=X", "GBP / USD": "GBPUSD=X"},
        "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F"}
    }

    # Sidebar inputs specifically inside this context
    str.sidebar.header("Market Selection")
    asset_type = str.sidebar.selectbox("Select Asset Class", list(ASSET_CLASSES.keys()))
    asset_name = str.sidebar.selectbox("Select Ticker", list(ASSET_CLASSES[asset_type].keys()))
    ticker = ASSET_CLASSES[asset_type][asset_name]

    timeframe = str.sidebar.selectbox("Interval Timeframe", ["1 Minute", "5 Minutes", "1 Hour"])
    
    # Auto-refresh interval adjustment to prevent API banning
    refresh_rate = str.sidebar.slider("Auto-Refresh Rate (Seconds)", min_value=5, max_value=60, value=10)

    interval_mapping = {
        "1 Minute": {"int": "1m", "period": "5d"},
        "5 Minutes": {"int": "5m", "period": "5d"},
        "1 Hour": {"int": "1h", "period": "730d"}
    }

    # Fetch Intraday Data
    def fetch_live_data(symbol, interval, period):
        try:
            # We bypass traditional caching here to force fresh data pulls on refresh
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty:
                return None
            data.reset_index(inplace=True)
            return data
        except Exception:
            return None

    chosen_interval = interval_mapping[timeframe]["int"]
    chosen_period = interval_mapping[timeframe]["period"]
    df = fetch_live_data(ticker, chosen_interval, chosen_period)

    if df is not None and len(df) > 50:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Calculate Technical Indicators
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Extract latest values
        latest_row = df.iloc[-1]
        current_price = float(latest_row['Close'])
        current_rsi = float(latest_row['RSI']) if not pd.isna(latest_row['RSI']) else 50.0
        current_macd = float(latest_row['MACD'])
        current_signal = float(latest_row['Signal_Line'])
        current_sma20 = float(latest_row['SMA_20'])
        current_sma50 = float(latest_row['SMA_50'])

        # Verdict Algorithm Engine
        votes = 0
        
        ma_verdict = "Neutral"
        if current_sma20 > current_sma50:
            ma_verdict = "Bullish (Buy)"
            votes += 1
        elif current_sma20 < current_sma50:
            ma_verdict = "Bearish (Sell)"
            votes -= 1
            
        rsi_verdict = "Neutral"
        if current_rsi < 30:
            rsi_verdict = "Oversold (Buy)"
            votes += 1
        elif current_rsi > 70:
            rsi_verdict = "Overbought (Sell)"
            votes -= 1
            
        macd_verdict = "Neutral"
        if current_macd > current_signal:
            macd_verdict = "Bullish Cross (Buy)"
            votes += 1
        elif current_macd < current_signal:
            macd_verdict = "Bearish Cross (Sell)"
            votes -= 1

        if votes >= 2:
            final_verdict = "STRONG BUY 🟢"
        elif votes == 1:
            final_verdict = "MODERATE BUY 📈"
        elif votes == -1:
            final_verdict = "MODERATE SELL 📉"
        elif votes <= -2:
            final_verdict = "STRONG SELL 🔴"
        else:
            final_verdict = "NEUTRAL ✖️"

        # UI Layout Elements
        str.subheader(f"Live Feed: {asset_name} ({ticker})")
        str.caption(f"Last updated status at: {datetime.now().strftime('%H:%M:%S')}")

        col1, col2, col3 = str.columns(3)
        col1.metric("Current Asset Price", f"${current_price:,.4f}")
        col2.metric("Consensus Net Score", f"{votes} / 3")
        col3.metric("Mathematical Verdict", final_verdict)

        # Charts
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        time_col = df['Datetime'] if 'Datetime' in df else df['Date']
        
        fig.add_trace(go.Candlestick(x=time_col, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candlestick"), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_col, y=df['SMA_20'], name="20 SMA"), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_col, y=df['SMA_50'], name="50 SMA"), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_col, y=df['RSI'], name="RSI (14)", line=dict(color='purple')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_white", margin=dict(t=20, b=20))
        str.plotly_chart(fig, use_container_width=True)

        # Execution Logs and Tables
        str.subheader("Indicators Breakdown Matrix")
        verdict_data = {
            "Analytical Sub-System": ["Moving Average Cross", "Relative Strength Index", "MACD Momentum Engine"],
            "Calculated State": [f"SMA20: {current_sma20:.4f} / SMA50: {current_sma50:.4f}", f"RSI Value: {current_rsi:.2f}", f"MACD Difference: {(current_macd - current_signal):.4f}"],
            "Sub-Verdict Action": [ma_verdict, rsi_verdict, macd_verdict]
        }
        str.table(pd.DataFrame(verdict_data))

    else:
        str.error("Market is currently closed or API rate limits have been temporarily exceeded. Retrying...")

    # Infinite Loop implementation for Auto-Rerun synchronization
    time.sleep(refresh_rate)
    str.rerun()
