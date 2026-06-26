import streamlit as str
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# Page config
str.set_page_config(page_title="QuantEdge Live Brokerage", layout="wide")

# ==========================================
# 1. INITIALIZE ADVANCED PERSISTENT MEMORY
# ==========================================
if "cash" not in str.session_state:
    str.session_state.cash = 10000.00  
if "portfolio" not in str.session_state:
    # Portfolio now tracks both quantity AND average entry price for P&L math
    str.session_state.portfolio = {}   
if "statement" not in str.session_state:
    str.session_state.statement = []   
if "engine_executed" not in str.session_state:
    str.session_state.engine_executed = False
if "current_market_data" not in str.session_state:
    str.session_state.current_market_data = None
if "last_analyzed_ticker" not in str.session_state:
    str.session_state.last_analyzed_ticker = None

ASSET_CLASSES = {
    "Equities (Stocks)": {"Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA", "Nvidia (NVDA)": "NVDA", "S&P 500 ETF (SPY)": "SPY"},
    "Cryptocurrency": {"Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (SOL)": "SOL-USD"},
    "Forex": {"EUR / USD": "EURUSD=X", "GBP / USD": "GBPUSD=X", "USD / JPY": "JPY=X"},
    "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F"}
}

# ==========================================
# 2. SIDEBAR & LIVE CONTROLS
# ==========================================
str.sidebar.header("🕹️ Terminal Controls")

def reset_engine():
    str.session_state.engine_executed = False

asset_type = str.sidebar.selectbox("Asset Class", list(ASSET_CLASSES.keys()), on_change=reset_engine)
asset_name = str.sidebar.selectbox("Select Ticker", list(ASSET_CLASSES[asset_type].keys()), on_change=reset_engine)
ticker = ASSET_CLASSES[asset_type][asset_name]

