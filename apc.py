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
st.set_page_config(page_title="QuantEdge Master Terminal", layout="wide")

# ==========================================
# 1. COMPREHENSIVE SESSION STATE & 100-ASSET MATRIX
# ==========================================
if "cash" not in st.session_state: st.session_state.cash = 100000.00
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "scan_results" not in st.session_state: st.session_state.scan_results = []
if "last_scan_time" not in st.session_state: st.session_state.last_scan_time = None

ASSET_CLASSES = {
    "Crypto-Currencies (24/7)": {
        "Bitcoin / USD": "BTC-USD", "Ethereum / USD": "ETH-USD", "Solana / USD": "SOL-USD", 
        "Ripple / USD": "XRP-USD", "Cardano / USD": "ADA-USD", "Dogecoin / USD": "DOGE-USD",
        "Polkadot / USD": "DOT-USD", "Polygon / USD": "MATIC-USD", "Litecoin / USD": "LTC-USD",
        "Shiba Inu / USD": "SHIB-USD", "Avalanche / USD": "AVAX-USD", "Chainlink / USD": "LINK-USD",
        "Uniswap / USD": "UNI-USD", "Cosmos / USD": "ATOM-USD", "Monero / USD": "XMR-USD",
        "Ethereum Classic": "ETC-USD", "Bitcoin Cash": "BCH-USD", "Stellar / USD": "XLM-USD",
        "Tron / USD": "TRX-USD", "Filecoin / USD": "FIL-USD"
    },
    "Foreign Exchange (FX)": {
        "EUR / USD": "EURUSD=X", "GBP / USD": "GBPUSD=X", "USD / JPY": "JPY=X", 
        "AUD / USD": "AUDUSD=X", "USD / CAD": "CAD=X", "USD / CHF": "CHF=X", 
        "NZD / USD": "NZDUSD=X", "EUR / GBP": "EURGBP=X", "EUR / JPY": "EURJPY=X", 
        "GBP / JPY": "GBPJPY=X", "AUD / JPY": "AUDJPY=X", "EUR / AUD": "EURAUD=X", 
        "EUR / CAD": "EURCAD=X", "EUR / CHF": "EURCHF=X", "AUD / CAD": "AUDCAD=X", 
        "CAD / JPY": "CADJPY=X", "CHF / JPY": "CHFJPY=X", "GBP / CHF": "GBPCHF=X", 
        "GBP / CAD": "GBPCAD=X", "GBP / AUD": "GBPAUD=X"
    },
    "Global Commodities": {
        "Gold (XAU)": "GC=F", "Silver": "SI=F", "Crude Oil (WTI)": "CL=F", 
        "Natural Gas": "NG=F", "Copper": "HG=F", "Platinum": "PL=F", 
        "Palladium": "PA=F", "Corn": "ZC=F", "Wheat": "ZW=F", "Soybeans": "ZS=F", 
        "Sugar": "SB=F", "Coffee": "KC=F", "Cotton": "CT=F", "Cocoa": "CC=F", 
        "Heating Oil": "HO=F", "RBOB Gasoline": "RB=F", "Live Cattle": "LE=F", 
        "Lean Hogs": "HE=F", "Feeder Cattle": "GF=F", "Rough Rice": "ZR=F"
    },
    "Global Equities": {
        "Apple Inc.": "AAPL", "Microsoft": "MSFT", "Alphabet (Google)": "GOOGL",
        "Amazon": "AMZN", "Nvidia": "NVDA", "Meta Platforms": "META", "Tesla": "TSLA",
        "Berkshire Hathaway": "BRK-B", "TSMC": "TSM", "Visa": "V", "JPMorgan Chase": "JPM",
        "Walmart": "WMT", "Johnson & Johnson": "JNJ", "Mastercard": "MA", "Procter & Gamble": "PG",
        "UnitedHealth": "UNH", "Home Depot": "HD", "Exxon Mobil": "XOM", "Disney": "DIS", "Bank of America": "BAC"
    },
    "Indian Equities (NSE)": {
        "Nifty 50 Index": "^NSEI", "Reliance Ind": "RELIANCE.NS", "TCS": "TCS.NS",
        "HDFC Bank": "HDFCBANK.NS", "Infosys": "INFY.NS", "ICICI Bank": "ICICIBANK.NS",
        "SBI": "SBIN.NS", "Bharti Airtel": "BHARTIARTL.NS", "ITC": "ITC.NS",
        "Larsen & Toubro": "LT.NS", "Bajaj Finance": "BAJFINANCE.NS", "HUL": "HINDUNILVR.NS",
        "Maruti Suzuki": "MARUTI.NS", "Axis Bank": "AXISBANK.NS", "Sun Pharma": "SUNPHARMA.NS",
        "Titan": "TITAN.NS", "UltraTech Cement": "ULTRACEMCO.NS", "Tata Motors": "TATAMOTORS.NS",
        "Wipro": "WIPRO.NS", "Kotak Mahindra": "KOTAKBANK.NS"
    }
}

