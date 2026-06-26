import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# Page config for high-end terminal presentation
st.set_page_config(page_title="QuantEdge Hyper-Drive Terminal", layout="wide")

# ==========================================
# 1. ADVANCED STATE ARCHITECTURE
# ==========================================
if "cash" not in st.session_state: st.session_state.cash = 100000.00  # Increased default scale
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "scan_results" not in st.session_state: st.session_state.scan_results = []
if "last_scan_time" not in st.session_state: st.session_state.last_scan_time = None

# Comprehensive Multi-Market Asset Matrix (Global + Indian NSE)
ASSET_CLASSES = {
    "Indian Equities (NSE)": {
        "Nifty 50 Index": "^NSEI",
        "Reliance Industries": "RELIANCE.NS",
        "Tata Consultancy Services": "TCS.NS",
        "Infosys": "INFY.NS",
        "HDFC Bank": "HDFCBANK.NS"
    },
    "Global Equities": {
        "Apple Inc.": "AAPL",
        "Tesla Motors": "TSLA",
        "Nvidia Corp.": "NVDA",
        "S&P 500 ETF": "SPY"
    },
    "Crypto-Currencies": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD"
    },
    "Foreign Exchange (FX)": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X"
    },
    "Commodities": {
        "Gold Futures": "GC=F",
        "Crude Oil Futures": "CL=F"
    }
}

# ==========================================
# 2. CONTROLS & TIMEFRAME MAPPING
# ==========================================
st.sidebar.header("🕹️ Terminal Parameters")

asset_type = st.sidebar.selectbox("Asset Universe", list(ASSET_CLASSES.keys()))
asset_name = st.sidebar.selectbox("Active Instrument", list(ASSET_CLASSES[asset_type].keys()))
ticker = ASSET_CLASSES[asset_type][asset_name]

timeframe = st.sidebar.selectbox(
    "Analysis Horizon", 
    ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour", "1 Day", "1 Week", "1 Month"]
)
chart_style = st.sidebar.radio("Plot Scheme", ["Candlestick", "Line Chart"])

st.sidebar.divider()
st.sidebar.header("⚡ Live Auto-Pilot")
auto_refresh = st.sidebar.toggle("Enable Fast-Sync Loop", value=False)
refresh_rate = st.sidebar.slider("Refresh Frame (Sec)", 5, 60, 10)

# Robust intervals paired with maximum safe lookbacks allowed by Yahoo Finance
TIMEFRAME_CONFIG = {
    "1 Minute":   {"int": "1m",  "period": "5d",   "horizon": "Short-Term"},
    "5 Minutes":  {"int": "5m",  "period": "5d",   "horizon": "Short-Term"},
    "15 Minutes": {"int": "15m", "period": "5d",   "horizon": "Short-Term"},
    "1 Hour":     {"int": "1h",  "period": "60d",  "horizon": "Medium-Term"},
    "1 Day":      {"int": "1d",  "period": "1y",   "horizon": "Medium-Term"},
    "1 Week":     {"int": "1wk", "period": "5y",   "horizon": "Long-Term"},
    "1 Month":    {"int": "1mo", "period": "max",  "horizon": "Long-Term"}
}

current_horizon = TIMEFRAME_CONFIG[timeframe]["horizon"]