timeframe = str.sidebar.selectbox("Interval Timeframe", ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour"], on_change=reset_engine)
chart_style = str.sidebar.radio("Visual Chart Style", ["Candlestick", "Line Chart"])

str.sidebar.divider()
str.sidebar.header("⚡ Live Auto-Pilot")
auto_refresh = str.sidebar.toggle("Enable Auto-Refresh Loop", value=False)
refresh_rate = str.sidebar.slider("Refresh Interval (Seconds)", min_value=10, max_value=60, value=15, help="Keep above 10s to avoid API bans.")

interval_mapping = {
    "1 Minute": {"int": "1m", "period": "2d", "secs": 60},
    "5 Minutes": {"int": "5m", "period": "5d", "secs": 300},
    "15 Minutes": {"int": "15m", "period": "5d", "secs": 900},
    "1 Hour": {"int": "1h", "period": "730d", "secs": 3600}
}

# Timer Math
now = datetime.now()
secs_in_interval = interval_mapping[timeframe]["secs"]
seconds_passed = (now.minute * 60 + now.second) % secs_in_interval
seconds_remaining = secs_in_interval - seconds_passed

# ==========================================
# 3. TAB NAVIGATION
# ==========================================
tab1, tab2 = str.tabs(["⚡ Live Trading Terminal", "💼 Portfolio & Live P&L"])

with tab1:
    str.title("⚡ QuantEdge Live Trading Terminal")
    
    # Restored Live Timer Banner
    t_col1, t_col2, t_col3 = str.columns(3)
    t_col1.metric("Active Market", f"{asset_name}")
    t_col2.metric("Candle Horizon", timeframe)
    t_col3.metric("⏳ Next Candle Cuts In", f"{seconds_remaining} seconds")
    str.divider()
    
    # Execution Logic (Manual or Auto-Pilot)
    execute_clicked = str.button("🔄 Execute Market Scan", use_container_width=True)
    
    if execute_clicked or auto_refresh:
        chosen_int = interval_mapping[timeframe]["int"]
        chosen_per = interval_mapping[timeframe]["period"]
        
        df = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
        
        if df is not None and len(df) > 50:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)
            
            # Standard Math
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
            
            # ADVANCED: Support, Resistance, and ATR (Volatility)
            df['Support'] = df['Low'].rolling(window=20).min()
            df['Resistance'] = df['High'].rolling(window=20).max()
            df['ATR'] = (df['High'] - df['Low']).rolling(window=14).mean()
            
            str.session_state.current_market_data = df
            str.session_state.engine_executed = True
            str.session_state.last_analyzed_ticker = ticker
        else:
            str.error("Market data unavailable. API limit reached or market closed.")
            str.session_state.engine_executed = False

    # Render Active Market Data
    if str.session_state.engine_executed and str.session_state.current_market_data is not None:
        df = str.session_state.current_market_data
        latest = df.iloc[-1]
        current_p = float(latest['Close'])
        support_p = float(latest['Support'])
        resistance_p = float(latest['Resistance'])
        atr_p = float(latest['ATR'])
        
        # Verdict Logic
        buy_votes, sell_votes = 0, 0
        
        if float(latest['SMA_20']) > float(latest['SMA_50']): buy_votes += 1
        else: sell_votes += 1
            
        rsi_v = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
        if rsi_v < 40: buy_votes += 1  # Adjusted for earlier signals
        elif rsi_v > 60: sell_votes += 1
            
        if float(latest['MACD']) > float(latest['Signal_Line']): buy_votes += 1
        else: sell_votes += 1

        if buy_votes > sell_votes:
            signal_output = "BUY"
            conf = (buy_votes / 3) * 100
            # Risk Math for Longs
            stop_loss = current_p - (atr_p * 1.5)
            take_profit = current_p + (atr_p * 2.5)
        elif sell_votes > buy_votes:
            signal_output = "SELL"
            conf = (sell_votes / 3) * 100
            # Risk Math for Shorts/Sells
            stop_loss = current_p + (atr_p * 1.5)
            take_profit = current_p - (atr_p * 2.5)
        else:
            signal_output = "NEUTRAL"
            conf = 50.0
            stop_loss = current_p - atr_p
            take_profit = current_p + atr_p

        # Visual Display
        str.subheader("🎯 Live Execution Matrix")
        m_col1, m_col2, m_col3, m_col4 = str.columns(4)
        m_col1.metric("Current Price", f"${current_p:,.4f}")
        m_col2.metric("System Signal", signal_output)
        m_col3.metric("Confidence", f"{conf:.1f}%")
        m_col4.metric("Volatility (ATR)", f"${atr_p:,.4f}")
        
        str.markdown("### 🛡️ Trade Setup & Risk Levels")
        r_col1, r_col2, r_col3, r_col4 = str.columns(4)
        r_col1.info(f"**Optimal Entry:**\n${current_p:,.4f}")
        r_col2.success(f"**Target (Exit):**\n${take_profit:,.4f}")
        r_col3.error(f"**Stop-Loss:**\n${stop_loss:,.4f}")
        r_col4.warning(f"**S/R Bounds:**\nS: ${support_p:,.2f} | R: ${resistance_p:,.2f}")

        # Dynamic Charts
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        time_column = df['Datetime'] if 'Datetime' in df else df['Date']
        
        if chart_style == "Candlestick":
            fig.add_trace(go.Candlestick(x=time_column, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=time_column, y=df['Close'], name="Price (Line)", line=dict(color='blue', width=2)), row=1, col=1)
            
        # Add Support/Resistance lines
        fig.add_trace(go.Scatter(x=time_column, y=df['Resistance'], name="Resistance", line=dict(color='red', width=1, dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_column, y=df['Support'], name="Support", line=dict(color='green', width=1, dash='dot')), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=time_column, y=df['RSI'], name="RSI (14)", line=dict(color='gray')), row=2, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_dark", margin=dict(t=10, b=10))
        str.plotly_chart(fig, use_container_width=True)

        # Paper Trading
        str.divider()
        str.subheader("💼 Terminal Execution")
        str.write(f"**Purchasing Power:** `${str.session_state.cash:,.2f}`")
        
        t_qty = str.number_input("Order Quantity", min_value=0.01, max_value=1000.0, value=1.00, step=0.1)
        active_ticker = str.session_state.last_analyzed_ticker

        btn_col1, btn_col2 = str.columns(2)
        if btn_col1.button("🟢 Execute Market BUY", use_container_width=True):
            cost = t_qty * current_p
            if str.session_state.cash >= cost:
                str.session_state.cash -= cost
                
                # Portfolio P&L Math updates
                if active_ticker in str.session_state.portfolio:
                    old_qty = str.session_state.portfolio[active_ticker]['qty']
                    old_avg = str.session_state.portfolio[active_ticker]['avg_entry']
                    new_qty = old_qty + t_qty
                    new_avg = ((old_qty * old_avg) + (t_qty * current_p)) / new_qty
                    str.session_state.portfolio[active_ticker] = {'qty': new_qty, 'avg_entry': new_avg}
                else:
                    str.session_state.portfolio[active_ticker] = {'qty': t_qty, 'avg_entry': current_p}
                
                str.session_state.statement.append({"Time": datetime.now().strftime("%H:%M:%S"), "Asset": active_ticker, "Action": "BUY", "Qty": t_qty, "Price": current_p})
                str.success(f"Filled BUY: {t_qty} {active_ticker} @ ${current_p:.2f}")

        if btn_col2.button("🔴 Execute Market SELL", use_container_width=True):
            if active_ticker in str.session_state.portfolio and str.session_state.portfolio[active_ticker]['qty'] >= t_qty:
                revenue = t_qty * current_p
                str.session_state.cash += revenue
                
                str.session_state.portfolio[active_ticker]['qty'] -= t_qty
                if str.session_state.portfolio[active_ticker]['qty'] <= 0:
                    del str.session_state.portfolio[active_ticker]
                    
                str.session_state.statement.append({"Time": datetime.now().strftime("%H:%M:%S"), "Asset": active_ticker, "Action": "SELL", "Qty": t_qty, "Price": current_p})
                str.success(f"Filled SELL: {t_qty} {active_ticker} @ ${current_p:.2f}")

# ==========================================
# PORTFOLIO & LIVE P&L TAB
# ==========================================
with tab2:
    str.header("📈 Live Portfolio Ledger")
    str.metric("Liquid Cash Balance", f"${str.session_state.cash:,.2f}")
    
    if str.session_state.portfolio:
        str.subheader("Open Positions & Live P&L")
        
        portfolio_data = []
        total_unrealized_pl = 0.0
        
        # We need a quick data pull to get the live price for all assets held
        for port_ticker, data in str.session_state.portfolio.items():
            try:
                live_price = float(yf.Ticker(port_ticker).history(period="1d")['Close'].iloc[-1])
            except:
                live_price = data['avg_entry'] # Fallback
                
            qty = data['qty']
            avg_entry = data['avg_entry']
            current_val = qty * live_price
            invested_val = qty * avg_entry
            pl_dollars = current_val - invested_val
            pl_percent = (pl_dollars / invested_val) * 100
            
            total_unrealized_pl += pl_dollars
            
            portfolio_data.append({
                "Asset": port_ticker,
                "Units Held": qty,
                "Avg Entry Price": f"${avg_entry:,.2f}",
                "Live Market Price": f"${live_price:,.2f}",
                "Open P&L ($)": f"${pl_dollars:,.2f}",
                "Open P&L (%)": f"{pl_percent:,.2f}%"
            })
            
        str.metric("Total Unrealized P&L", f"${total_unrealized_pl:,.2f}", delta=f"${total_unrealized_pl:,.2f}")
        str.dataframe(pd.DataFrame(portfolio_data), use_container_width=True)
    else:
        str.info("Your portfolio is currently empty.")
        
    if str.session_state.statement:
        str.subheader("Trade History Ledger")
        str.dataframe(pd.DataFrame(str.session_state.statement).iloc[::-1], use_container_width=True) # Reverses order to show newest first

# ==========================================
# 4. THE AUTO-REFRESH LOOP
# ==========================================
if auto_refresh:
    time.sleep(refresh_rate)
    str.rerun()
