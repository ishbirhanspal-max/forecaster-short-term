import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Page config for high-end terminal presentation
st.set_page_config(page_title="QuantEdge Hyper-Drive Terminal", layout="wide")

# ==========================================
# 1. ADVANCED STATE ARCHITECTURE
# ==========================================
if "cash" not in st.session_state: st.session_state.cash = 100000.00
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

# Flatten dictionary for seamless global search indexing
FLAT_ASSET_INDEX = {}
for cat, items in ASSET_CLASSES.items():
    for name, tick in items.items():
        FLAT_ASSET_INDEX[f"{name} ({tick})"] = {"ticker": tick, "name": name, "category": cat}

# ==========================================
# 2. CONTROLS, SEARCH, AND BALANCE desk
# ==========================================
st.sidebar.header("🕹️ Terminal Navigation panel")

# Persistent Portfolio Balance Controller
st.sidebar.subheader("💰 Capital Control Center")
new_balance = st.sidebar.number_input("Adjust Account Balance", min_value=0.0, value=float(st.session_state.cash), step=1000.0)
if new_balance != st.session_state.cash:
    st.session_state.cash = new_balance

st.sidebar.divider()

# Live Omni-Search Bar Engine
st.sidebar.subheader("🔍 Omni-Asset Search")
search_query = st.sidebar.text_input("Search Assets (e.g., Gold, Reliance, BTC)", "").lower()

# Filter active choices based on the omni-search string
filtered_options = [k for k in FLAT_ASSET_INDEX.keys() if search_query in k.lower()]

if not filtered_options:
    st.sidebar.warning("No tracking symbols match your search filter.")
    filtered_options = list(FLAT_ASSET_INDEX.keys())

selected_search_key = st.sidebar.selectbox("Active Selected Instrument", filtered_options)
active_asset_meta = FLAT_ASSET_INDEX[selected_search_key]
ticker = active_asset_meta["ticker"]
asset_name = active_asset_meta["name"]

timeframe = st.sidebar.selectbox(
    "Analysis Horizon", 
    ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour", "1 Day", "1 Week", "1 Month"]
)
chart_style = st.sidebar.radio("Plot Scheme", ["Candlestick", "Line Chart"])

st.sidebar.divider()
st.sidebar.header("⚡ Live Auto-Pilot")
auto_refresh = st.sidebar.toggle("Enable Fast-Sync Loop", value=False)
refresh_rate = st.sidebar.slider("Refresh Frame (Sec)", 5, 60, 10)

# Timed lookback assignments mapped to specific horizons
TIMEFRAME_CONFIG = {
    "1 Minute":   {"int": "1m",  "period": "5d",   "horizon": "Short-Term"},
    "5 Minutes":  {"int": "5m",  "period": "5d",   "horizon": "Short-Term"},
    "15 Minutes": {"int": "15m", "period": "5d",   "horizon": "Short-Term"},
    "1 Hour":     {"int": "1h",  "period": "60d",  "horizon": "Medium-Term"},
    "1 Day":      {"int": "1d",  "period": "2y",   "horizon": "Medium-Term"},
    "1 Week":     {"int": "1wk", "period": "5y",   "horizon": "Long-Term"},
    "1 Month":    {"int": "1mo", "period": "max",  "horizon": "Long-Term"}
}

current_horizon = TIMEFRAME_CONFIG[timeframe]["horizon"]

# ==========================================
# 3. NATIVE ADVANCED MATHEMATICS ENGINE
# ==========================================
def calculate_advanced_analytics(df):
    """Calculates overlays, indicators, and candlestick patterns natively."""
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
    
    # Candlestick Pattern Detection
    body = (df['Close'] - df['Open']).abs()
    candle_range = df['High'] - df['Low'] + 1e-9
    
    df['Pattern_Doji'] = body <= (candle_range * 0.1)
    
    lower_shade = np.where(df['Close'] > df['Open'], df['Open'] - df['Low'], df['Close'] - df['Low'])
    upper_shade = np.where(df['Close'] > df['Open'], df['High'] - df['Close'], df['High'] - df['Open'])
    df['Pattern_Hammer'] = (lower_shade >= 2 * body) & (upper_shade <= (candle_range * 0.10)) & (body > 0)
    
    prev_body = body.shift(1)
    prev_dir = np.sign(df['Close'] - df['Open']).shift(1)
    curr_dir = np.sign(df['Close'] - df['Open'])
    
    df['Pattern_Bullish_Engulfing'] = (curr_dir == 1) & (prev_dir == -1) & (df['Close'] >= df['Open'].shift(1)) & (df['Open'] <= df['Close'].shift(1))
    df['Pattern_Bearish_Engulfing'] = (curr_dir == -1) & (prev_dir == 1) & (df['Close'] <= df['Open'].shift(1)) & (df['Open'] >= df['Close'].shift(1))
    
    df.bfill(inplace=True)
    return df

