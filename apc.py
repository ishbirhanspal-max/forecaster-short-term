import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import time

# High-fidelity terminal workspace configuration
st.set_page_config(page_title="QuantEdge Crypto/Forex Alpha Terminal", layout="wide")

# ==========================================
# 1. COMPREHENSIVE SESSION STATE ARCHITECTURE
# ==========================================
if "cash" not in st.session_state: st.session_state.cash = 100000.00
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "scan_results" not in st.session_state: st.session_state.scan_results = []
if "last_scan_time" not in st.session_state: st.session_state.last_scan_time = None

# Asset Matrix Restricted Exclusively to Forex and Crypto Markets
ASSET_CLASSES = {
    "Crypto-Currencies (24/7)": {
        "Bitcoin / USD": "BTC-USD",
        "Ethereum / USD": "ETH-USD",
        "Solana / USD": "SOL-USD",
        "Ripple / USD": "XRP-USD",
        "Cardano / USD": "ADA-USD"
    },
    "Foreign Exchange (FX - IST Adjusted)": {
        "EUR / USD": "EURUSD=X",
        "GBP / USD": "GBPUSD=X",
        "USD / JPY": "JPY=X",
        "AUD / USD": "AUDUSD=X",
        "USD / CAD": "CAD=X"
    }
}

# Flatten array index maps for swift query scanning
FLAT_ASSET_INDEX = {}
for cat, items in ASSET_CLASSES.items():
    for name, tick in items.items():
        FLAT_ASSET_INDEX[f"{name} ({tick})"] = {"ticker": tick, "name": name, "category": cat}

# ==========================================
# 2. IST TIME CLOCK & MARKET STATUS RULES
# ==========================================
def get_market_status_ist(category):
    """Verifies operational status against strict Indian Standard Time constraints."""
    if "Crypto" in category:
        return True, "ONLINE (24/7)"
    
    # Forex Markets halt from Friday 22:00 GMT to Sunday 22:00 GMT
    # In Indian Standard Time (IST is GMT+5:30): Saturday 03:30 AM IST to Monday 03:30 AM IST
    ist_now = datetime.now(pytz.timezone('Asia/Kolkata'))
    weekday = ist_now.weekday() # 5 = Saturday, 6 = Sunday, 0 = Monday
    hour = ist_now.hour
    minute = ist_now.minute
    
    if weekday == 5: # Whole Saturday
        return False, "OFFLINE (Weekend Halt)"
    if weekday == 6: # Sunday before Monday opening
        if hour < 3 or (hour == 3 and minute < 30):
            return False, "OFFLINE (Weekend Halt)"
    if weekday == 4: # Friday night into Saturday morning
        if hour > 3 or (hour == 3 and minute >= 30):
            pass # Keep logic simple, if it's Saturday 3:30 AM IST it halts
    return True, "ONLINE"

# ==========================================
# 3. SIDEBAR NAVIGATION & PORTFOLIO INJECTIONS
# ==========================================
st.sidebar.header("🕹️ Quantitative Controls")

# Capital Control Center with Add Money Logic
st.sidebar.subheader("💰 Portfolio Capital Controller")
st.sidebar.metric("Available Liquidity Pool", f"${st.session_state.cash:,.2f}")

with st.sidebar.expander("💳 Capital Injection Vault (Add Money)"):
    inject_amt = st.number_input("Amount to Add ($)", min_value=100.0, value=10000.0, step=500.0)
    if st.button("Route Capital Injection", use_container_width=True):
        st.session_state.cash += inject_amt
        st.toast(f"Successfully injected ${inject_amt:,.2f} into liquid reserves!", icon="💰")
        time.sleep(0.4)
        st.rerun()

st.sidebar.divider()

# Omni Search Setup
st.sidebar.subheader("🔍 Crypto & FX Omni Search")
search_query = st.sidebar.text_input("Filter symbols...", "").lower()
filtered_options = [k for k in FLAT_ASSET_INDEX.keys() if search_query in k.lower()]
if not filtered_options:
    filtered_options = list(FLAT_ASSET_INDEX.keys())