FLAT_ASSET_INDEX = {f"{n} ({t})": {"ticker": t, "name": n, "category": c} for c, items in ASSET_CLASSES.items() for n, t in items.items()}

# ==========================================
# 2. IST TIME CLOCK & MARKET STATUS RULES
# ==========================================
def get_market_status_ist(category):
    if "Crypto" in category: return True, "ONLINE (24/7)"
    ist_now = datetime.now(pytz.timezone('Asia/Kolkata'))
    weekday = ist_now.weekday() 
    hour = ist_now.hour
    minute = ist_now.minute
    
    if weekday == 5: return False, "OFFLINE (Weekend Halt)"
    if weekday == 6:
        if hour < 3 or (hour == 3 and minute < 30): return False, "OFFLINE (Weekend Halt)"
    return True, "ONLINE"

# ==========================================
# 3. SIDEBAR NAVIGATION & LIVE CONTROLS
# ==========================================
st.sidebar.header("🕹️ Quantitative Controls")

st.sidebar.subheader("🔍 Omni-Asset Search")
search_query = st.sidebar.text_input("Filter symbols (e.g., Gold, Reliance)...", "").lower()
filtered_options = [k for k in FLAT_ASSET_INDEX.keys() if search_query in k.lower()]
if not filtered_options: filtered_options = list(FLAT_ASSET_INDEX.keys())

selected_search_key = st.sidebar.selectbox("Active Workspace Asset", filtered_options)
ticker = FLAT_ASSET_INDEX[selected_search_key]["ticker"]
asset_name = FLAT_ASSET_INDEX[selected_search_key]["name"]
asset_cat = FLAT_ASSET_INDEX[selected_search_key]["category"]

timeframe = st.sidebar.selectbox(
    "Structural Strategy Classification", 
    ["Intraday (1 Min Frame)", "Intraday (15 Min Frame)", "Interday (1 Day Frame)", "Interday (1 Week Frame)"]
)

st.sidebar.divider()
find_now_pressed = st.sidebar.button("⚡ FIND NOW (Live Sync)", type="primary", use_container_width=True)
auto_refresh = st.sidebar.toggle("Enable Background Auto-Sync", value=False)

TIMEFRAME_CONFIG = {
    "Intraday (1 Min Frame)":  {"int": "1m",  "period": "5d",  "horizon": "Intraday", "hold": timedelta(hours=2), "hold_str": "2 Hours"},
    "Intraday (15 Min Frame)": {"int": "15m", "period": "1mo", "horizon": "Intraday", "hold": timedelta(hours=12), "hold_str": "12 Hours"},
    "Interday (1 Day Frame)":  {"int": "1d",  "period": "2y",  "horizon": "Interday", "hold": timedelta(days=21), "hold_str": "21 Days"},
    "Interday (1 Week Frame)": {"int": "1wk", "period": "5y",  "horizon": "Interday", "hold": timedelta(days=180), "hold_str": "6 Months"}
}

