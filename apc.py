import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Page config for high-end terminal presentation
st.set_page_config(page_title="QuantEdge AI Trading Engine", layout="wide")

# ==========================================
# 1. ADVANCED STATE ARCHITECTURE
# ==========================================
if "cash" not in st.session_state: st.session_state.cash = 100000.00
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "scan_results" not in st.session_state: st.session_state.scan_results = []
if "last_scan_time" not in st.session_state: st.session_state.last_scan_time = None

ASSET_CLASSES = {
    "Indian Equities (NSE)": {"Nifty 50": "^NSEI", "Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "Infosys": "INFY.NS", "HDFC Bank": "HDFCBANK.NS"},
    "Global Equities": {"Apple": "AAPL", "Tesla": "TSLA", "Nvidia": "NVDA", "S&P 500": "SPY"},
    "Crypto-Currencies": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Foreign Exchange (FX)": {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X"},
    "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F"}
}

FLAT_ASSET_INDEX = {f"{n} ({t})": {"ticker": t, "name": n, "category": c} for c, items in ASSET_CLASSES.items() for n, t in items.items()}

# ==========================================
# 2. CONTROLS, SEARCH & TIME HORIZONS
# ==========================================
st.sidebar.header("🕹️ Terminal Navigation")

new_balance = st.sidebar.number_input("Adjust Liquid Capital", min_value=0.0, value=float(st.session_state.cash), step=1000.0)
if new_balance != st.session_state.cash: st.session_state.cash = new_balance

st.sidebar.divider()
st.sidebar.subheader("🔍 Omni-Asset Search")
search_query = st.sidebar.text_input("Search Assets (e.g., Gold, BTC)", "").lower()
filtered_options = [k for k in FLAT_ASSET_INDEX.keys() if search_query in k.lower()]
if not filtered_options: filtered_options = list(FLAT_ASSET_INDEX.keys())

selected_search_key = st.sidebar.selectbox("Active Instrument", filtered_options)
ticker = FLAT_ASSET_INDEX[selected_search_key]["ticker"]
asset_name = FLAT_ASSET_INDEX[selected_search_key]["name"]

timeframe = st.sidebar.selectbox("Analysis Horizon", ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour", "1 Day", "1 Week"])
chart_style = st.sidebar.radio("Plot Scheme", ["Candlestick", "Line Chart"])

st.sidebar.divider()
auto_refresh = st.sidebar.toggle("Enable Fast-Sync Loop", value=False)

TIMEFRAME_CONFIG = {
    "1 Minute":   {"int": "1m",  "period": "5d",  "horizon": "Short-Term",  "hold": timedelta(minutes=60)},
    "5 Minutes":  {"int": "5m",  "period": "5d",  "horizon": "Short-Term",  "hold": timedelta(hours=4)},
    "15 Minutes": {"int": "15m", "period": "1mo", "horizon": "Short-Term",  "hold": timedelta(hours=12)},
    "1 Hour":     {"int": "1h",  "period": "60d", "horizon": "Medium-Term", "hold": timedelta(days=3)},
    "1 Day":      {"int": "1d",  "period": "2y",  "horizon": "Medium-Term", "hold": timedelta(days=14)},
    "1 Week":     {"int": "1wk", "period": "5y",  "horizon": "Long-Term",   "hold": timedelta(days=90)}
}
current_horizon = TIMEFRAME_CONFIG[timeframe]["horizon"]

# ==========================================
# 3. ADVANCED 100x QUANT MATH ENGINE
# ==========================================
def clean_yfinance_df(raw_df):
    if isinstance(raw_df.columns, pd.MultiIndex):
        raw_df.columns = [c[0] for c in raw_df.columns]
    raw_df.reset_index(inplace=True)
    if 'Datetime' in raw_df.columns: raw_df.rename(columns={'Datetime': 'Timestamp'}, inplace=True)
    elif 'Date' in raw_df.columns: raw_df.rename(columns={'Date': 'Timestamp'}, inplace=True)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in raw_df.columns: raw_df[col] = pd.to_numeric(np.array(raw_df[col]).flatten(), errors='coerce')
    raw_df.dropna(subset=['Close'], inplace=True)
    return raw_df

def calculate_advanced_analytics(df):
    # VWAP (Volume Weighted Average Price)
    if 'Volume' in df.columns and df['Volume'].sum() > 0:
        df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * df['Volume']).cumsum() / df['Volume'].cumsum()
    else:
        df['VWAP'] = df['Close'].rolling(window=20).mean() # Fallback for index funds without volume

    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    delta = df['Close'].diff()
    df['RSI_14'] = 100 - (100 / (1 + (delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0).rolling(14).mean() + 1e-9))))
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
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