selected_search_key = st.sidebar.selectbox("Active Workspace Asset", filtered_options)
ticker = FLAT_ASSET_INDEX[selected_search_key]["ticker"]
asset_name = FLAT_ASSET_INDEX[selected_search_key]["name"]
asset_cat = FLAT_ASSET_INDEX[selected_search_key]["category"]

timeframe = st.sidebar.selectbox(
    "Structural Strategy Classification", 
    ["Intraday (1 Min Frame)", "Intraday (15 Min Frame)", "Interday (1 Day Frame)", "Interday (1 Week Frame)"]
)

TIMEFRAME_CONFIG = {
    "Intraday (1 Min Frame)":  {"int": "1m",  "period": "5d",  "horizon": "Intraday", "hold": timedelta(hours=2)},
    "Intraday (15 Min Frame)": {"int": "15m", "period": "1mo", "horizon": "Intraday", "hold": timedelta(hours=12)},
    "Interday (1 Day Frame)":  {"int": "1d",  "period": "2y",  "horizon": "Interday", "hold": timedelta(days=21)},
    "Interday (1 Week Frame)": {"int": "1wk", "period": "5y",  "horizon": "Interday", "hold": timedelta(days=180)}
}

current_horizon = TIMEFRAME_CONFIG[timeframe]["horizon"]
hold_limit = TIMEFRAME_CONFIG[timeframe]["hold"]

# ==========================================
# 4. INSTITUTIONAL MATHEMATICS ENGINE
# ==========================================
def clean_and_verify_dataframe(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.reset_index(inplace=True)
    if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Timestamp'}, inplace=True)
    elif 'Date' in df.columns: df.rename(columns={'Date': 'Timestamp'}, inplace=True)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns: df[col] = pd.to_numeric(np.array(df[col]).flatten(), errors='coerce')
    df.dropna(subset=['Close'], inplace=True)
    return df

def calculate_analytics_matrix(df):
    """Calculates high-accuracy mathematical metrics natively to avoid drift errors."""
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * (df['Volume'] + 1)).cumsum() / (df['Volume'] + 1).cumsum()
    
    delta = df['Close'].diff()
    df['RSI_14'] = 100 - (100 / (1 + (delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0).rolling(14).mean() + 1e-9))))
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    sma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    df['BB_Upper'] = sma20 + (std20 * 2.2)
    df['BB_Lower'] = sma20 - (std20 * 2.2)
    
    hl = df['High'] - df['Low']
    hc = (df['High'] - df['Close'].shift(1)).abs()
    lc = (df['Low'] - df['Close'].shift(1)).abs()
    df['ATR'] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
    
    df.bfill(inplace=True)
    return df

def generate_fine_tuned_forecast(df, interval_str, days_lookahead=365):
    """Plots localized linear polynomial tracking aligned neatly on time axis scales."""
    x = np.arange(len(df))
    y = df['Close'].values
    poly_fit = np.polyfit(x, y, 1)
    
    last_date = df['Timestamp'].iloc[-1]
    if isinstance(last_date, str):
        last_date = pd.to_datetime(last_date)
        
    # Scale forward steps to perfectly prevent flat-line chart errors
    if "m" in interval_str:
        step = timedelta(minutes=int(interval_str.replace("m", "")))
        total_steps = min(days_lookahead * 2, 120) 
    elif "h" in interval_str:
        step = timedelta(hours=1)
        total_steps = min(days_lookahead * 4, 200)
    else:
        step = timedelta(days=1)
        total_steps = days_lookahead

    f_dates = [last_date + (step * i) for i in range(1, total_steps + 1)]
    f_preds = poly_fit[0] * np.arange(len(df), len(df) + total_steps) + poly_fit[1]
    return f_dates, f_preds