current_horizon = TIMEFRAME_CONFIG[timeframe]["horizon"]
hold_limit = TIMEFRAME_CONFIG[timeframe]["hold"]
hold_str = TIMEFRAME_CONFIG[timeframe]["hold_str"]

# ==========================================
# 4. UPGRADED MATHEMATICS & FFT ENGINE
# ==========================================
def clean_and_verify_dataframe(df):
    if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
    df.reset_index(inplace=True)
    if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Timestamp'}, inplace=True)
    elif 'Date' in df.columns: df.rename(columns={'Date': 'Timestamp'}, inplace=True)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns: df[col] = pd.to_numeric(np.array(df[col]).flatten(), errors='coerce')
    df.dropna(subset=['Close'], inplace=True)
    return df

def calculate_analytics_matrix(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    if df['Volume'].sum() > 0:
        df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * df['Volume']).cumsum() / df['Volume'].cumsum()
    else:
        df['VWAP'] = df['Close'].rolling(window=14).mean()
    
    delta = df['Close'].diff()
    df['RSI_14'] = 100 - (100 / (1 + (delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0).rolling(14).mean() + 1e-9))))
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    sma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    df['BB_Upper'] = sma20 + (std20 * 2.0)
    df['BB_Lower'] = sma20 - (std20 * 2.0)
    
    hl, hc, lc = df['High'] - df['Low'], (df['High'] - df['Close'].shift(1)).abs(), (df['Low'] - df['Close'].shift(1)).abs()
    df['ATR'] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
    
    df['KC_Upper'] = df['EMA_21'] + (df['ATR'] * 1.5)
    df['KC_Lower'] = df['EMA_21'] - (df['ATR'] * 1.5)
    df['Squeeze_Active'] = (df['BB_Upper'] < df['KC_Upper']) & (df['BB_Lower'] > df['KC_Lower'])
    
    # Dynamic Support and Resistance Channels (20-period Min/Max)
    df['Resistance'] = df['High'].rolling(window=20).max()
    df['Support'] = df['Low'].rolling(window=20).min()
    
    df.bfill(inplace=True)
    return df

def generate_cyclical_harmonic_forecast(ticker_symbol, df_current, days_lookahead=365):
    try:
        macro_raw = yf.download(ticker_symbol, period="2y", interval="1d", progress=False)
        macro_df = clean_and_verify_dataframe(macro_raw) if not macro_raw.empty else df_current.copy()
    except: macro_df = df_current.copy()
        
    prices = macro_df['Close'].values
    n = len(prices)
    t = np.arange(0, n)
    slope, intercept = np.polyfit(t, prices, 1)
    detrended = prices - (slope * t + intercept)
    
    fft_vals = np.fft.fft(detrended)
    frequencies = np.fft.fftfreq(n)
    idx = np.argsort(np.absolute(fft_vals))[::-1]
    
    future_steps = int(days_lookahead)
    t_ext = np.arange(0, n + future_steps)
    harmonic_wave = np.zeros(t_ext.size)
    
    for i in idx[:12]:
        amplitude = np.absolute(fft_vals[i]) / n
        phase = np.angle(fft_vals[i])
        harmonic_wave += amplitude * np.cos(2 * np.pi * frequencies[i] * t_ext + phase)
        
    full_prediction = harmonic_wave + (slope * t_ext + intercept)
    future_predictions = full_prediction[n:]
    
    last_price = float(df_current['Close'].iloc[-1])
    current_atr = float(df_current['ATR'].iloc[-1])
    max_variance = current_atr * days_lookahead * 0.15 
    
    future_predictions = np.clip(future_predictions, last_price - max_variance, last_price + max_variance)
    
    last_date = df_current['Timestamp'].iloc[-1]
    if isinstance(last_date, str): last_date = pd.to_datetime(last_date)
    time_step = timedelta(days=1) if days_lookahead > 30 else timedelta(hours=12)
    future_dates = [last_date + (time_step * i) for i in range(1, future_steps + 1)]
    
    return future_dates, future_predictions