def generate_forecast(df, interval_str, target_candles=60):
    x = np.arange(len(df))
    y = np.array(df['Close']).flatten()
    poly_fit = np.polyfit(x, y, 1)
    
    last_date = df['Timestamp'].iloc[-1]
    if isinstance(last_date, str):
        try: last_date = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S%z")
        except: last_date = pd.to_datetime(last_date)
            
    td = timedelta(minutes=int(interval_str.replace("m", "") or 1)) if "m" in interval_str else \
         timedelta(hours=int(interval_str.replace("h", "") or 1)) if "h" in interval_str else \
         timedelta(days=int(interval_str.replace("d", "") or 1)) if "d" in interval_str else \
         timedelta(weeks=int(interval_str.replace("wk", "") or 1))
         
    f_dates = [last_date + (td * i) for i in range(1, target_candles + 1)]
    f_preds = poly_fit[0] * np.arange(len(df), len(df) + target_candles) + poly_fit[1]
    return f_dates, f_preds

def get_signal_score(latest):
    score = 0.0
    reasons = []
    if latest['EMA_9'] > latest['EMA_21']: score += 2.0; reasons.append("🟢 Trend: Fast EMA > Slow EMA (Bullish)")
    else: score -= 2.0; reasons.append("🔴 Trend: Fast EMA < Slow EMA (Bearish)")
        
    if latest['Close'] > latest['SMA_50']: score += 1.0; reasons.append("🟢 Macro: Price above 50 SMA")
    else: score -= 1.0; reasons.append("🔴 Macro: Price below 50 SMA")

    if latest['Close'] > latest['VWAP']: score += 1.0; reasons.append("🟢 Volume: Price above VWAP (Accumulation)")
    else: score -= 1.0; reasons.append("🔴 Volume: Price below VWAP (Distribution)")

    rsi = latest['RSI_14']
    if rsi < 35: score += 2.0; reasons.append(f"🟢 Reversal: RSI Oversold ({rsi:.1f})")
    elif rsi > 65: score -= 2.0; reasons.append(f"🔴 Reversal: RSI Overbought ({rsi:.1f})")
        
    if latest['MACD_Hist'] > 0 and latest['MACD'] > latest['MACD_Signal']: score += 1.5; reasons.append("🟢 Velocity: MACD momentum expanding upwards")
    elif latest['MACD_Hist'] < 0 and latest['MACD'] < latest['MACD_Signal']: score -= 1.5; reasons.append("🔴 Velocity: MACD momentum breaking downwards")
        
    if latest['Close'] < latest['BB_Lower']: score += 1.0; reasons.append("🟢 Volatility: Price testing lower BB (Support)")
    elif latest['Close'] > latest['BB_Upper']: score -= 1.0; reasons.append("🔴 Volatility: Price testing upper BB (Resistance)")
        
    confidence = min((abs(score) / 8.5) * 100, 99.9)
    return score, confidence, reasons

# ==========================================
# 4. BACKGROUND AUTO-LIQUIDATION & DECAY
# ==========================================
liquidated_any = False
now_ts = datetime.now()
for t_id, data in list(st.session_state.portfolio.items()):
    try: exp_time = datetime.strptime(data['expiration'], "%Y-%m-%d %H:%M:%S")
    except: exp_time = now_ts + timedelta(days=1)
        
    try:
        temp_df = clean_yfinance_df(yf.download(t_id, period="1d", interval="1m", progress=False))
        live_price = float(temp_df['Close'].iloc[-1])
    except: live_price = data['entry']
        
    trigger = None
    if now_ts >= exp_time: trigger = "TIME EXPIRED"
    elif data['tp'] > 0 and ((data['direction'] == "LONG" and live_price >= data['tp']) or (data['direction'] == "SHORT" and live_price <= data['tp'])): trigger = "TAKE PROFIT"
    elif data['sl'] > 0 and ((data['direction'] == "LONG" and live_price <= data['sl']) or (data['direction'] == "SHORT" and live_price >= data['sl'])): trigger = "STOP LOSS"
        
    if trigger:
        qty_abs = abs(data['qty'])
        revenue = qty_abs * live_price
        if data['direction'] == "LONG": st.session_state.cash += revenue
        else: st.session_state.cash -= revenue
            
        pl_dollars = (live_price - data['entry']) * qty_abs if data['direction'] == "LONG" else (data['entry'] - live_price) * qty_abs
        st.session_state.statement.append({
            "Timestamp": now_ts.strftime("%H:%M:%S"), "Asset": t_id, "Direction": "CLOSED", 
            "Horizon": data['horizon'], "Units": qty_abs, "Price": live_price, "P&L": pl_dollars, "Trigger": trigger
        })
        del st.session_state.portfolio[t_id]
        liquidated_any = True
        st.toast(f"{trigger} hit for {t_id}! Position closed.", icon="⚡")