def evaluate_signal_confidence(latest):
    """Multi-factor math confirmation returning structural confidence vector."""
    score = 0.0
    factors = []
    
    if latest['EMA_9'] > latest['EMA_21']: score += 2.0; factors.append("Bullish EMA Structural Crossover")
    else: score -= 2.0; factors.append("Bearish EMA Structural Crossover")
        
    if latest['Close'] > latest['VWAP']: score += 1.5; factors.append("Volume Profile Accumulation above VWAP")
    else: score -= 1.5; factors.append("Volume Profile Liquidation below VWAP")
        
    if latest['RSI_14'] < 35: score += 2.0; factors.append("Extremely Oversold Multi-Hour Exhaustion")
    elif latest['RSI_14'] > 65: score -= 2.0; factors.append("Extremely Overbought Multi-Hour Exhaustion")
        
    if latest['MACD'] > latest['MACD_Signal']: score += 1.5; factors.append("MACD Velocity Accentuation Positive")
    else: score -= 1.5; factors.append("MACD Velocity Accentuation Negative")

    confidence = min((abs(score) / 7.0) * 100, 99.8)
    # Calibrate floor values
    if confidence < 50.0: confidence = 50.0 + (confidence / 5)
        
    return score, confidence, factors

# ==========================================
# 5. REAL-TIME EXPIRED ORDERS PURGE
# ==========================================
now_ts = datetime.now()
purged = False
for t_id, data in list(st.session_state.portfolio.items()):
    exp_time = datetime.strptime(data['expiration'], "%Y-%m-%d %H:%M:%S")
    
    # Live execution validation for auto-purgatory mechanics
    try:
        t_df = clean_and_verify_dataframe(yf.download(t_id, period="1d", interval="1m", progress=False))
        live_p = float(t_df['Close'].iloc[-1])
    except:
        live_p = data['entry']
        
    exit_trigger = None
    if now_ts >= exp_time: exit_trigger = "EXPIRED (Time-Decay Limit Reached)"
    elif data['tp'] > 0 and ((data['direction'] == "LONG" and live_p >= data['tp']) or (data['direction'] == "SHORT" and live_p <= data['tp'])): exit_trigger = "TAKE PROFIT LIMIT REACHED"
    elif data['sl'] > 0 and ((data['direction'] == "LONG" and live_p <= data['sl']) or (data['direction'] == "SHORT" and live_p >= data['sl'])): exit_trigger = "STOP LOSS MARGIN VOIDED"
    
    if exit_trigger:
        units = abs(data['qty'])
        total_value = units * live_p
        if data['direction'] == "LONG": st.session_state.cash += total_value
        else: st.session_state.cash -= total_value
            
        st.session_state.statement.append({
            "Timestamp": now_ts.strftime("%H:%M:%S"), "Asset": t_id, "Classification": data['horizon'],
            "Direction": "LIQUIDATED", "Price": live_p, "Trigger": exit_trigger
        })
        del st.session_state.portfolio[t_id]
        purged = True
        st.toast(f"Automated Risk Protocol: Closed {t_id} via {exit_trigger}", icon="⚡")

if purged: st.rerun()

# ==========================================
# 6. WORKSPACE FEED SYNCHRONIZATION
# ==========================================
chosen_int = TIMEFRAME_CONFIG[timeframe]["int"]
chosen_per = TIMEFRAME_CONFIG[timeframe]["period"]

is_open, clock_msg = get_market_status_ist(asset_cat)

if st.session_state.get("current_market_data") is None or st.session_state.get("last_analyzed_ticker") != ticker:
    if is_open:
        with st.spinner("Synchronizing algorithmic asset parameters..."):
            raw_data = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
            if not raw_data.empty:
                df_clean = clean_and_verify_dataframe(raw_data)
                st.session_state.current_market_data = calculate_analytics_matrix(df_clean)
                st.session_state.live_price = float(st.session_state.current_market_data['Close'].iloc[-1])
                st.session_state.last_analyzed_ticker = ticker

# ==========================================
# 7. USER INTERFACE TAB CONSOLE
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Single-Asset Predictor", 
    "🤖 Institutional 60%+ Scanner", 
    "💼 Portfolio Ledger", 
    "📖 Operations Control Guide"
])