def evaluate_signal_confidence(latest):
    score = 0.0
    factors = []
    
    if latest.get('EMA_9', 0) > latest.get('EMA_21', 0): score += 2.0; factors.append("📈 Bullish EMA Structural Crossover")
    else: score -= 2.0; factors.append("📉 Bearish EMA Structural Crossover")
        
    vwap_val = latest.get('VWAP', latest.get('Close', 1))
    close_val = latest.get('Close', 1)
    dist_to_vwap = abs(close_val - vwap_val) / (vwap_val + 1e-9)
    
    if dist_to_vwap > 0.05: score -= 1.0; factors.append("⚠️ Overextended from VWAP Anchor (Reversion Risk)")
    elif close_val > vwap_val: score += 1.5; factors.append("📊 Volume Profile Accumulation (Above VWAP)")
    else: score -= 1.5; factors.append("📊 Volume Profile Liquidation (Below VWAP)")
        
    rsi_val = latest.get('RSI_14', 50)
    if rsi_val < 35: score += 2.5; factors.append("⚡ Highly Oversold Multi-Hour Exhaustion")
    elif rsi_val > 65: score -= 2.5; factors.append("⚡ Highly Overbought Multi-Hour Exhaustion")
        
    if latest.get('MACD', 0) > latest.get('MACD_Signal', 0): score += 1.5; factors.append("🚀 Positive MACD Velocity Accentuation")
    else: score -= 1.5; factors.append("🩸 Negative MACD Velocity Accentuation")
        
    if latest.get('Squeeze_Active', False):
        factors.append("🔥 VOLATILITY SQUEEZE DETECTED: Explosive Breakout Imminent")
        score *= 1.2 

    confidence = min((abs(score) / 7.5) * 100, 99.8)
    if confidence < 50.0: confidence = 50.0 + (confidence / 5)
    return score, confidence, factors

# ==========================================
# 5. REAL-TIME EXPIRED ORDERS PURGE & LIVE P/L
# ==========================================
now_ts = datetime.now()
purged = False

# Batch fetch live prices for the portfolio to calculate Live P/L
portfolio_live_prices = {}
if st.session_state.portfolio:
    try:
        port_tickers = " ".join(list(st.session_state.portfolio.keys()))
        live_port_data = yf.download(port_tickers, period="1d", interval="1m", progress=False)
        if isinstance(live_port_data.columns, pd.MultiIndex):
            for t_id in st.session_state.portfolio.keys():
                try: portfolio_live_prices[t_id] = float(live_port_data['Close'][t_id].dropna().iloc[-1])
                except: pass
        else:
            t_id = list(st.session_state.portfolio.keys())[0]
            try: portfolio_live_prices[t_id] = float(live_port_data['Close'].dropna().iloc[-1])
            except: pass
    except: pass

for t_id, data in list(st.session_state.portfolio.items()):
    exp_time = datetime.strptime(data['expiration'], "%Y-%m-%d %H:%M:%S")
    live_p = portfolio_live_prices.get(t_id, data['entry'])
        
    exit_trigger = None
    if now_ts >= exp_time: exit_trigger = "EXPIRED (Time-Decay Limit)"
    elif data['tp'] > 0 and ((data['direction'] == "LONG" and live_p >= data['tp']) or (data['direction'] == "SHORT" and live_p <= data['tp'])): exit_trigger = "TARGET HIT"
    elif data['sl'] > 0 and ((data['direction'] == "LONG" and live_p <= data['sl']) or (data['direction'] == "SHORT" and live_p >= data['sl'])): exit_trigger = "STOP LOSS TRIGGERED"
    
    if exit_trigger:
        units = abs(data['qty'])
        total_value = units * live_p
        if data['direction'] == "LONG": st.session_state.cash += total_value
        else: st.session_state.cash -= total_value
            
        st.session_state.statement.append({
            "Timestamp": now_ts.strftime("%H:%M:%S"), "Asset": t_id, "Classification": data.get('horizon', 'Unknown'),
            "Direction": "LIQUIDATED", "Price": live_p, "Trigger": exit_trigger
        })
        del st.session_state.portfolio[t_id]
        purged = True
        st.toast(f"Risk Protocol: Closed {t_id} via {exit_trigger}", icon="⚡")