def generate_one_year_forecast(df, target_days=365):
    """Applies a first-degree polynomial regression to forecast a 1-year forward path."""
    x = np.arange(len(df))
    y = df['Close'].values
    
    poly_fit = np.polyfit(x, y, 1)
    slope = poly_fit[0]
    intercept = poly_fit[1]
    
    last_date = df['Timestamp'].iloc[-1]
    if isinstance(last_date, str):
        last_date = datetime.strptime(last_date, "%Y-%m-%d")
        
    future_timestamps = [last_date + timedelta(days=i) for i in range(1, target_days + 1)]
    future_indices = np.arange(len(df), len(df) + target_days)
    future_predictions = slope * future_indices + intercept
    
    return future_timestamps, future_predictions

# ==========================================
# 4. DATA PIPELINE SYNCHRONIZER
# ==========================================
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

chosen_int = TIMEFRAME_CONFIG[timeframe]["int"]
chosen_per = TIMEFRAME_CONFIG[timeframe]["period"]

# Force download if asset changes or frame isn't loaded
if st.session_state.get("current_market_data") is None or st.session_state.get("last_analyzed_ticker") != ticker:
    with st.spinner("Downloading synchronized market matrix..."):
        raw_df = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
        if raw_df is not None and not raw_df.empty:
            if isinstance(raw_df.columns, pd.MultiIndex):
                raw_df.columns = raw_df.columns.get_level_values(0)
            raw_df.reset_index(inplace=True)
            
            if 'Datetime' in raw_df.columns:
                raw_df.rename(columns={'Datetime': 'Timestamp'}, inplace=True)
            elif 'Date' in raw_df.columns:
                raw_df.rename(columns={'Date': 'Timestamp'}, inplace=True)
                
            st.session_state.current_market_data = calculate_advanced_analytics(raw_df)
            st.session_state.live_price = float(st.session_state.current_market_data['Close'].iloc[-1])
            st.session_state.last_analyzed_ticker = ticker

