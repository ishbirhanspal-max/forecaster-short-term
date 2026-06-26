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
# 1. COMPREHENSIVE SESSION STATE & 150-ASSET MATRIX
# ==========================================
if "cash" not in st.session_state: st.session_state.cash = 100000.00
if "total_deposited" not in st.session_state: st.session_state.total_deposited = 100000.00
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "scan_results" not in st.session_state: st.session_state.scan_results = []
if "last_scan_time" not in st.session_state: st.session_state.last_scan_time = None
if "realized_pl" not in st.session_state: st.session_state.realized_pl = {"Intraday": 0.0, "Interday": 0.0}

ASSET_CLASSES = {
    "Crypto-Currencies (24/7)": {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Ripple": "XRP-USD", "Cardano": "ADA-USD", 
        "Dogecoin": "DOGE-USD", "Polkadot": "DOT-USD", "Polygon": "MATIC-USD", "Litecoin": "LTC-USD", "Shiba Inu": "SHIB-USD", 
        "Avalanche": "AVAX-USD", "Chainlink": "LINK-USD", "Uniswap": "UNI-USD", "Cosmos": "ATOM-USD", "Monero": "XMR-USD",
        "Ethereum Classic": "ETC-USD", "Bitcoin Cash": "BCH-USD", "Stellar": "XLM-USD", "Tron": "TRX-USD", "Filecoin": "FIL-USD"
    },
    "Foreign Exchange (FX)": {
        "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X", "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", 
        "USD/CHF": "CHF=X", "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X", "GBP/JPY": "GBPJPY=X", 
        "AUD/JPY": "AUDJPY=X", "EUR/AUD": "EURAUD=X", "EUR/CAD": "EURCAD=X", "EUR/CHF": "EURCHF=X", "AUD/CAD": "AUDCAD=X", 
        "CAD/JPY": "CADJPY=X", "CHF/JPY": "CHFJPY=X", "GBP/CHF": "GBPCHF=X", "GBP/CAD": "GBPCAD=X", "GBP/AUD": "GBPAUD=X"
    },
    "Global Commodities": {
        "Gold (XAU)": "GC=F", "Silver": "SI=F", "Crude Oil (WTI)": "CL=F", "Natural Gas": "NG=F", "Copper": "HG=F", 
        "Platinum": "PL=F", "Palladium": "PA=F", "Corn": "ZC=F", "Wheat": "ZW=F", "Soybeans": "ZS=F", 
        "Sugar": "SB=F", "Coffee": "KC=F", "Cotton": "CT=F", "Cocoa": "CC=F", "Heating Oil": "HO=F", 
        "RBOB Gasoline": "RB=F", "Live Cattle": "LE=F", "Lean Hogs": "HE=F", "Feeder Cattle": "GF=F", "Rough Rice": "ZR=F"
    },
    "Global Equities": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Alphabet": "GOOGL", "Amazon": "AMZN", "Nvidia": "NVDA", 
        "Meta Platforms": "META", "Tesla": "TSLA", "Berkshire Hathaway": "BRK-B", "TSMC": "TSM", "Visa": "V", 
        "JPMorgan Chase": "JPM", "Walmart": "WMT", "Johnson & Johnson": "JNJ", "Mastercard": "MA", "Procter & Gamble": "PG",
        "UnitedHealth": "UNH", "Home Depot": "HD", "Exxon Mobil": "XOM", "Disney": "DIS", "Bank of America": "BAC"
    },
    "Indian Equities (NSE)": {
        "Nifty 50 Index": "^NSEI", "Reliance Ind": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS", "Infosys": "INFY.NS", 
        "ICICI Bank": "ICICIBANK.NS", "SBI": "SBIN.NS", "Bharti Airtel": "BHARTIARTL.NS", "ITC": "ITC.NS", "Larsen & Toubro": "LT.NS", 
        "Bajaj Finance": "BAJFINANCE.NS", "HUL": "HINDUNILVR.NS", "Maruti Suzuki": "MARUTI.NS", "Axis Bank": "AXISBANK.NS", "Sun Pharma": "SUNPHARMA.NS",
        "Titan": "TITAN.NS", "UltraTech Cement": "ULTRACEMCO.NS", "Tata Motors": "TATAMOTORS.NS", "Wipro": "WIPRO.NS", "Kotak Bank": "KOTAKBANK.NS"
    }
}