if purged: st.rerun()

# ==========================================
# 6. WORKSPACE FEED SYNCHRONIZATION
# ==========================================
chosen_int = TIMEFRAME_CONFIG[timeframe]["int"]
chosen_per = TIMEFRAME_CONFIG[timeframe]["period"]
is_open, clock_msg = get_market_status_ist(asset_cat)

if auto_refresh: time.sleep(10); st.rerun()

if find_now_pressed or st.session_state.get("current_market_data") is None or st.session_state.get("last_analyzed_ticker") != ticker:
    with st.spinner(f"Executing Live Market Sync for {ticker}..."):
        raw_data = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
        if not raw_data.empty:
            df_clean = clean_and_verify_dataframe(raw_data)
            st.session_state.current_market_data = calculate_analytics_matrix(df_clean)
            st.session_state.live_price = float(st.session_state.current_market_data['Close'].iloc[-1])
            st.session_state.last_analyzed_ticker = ticker
            if find_now_pressed: st.toast("Live Matrix Synchronization Complete.", icon="⚡")

# ==========================================
# 7. USER INTERFACE TAB CONSOLE
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Single-Asset Predictor", 
    "🤖 100-Asset Multi-Scanner", 
    "💼 Portfolio Ledger & Live P/L", 
    "📖 Operations Guide"
])