# ==========================================
# 5. USER INTERFACE NAVIGATION TABS
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
        st.caption(f"Strategy Mandate Grouping: **{current_horizon} Profile**")
        
        # Algorithmic Signal Engine Rules
        score = 0.0
        reasons = []
        
        if latest['EMA_9'] > latest['EMA_21']: 
            score += 1.0; reasons.append("Bullish Trend: Short-term exponential velocity tracking above major structure.")
        else: 
            score -= 1.0; reasons.append("Bearish Trend: Short-term exponential velocity breaking below major structure.")
            
        if latest['RSI_14'] < 32: 
            score += 1.5; reasons.append(f"Oversold Condition: RSI ({latest['RSI_14']:.1f}) indicates buying pressure vacuum.")
        elif latest['RSI_14'] > 68: 
            score -= 1.5; reasons.append(f"Overbought Condition: RSI ({latest['RSI_14']:.1f}) indicates counter-trend variance risk.")
            
        if latest['Pattern_Bullish_Engulfing']:
            score += 2.0; reasons.append("Structural Pattern: Bullish Engulfing candle confirmation verified.")
        if latest['Pattern_Bearish_Engulfing']:
            score -= 2.0; reasons.append("Structural Pattern: Bearish Engulfing candle confirmation verified.")
            
        confidence_pct = min((abs(score) / 4.5) * 100, 99.5) if score != 0 else 50.0
        verdict = "STRATEGIC LONG 🟢" if score > 0.5 else ("STRATEGIC SHORT 🔴" if score < -0.5 else "NEUTRAL ⚪")
        
        atr_val = latest['ATR']
        proj_exit = curr_p + (atr_val * 2.5) if score >= 0 else curr_p - (atr_val * 2.5)
        proj_sl = curr_p - (atr_val * 1.5) if score >= 0 else curr_p + (atr_val * 1.5)

        # Performance Summary Cards
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Live Execution Price", f"${curr_p:,.2f}" if "NS" not in ticker else f"₹{curr_p:,.2f}")
        m_col2.metric("Liquid Capital Available", f"${st.session_state.cash:,.2f}")
        m_col3.metric("System Verdict", verdict)
        m_col4.metric("Signal Confidence", f"{confidence_pct:.1f}%")

        with st.expander("🔬 View Mathematical Formula & Indication Logs"):
            for r in reasons: st.write(f"• {r}")

        # Compute and Add 1-Year Predictive Forecast Curves
        f_dates, f_preds = generate_one_year_forecast(df)
        
        # Plot configurations
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        if chart_style == "Candlestick":
            fig.add_trace(go.Candlestick(x=df['Timestamp'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market Price"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Close'], name="Close Price Line", line=dict(color='#00ffcc', width=2)), row=1, col=1)
            
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['EMA_9'], line=dict(color='yellow', width=1.2), name="9 EMA"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['EMA_21'], line=dict(color='fuchsia', width=1.2), name="21 EMA"), row=1, col=1)
        
        # Append 1-Year Forecast Curve to the Main Plot
        fig.add_trace(go.Scatter(x=f_dates, y=f_preds, line=dict(color='cyan', width=2, dash='dash'), name="1-Year Predictive Curve"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['RSI_14'], line=dict(color='orange', width=1.5), name="RSI Engine"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_dark", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Execution Desk Module
        st.markdown("### 💼 Automated Position Entry Desk")
        with st.form("execution_desk_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            trade_qty = f_col1.number_input("Position Asset Units", min_value=0.01, value=1.0, step=1.0)
            custom_tp = f_col2.number_input("Take Profit Target Price", value=float(proj_exit))
            custom_sl = f_col3.number_input("Stop Loss Floor Price", value=float(proj_sl))
            
            b1, b2 = st.columns(2)
            exe_long = b1.form_submit_button("🟢 ROUTE AUTOMATED LONG POSITION", use_container_width=True)
            exe_short = b2.form_submit_button("🔴 ROUTE AUTOMATED SHORT POSITION", use_container_width=True)
            
            if exe_long or exe_short:
                direction_string = "LONG" if exe_long else "SHORT"
                total_cost = trade_qty * curr_p
                
                if direction_string == "LONG" and total_cost > st.session_state.cash:
                    st.error("Order rejected: Insufficient liquid trading capital.")
                else:
                    if direction_string == "LONG":
                        st.session_state.cash -= total_cost
                    else:
                        st.session_state.cash += total_cost
                        
                    st.session_state.portfolio[ticker] = {
                        "asset_name": asset_name, "qty": trade_qty if direction_string == "LONG" else -trade_qty,
                        "entry": curr_p, "tp": custom_tp, "sl": custom_sl, "horizon": current_horizon,
                        "direction": direction_string, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.statement.append({
                        "Timestamp": datetime.now().strftime("%H:%M:%S"), "Asset": ticker,
                        "Direction": direction_string, "Horizon": current_horizon, "Units": trade_qty, "Price": curr_p
                    })
                    st.toast(f"Position successfully logged inside the {current_horizon} Desk!", icon="🚨")
                    time.sleep(0.5)
                    st.rerun()

# ------------------------------------------
# TAB 2: GLOBAL MULTI-ASSET SCANNER
# ------------------------------------------
with tab2:
    st.title("🤖 Global Multi-Asset System Scanner")
    st.write("Scans Forex, Commodities, Cryptocurrencies, and Indian Equity spaces simultaneously for profitable anomalies.")
    
    if st.button("🚀 EXECUTE FULL CROSS-MARKET QUANT AUDIT", use_container_width=True):
        detected_setups = []
        with st.spinner("Processing deep regression scans across global liquidity networks..."):
            for option_key, metadata in FLAT_ASSET_INDEX.items():
                try:
                    s_tick = metadata["ticker"]
                    s_name = metadata["name"]
                    s_cat = metadata["category"]
                    
                    s_int = TIMEFRAME_CONFIG[timeframe]["int"]
                    s_per = TIMEFRAME_CONFIG[timeframe]["period"]
                    
                    s_df = yf.download(s_tick, period=s_per, interval=s_int, progress=False)
                    if not s_df.empty and len(s_df) > 20:
                        if isinstance(s_df.columns, pd.MultiIndex):
                            s_df.columns = s_df.columns.get_level_values(0)
                        s_df.reset_index(inplace=True)
                        s_df = calculate_advanced_analytics(s_df)
                        
                        s_latest = s_df.iloc[-1]
                        s_close = float(s_latest['Close'])
                        s_atr = s_latest['ATR']
                        
                        # Directional calculation check
                        chk_score = 0
                        if s_latest['EMA_9'] > s_latest['EMA_21']: chk_score += 1
                        else: chk_score -= 1
                        if s_latest['RSI_14'] < 35: chk_score += 1
                        elif s_latest['RSI_14'] > 65: chk_score -= 1
                        
                        if abs(chk_score) >= 1:
                            s_dir = "LONG 🟢" if chk_score > 0 else "SHORT 🔴"
                            s_tp = s_close + (s_atr * 2.2) if chk_score > 0 else s_close - (s_atr * 2.2)
                            s_sl = s_close - (s_atr * 1.5) if chk_score > 0 else s_close + (s_atr * 1.5)
                            
                            detected_setups.append({
                                "Market Segment": s_cat, "Asset": s_name, "Ticker": s_tick,
                                "Allocation Portfolio Tier": TIMEFRAME_CONFIG[timeframe]["horizon"],
                                "Strategic Direction": s_dir, "Spot Price": s_close, "Target (TP)": s_tp, "Stop-Loss (SL)": s_sl
                            })
                except:
                    pass
            
            st.session_state.scan_results = detected_setups
            st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.session_state.scan_results:
        st.markdown(f"#### Active Anomalies Discovered at: `{st.session_state.last_scan_time}`")
        st.dataframe(pd.DataFrame(st.session_state.scan_results), use_container_width=True)
    else:
        st.info("System Scanner is ready. Initiate system scan above.")

# ------------------------------------------
# TAB 3: ACTIVE TERM LEDGERS
# ------------------------------------------
with tab3:
    st.title("💼 Horizon Risk Management Modules")
    st.metric("Persistent Account Balance Available", f"${st.session_state.cash:,.2f}")
    
    l_tab1, l_tab2, l_tab3 = st.tabs(["⏱️ Short-Term Risk Ledger", "📅 Medium-Term Risk Ledger", "🏆 Long-Term Structural Portfolio"])
    
    def generate_horizon_view(target_horizon_string):
        matched_positions = {k: v for k, v in st.session_state.portfolio.items() if v['horizon'] == target_horizon_string}
        
        if matched_positions:
            rows = []
            for t_id, data in matched_positions.items():
                rows.append({
                    "Asset Code": t_id, "Description": data['asset_name'], "Direction": data['direction'],
                    "Units Allocated": abs(data['qty']), "Entry Locked": f"{data['entry']:,.4f}",
                    "Target Floor (TP)": f"{data['tp']:,.4f}", "Stop Loss (SL)": f"{data['sl']:,.4f}", "Entry Timestamp": data['timestamp']
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            
            liquidate_selection = st.selectbox("Select Exposure Target to Terminate", list(matched_positions.keys()), key=f"select_{target_horizon_string}")
            if st.button("💥 LIQUIDATE SPECIFIED RISK", key=f"kill_btn_{target_horizon_string}", use_container_width=True):
                closed_item = st.session_state.portfolio[liquidate_selection]
                # Restore capital adjustment calculations
                returned_value = abs(closed_item['qty']) * closed_item['entry']
                if closed_item['direction'] == "LONG":
                    st.session_state.cash += returned_value
                else:
                    st.session_state.cash -= returned_value
                    
                del st.session_state.portfolio[liquidate_selection]
                st.toast("Position removed successfully.", icon="💥")
                time.sleep(0.5)
                st.rerun()
        else:
            st.info(f"No capital allocations active under the {target_horizon_string} framework.")

    with l_tab1: generate_horizon_view("Short-Term")
    with l_tab2: generate_horizon_view("Medium-Term")
    with l_tab3: generate_horizon_view("Long-Term")

    if st.session_state.statement:
        st.subheader("📋 Historical Order Archive Trails")
        st.dataframe(pd.DataFrame(st.session_state.statement).iloc[::-1], use_container_width=True)

# ------------------------------------------
# TAB 4: TERMINAL USER MANUAL
# ------------------------------------------
with tab4:
    st.title("📖 Quantitative Engine Operations Blueprint")
    st.markdown("""
    ### ⚙️ How to Operate the Hyper-Drive Engine
    1. **Using the Search Engine:** Enter characters into the **Omni-Asset Search** on the left. The dropdown updates instantly to show relevant global currencies, cryptos, metals, or Indian equities matching your keywords.
    2. **Balance Override Persistence:** Change the wallet numbers inside the **Capital Control Center** module. This configuration overrides state parameters and updates balances permanently across actions.
    3. **1-Year Regression Forecast Vector:** The system fits a mathematical linear polynomial trend projection line directly across historical arrays. It automatically visualizes a dashed cyan curve 365 days forward into the future to forecast long-term macro trends.
    """)