FLAT_ASSET_INDEX = {f"{n} ({t})": {"ticker": t, "name": n, "category": c} for c, items in ASSET_CLASSES.items() for n, t in items.items()}

# ==========================================
# 2. IST TIME CLOCK & MARKET STATUS RULES
# ==========================================
def get_market_status_ist(category):
    if "Crypto" in category: return True, "ONLINE (24/7)"
    ist_now = datetime.now(pytz.timezone('Asia/Kolkata'))
    weekday, hour, minute = ist_now.weekday(), ist_now.hour, ist_now.minute
    if weekday == 5: return False, "OFFLINE (Weekend Halt)"
    if weekday == 6 and (hour < 3 or (hour == 3 and minute < 30)): return False, "OFFLINE (Weekend Halt)"
    return True, "ONLINE"

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.header("🕹️ Quantitative Controls")

st.sidebar.subheader("📂 Market Filter")
selected_category_filter = st.sidebar.selectbox("Isolate Asset Class", ["All Markets"] + list(ASSET_CLASSES.keys()))

st.sidebar.subheader("🔍 Omni-Asset Search")
search_query = st.sidebar.text_input("Filter symbols...", "").lower()

filtered_options = [k for k, v in FLAT_ASSET_INDEX.items() if (selected_category_filter == "All Markets" or v["category"] == selected_category_filter) and search_query in k.lower()]
if not filtered_options: 
    st.sidebar.warning("No assets match this filter.")
    filtered_options = list(FLAT_ASSET_INDEX.keys())

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
# 4. UPGRADED MATHEMATICS ENGINE
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
    else: df['VWAP'] = df['Close'].rolling(window=14).mean()
    
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
    
    body = (df['Close'] - df['Open']).abs()
    candle_range = df['High'] - df['Low'] + 1e-9
    lower_shade = np.where(df['Close'] > df['Open'], df['Open'] - df['Low'], df['Close'] - df['Low'])
    upper_shade = np.where(df['Close'] > df['Open'], df['High'] - df['Close'], df['High'] - df['Open'])
    df['Pattern_Hammer'] = (lower_shade >= 2 * body) & (upper_shade <= (candle_range * 0.10)) & (body > 0)
    
    curr_dir = np.sign(df['Close'] - df['Open'])
    prev_dir = np.sign(df['Close'].shift(1) - df['Open'].shift(1))
    df['Pattern_Bullish_Engulfing'] = (curr_dir == 1) & (prev_dir == -1) & (df['Close'] >= df['Open'].shift(1)) & (df['Open'] <= df['Close'].shift(1))
    df['Pattern_Bearish_Engulfing'] = (curr_dir == -1) & (prev_dir == 1) & (df['Close'] <= df['Open'].shift(1)) & (df['Open'] >= df['Close'].shift(1))

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
    
    for i in idx[:15]: 
        amplitude = (np.absolute(fft_vals[i]) / n) * 1.5 
        phase = np.angle(fft_vals[i])
        harmonic_wave += amplitude * np.cos(2 * np.pi * frequencies[i] * t_ext + phase)
        
    full_prediction = harmonic_wave + (slope * t_ext + intercept)
    future_predictions = full_prediction[n:]
    
    last_price = float(df_current['Close'].iloc[-1])
    current_atr = float(df_current['ATR'].iloc[-1])
    max_variance = current_atr * days_lookahead * 0.25 
    future_predictions = np.clip(future_predictions, last_price - max_variance, last_price + max_variance)
    
    last_date = df_current['Timestamp'].iloc[-1]
    if isinstance(last_date, str): last_date = pd.to_datetime(last_date)
    time_step = timedelta(days=1) if days_lookahead > 30 else timedelta(hours=12)
    future_dates = [last_date + (time_step * i) for i in range(1, future_steps + 1)]
    return future_dates, future_predictions