# ==========================================
# 3. NATIVE COMPREHENSIVE MATH ENGINE
# ==========================================
def calculate_advanced_analytics(df):
    """Calculates quantitative overlays and classic patterns natively."""
    # Moving Averages
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # MACD Setup
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    sma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    df['BB_Upper'] = sma20 + (std20 * 2)
    df['BB_Lower'] = sma20 - (std20 * 2)
    
    # Average True Range (ATR)
    hl = df['High'] - df['Low']
    hc = (df['High'] - df['Close'].shift(1)).abs()
    lc = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # --- CANDLESTICK PATTERN DETECTION ENGINE ---
    body = (df['Close'] - df['Open']).abs()
    candle_range = df['High'] - df['Low'] + 1e-9
    
    # Pattern 1: Doji Line
    df['Pattern_Doji'] = body <= (candle_range * 0.1)
    
    # Pattern 2: Hammer (Bullish Reversal)
    lower_shade = np.where(df['Close'] > df['Open'], df['Open'] - df['Low'], df['Close'] - df['Low'])
    upper_shade = np.where(df['Close'] > df['Open'], df['High'] - df['Close'], df['High'] - df['Open'])
    df['Pattern_Hammer'] = (lower_shade >= 2 * body) & (upper_shade <= (candle_range * 0.10)) & (body > 0)
    
    # Pattern 3: Engulfing Formations
    prev_body = body.shift(1)
    prev_dir = np.sign(df['Close'] - df['Open']).shift(1)
    curr_dir = np.sign(df['Close'] - df['Open'])
    
    df['Pattern_Bullish_Engulfing'] = (curr_dir == 1) & (prev_dir == -1) & (df['Close'] >= df['Open'].shift(1)) & (df['Open'] <= df['Close'].shift(1))
    df['Pattern_Bearish_Engulfing'] = (curr_dir == -1) & (prev_dir == 1) & (df['Close'] <= df['Open'].shift(1)) & (df['Open'] >= df['Close'].shift(1))
    
    df.bfill(inplace=True)
    return df

# ==========================================
# 4. DATA PIPELINE SYNCHRONIZER
# ==========================================
sync_triggered = st.sidebar.button("🔄 Instant Matrix Sync", use_container_width=True)

# Defensive execution barrier
if sync_triggered or auto_refresh or st.session_state.current_market_data is None or st.session_state.last_analyzed_ticker != ticker:
    chosen_int = TIMEFRAME_CONFIG[timeframe]["int"]
    chosen_per = TIMEFRAME_CONFIG[timeframe]["period"]
    
    with st.spinner("Accessing distributed institutional feeds..."):
        raw_df = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
        
        if raw_df is not None and not raw_df.empty:
            if isinstance(raw_df.columns, pd.MultiIndex):
                raw_df.columns = raw_df.columns.get_level_values(0)
            raw_df.reset_index(inplace=True)
            
            # Map time headers uniformly
            if 'Datetime' in raw_df.columns:
                raw_df.rename(columns={'Datetime': 'Timestamp'}, inplace=True)
            elif 'Date' in raw_df.columns:
                raw_df.rename(columns={'Date': 'Timestamp'}, inplace=True)
                
            processed_df = calculate_advanced_analytics(raw_df)
            
            st.session_state.live_price = float(processed_df['Close'].iloc[-1])
            st.session_state.current_market_data = processed_df
            st.session_state.last_analyzed_ticker = ticker

# ==========================================
# 5. USER INTERFACE TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Single-Asset Forecast Matrix", 
    "🤖 Global Multi-Asset Scanner", 
    "💼 Active Term Ledgers", 
    "📖 Terminal User Manual"
])