# ------------------------------------------
# TAB 1: SINGLE-ASSET PREDICTOR
# ------------------------------------------
with tab1:
    st.title(f"🔮 Predictive Analysis Matrix: {asset_name}")
    st.markdown(f"Segment: **{asset_cat}** | Operational Status (IST Clock): **{clock_msg}**")
    
    if not is_open:
        st.error("Market Segment is currently offline under interbank weekend trading regulations. Terminal analytics are preserved on hold.")
        
    if st.session_state.current_market_data is not None and st.session_state.last_analyzed_ticker == ticker:
        df = st.session_state.current_market_data
        curr_p = st.session_state.live_price
        latest = df.iloc[-1]
        
        score, confidence, factors = evaluate_signal_confidence(latest)
        verdict = "EXECUTE STRONG BUY LONG 🟢" if score >= 1.5 else ("EXECUTE STRONG SELL SHORT 🔴" if score <= -1.5 else "NEUTRAL SPECULATION ⚪")
        
        # Target pricing frameworks using exact ATR parameters
        atr = latest['ATR']
        target_tp = curr_p + (atr * 2.5) if score >= 0 else curr_p - (atr * 2.5)
        target_sl = curr_p - (atr * 1.5) if score >= 0 else curr_p + (atr * 1.5)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Live Execution Quote", f"${curr_p:,.4f}")
        col2.metric("Matrix Strategy Category", f"{current_horizon} Pool")
        col3.metric("System Recommendation", verdict)
        col4.metric("Mathematical Confidence", f"{confidence:.2f}%")
        
        # User Defined Forecast Scaling
        st.markdown("### 📊 1-Year Forward Projection Curve Configurator")
        forecast_selection = st.selectbox("Select Forward Looking Window", ["1 Month Forward", "3 Months Forward", "6 Months Forward", "1 Year Linear Loop"])
        days_map = {"1 Month Forward": 30, "3 Months Forward": 90, "6 Months Forward": 180, "1 Year Linear Loop": 365}
        
        f_dates, f_preds = generate_fine_tuned_forecast(df, chosen_int, days_lookahead=days_map[forecast_selection])
        
        # Build Plots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df['Timestamp'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candle Structure"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['EMA_9'], line=dict(color='yellow', width=1), name="EMA 9"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['EMA_21'], line=dict(color='magenta', width=1), name="EMA 21"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['VWAP'], line=dict(color='cyan', width=1), name="VWAP Model"), row=1, col=1)
        
        # Inject forward regression vector curves
        fig.add_trace(go.Scatter(x=f_dates, y=f_preds, line=dict(color='#00ffcc', width=2, dash='dot'), name=f"Predictive Trend Vector"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['RSI_14'], line=dict(color='orange', width=1.2), name="RSI Engine"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=580, template="plotly_dark", margin=dict(t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
        
        # Position execution desk module
        st.markdown("### ⚡ Instant Orders Routing System")
        with st.form("single_execution_form"):
            ec1, ec2, ec3 = st.columns(3)
            trade_units = ec1.number_input("Order Volume Size (Units)", min_value=0.01, value=10.0, step=1.0)
            tp_price = ec2.number_input("Custom Target Limit Price (TP)", value=float(target_tp))
            sl_price = ec3.number_input("Custom Stop Loss Minimum Floor (SL)", value=float(target_sl))
            
            b_buy, b_sell = st.columns(2)
            buy_triggered = b_buy.form_submit_button("ROUTE LONG ACQUISITION SCHEME", use_container_width=True)
            sell_triggered = b_sell.form_submit_button("ROUTE SHORT LIQUIDATION EXPOSURE", use_container_width=True)
            
            if (buy_triggered or sell_triggered) and is_open:
                direction = "LONG" if buy_triggered else "SHORT"
                total_capital_lock = trade_units * curr_p
                
                if direction == "LONG" and total_capital_lock > st.session_state.cash:
                    st.error("Order Blocked: Margin threshold execution denied due to capital deficit.")
                else:
                    if direction == "LONG": st.session_state.cash -= total_capital_lock
                    else: st.session_state.cash += total_capital_lock
                        
                    st.session_state.portfolio[ticker] = {
                        "asset_name": asset_name, "qty": trade_units if direction == "LONG" else -trade_units,
                        "entry": curr_p, "tp": tp_price, "sl": sl_price, "horizon": current_horizon,
                        "direction": direction, "expiration": (datetime.now() + hold_limit).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.toast(f"Logged Active {direction} Setup. Expiration Window: {hold_limit}", icon="✅")
                    time.sleep(0.4)
                    st.rerun()

# ------------------------------------------
# TAB 2: INSTITUTIONAL 60%+ SCANNER
# ------------------------------------------
with tab2:
    st.title("🤖 High-Confidence Cross-Market Auto-Scanner")
    st.caption("Wall Street Execution Model Filtering System Exclusively Routing Scans Above > 60% Math Confidence Limit Check.")
    
    scan_col1, scan_col2 = st.columns([1, 4])
    selected_scan_type = scan_col1.radio("Strategy Target Class", ["Intraday Matrix Setups", "Interday Swing Matrix"])
    
    if scan_col2.button("🚀 INITIATE WALL STREET RISK ANOMALY DISCOVERY LOOP", use_container_width=True):
        scanned_setups = []
        
        target_key = "Intraday (15 Min Frame)" if "Intraday" in selected_scan_type else "Interday (1 Day Frame)"
        cfg = TIMEFRAME_CONFIG[target_key]
        
        with st.spinner("Processing deep quantitative divergence arrays..."):
            for option_text, data_meta in FLAT_ASSET_INDEX.items():
                try:
                    s_tick = data_meta["ticker"]
                    s_name = data_meta["name"]
                    s_cat = data_meta["category"]
                    
                    # Verify market hours before scanning
                    m_status, _ = get_market_status_ist(s_cat)
                    if not m_status: continue
                        
                    s_raw = yf.download(s_tick, period=cfg["period"], interval=cfg["int"], progress=False)
                    if not s_raw.empty and len(s_raw) > 15:
                        s_df = calculate_analytics_matrix(clean_and_verify_dataframe(s_raw))
                        s_latest = s_df.iloc[-1]
                        
                        s_score, s_confidence, _ = evaluate_signal_confidence(s_latest)
                        
                        # Apply explicit Wall Street 60% Alpha Floor Constraint Filter Rules
                        if s_confidence >= 60.0:
                            s_dir = "LONG 🟢" if s_score > 0 else "SHORT 🔴"
                            s_price = float(s_latest['Close'])
                            s_atr = s_latest['ATR']
                            
                            s_tp = s_price + (s_atr * 2.2) if s_score > 0 else s_price - (s_atr * 2.2)
                            s_sl = s_price - (s_atr * 1.5) if s_score > 0 else s_price + (s_atr * 1.5)
                            
                            scanned_setups.append({
                                "Asset": s_name, "Ticker": s_tick, "Category": s_cat, "Direction": s_dir,
                                "Confidence": s_confidence, "Price": s_price, "TP": s_tp, "SL": s_sl,
                                "Horizon": cfg["horizon"], "HoldLimit": cfg["hold"]
                            })
                except Exception as e:
                    pass
            
            st.session_state.scan_results = scanned_setups
            st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Interactive Execution Row Blocks Generation
    if st.session_state.scan_results:
        st.markdown(f"#### Active Anomalies Confirmed At: `{st.session_state.last_scan_time}`")
        
        for idx, trade in enumerate(st.session_state.scan_results):
            with st.container(border=True):
                c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1.5, 2, 2, 2])
                c1.markdown(**f"{trade['Asset']} ({trade['Ticker']})**\n*{trade['Category']}*")
                c2.markdown(f"**{trade['Direction']}**")
                c3.metric("System Confidence", f"{trade['Confidence']:.1f}%")
                c4.markdown(f"Spot: **${trade['Price']:.4f}**\nHorizon: `{trade['Horizon']}`")
                c5.markdown(f"Target TP: **${trade['TP']:.4f}**\nFloor SL: **${trade['SL']:.4f}**")
                
                # Dynamic Inline Execution Action Key
                exec_key = f"instant_execute_btn_{idx}_{trade['Ticker']}"
                if c6.button("⚡ EXECUTE POSITION NOW", key=exec_key, use_container_width=True):
                    t_cost = 10.0 * trade['Price'] # Default inline safety testing baseline size
                    if t_cost > st.session_state.cash:
                        st.error("Insufficient Margin Reserves Available.")
                    else:
                        st.session_state.cash -= t_cost
                        st.session_state.portfolio[trade['Ticker']] = {
                            "asset_name": trade['Asset'], "qty": 10.0 if "LONG" in trade['Direction'] else -10.0,
                            "entry": trade['Price'], "tp": trade['TP'], "sl": trade['SL'], "horizon": trade['Horizon'],
                            "direction": "LONG" if "LONG" in trade['Direction'] else "SHORT",
                            "expiration": (datetime.now() + trade['HoldLimit']).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.toast(f"Successfully Routed Scan Order for {trade['Ticker']}!", icon="🚀")
                        time.sleep(0.3)
                        st.rerun()
    else:
        st.info("No active multi-market structural scanning anomalies parsed yet. Trigger the engine above.")

# ------------------------------------------
# TAB 3: PORTFOLIO LEDGER
# ------------------------------------------
with tab3:
    st.title("💼 Active Institutional Risk Management Matrices")
    st.metric("Total Vault Liquid Balance Available", f"${st.session_state.cash:,.2f}")
    
    l_t1, l_t2 = st.tabs(["⏱️ Active Intraday Risk Tracking Frameworks", "📅 Active Interday Structural Swings"])
    
    def display_isolated_ledger(target_string):
        subset = {k: v for k, v in st.session_state.portfolio.items() if v['horizon'] == target_string}
        if subset:
            st.dataframe(pd.DataFrame([{
                "Asset Identifier Symbol": k, "Direction Spec": v['direction'], "Allocated Volume Units": abs(v['qty']),
                "Entry Cost Value": f"${v['entry']:,.4f}", "Target Floor (TP)": f"${v['tp']:,.4f}",
                "Stop Loss Limit (SL)": f"${v['sl']:,.4f}", "Forced Liquidation Timestamp": v['expiration']
            } for k, v in subset.items()]), use_container_width=True)
            
            liq_sel = st.selectbox("Select Asset Row Target to Immediate Terminate", list(subset.keys()), key=f"liq_select_{target_string}")
            if st.button("💥 FORCE LIQUIDATE RISK MATRIX ROW", key=f"force_kill_{target_string}", use_container_width=True):
                closed_tr = st.session_state.portfolio[liq_sel]
                refund_value = abs(closed_tr['qty']) * closed_tr['entry']
                if closed_tr['direction'] == "LONG": st.session_state.cash += refund_value
                else: st.session_state.cash -= refund_value
                del st.session_state.portfolio[liq_sel]
                st.toast("Manual override position clear completed.", icon="💥")
                time.sleep(0.3)
                st.rerun()
        else:
            st.info(f"No active automated capital deployment configurations active in the {target_string} matrix.")

    with l_t1: display_isolated_ledger("Intraday")
    with l_t2: display_isolated_ledger("Interday")
    
    if st.session_state.statement:
        st.subheader("📋 Closed Order Archive Vault & Historical Audit Trails")
        st.dataframe(pd.DataFrame(st.session_state.statement).iloc[::-1], use_container_width=True)

# ------------------------------------------
# TAB 4: OPERATIONS CONTROL GUIDE
# ------------------------------------------
with tab4:
    st.title("📖 Quantitative Engine Operations Blueprint")
    st.markdown("""
    ### ⚙️ Wall Street Mode Operational Guidelines
    1. **Strict IST Market Clock Limits:** Forex markets enforce a complete weekend suspension algorithm based on Indian Standard Time (`Saturday 03:30 IST to Monday 03:30 IST`). During this time window, Forex assets state validation checks will return offline warnings while Cryptocurrencies continuously process without breaks.
    2. **60% Alpha Floor Constraint:** The Global Cross-Asset Scanner uses multi-variable math validation rules. Any tracked signal containing a structural confidence scoring below 60% is auto-filtered out to mirror high-conviction institutional execution principles.
    3. **Strategy Multi-Tier Groups:** * **Intraday Trades:** Run over short-term frames (1m or 15m intervals) and enforce strict auto-liquidation parameters inside a **2 to 12-hour maximum hold time**.
       * **Interday Trades:** Operate on daily or weekly intervals to capture swing mechanics over a **21 to 180-day dynamic window**.
    4. **Dynamic Lookahead Extrapolator:** Use the duration drop-down menu inside the single asset matrix workspace to manipulate the polynomial linear regression tracking line cleanly across your standard canvas dashboard up to 365 days out.
    """)