with tab1:
    st.title(f"🔮 Predictive Analysis Matrix: {asset_name}")
    st.markdown(f"Segment: **{asset_cat}** | Operational Status (IST Clock): **{clock_msg}**")
    
    if not is_open: st.warning("Market Segment is offline under weekend trading regulations. Execution disabled.")
        
    if st.session_state.current_market_data is not None and st.session_state.last_analyzed_ticker == ticker:
        df = st.session_state.current_market_data
        curr_p = st.session_state.live_price
        latest = df.iloc[-1]
        
        score, confidence, factors = evaluate_signal_confidence(latest)
        verdict = "EXECUTE STRONG BUY LONG 🟢" if score >= 1.5 else ("EXECUTE STRONG SELL SHORT 🔴" if score <= -1.5 else "NEUTRAL SPECULATION ⚪")
        
        atr = latest.get('ATR', 0)
        target_tp = curr_p + (atr * 2.5) if score >= 0 else curr_p - (atr * 2.5)
        target_sl = curr_p - (atr * 1.5) if score >= 0 else curr_p + (atr * 1.5)
        sup = latest.get('Support', curr_p)
        res = latest.get('Resistance', curr_p)
        
        # Comprehensive Execution Data Dashboard
        st.markdown("### 🎯 Trade Parameters & Technical Levels")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Optimal Entry (Live)", f"${curr_p:,.4f}")
        col2.metric("Target (Take Profit)", f"${target_tp:,.4f}")
        col3.metric("Floor (Stop Loss)", f"${target_sl:,.4f}")
        col4.metric("Mathematical Confidence", f"{confidence:.2f}%")
        
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("System Recommendation", verdict)
        col6.metric("Max Hold Duration", f"{hold_str}")
        col7.metric("Dynamic Support", f"${sup:,.4f}")
        col8.metric("Dynamic Resistance", f"${res:,.4f}")
        
        st.markdown("### 📋 Quant Rationale (Reasons for Trade)")
        st.markdown(f"**Structural Trajectory:** Formulating a setup with **{confidence:.2f}%** conviction based on strict algorithmic alignment.")
        for factor in factors: st.markdown(f"- {factor}")
            
        st.markdown("### 📊 Advanced Damped Harmonic Forecast Curve")
        forecast_selection = st.selectbox("Select Cyclical Lookahead Window", ["1 Month Cyclical Horizon", "3 Months Cyclical Horizon", "6 Months Cyclical Horizon", "1 Year Macro Advanced Loop"])
        days_map = {"1 Month Cyclical Horizon": 30, "3 Months Cyclical Horizon": 90, "6 Months Cyclical Horizon": 180, "1 Year Macro Advanced Loop": 365}
        
        f_dates, f_preds = generate_cyclical_harmonic_forecast(ticker, df, days_lookahead=days_map[forecast_selection])
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df['Timestamp'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candles"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['VWAP'], line=dict(color='cyan', width=1), name="VWAP Anchor"), row=1, col=1)
        fig.add_trace(go.Scatter(x=f_dates, y=f_preds, line=dict(color='#00ffcc', width=2, dash='dot'), name="FFT Harmonic Projection"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['RSI_14'], line=dict(color='orange', width=1.2), name="RSI Tracker"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=580, template="plotly_dark", margin=dict(t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### ⚡ Instant Orders Routing System")
        with st.form("single_execution_form"):
            ec1, ec2, ec3 = st.columns(3)
            trade_units = ec1.number_input("Order Volume Size (Units)", min_value=0.01, value=10.0, step=1.0)
            tp_price = ec2.number_input("Custom Target Limit Price (TP)", value=float(target_tp))
            sl_price = ec3.number_input("Custom Stop Loss Minimum Floor (SL)", value=float(target_sl))
            
            b_buy, b_sell = st.columns(2)
            buy_triggered = b_buy.form_submit_button("ROUTE LONG ACQUISITION SCHEME", use_container_width=True, disabled=not is_open)
            sell_triggered = b_sell.form_submit_button("ROUTE SHORT LIQUIDATION EXPOSURE", use_container_width=True, disabled=not is_open)
            
            if (buy_triggered or sell_triggered) and is_open:
                direction = "LONG" if buy_triggered else "SHORT"
                total_capital_lock = trade_units * curr_p
                
                if direction == "LONG" and total_capital_lock > st.session_state.cash: st.error("Margin deficit.")
                else:
                    if direction == "LONG": st.session_state.cash -= total_capital_lock
                    else: st.session_state.cash += total_capital_lock
                        
                    st.session_state.portfolio[ticker] = {
                        "asset_name": asset_name, "qty": trade_units if direction == "LONG" else -trade_units,
                        "entry": curr_p, "tp": tp_price, "sl": sl_price, "horizon": current_horizon,
                        "direction": direction, "expiration": (datetime.now() + hold_limit).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.toast(f"Logged Active {direction} Setup. Expiration: {hold_str}", icon="✅")
                    time.sleep(0.4); st.rerun()

with tab2:
    st.title("🤖 100-Asset Institutional Alpha Scanner")
    st.caption("Mass-scans 100 global instruments (Crypto, Forex, Commodities, Equities). Only signals mapping **>60.0% Confidence** are displayed.")
    
    scan_col1, scan_col2 = st.columns([1, 4])
    selected_scan_type = scan_col1.radio("Strategy Target Class", ["Intraday Matrix Setups", "Interday Swing Matrix"])
    
    if scan_col2.button("🚀 INITIATE 100-ASSET 60%+ CONFIDENCE SCAN", use_container_width=True):
        scanned_setups = []
        target_key = "Intraday (15 Min Frame)" if "Intraday" in selected_scan_type else "Interday (1 Day Frame)"
        cfg = TIMEFRAME_CONFIG[target_key]
        
        # Progress bar for scanning 100 assets
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_assets = len(FLAT_ASSET_INDEX)
        
        for i, (option_text, data_meta) in enumerate(FLAT_ASSET_INDEX.items()):
            try:
                s_tick, s_name, s_cat = data_meta["ticker"], data_meta["name"], data_meta["category"]
                m_status, _ = get_market_status_ist(s_cat)
                
                status_text.text(f"Scanning ({i}/{total_assets}): {s_name}...")
                progress_bar.progress(int((i / total_assets) * 100))
                    
                s_raw = yf.download(s_tick, period=cfg["period"], interval=cfg["int"], progress=False)
                if not s_raw.empty and len(s_raw) > 15:
                    s_df = calculate_analytics_matrix(clean_and_verify_dataframe(s_raw))
                    s_latest = s_df.iloc[-1]
                    s_score, s_confidence, s_factors = evaluate_signal_confidence(s_latest)
                    
                    if s_confidence >= 60.0:
                        s_dir = "LONG 🟢" if s_score > 0 else "SHORT 🔴"
                        s_price = float(s_latest['Close'])
                        s_atr = s_latest.get('ATR', 0)
                        s_tp = s_price + (s_atr * 2.2) if s_score > 0 else s_price - (s_atr * 2.2)
                        s_sl = s_price - (s_atr * 1.5) if s_score > 0 else s_price + (s_atr * 1.5)
                        
                        scanned_setups.append({
                            "Asset": s_name, "Ticker": s_tick, "Category": s_cat, "Direction": s_dir,
                            "Confidence": s_confidence, "Price": s_price, "TP": s_tp, "SL": s_sl,
                            "Horizon": cfg["horizon"], "HoldLimit": cfg["hold"], "HoldStr": cfg["hold_str"],
                            "MarketOpen": m_status, "Factors": s_factors
                        })
            except Exception as e: pass
            
        progress_bar.empty()
        status_text.empty()
        st.session_state.scan_results = scanned_setups
        st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.session_state.scan_results:
        st.markdown(f"#### Active Strong Anomalies Confirmed At: `{st.session_state.last_scan_time}`")
        for idx, trade in enumerate(st.session_state.scan_results):
            with st.container(border=True):
                c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1.5, 2, 2, 2])
                c1.markdown(f"**{trade.get('Asset')} ({trade.get('Ticker')})**\n*{trade.get('Category')}*")
                c2.markdown(f"**{trade.get('Direction')}**")
                c3.metric("Confidence", f"{trade.get('Confidence'):.1f}%")
                c4.markdown(f"Entry Spot: **${trade.get('Price'):.4f}**\nHold Time: `{trade.get('HoldStr')}`")
                c5.markdown(f"Target TP: **${trade.get('TP'):.4f}**\nFloor SL: **${trade.get('SL'):.4f}**")
                
                if trade.get('MarketOpen'):
                    if c6.button("⚡ EXECUTE NOW", key=f"sbtn_{idx}_{trade.get('Ticker')}", use_container_width=True):
                        t_cost = 10.0 * trade.get('Price')
                        if t_cost > st.session_state.cash: st.error("Insufficient Margin.")
                        else:
                            st.session_state.cash -= t_cost
                            st.session_state.portfolio[trade['Ticker']] = {
                                "asset_name": trade['Asset'], "qty": 10.0 if "LONG" in trade['Direction'] else -10.0,
                                "entry": trade['Price'], "tp": trade['TP'], "sl": trade['SL'], "horizon": trade['Horizon'],
                                "direction": "LONG" if "LONG" in trade['Direction'] else "SHORT",
                                "expiration": (datetime.now() + trade['HoldLimit']).strftime("%Y-%m-%d %H:%M:%S")
                            }
                            st.toast(f"Routed Order for {trade['Ticker']}!", icon="🚀")
                            time.sleep(0.3); st.rerun()
                else: c6.markdown("🛑 **Closed (Weekend)**")
                    
                with st.expander("👁️ View Search & Trade Logic Rationale"):
                    for r in trade.get('Factors', []): st.markdown(f"- {r}")
    else: st.info("Scanner idle. Awaiting compilation loops.")

with tab3:
    st.title("💼 Institutional Portfolio Ledger & Live P/L")
    
    bal_col, add_col = st.columns([2, 1])
    bal_col.metric("Total Vault Liquid Balance", f"${st.session_state.cash:,.2f}")
    
    with add_col.expander("💳 Inject Capital / Add Money", expanded=False):
        inject_amt_portfolio = st.number_input("Amount to Inject ($)", min_value=100.0, value=5000.0, step=1000.0, key="inject_port")
        if st.button("Confirm Capital Deposit", use_container_width=True):
            st.session_state.cash += inject_amt_portfolio
            st.toast(f"Successfully Deposited: ${inject_amt_portfolio:,.2f}", icon="✅")
            time.sleep(0.4); st.rerun()
    
    st.divider()
    l_t1, l_t2 = st.tabs(["⏱️ Intraday Modules", "📅 Interday Structures"])
    
    def display_isolated_ledger(target_string):
        subset = {k: v for k, v in st.session_state.portfolio.items() if v.get('horizon', '') == target_string}
        if subset:
            portfolio_rows = []
            for k, v in subset.items():
                live_pr = portfolio_live_prices.get(k, v['entry'])
                qty_abs = abs(v['qty'])
                unrealized_pl = (live_pr - v['entry']) * qty_abs if v['direction'] == "LONG" else (v['entry'] - live_pr) * qty_abs
                
                portfolio_rows.append({
                    "Asset": k, "Direction": v['direction'], "Units": qty_abs, 
                    "Entry": f"${v['entry']:,.4f}", "Live Price": f"${live_pr:,.4f}",
                    "Take Profit": f"${v['tp']:,.4f}", "Stop Loss": f"${v['sl']:,.4f}", 
                    "Live P/L ($)": f"${unrealized_pl:,.2f}", "Auto-Closes At": v['expiration']
                })
                
            st.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True)
            
            liq_sel = st.selectbox("Select Asset to Immediately Terminate", list(subset.keys()), key=f"liq_{target_string}")
            if st.button("💥 FORCE LIQUIDATE RISK MATRIX", key=f"kill_{target_string}", use_container_width=True):
                closed_tr = st.session_state.portfolio[liq_sel]
                live_exit = portfolio_live_prices.get(liq_sel, closed_tr['entry'])
                refund_value = abs(closed_tr['qty']) * live_exit
                
                if closed_tr['direction'] == "LONG": st.session_state.cash += refund_value
                else: st.session_state.cash -= refund_value
                
                del st.session_state.portfolio[liq_sel]
                st.toast("Manual override cleared.", icon="💥")
                time.sleep(0.3); st.rerun()
        else: st.info(f"No active automated positions inside the {target_string} matrix.")

    with l_t1: display_isolated_ledger("Intraday")
    with l_t2: display_isolated_ledger("Interday")

with tab4:
    st.title("📖 Quantitative Operations Blueprint")
    st.markdown("""
    ### ⚙️ Engine Upgrades & Mathematical Logic
    1. **100-Asset Scalability:** The scanner now loops through 100 of the world's most liquid instruments across 5 sectors. A loading bar tracks the global synchronization.
    2. **Live P/L Matrix:** The Portfolio Ledger actively pulls real-time market data in the background and computes your precise floating profit/loss for every open position. 
    3. **Precision Entry Matrix:** The single asset predictor now details explicit Entry bounds, Mathematical Support and Resistance floors, and the exact "Hold Time" duration dictated by the quantitative decay limit.
    """)
