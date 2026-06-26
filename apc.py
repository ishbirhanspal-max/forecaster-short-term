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
    str.session_state.portfolio = {}   
if "statement" not in str.session_state:
    str.session_state.statement = []   
if "engine_executed" not in str.session_state:
    str.session_state.engine_executed = False
if "current_market_data" not in str.session_state:
    str.session_state.current_market_data = None
if "last_analyzed_ticker" not in str.session_state:
    str.session_state.last_analyzed_ticker = None
if "live_price" not in str.session_state:
    str.session_state.live_price = 0.0

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
auto_refresh = str.sidebar.toggle("Enable Fast-Sync Loop", value=False)
refresh_rate = str.sidebar.slider("Refresh Interval (Seconds)", min_value=3, max_value=60, value=5)

interval_mapping = {
    "1 Minute": {"int": "1m", "period": "1d"},
    "5 Minutes": {"int": "5m", "period": "5d"},
    "15 Minutes": {"int": "15m", "period": "5d"},
    "1 Hour": {"int": "1h", "period": "60d"}
}

# ==========================================
# 3. FAST DATA PULL & AUTO-LIQUIDATION
# ==========================================
execute_clicked = str.sidebar.button("🔄 Force Data Sync", use_container_width=True)

if execute_clicked or auto_refresh or not str.session_state.engine_executed:
    chosen_int = interval_mapping[timeframe]["int"]
    chosen_per = interval_mapping[timeframe]["period"]
    
    df = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
    
    if df is not None and not df.empty:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['RSI'] = 100 - (100 / (1 + (df['Close'].diff().where(df['Close'].diff() > 0, 0).rolling(window=14).mean() / -df['Close'].diff().where(df['Close'].diff() < 0, 0).rolling(window=14).mean())))
        
        latest_price = float(df['Close'].iloc[-1])
        str.session_state.live_price = latest_price
        str.session_state.current_market_data = df
        str.session_state.engine_executed = True
        str.session_state.last_analyzed_ticker = ticker
        
        # --- AUTO-LIQUIDATION ENGINE ---
        if ticker in str.session_state.portfolio:
            pos = str.session_state.portfolio[ticker]
            trigger = None
            if pos['tp'] > 0 and latest_price >= pos['tp']:
                trigger = "TAKE PROFIT"
            elif pos['sl'] > 0 and latest_price <= pos['sl']:
                trigger = "STOP LOSS"
                
            if trigger:
                revenue = pos['qty'] * latest_price
                str.session_state.cash += revenue
                str.session_state.statement.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Asset": ticker,
                    "Action": f"AUTO-SELL ({trigger})",
                    "Qty": pos['qty'],
                    "Price": latest_price,
                    "Total Value": revenue
                })
                del str.session_state.portfolio[ticker]
                str.toast(f"{trigger} HIT! Auto-Sold {ticker} @ ${latest_price:.2f}", icon="🔥")

# ==========================================
# 4. TAB NAVIGATION & UI
# ==========================================
tab1, tab2 = str.tabs(["⚡ Fast-Execution Terminal", "💼 Portfolio Ledger"])