# ------------------------------------------
# TAB 1: SINGLE-ASSET FORECAST MATRIX
# ------------------------------------------
with tab1:
    if st.session_state.current_market_data is not None:
        df = st.session_state.current_market_data
        curr_p = st.session_state.live_price
        latest = df.iloc[-1]
        
        st.title(f"🔮 Predictive Analysis Matrix: {asset_name} ({ticker})")
        st.caption(f"Strategy Category Allocation: **{current_horizon} Profile**")
        
        # Predictive Scoring Weighting System
        score = 0.0
        max_score = 7.5
        reasons = []
        
        # Metric Extraction
        e9, e21 = latest['EMA_9'], latest['EMA_21']
        rsi = latest['RSI_14']
        macd, macd_sig = latest['MACD'], latest['MACD_Signal']
        upper_b, lower_b = latest['BB_Upper'], latest['BB_Lower']
        atr_val = latest['ATR']
        
        # Signal Rules
        if e9 > e21: 
            score += 1.0; reasons.append("Bullish Trend: 9 EMA is processing over the 21 EMA.")
        else: 
            score -= 1.0; reasons.append("Bearish Trend: 9 EMA is diving below the 21 EMA.")
            
        if rsi < 30: 
            score += 1.5; reasons.append(f"Oversold Condition: RSI ({rsi:.1f}) implies near-term buying pressure.")
        elif rsi > 70: 
            score -= 1.5; reasons.append(f"Overbought Condition: RSI ({rsi:.1f}) implies near-term technical exhaustion.")
            
        if macd > macd_sig: 
            score += 1.0; reasons.append("Positive Momentum: MACD histograms expanding upwards.")
        else: 
            score -= 1.0; reasons.append("Negative Momentum: MACD histograms shrinking downwards.")
            
        if curr_p > upper_b: 
            score -= 1.0; reasons.append("Volatility Alert: Price overextended past Upper Bollinger Band.")
        elif curr_p < lower_b: 
            score += 1.0; reasons.append("Volatility Alert: Price overextended below Lower Bollinger Band.")

        # Pattern Insertion Weights
        if latest['Pattern_Bullish_Engulfing']:
            score += 2.0; reasons.append("CANDLESTICK ENGULFING: High-reliability Bullish Engulfing structural lock completed.")
        if latest['Pattern_Bearish_Engulfing']:
            score -= 2.0; reasons.append("CANDLESTICK ENGULFING: High-reliability Bearish Engulfing structural lock completed.")
        if latest['Pattern_Hammer']:
            score += 1.0; reasons.append("CANDLESTICK PATTERN: Bottoming Hammer structure detected.")
        if latest['Pattern_Doji']:
            reasons.append("CANDLESTICK PATTERN: Doji indecision candle observed.")

        # Confidence Normalization
        confidence_pct = min((abs(score) / max_score) * 100, 99.9)
        
        if score >= 1.5:
            verdict = "STRATEGIC LONG 🟢"
            proj_exit = curr_p + (atr_val * 2.5)
            proj_sl = curr_p - (atr_val * 1.5)
        elif score <= -1.5:
            verdict = "STRATEGIC SHORT 🔴"
            proj_exit = curr_p - (atr_val * 2.5)
            proj_sl = curr_p + (atr_val * 1.5)
        else:
            verdict = "NEUTRAL POSITION ⚪"
            proj_exit, proj_sl = upper_b, lower_b
            confidence_pct = 50.0

        # Metric Displays
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Live Feed Price", f"${curr_p:,.2f}" if "NS" not in ticker else f"₹{curr_p:,.2f}")
        m_col2.metric("Target Horizon Allocation", current_horizon)
        m_col3.metric("System Verdict", verdict)
        m_col4.metric("Algorithmic Confidence", f"{confidence_pct:.1f}%")

        # Rationale Expander
        with st.expander("🔬 View Algorithmic Calculation Logs"):
            for r in reasons: st.write(f"• {r}")

        # Multi-Subplot Advanced Analytics Chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        if chart_style == "Candlestick":
            fig.add_trace(go.Candlestick(x=df['Timestamp'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price Structure"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Close'], name="Line Metric", line=dict(color='#00ffcc', width=2)), row=1, col=1)
            
        # Overlays
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['EMA_9'], line=dict(color='yellow', width=1.2), name="9 EMA"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['EMA_21'], line=dict(color='fuchsia', width=1.2), name="21 EMA"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['BB_Upper'], line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dot'), name="BBU"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['BB_Lower'], line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dot'), name="BBL"), row=1, col=1)
        
        # RSI on Subplot 2
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['RSI_14'], line=dict(color='orange', width=1.5), name="RSI (14)"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Dynamic Execution Desk
        st.markdown("### 💼 Dynamic Asset Execution Desk")
        with st.form("trade_execution_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            qty = f_col1.number_input("Trade Position Units", min_value=0.01, value=10.0, step=1.0)
            custom_tp = f_col2.number_input("Custom Target Price", value=float(proj_exit))
            custom_sl = f_col3.number_input("Custom Stop Loss", value=float(proj_sl))
            
            b1, b2 = st.columns(2)
            buy_triggered = b1.form_submit_button("🟢 ROUTE BUY/LONG ORDER", use_container_width=True)
            sell_triggered = b2.form_submit_button("🔴 ROUTE SELL/SHORT ORDER", use_container_width=True)
            
            if buy_triggered or sell_triggered:
                order_direction = "LONG" if buy_triggered else "SHORT"
                cost = qty * curr_p
                
                # Assign allocation category automatically
                st.session_state.portfolio[ticker] = {
                    "asset_name": asset_name, "qty": qty if order_direction == "LONG" else -qty,
                    "entry": curr_p, "tp": custom_tp, "sl": custom_sl, "horizon": current_horizon,
                    "direction": order_direction, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.statement.append({
                    "Timestamp": datetime.now().strftime("%H:%M:%S"), "Asset": ticker,
                    "Direction": order_direction, "Horizon": current_horizon, "Units": qty, "Execution Price": curr_p
                })
                st.toast(f"Order successfully routed to {current_horizon} Portfolio Ledger!", icon="✅")
                time.sleep(0.5)
                st.rerun()

# ------------------------------------------
# TAB 2: GLOBAL MULTI-ASSET SCANNER
# ------------------------------------------
with tab2:
    st.title("🤖 High-Frequency Market Scanner Engine")
    st.write("Scans all asset classes simultaneously across global and Indian markets for trade signals.")
    
    if st.button("🚀 EXECUTE FULL SYSTEM SCAN", use_container_width=True):
        scanned_setups = []
        
        # Flatten dictionary for seamless automated scanning loops
        flat_watchlist = {}
        for cat, components in ASSET_CLASSES.items():
            for name, tick in components.items():
                flat_watchlist[tick] = (name, cat)
                
        with st.spinner(f"Processing real-time quantitative loops for {len(flat_watchlist)} global instruments..."):
            for tick, (name, cat) in flat_watchlist.items():
                try:
                    s_int = TIMEFRAME_CONFIG[timeframe]["int"]
                    s_per = TIMEFRAME_CONFIG[timeframe]["period"]
                    scan_df = yf.download(tick, period=s_per, interval=s_int, progress=False)
                    
                    if not scan_df.empty and len(scan_df) > 25:
                        if isinstance(scan_df.columns, pd.MultiIndex): 
                            scan_df.columns = scan_df.columns.get_level_values(0)
                        scan_df.reset_index(inplace=True)
                        scan_df = calculate_advanced_analytics(scan_df)
                        
                        # Lightweight local logic check for scanner reporting
                        last_row = scan_df.iloc[-1]
                        s_close = float(last_row['Close'])
                        s_atr = last_row['ATR']
                        
                        # Score verification
                        s_score = 0
                        if last_row['EMA_9'] > last_row['EMA_21']: s_score += 1
                        else: s_score -= 1
                        if last_row['RSI_14'] < 35: s_score += 1.5
                        elif last_row['RSI_14'] > 65: s_score -= 1.5
                        
                        if abs(s_score) >= 1.5:
                            s_dir = "LONG 🟢" if s_score > 0 else "SHORT 🔴"
                            s_tp = s_close + (s_atr * 2) if s_score > 0 else s_close - (s_atr * 2)
                            s_sl = s_close - (s_atr * 1.5) if s_score > 0 else s_close + (s_atr * 1.5)
                            
                            scanned_setups.append({
                                "Asset": name, "Ticker": tick, "Horizon": TIMEFRAME_CONFIG[timeframe]["horizon"],
                                "Direction": s_dir, "Price": s_close, "Target": s_tp, "Stop-Loss": s_sl, "Power": abs(s_score)
                            })
                except:
                    pass
            
            scanned_setups.sort(key=lambda x: x['Power'], reverse=True)
            st.session_state.scan_results = scanned_setups
            st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.session_state.scan_results:
        st.markdown(f"#### Live Setups Identified at: `{st.session_state.last_scan_time}`")
        st.dataframe(pd.DataFrame(st.session_state.scan_results), use_container_width=True)
    else:
        st.info("Scanner Engine sitting idle. Execute automated system scan above.")

# ------------------------------------------
# TAB 3: ACTIVE TERM LEDGERS
# ------------------------------------------
with tab3:
    st.title("💼 Distributed Horizon Risk Ledgers")
    
    # Structural separation into specific requested tracking tiers
    t1, t2, t3 = st.tabs(["⏱️ Short-Term Risk Ledger", "📅 Medium-Term Risk Ledger", "🏆 Long-Term Structural Portfolio"])
    
    def render_ledger_for_horizon(horizon_name):
        relevant_positions = {k: v for k, v in st.session_state.portfolio.items() if v['horizon'] == horizon_name}
        
        if relevant_positions:
            rows = []
            for t_id, data in relevant_positions.items():
                rows.append({
                    "Asset Unique ID": t_id, "Description": data['asset_name'], "Direction": data['direction'],
                    "Allocation Volume": abs(data['qty']), "Locked Entry": f"{data['entry']:,.4f}",
                    "Take Profit": f"{data['tp']:,.4f}", "Stop Loss": f"{data['sl']:,.4f}", "Timestamp": data['timestamp']
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            
            # Liquidation Action block
            target_close = st.selectbox("Select Asset to Liquidate", list(relevant_positions.keys()), key=f"close_{horizon_name}")
            if st.button("💥 LIQUIDATE EXPOSURE", key=f"btn_{horizon_name}"):
                del st.session_state.portfolio[target_close]
                st.toast(f"Position offloaded cleanly.", icon="🚀")
                time.sleep(0.5)
                st.rerun()
        else:
            st.info(f"No allocations deployed under the {horizon_name} mandate.")

    with t1: render_ledger_for_horizon("Short-Term")
    with t2: render_ledger_for_horizon("Medium-Term")
    with t3: render_ledger_for_horizon("Long-Term")
    
    if st.session_state.statement:
        st.subheader("📋 Order Audit Trails")
        st.dataframe(pd.DataFrame(st.session_state.statement).iloc[::-1], use_container_width=True)

# ------------------------------------------
# TAB 4: TERMINAL USER MANUAL
# ------------------------------------------
with tab4:
    st.title("📖 Quantitative Engine Operations Blueprint")
    st.markdown("""
    Welcome to the terminal manual. Below is the workflow layout explaining how this platform processes multi-market assets.
    
    ### ⚙️ Standard Operating Workflow
    1. **Asset Selection:** Use the **Terminal Parameters Panel** on the left to swap between Indian Equity Markets (NSE), Cryptocurrencies, Global Indices, Forex pairs, or Commodities.
    2. **Analysis Horizon Configuration:** Changing the timeframes automatically maps your strategies:
        * `1m`, `5m`, `15m` $\rightarrow$ Classified automatically inside the **Short-Term Risk Ledger**.
        * `1h`, `1d` $\rightarrow$ Routed directly inside the **Medium-Term Risk Ledger**.
        * `1wk`, `1mo` $\rightarrow$ Escalated to the **Long-Term Structural Portfolio**.
    3. **Automated Scanner Module:** Head over to the **Global Multi-Asset Scanner** tab to run algorithmic audits on the entire asset index simultaneously instead of looking at charts one-by-one.
    
    ### 🛡️ Risk Management Parameters
    The forecast matrix automatically targets strategic points based on an asset's **ATR (Average True Range)**. 
    * **Take Profit:** Projected at an expansion of $+2.5 \times \text{ATR}$ to capture clean trend peaks.
    * **Stop Loss:** Locked firmly at $-1.5 \times \text{ATR}$ to protect capital against sudden market turns.
    """)