def evaluate_signal_confidence(latest):
    score = 0.0
    factors = []
    
    if latest.get('EMA_9', 0) > latest.get('EMA_21', 0): score += 1.5; factors.append("📈 Core Trend: 9 EMA > 21 EMA (Momentum Up)")
    else: score -= 1.5; factors.append("📉 Core Trend: 9 EMA < 21 EMA (Momentum Down)")
        
    close_val = latest.get('Close', 1)
    if close_val >= latest.get('BB_Upper', close_val * 1.1):
        score -= 2.0; factors.append("⚠️ MEAN REVERSION: Price mathematically overextended at Upper Bollinger Band. Short reversion likely.")
    elif close_val <= latest.get('BB_Lower', close_val * 0.9):
        score += 2.0; factors.append("⚠️ MEAN REVERSION: Price mathematically exhausted at Lower Bollinger Band. Long bounce likely.")
        
    if latest.get('Pattern_Bullish_Engulfing', False): score += 2.0; factors.append("🕯️ CANDLESTICK: Bullish Engulfing Pattern Locked")
    elif latest.get('Pattern_Bearish_Engulfing', False): score -= 2.0; factors.append("🕯️ CANDLESTICK: Bearish Engulfing Pattern Locked")
    elif latest.get('Pattern_Hammer', False): score += 1.0; factors.append("🕯️ CANDLESTICK: Bottoming Hammer Detected")
        
    vwap_val = latest.get('VWAP', close_val)
    if close_val > vwap_val: score += 1.0; factors.append("📊 Accumulation above VWAP")
    else: score -= 1.0; factors.append("📊 Liquidation below VWAP")
        
    rsi_val = latest.get('RSI_14', 50)
    if rsi_val < 35: score += 2.0; factors.append(f"⚡ RSI Oversold ({rsi_val:.1f}) - Sellers Exhausted")
    elif rsi_val > 65: score -= 2.0; factors.append(f"⚡ RSI Overbought ({rsi_val:.1f}) - Buyers Exhausted")
        
    if latest.get('MACD', 0) > latest.get('MACD_Signal', 0): score += 1.5; factors.append("🚀 MACD Velocity Accel")
    else: score -= 1.5; factors.append("🩸 MACD Velocity Decay")
        
    if latest.get('Squeeze_Active', False):
        factors.append("🔥 VOLATILITY SQUEEZE: Bands compressed. Breakout imminent.")
        score *= 1.3 

    confidence = min((abs(score) / 9.0) * 100, 99.8)
    if confidence < 50.0: confidence = 50.0 + (confidence / 5)
    return score, confidence, factors

# ==========================================
# 5. REAL-TIME EXPIRED ORDERS PURGE & LIVE P/L
# ==========================================
now_ts = datetime.now()
purged = False

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
    if now_ts >= exp_time: exit_trigger = "TIME DECAY LIMIT REACHED"
    elif data['tp'] > 0 and ((data['direction'] == "LONG" and live_p >= data['tp']) or (data['direction'] == "SHORT" and live_p <= data['tp'])): exit_trigger = "TAKE PROFIT MET"
    elif data['sl'] > 0 and ((data['direction'] == "LONG" and live_p <= data['sl']) or (data['direction'] == "SHORT" and live_p >= data['sl'])): exit_trigger = "STOP LOSS MET"
    
    if exit_trigger:
        qty_abs = abs(data['qty'])
        pl_dollars = (live_p - data['entry']) * qty_abs if data['direction'] == "LONG" else (data['entry'] - live_p) * qty_abs
        
        st.session_state.cash += (data['entry'] * qty_abs) + pl_dollars
        st.session_state.realized_pl[data['horizon']] += pl_dollars
            
        st.session_state.statement.append({
            "Time": now_ts.strftime("%Y-%m-%d %H:%M"), "Asset": t_id, "Type": data['horizon'],
            "Dir": data['direction'], "Exit Price": live_p, "P/L": pl_dollars, "Trigger": exit_trigger
        })
        del st.session_state.portfolio[t_id]
        purged = True
        st.toast(f"Closed {t_id} via {exit_trigger}. P/L: ${pl_dollars:.2f}", icon="⚡")

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
    "🔮 Predictor & Forecast", 
    "🤖 Alpha Scanner (150 Assets)", 
    "💼 Portfolio & Live P/L", 
    "📓 Master Trade Book"
])