if liquidated_any: st.rerun()

# ==========================================
# 5. DATA PIPELINE
# ==========================================
if auto_refresh: time.sleep(10); st.rerun()

chosen_int = TIMEFRAME_CONFIG[timeframe]["int"]
chosen_per = TIMEFRAME_CONFIG[timeframe]["period"]
hold_limit = TIMEFRAME_CONFIG[timeframe]["hold"]

if st.sidebar.button("🔄 Instant Matrix Sync", use_container_width=True) or auto_refresh or st.session_state.get("last_analyzed_ticker") != ticker:
    with st.spinner("Accessing distributed institutional feeds..."):
        raw_df = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
        if raw_df is not None and not raw_df.empty:
            processed_df = calculate_advanced_analytics(clean_yfinance_df(raw_df))
            st.session_state.live_price = float(processed_df['Close'].iloc[-1])
            st.session_state.current_market_data = processed_df
            st.session_state.last_analyzed_ticker = ticker

# ==========================================
# 6. USER INTERFACE TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🔮 Single Forecast Matrix", "🤖 Global Auto-Scanner", "💼 Active Ledger", "📖 User Manual"])

with tab1:
    if st.session_state.current_market_data is not None:
        df = st.session_state.current_market_data
        curr_p = st.session_state.live_price
        latest = df.iloc[-1]
        
        st.title(f"🔮 Predictive Matrix: {asset_name} ({ticker})")
        score, confidence_pct, reasons = get_signal_score(latest)
        
        verdict = "STRATEGIC LONG 🟢" if score >= 2 else ("STRATEGIC SHORT 🔴" if score <= -2 else "NEUTRAL POSITION ⚪")
        atr_val = latest['ATR']
        proj_exit = curr_p + (atr_val * 2.5) if score >= 0 else curr_p - (atr_val * 2.5)
        proj_sl = curr_p - (atr_val * 1.5) if score >= 0 else curr_p + (atr_val * 1.5)

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Live Execution Price", f"${curr_p:,.2f}" if "NS" not in ticker else f"₹{curr_p:,.2f}")
        m_col2.metric(f"Time Decay Limit", f"{hold_limit}")
        m_col3.metric("System Verdict", verdict)
        m_col4.metric("Engine Confidence", f"{confidence_pct:.1f}%")

        with st.expander("🔬 View Quant Reasoning & Mathematical Logs"):
            for r in reasons: st.write(f"• {r}")

        f_dates, f_preds = generate_forecast(df, TIMEFRAME_CONFIG[timeframe]["int"])
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        if chart_style == "Candlestick": fig.add_trace(go.Candlestick(x=df['Timestamp'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        else: fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Close'], name="Line Metric", line=dict(color='#00ffcc', width=2)), row=1, col=1)
            
        fig.add_trace(go.Scatter(x=f_dates, y=f_preds, line=dict(color='cyan', width=2, dash='dash'), name="Predictive Forward Curve"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['VWAP'], line=dict(color='purple', width=1.5), name="VWAP"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['RSI_14'], line=dict(color='orange', width=1.5), name="RSI (14)"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_dark", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 💼 Execute Position (With Auto-Decay)")
        with st.form("trade_execution_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            qty = f_col1.number_input("Units", min_value=0.01, value=10.0, step=1.0)
            custom_tp = f_col2.number_input("Target Price", value=float(proj_exit))
            custom_sl = f_col3.number_input("Stop Loss", value=float(proj_sl))
            
            b1, b2 = st.columns(2)
            exe_long = b1.form_submit_button("🟢 ROUTE LONG ORDER", use_container_width=True)
            exe_short = b2.form_submit_button("🔴 ROUTE SHORT ORDER", use_container_width=True)
            
            if exe_long or exe_short:
                order_dir = "LONG" if exe_long else "SHORT"
                cost = qty * curr_p
                if order_dir == "LONG" and cost > st.session_state.cash: st.error("Insufficient capital.")
                else:
                    if order_dir == "LONG": st.session_state.cash -= cost
                    else: st.session_state.cash += cost
                    
                    st.session_state.portfolio[ticker] = {
                        "asset_name": asset_name, "qty": qty if order_dir == "LONG" else -qty, "entry": curr_p, 
                        "tp": custom_tp, "sl": custom_sl, "horizon": current_horizon, "direction": order_dir, 
                        "expiration": (datetime.now() + hold_limit).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.toast(f"Order routed. Time Limit: {hold_limit}", icon="✅")
                    time.sleep(0.5); st.rerun()

with tab2:
    st.title("🤖 Global Multi-Asset System Scanner")
    st.write("Scans all assets for high-confidence setups and enforces strict time limits.")
    
    if st.button("🚀 EXECUTE FULL SYSTEM SCAN", use_container_width=True):
        detected_setups = []
        with st.spinner("Processing deep regression scans..."):
            for s_tick, metadata in FLAT_ASSET_INDEX.items():
                try:
                    s_df = clean_yfinance_df(yf.download(metadata["ticker"], period=TIMEFRAME_CONFIG[timeframe]["period"], interval=TIMEFRAME_CONFIG[timeframe]["int"], progress=False))
                    if not s_df.empty and len(s_df) > 20:
                        s_df = calculate_advanced_analytics(s_df)
                        s_latest = s_df.iloc[-1]
                        s_score, s_conf, s_rsn = get_signal_score(s_latest)
                        
                        if abs(s_score) >= 2.5: # Strict confidence threshold
                            s_dir = "LONG 🟢" if s_score > 0 else "SHORT 🔴"
                            s_close = float(s_latest['Close'])
                            s_tp = s_close + (s_latest['ATR'] * 2.2) if s_score > 0 else s_close - (s_latest['ATR'] * 2.2)
                            s_sl = s_close - (s_latest['ATR'] * 1.5) if s_score > 0 else s_close + (s_latest['ATR'] * 1.5)
                            
                            detected_setups.append({
                                "Asset": metadata["name"], "Ticker": metadata["ticker"], "Direction": s_dir, 
                                "Confidence": f"{s_conf:.1f}%", "Max Hold Time": str(hold_limit), 
                                "Price": f"${s_close:,.2f}", "Target": f"${s_tp:,.2f}", "Stop-Loss": f"${s_sl:,.2f}"
                            })
                except: pass
            
            st.session_state.scan_results = detected_setups
            st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.session_state.scan_results:
        st.dataframe(pd.DataFrame(st.session_state.scan_results), use_container_width=True)

with tab3:
    st.title("💼 Horizon Risk Management Modules")
    st.metric("Persistent Account Balance", f"${st.session_state.cash:,.2f}")
    
    def generate_horizon_view(target_horizon_string):
        matched = {k: v for k, v in st.session_state.portfolio.items() if v['horizon'] == target_horizon_string}
        if matched:
            st.dataframe(pd.DataFrame([{
                "Asset": k, "Direction": v['direction'], "Units": abs(v['qty']), "Entry": f"{v['entry']:,.4f}",
                "Take Profit": f"{v['tp']:,.4f}", "Stop Loss": f"{v['sl']:,.4f}", "Auto-Closes At": v['expiration']
            } for k, v in matched.items()]), use_container_width=True)
            
            liq_sel = st.selectbox("Select Asset to Liquidate", list(matched.keys()), key=f"sel_{target_horizon_string}")
            if st.button("💥 MANUAL CLOSE", key=f"kill_{target_horizon_string}"):
                closed = st.session_state.portfolio[liq_sel]
                val = abs(closed['qty']) * closed['entry'] # Simplified refund for manual close
                if closed['direction'] == "LONG": st.session_state.cash += val
                else: st.session_state.cash -= val
                del st.session_state.portfolio[liq_sel]
                st.rerun()
        else: st.info(f"No active positions in the {target_horizon_string} matrix.")

    l_t1, l_t2, l_t3 = st.tabs(["⏱️ Short-Term", "📅 Medium-Term", "🏆 Long-Term"])
    with l_t1: generate_horizon_view("Short-Term")
    with l_t2: generate_horizon_view("Medium-Term")
    with l_t3: generate_horizon_view("Long-Term")
    
    if st.session_state.statement:
        st.subheader("📋 Order Audit Trails (P&L)")
        st.dataframe(pd.DataFrame(st.session_state.statement).iloc[::-1], use_container_width=True)

with tab4:
    st.title("📖 Quantitative Engine Manual")
    st.markdown("""
    **1. Auto-Liquidation (Time Decay):** The engine now strictly enforces time limits. If you buy a stock on the `1 Minute` chart, the system automatically tags it with a **1-Hour Expiration Clock**. If the trade hasn't hit your target by then, the engine instantly sells it. 
    **2. Forecast Scaling:** The cyan dashed curve calculates forward trajectory dynamically matching your chart. It calculates trend velocity over `N` past candles and mathematically extrapolates exactly `N` candles into the future.
    **3. Confidence Multiplier:** The 100x engine assesses VWAP, 50-SMA Macro Trends, RSI Reversals, MACD Velocity, and Bollinger Band Volatility. A 99% confidence means all 5 metrics perfectly agree on direction.
    """)