with tab1:
    if str.session_state.engine_executed and str.session_state.current_market_data is not None:
        df = str.session_state.current_market_data
        current_p = str.session_state.live_price
        active_ticker = str.session_state.last_analyzed_ticker
        
        str.title(f"⚡ {asset_name} Terminal")
        
        # ==========================================
        # RESTORED: THE LIVE RISK DASHBOARD
        # ==========================================
        if active_ticker in str.session_state.portfolio:
            str.markdown("### 🛡️ Active Position Dashboard")
            pos = str.session_state.portfolio[active_ticker]
            avg_entry = pos.get('avg_entry', 0.0)
            tp = pos.get('tp', 0.0)
            sl = pos.get('sl', 0.0)
            qty = pos.get('qty', 0.0)
            
            pl_dollars = (current_p - avg_entry) * qty
            pl_percent = ((current_p - avg_entry) / avg_entry) * 100 if avg_entry > 0 else 0.0
            
            # 5-Column Grid for live tracking
            dash_col1, dash_col2, dash_col3, dash_col4, dash_col5 = str.columns(5)
            dash_col1.metric("Live Price", f"${current_p:,.4f}", delta=f"{pl_percent:,.2f}% P&L")
            dash_col2.metric("Avg Entry Price", f"${avg_entry:,.4f}")
            dash_col3.metric("Take Profit Target", f"${tp:,.4f}" if tp > 0 else "None")
            dash_col4.metric("Stop Loss Target", f"${sl:,.4f}" if sl > 0 else "None")
            dash_col5.metric("Unrealized P&L", f"${pl_dollars:,.2f}", delta_color="normal" if pl_dollars >= 0 else "inverse")
            str.divider()
        else:
            # If no open position, just show the giant live price
            str.metric(f"Live Market Price ({timeframe} Sync)", f"${current_p:,.4f}")
            str.divider()

        # ==========================================
        # DYNAMIC CHARTING
        # ==========================================
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        time_column = df['Datetime'] if 'Datetime' in df else df['Date']
        
        if chart_style == "Candlestick":
            fig.add_trace(go.Candlestick(x=time_column, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=time_column, y=df['Close'], name="Price", line=dict(color='cyan', width=2)), row=1, col=1)
            
        fig.add_trace(go.Scatter(x=time_column, y=df['SMA_20'], name="20 SMA", line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_column, y=df['RSI'], name="RSI (14)", line=dict(color='gray')), row=2, col=1)
        
        # Draw physical target lines on the chart
        if active_ticker in str.session_state.portfolio:
            if tp > 0:
                fig.add_hline(y=tp, line_dash="dash", line_color="green", annotation_text="Take Profit", row=1, col=1)
            if sl > 0:
                fig.add_hline(y=sl, line_dash="dash", line_color="red", annotation_text="Stop Loss", row=1, col=1)
            fig.add_hline(y=avg_entry, line_dash="dot", line_color="blue", annotation_text="Entry", row=1, col=1)

        fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(t=10, b=10))
        str.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # ZERO-LAG MANUAL EXECUTION FORM
        # ==========================================
        str.markdown("### 💼 Manual Order Entry (Zero-Lag)")
        str.write(f"**Purchasing Power:** `${str.session_state.cash:,.2f}`")
        
        with str.form("trade_execution_form"):
            t_col1, t_col2, t_col3 = str.columns(3)
            t_qty = t_col1.number_input("Quantity", min_value=0.01, max_value=1000.0, value=1.00, step=0.1)
            tp_price = t_col2.number_input("Take Profit Target ($)", min_value=0.0, value=float(current_p * 1.02), step=0.01, help="Set 0 to disable")
            sl_price = t_col3.number_input("Stop Loss Target ($)", min_value=0.0, value=float(current_p * 0.98), step=0.01, help="Set 0 to disable")
            
            btn_col1, btn_col2 = str.columns(2)
            buy_intent = btn_col1.form_submit_button("🟢 Execute BUY", use_container_width=True)
            sell_intent = btn_col2.form_submit_button("🔴 Close POSITION", use_container_width=True)

        # Processing Execution
        if buy_intent:
            cost = t_qty * current_p
            if str.session_state.cash >= cost:
                str.session_state.cash -= cost
                if active_ticker in str.session_state.portfolio:
                    old_qty = str.session_state.portfolio[active_ticker].get('qty', 0)
                    old_avg = str.session_state.portfolio[active_ticker].get('avg_entry', 0)
                    new_qty = old_qty + t_qty
                    new_avg = ((old_qty * old_avg) + (t_qty * current_p)) / new_qty
                    str.session_state.portfolio[active_ticker] = {'qty': new_qty, 'avg_entry': new_avg, 'tp': tp_price, 'sl': sl_price}
                else:
                    str.session_state.portfolio[active_ticker] = {'qty': t_qty, 'avg_entry': current_p, 'tp': tp_price, 'sl': sl_price}
                
                str.session_state.statement.append({"Time": datetime.now().strftime("%H:%M:%S"), "Asset": active_ticker, "Action": "BUY", "Qty": t_qty, "Price": current_p, "Total Value": cost})
                str.success(f"Executed BUY: {t_qty} {active_ticker} @ ${current_p:.2f}")
                time.sleep(0.5)
                str.rerun()
            else:
                str.error("Insufficient Capital.")

        if sell_intent:
            if active_ticker in str.session_state.portfolio and str.session_state.portfolio[active_ticker].get('qty', 0) >= t_qty:
                revenue = t_qty * current_p
                str.session_state.cash += revenue
                
                str.session_state.portfolio[active_ticker]['qty'] -= t_qty
                if str.session_state.portfolio[active_ticker]['qty'] <= 0:
                    del str.session_state.portfolio[active_ticker]
                    
                str.session_state.statement.append({"Time": datetime.now().strftime("%H:%M:%S"), "Asset": active_ticker, "Action": "MANUAL SELL", "Qty": t_qty, "Price": current_p, "Total Value": revenue})
                str.success(f"Executed SELL: {t_qty} {active_ticker} @ ${current_p:.2f}")
                time.sleep(0.5)
                str.rerun()
            else:
                str.error("You do not own enough units to sell.")
    else:
        str.info("Waiting for market data connection...")

# ==========================================
# TAB 2: PORTFOLIO & RISK LEDGER
# ==========================================
with tab2:
    str.header("📈 Active Risk Ledger")
    str.metric("Liquid Cash Balance", f"${str.session_state.cash:,.2f}")
    
    if str.session_state.portfolio:
        str.subheader("Open Positions & Active Targets")
        portfolio_data = []
        for port_ticker, data in str.session_state.portfolio.items():
            if not isinstance(data, dict):
                data = {'qty': float(data), 'avg_entry': 0.0, 'tp': 0.0, 'sl': 0.0}
            qty = data.get('qty', 0.0)
            avg_entry = data.get('avg_entry', 0.0)
            tp = data.get('tp', 0.0)
            sl = data.get('sl', 0.0)
            live_price = str.session_state.live_price if port_ticker == str.session_state.last_analyzed_ticker else avg_entry
            pl_dollars = (live_price - avg_entry) * qty
            
            portfolio_data.append({
                "Asset": port_ticker,
                "Units": qty,
                "Entry": f"${avg_entry:,.2f}",
                "Take Profit": f"${tp:,.2f}" if tp > 0 else "None",
                "Stop Loss": f"${sl:,.2f}" if sl > 0 else "None",
                "Live P&L": f"${pl_dollars:,.2f}"
            })
        str.dataframe(pd.DataFrame(portfolio_data), use_container_width=True)
    else:
        str.info("Your portfolio is completely flat. No open positions.")
        
    if str.session_state.statement:
        str.subheader("Execution History")
        str.dataframe(pd.DataFrame(str.session_state.statement).iloc[::-1], use_container_width=True)

# ==========================================
# 5. THE AUTO-REFRESH LOOP
# ==========================================
if auto_refresh:
    time.sleep(refresh_rate)
    str.rerun()