with tab1:
    st.title(f"🔮 Predictive Analysis Matrix: {asset_name}")
    st.markdown(f"Segment: **{asset_cat}** | Market Clock: **{clock_msg}**")
    
    if not is_open: st.warning("Market is offline (Weekend). Analytics available; execution disabled.")
        
    if st.session_state.current_market_data is not None and st.session_state.last_analyzed_ticker == ticker:
        df = st.session_state.current_market_data
        curr_p = st.session_state.live_price
        latest = df.iloc[-1]
        
        score, confidence, factors = evaluate_signal_confidence(latest)
        
        # SINGLE ASSET MASTER VERDICT
        if score >= 1.5: verdict = "EXECUTE STRONG BUY LONG 🟢"
        elif score <= -1.5: verdict = "EXECUTE STRONG SELL SHORT 🔴"
        else: verdict = "NEUTRAL SPECULATION ⚪"
        
        atr = latest.get('ATR', curr_p * 0.01)
        target_tp = curr_p + (atr * 2.5) if score >= 0 else curr_p - (atr * 2.5)
        target_sl = curr_p - (atr * 1.5) if score >= 0 else curr_p + (atr * 1.5)
        sup = latest.get('Support', curr_p)
        res = latest.get('Resistance', curr_p)
        
        st.markdown("### 🎯 Dynamic Trade Parameters & Time Limits")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Optimal Entry (Live)", f"${curr_p:,.4f}")
        c2.metric("Target (Take Profit)", f"${target_tp:,.4f}")
        c3.metric("Floor (Stop Loss)", f"${target_sl:,.4f}")
        c4.metric("Mathematical Confidence", f"{confidence:.2f}%")
        
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Master Asset Verdict", verdict)
        c6.metric("Auto-Exit Duration", f"{hold_str}", help="Trade automatically closes after this time if TP/SL are not hit.")
        c7.metric("Dynamic Support", f"${sup:,.4f}")
        c8.metric("Dynamic Resistance", f"${res:,.4f}")
        
        with st.expander("👁️ Why is the Algorithm Suggesting This? (Trade Rationale)", expanded=True):
            st.markdown(f"*Algorithm Verdict reflects underlying mathematics, analyzing price-action patterns and indicators.*")
            for factor in factors: st.markdown(f"- {factor}")
            
        st.markdown("### 📊 Active Harmonic Forecast Curve (Volatility Injected)")
        f_sel = st.selectbox("Cyclical Lookahead Window", ["1 Month (30 Days)", "3 Months (90 Days)", "6 Months (180 Days)", "1 Year Macro (365 Days)"])
        d_map = {"1 Month (30 Days)": 30, "3 Months (90 Days)": 90, "6 Months (180 Days)": 180, "1 Year Macro (365 Days)": 365}
        
        f_dates, f_preds = generate_cyclical_harmonic_forecast(ticker, df, days_lookahead=d_map[f_sel])
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df['Timestamp'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candles"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['VWAP'], line=dict(color='cyan', width=1), name="VWAP"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['BB_Upper'], line=dict(color='gray', dash='dot', width=1), name="Upper BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['BB_Lower'], line=dict(color='gray', dash='dot', width=1), name="Lower BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=f_dates, y=f_preds, line=dict(color='#00ffcc', width=2), name="FFT Harmonic Curve"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['RSI_14'], line=dict(color='orange', width=1.2), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark", margin=dict(t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### ⚡ Risk-Adjusted Execution Desk")
        st.info(f"**Capital Rule:** If Target (${target_tp:,.2f}) or Stop Loss (${target_sl:,.2f}) is not hit within **{hold_str}**, the engine will force exit.")
        with st.form("single_execution_form"):
            e1, e2, e3 = st.columns(3)
            risk_pct = e1.slider("Risk Percentage of Account (%)", 1.0, 10.0, 2.0, 0.5)
            tp_price = e2.number_input("Custom Target (TP)", value=float(target_tp))
            sl_price = e3.number_input("Custom Stop Loss (SL)", value=float(target_sl))
            
            risk_dollars = st.session_state.cash * (risk_pct / 100)
            sl_distance = abs(curr_p - sl_price) if abs(curr_p - sl_price) > 0 else 1
            calculated_units = round(risk_dollars / sl_distance, 4)
            st.write(f"**Auto-Position Sizer:** Risking {risk_pct}% (${risk_dollars:,.2f}) equates to purchasing **{calculated_units} Units**.")
            
            b_buy, b_sell = st.columns(2)
            buy_triggered = b_buy.form_submit_button("ROUTE LONG ORDER", use_container_width=True, disabled=not is_open)
            sell_triggered = b_sell.form_submit_button("ROUTE SHORT ORDER", use_container_width=True, disabled=not is_open)
            
            if (buy_triggered or sell_triggered) and is_open:
                direction = "LONG" if buy_triggered else "SHORT"
                total_cost = calculated_units * curr_p
                
                if direction == "LONG" and total_cost > st.session_state.cash: st.error("Margin deficit.")
                else:
                    if direction == "LONG": st.session_state.cash -= total_cost
                    else: st.session_state.cash += total_cost
                        
                    st.session_state.portfolio[ticker] = {
                        "asset_name": asset_name, "qty": calculated_units if direction == "LONG" else -calculated_units,
                        "entry": curr_p, "tp": tp_price, "sl": sl_price, "horizon": current_horizon,
                        "direction": direction, "expiration": (datetime.now() + hold_limit).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.toast(f"Executed! Auto-Exit enforced at: {hold_str}", icon="✅")
                    time.sleep(0.4); st.rerun()

with tab2:
    st.title("🤖 150-Asset Class Auto-Scanner")
    
    scan_col1, scan_col2, scan_col3 = st.columns([2, 2, 2])
    scan_cat_filter = scan_col1.selectbox("Target Asset Class", ["All Markets"] + list(ASSET_CLASSES.keys()))
    scan_time_filter = scan_col2.radio("Strategy Matrix", ["Intraday Matrix Setups", "Interday Swing Matrix"])
    
    if scan_col3.button("🚀 INITIATE 60%+ WALL STREET SCAN", use_container_width=True):
        scanned_setups = []
        target_key = "Intraday (15 Min Frame)" if "Intraday" in scan_time_filter else "Interday (1 Day Frame)"
        cfg = TIMEFRAME_CONFIG[target_key]
        
        target_assets = {k: v for k, v in FLAT_ASSET_INDEX.items() if scan_cat_filter == "All Markets" or v["category"] == scan_cat_filter}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        long_count = 0
        short_count = 0
        
        for i, (option_text, data_meta) in enumerate(target_assets.items()):
            try:
                s_tick, s_name, s_cat = data_meta["ticker"], data_meta["name"], data_meta["category"]
                m_status, _ = get_market_status_ist(s_cat)
                
                status_text.text(f"Scanning ({i+1}/{len(target_assets)}): {s_name}...")
                progress_bar.progress(int(((i+1) / len(target_assets)) * 100))
                    
                s_raw = yf.download(s_tick, period=cfg["period"], interval=cfg["int"], progress=False)
                if not s_raw.empty and len(s_raw) > 15:
                    s_df = calculate_analytics_matrix(clean_and_verify_dataframe(s_raw))
                    s_latest = s_df.iloc[-1]
                    s_score, s_confidence, s_factors = evaluate_signal_confidence(s_latest)
                    
                    if s_confidence >= 60.0:
                        s_dir = "LONG 🟢" if s_score > 0 else "SHORT 🔴"
                        if s_score > 0: long_count += 1
                        else: short_count += 1
                            
                        s_price = float(s_latest['Close'])
                        s_atr = s_latest.get('ATR', s_price * 0.01)
                        s_tp = s_price + (s_atr * 2.2) if s_score > 0 else s_price - (s_atr * 2.2)
                        s_sl = s_price - (s_atr * 1.5) if s_score > 0 else s_price + (s_atr * 1.5)
                        
                        scanned_setups.append({
                            "Asset": s_name, "Ticker": s_tick, "Category": s_cat, "Direction": s_dir,
                            "Confidence": s_confidence, "Price": s_price, "TP": s_tp, "SL": s_sl,
                            "Horizon": cfg["horizon"], "HoldLimit": cfg["hold"], "HoldStr": cfg["hold_str"],
                            "MarketOpen": m_status, "Factors": s_factors
                        })
            except: pass
            
        progress_bar.empty(); status_text.empty()
        st.session_state.scan_results = sorted(scanned_setups, key=lambda x: (x['Category'], -x['Confidence']))
        st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # SCANNER MASTER VERDICT
        total_found = long_count + short_count
        if total_found > 0:
            if long_count / total_found > 0.6: st.session_state.macro_verdict = f"🟢 MACRO MARKET VERDICT: BULLISH BIAS ({round((long_count/total_found)*100)}% Long Signals)"
            elif short_count / total_found > 0.6: st.session_state.macro_verdict = f"🔴 MACRO MARKET VERDICT: BEARISH BIAS ({round((short_count/total_found)*100)}% Short Signals)"
            else: st.session_state.macro_verdict = f"⚪ MACRO MARKET VERDICT: CHOPPY / FRAGMENTED (Mixed Signals Detected)"
        else: st.session_state.macro_verdict = "⚪ MACRO MARKET VERDICT: NO HIGH-CONFIDENCE SIGNALS"

    if st.session_state.scan_results:
        st.markdown(f"### {st.session_state.get('macro_verdict', '')}")
        st.markdown(f"#### Setups Discovered At: `{st.session_state.last_scan_time}`")
        
        current_display_cat = ""
        for idx, trade in enumerate(st.session_state.scan_results):
            if trade['Category'] != current_display_cat:
                current_display_cat = trade['Category']
                st.markdown(f"### 🌐 {current_display_cat}")
                
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1.5, 2.5, 2])
                c1.markdown(f"**{trade['Asset']} ({trade['Ticker']})**")
                c2.markdown(f"**{trade['Direction']}**")
                c3.metric("Confidence", f"{trade['Confidence']:.1f}%")
                
                c4.markdown(f"Spot: **${trade['Price']:.4f}**\n🚨 **Auto-Exit in:** `{trade['HoldStr']}` if no TP/SL")
                
                if trade['MarketOpen']:
                    if c5.button("⚡ EXECUTE (2% RISK)", key=f"sbtn_{idx}_{trade['Ticker']}", use_container_width=True):
                        r_dollars = st.session_state.cash * 0.02
                        sl_dist = abs(trade['Price'] - trade['SL']) or 1
                        t_units = round(r_dollars / sl_dist, 4)
                        
                        if (t_units * trade['Price']) > st.session_state.cash: st.error("Margin deficit.")
                        else:
                            if "LONG" in trade['Direction']: st.session_state.cash -= (t_units * trade['Price'])
                            else: st.session_state.cash += (t_units * trade['Price'])
                            
                            st.session_state.portfolio[trade['Ticker']] = {
                                "asset_name": trade['Asset'], "qty": t_units if "LONG" in trade['Direction'] else -t_units,
                                "entry": trade['Price'], "tp": trade['TP'], "sl": trade['SL'], "horizon": trade['Horizon'],
                                "direction": "LONG" if "LONG" in trade['Direction'] else "SHORT",
                                "expiration": (datetime.now() + trade['HoldLimit']).strftime("%Y-%m-%d %H:%M:%S")
                            }
                            st.toast(f"Routed Auto-Risk Order for {trade['Ticker']}!", icon="🚀")
                            time.sleep(0.3); st.rerun()
                else: c5.markdown("🛑 **Closed (Weekend)**")
                    
                with st.expander("👁️ View Trade Logic & Candlestick Reasoning"):
                    st.markdown(f"**Target TP:** `${trade['TP']:.4f}` | **Floor SL:** `${trade['SL']:.4f}`")
                    for r in trade['Factors']: st.markdown(f"- {r}")
    else: st.info("Scanner idle. Awaiting compilation loops.")

with tab3:
    st.title("💼 Master P/L Dashboard & Ledger")
    
    bal_col, add_col, reset_col = st.columns([2, 1, 1])
    bal_col.metric("Liquid Cash Balance", f"${st.session_state.cash:,.2f}")
    
    with add_col.expander("💳 Inject Capital / Add Money", expanded=False):
        inject_amt_portfolio = st.number_input("Amount to Inject ($)", min_value=100.0, value=5000.0, step=1000.0)
        if st.button("Confirm Deposit", use_container_width=True):
            st.session_state.cash += inject_amt_portfolio
            st.session_state.total_deposited += inject_amt_portfolio
            st.rerun()
            
    with reset_col.expander("⚠️ Master Reset", expanded=False):
        st.warning("This will instantly liquidate all positions and wipe historical records.")
        if st.button("🚨 WIPE PORTFOLIO", use_container_width=True):
            st.session_state.portfolio = {}
            st.session_state.statement = []
            st.session_state.realized_pl = {"Intraday": 0.0, "Interday": 0.0}
            st.session_state.cash = st.session_state.total_deposited
            st.toast("Portfolio completely reset.", icon="🔥")
            time.sleep(0.5)
            st.rerun()
    
    st.divider()
    
    unrealized_intra, unrealized_inter = 0.0, 0.0
    total_open_value = 0.0
    
    for k, v in st.session_state.portfolio.items():
        live_pr = portfolio_live_prices.get(k, v['entry'])
        qty_abs = abs(v['qty'])
        total_open_value += (qty_abs * live_pr)
        
        pl = (live_pr - v['entry']) * qty_abs if v['direction'] == "LONG" else (v['entry'] - live_pr) * qty_abs
        if v['horizon'] == "Intraday": unrealized_intra += pl
        else: unrealized_inter += pl

    total_equity = st.session_state.cash + total_open_value
    net_pl_dollars = total_equity - st.session_state.total_deposited
    net_pl_percent = (net_pl_dollars / st.session_state.total_deposited) * 100 if st.session_state.total_deposited > 0 else 0

    master_v_col, met_col1, met_col2 = st.columns([2, 1, 1])
    
    if net_pl_percent > 5.0: port_verdict = "🟢 EXCELLENT (Strong Growth Phase)"
    elif net_pl_percent < -5.0: port_verdict = "🔴 CRITICAL (Drawdown Phase)"
    else: port_verdict = "⚪ STABLE (Consolidation Phase)"
    
    master_v_col.metric("Master Portfolio Health Verdict", port_verdict)
    met_col1.metric("Total Account Equity", f"${total_equity:,.2f}")
    met_col2.metric("Net Portfolio Return (%)", f"{net_pl_percent:,.2f}%", delta=f"${net_pl_dollars:,.2f}")

    st.divider()
    
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Intraday Unrealized P/L", f"${unrealized_intra:,.2f}", delta=f"{unrealized_intra:,.2f}")
    p2.metric("Intraday Realized P/L", f"${st.session_state.realized_pl['Intraday']:,.2f}", delta=f"{st.session_state.realized_pl['Intraday']:,.2f}")
    p3.metric("Interday Unrealized P/L", f"${unrealized_inter:,.2f}", delta=f"{unrealized_inter:,.2f}")
    p4.metric("Interday Realized P/L", f"${st.session_state.realized_pl['Interday']:,.2f}", delta=f"{st.session_state.realized_pl['Interday']:,.2f}")

    st.divider()
    l_t1, l_t2 = st.tabs(["⏱️ Intraday Open Positions", "📅 Interday Open Positions"])
    
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
                    "Live P/L ($)": f"${unrealized_pl:,.2f}", "Auto-Closes At": v['expiration']
                })
            st.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True)
            
            liq_sel = st.selectbox("Select Asset to Force Terminate", list(subset.keys()), key=f"liq_{target_string}")
            if st.button("💥 FORCE LIQUIDATE (MARKET ORDER)", key=f"kill_{target_string}", use_container_width=True):
                closed_tr = st.session_state.portfolio[liq_sel]
                live_exit = portfolio_live_prices.get(liq_sel, closed_tr['entry'])
                qty = abs(closed_tr['qty'])
                
                pl_dollars = (live_exit - closed_tr['entry']) * qty if closed_tr['direction'] == "LONG" else (closed_tr['entry'] - live_exit) * qty
                if closed_tr['direction'] == "LONG": st.session_state.cash += (closed_tr['entry'] * qty) + pl_dollars
                else: st.session_state.cash -= (closed_tr['entry'] * qty) - pl_dollars
                
                st.session_state.realized_pl[target_string] += pl_dollars
                
                st.session_state.statement.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M"), "Asset": liq_sel, "Type": target_string,
                    "Dir": closed_tr['direction'], "Exit Price": live_exit, "P/L": pl_dollars, "Trigger": "MANUAL FORCE CLOSE"
                })
                del st.session_state.portfolio[liq_sel]
                st.rerun()
        else: st.info(f"No active positions in the {target_string} matrix.")

    with l_t1: display_isolated_ledger("Intraday")
    with l_t2: display_isolated_ledger("Interday")

with tab4:
    st.title("📓 Master Trade Book (Blotter)")
    st.markdown("A consolidated log of every historic transaction processed through the execution engine.")
    
    if st.session_state.statement:
        df_statement = pd.DataFrame(st.session_state.statement)
        
        total_trades = len(df_statement)
        winning_trades = len(df_statement[df_statement['P/L'] > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        best_trade = df_statement['P/L'].max()
        worst_trade = df_statement['P/L'].min()
        
        tb1, tb2, tb3, tb4 = st.columns(4)
        tb1.metric("Total Executions", total_trades)
        tb2.metric("System Win Rate", f"{win_rate:.1f}%")
        tb3.metric("Best Single Trade", f"${best_trade:,.2f}")
        tb4.metric("Worst Single Trade", f"${worst_trade:,.2f}")
        
        st.divider()
        st.dataframe(df_statement.iloc[::-1], use_container_width=True)
    else:
        st.info("The Master Trade Book is empty. Route an order to begin tracking analytics.")
