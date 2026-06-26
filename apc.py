import streamlit as str
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Page configuration
str.set_page_config(page_title="Advanced Consensus Engine", layout="wide")

# Navigation Tabs
tab1, tab2, tab3 = str.tabs(["⚡ Live Verdict Engine", "📖 System Documentation", "⚠️ Risk Disclaimer"])

# Global Asset Inventory
ASSET_CLASSES = {
    "Cryptocurrency": {"Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (SOL)": "SOL-USD"},
    "Forex": {"EUR / USD": "EURUSD=X", "GBP / USD": "GBPUSD=X", "USD / JPY": "JPY=X"},
    "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F", "Silver": "SI=F"}
}

# ==========================================
# SIDEBAR CONTROL PANEL
# ==========================================
str.sidebar.header("🎛️ Control Panel")

# Create a clean form layout for execution settings
with str.sidebar.form(key="config_form"):
    asset_type = str.selectbox("Asset Class", list(ASSET_CLASSES.keys()))
    asset_name = str.selectbox("Select Ticker", list(ASSET_CLASSES[asset_type].keys()))
    ticker = ASSET_CLASSES[asset_type][asset_name]
    
    timeframe = str.selectbox("Interval Timeframe", ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour"])
    
    # The manual execute button requested
    submit_button = str.form_submit_button(label="🚀 Execute Analysis", use_container_width=True)

interval_mapping = {
    "1 Minute": {"int": "1m", "period": "2d"},
    "5 Minutes": {"int": "5m", "period": "5d"},
    "15 Minutes": {"int": "15m", "period": "5d"},
    "1 Hour": {"int": "1h", "period": "730d"}
}

# ==========================================
# TAB 1: LIVE VERDICT ENGINE
# ==========================================
with tab1:
    str.title("📊 Real-Time Multi-Tool Verdict Engine")
    
    # Banner showing running ticker prices for reference
    str.markdown("### 🏪 Live Market Watch")
    ticker_cols = str.columns(3)
    
    # Fast background data pull to build a continuous ticker ribbon
    def get_ticker_summary(symbol):
        try:
            t_data = yf.Ticker(symbol).history(period="1d")
            if not t_data.empty:
                return float(t_data['Close'].iloc[-1])
            return 0.0
        except:
            return 0.0

    with str.spinner("Refreshing market watch ribbon..."):
        btc_p = get_ticker_summary("BTC-USD")
        eur_p = get_ticker_summary("EURUSD=X")
        gold_p = get_ticker_summary("GC=F")
        
    ticker_cols[0].metric("BTC/USD Ticker", f"${btc_p:,.2f}" if btc_p > 0 else "Offline")
    ticker_cols[1].metric("EUR/USD Ticker", f"${eur_p:,.4f}" if eur_p > 0 else "Offline")
    ticker_cols[2].metric("Gold Futures Ticker", f"${gold_p:,.2f}" if gold_p > 0 else "Offline")
    
    str.divider()

    # Trigger action only when the Execute form button is manually pressed
    if submit_button:
        with str.status(f"Running multi-indicator analysis matrix for {asset_name}...", expanded=True) as status:
            str.write("Connecting to data streams...")
            chosen_interval = interval_mapping[timeframe]["int"]
            chosen_period = interval_mapping[timeframe]["period"]
            
            df = yf.download(ticker, period=chosen_period, interval=chosen_interval, progress=False)
            
            if df is not None and len(df) > 50:
                str.write("Cleaning structures and compiling math models...")
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Math Indicators Engine
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
                
                latest_row = df.iloc[-1]
                current_price = float(latest_row['Close'])
                current_rsi = float(latest_row['RSI']) if not pd.isna(latest_row['RSI']) else 50.0
                current_macd = float(latest_row['MACD'])
                current_signal = float(latest_row['Signal_Line'])
                current_sma20 = float(latest_row['SMA_20'])
                current_sma50 = float(latest_row['SMA_50'])
                
                # Evaluation Metrics
                votes = 0
                reasons = []
                
                if current_sma20 > current_sma50:
                    votes += 1
                    reasons.append("Short-term momentum is upward (20 SMA crossed above 50 SMA).")
                else:
                    votes -= 1
                    reasons.append("Short-term momentum is downward (20 SMA tracking below 50 SMA).")
                    
                if current_rsi < 30:
                    votes += 1
                    reasons.append("Asset conditions show oversold extreme (RSI below 30), suggesting a potential near-term reversal upward.")
                elif current_rsi > 70:
                    votes -= 1
                    reasons.append("Asset conditions show overbought extreme (RSI above 70), indicating a risk of near-term exhaustion.")
                else:
                    reasons.append(f"RSI momentum stays neutral at {current_rsi:.2f} within standard bounds.")
                    
                if current_macd > current_signal:
                    votes += 1
                    reasons.append("MACD line crossed above the signal line, issuing a bullish structural trigger.")
                else:
                    votes -= 1
                    reasons.append("MACD line crossed below the signal line, verifying bearish structural selling pressure.")

                status.update(label="Analysis complete!", state="complete", expanded=False)
                
                # Display Results Panels Dynamically
                str.subheader(f"Analysis Summary: {asset_name} ({timeframe} View)")
                
                # Visual Verdict Block Callouts
                if votes >= 2:
                    str.success(f"### FINAL VERDICT: STRONG BUY (Score: {votes}/3)")
                elif votes == 1:
                    str.info(f"### FINAL VERDICT: MODERATE BUY (Score: {votes}/3)")
                elif votes == -1:
                    str.warning(f"### FINAL VERDICT: MODERATE SELL (Score: {votes}/3)")
                elif votes <= -2:
                    str.error(f"### FINAL VERDICT: STRONG SELL (Score: {votes}/3)")
                else:
                    str.markdown("### FINAL VERDICT: NEUTRAL TRACKING (Score: 0/3)")
                
                # Display explicit reasoning
                str.markdown("#### 🧠 Verdict Rationale & Reasoning Breakdown")
                for r in reasons:
                    str.markdown(f"- {r}")

                # Charts Render
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                time_col = df['Datetime'] if 'Datetime' in df else df['Date']
                
                fig.add_trace(go.Candlestick(x=time_col, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candles"), row=1, col=1)
                fig.add_trace(go.Scatter(x=time_col, y=df['SMA_20'], name="20 SMA"), row=1, col=1)
                fig.add_trace(go.Scatter(x=time_col, y=df['SMA_50'], name="50 SMA"), row=1, col=1)
                fig.add_trace(go.Scatter(x=time_col, y=df['RSI'], name="RSI (14)", line=dict(color='purple')), row=2, col=1)
                fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="simple_white", margin=dict(t=10, b=10))
                str.plotly_chart(fig, use_container_width=True)

            else:
                status.update(label="Error retrieving historical vectors.", state="error")
                str.error("Data parameters could not be processed. Please confirm ticker configuration or execution parameters.")
    else:
        str.info("Select your asset configuration parameters in the sidebar control panel and click 'Execute Analysis' to run calculations.")

# ==========================================
# TAB 2 & 3: SYSTEM DOCUMENTS & DISCLAIMER
# ==========================================
with tab2:
    str.header("System Architecture Documentation")
    str.write("This engine pulls fresh technical layers directly from public financial markets to isolate momentum shifts.")

with tab3:
    str.header("Legal Limitations & Risk Disclosure")
    str.warning("Trading contains absolute market financial risk. This tool does not guarantee operational accuracy.")
