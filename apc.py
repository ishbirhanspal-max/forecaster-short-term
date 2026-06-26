import streamlit as str
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Page config
str.set_page_config(page_title="QuantEdge Consensus Brokerage", layout="wide")

# ==========================================
# 1. INITIALIZE PERSISTENT PAPER TRADING STATE
# ==========================================
if "cash" not in str.session_state:
    str.session_state.cash = 10000.00  # Starting virtual capital
if "portfolio" not in str.session_state:
    str.session_state.portfolio = {}   # Tracks ticker: quantity
if "statement" not in str.session_state:
    str.session_state.statement = []   # List of transaction dicts

# ==========================================
# 2. NAVIGATION ARCHITECTURE
# ==========================================
tab1, tab2, tab3 = str.tabs(["⚡ Live Trading Terminal", "💼 Portfolio & Statements", "⚠️ Risk Protocols"])

ASSET_CLASSES = {
    "Cryptocurrency": {"Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD"},
    "Forex": {"EUR / USD": "EURUSD=X", "GBP / USD": "GBPUSD=X"},
    "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F"}
}

# Sidebar configuration panel
str.sidebar.header("🕹️ Terminal Controls")
asset_type = str.sidebar.selectbox("Asset Class", list(ASSET_CLASSES.keys()))
asset_name = str.sidebar.selectbox("Select Ticker", list(ASSET_CLASSES[asset_type].keys()))
ticker = ASSET_CLASSES[asset_type][asset_name]
timeframe = str.sidebar.selectbox("Interval Timeframe", ["1 Minute", "5 Minutes", "1 Hour"])

interval_mapping = {
    "1 Minute": {"int": "1m", "period": "2d", "secs": 60},
    "5 Minutes": {"int": "5m", "period": "5d", "secs": 300},
    "1 Hour": {"int": "1h", "period": "730d", "secs": 3600}
}

# Calculate exact time remaining until next data candle cuts
now = datetime.now()
secs_in_interval = interval_mapping[timeframe]["secs"]
seconds_passed = (now.minute * 60 + now.second) % secs_in_interval
seconds_remaining = secs_in_interval - seconds_passed

# ==========================================
# TAB 1: LIVE TRADING TERMINAL
# ==========================================
with tab1:
    str.title("⚡ QuantEdge Live Trading Terminal")
    
    # Live Ticker & Countdown Banner Row
    tick_col1, tick_col2, tick_col3 = str.columns(3)
    tick_col1.metric("Selected Instrument", f"{asset_name} ({ticker})")
    tick_col2.metric("Candle Horizon Timeframe", timeframe)
    tick_col3.metric("Seconds Until Next Candle", f"{seconds_remaining}s", help="Time remaining until the current time candle closes and a new one updates.")
    
    str.divider()
    
    # Single manual trigger button for execution
    execute_clicked = str.button("🔄 Pull Market Data & Execute Signal Scan", use_container_width=True)
    
    if execute_clicked:
        with str.spinner("Querying market feeds and executing quantitative equations..."):
            chosen_int = interval_mapping[timeframe]["int"]
            chosen_per = interval_mapping[timeframe]["period"]
            df = yf.download(ticker, period=chosen_per, interval=chosen_int, progress=False)
            
            if df is not None and len(df) > 50:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                df.reset_index(inplace=True)
                
                # Math Processing Engine
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
                
                latest = df.iloc[-1]
                current_p = float(latest['Close'])
                
                # Vote Matrix Logic
                buy_votes = 0
                sell_votes = 0
                reasons = []
                
                # Check 1: SMA Cross
                if float(latest['SMA_20']) > float(latest['SMA_50']):
                    buy_votes += 1
                    reasons.append("Bullish Bias: The 20 SMA is riding above the 50 SMA, confirming upward short-term structural support.")
                else:
                    sell_votes += 1
                    reasons.append("Bearish Bias: The 20 SMA is tracking below the 50 SMA, showing descending structural pressure.")
                    
                # Check 2: RSI Exhaustion
                rsi_v = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
                if rsi_v < 30:
                    buy_votes += 1
                    reasons.append(f"Oversold Signal: RSI is deeply depressed at {rsi_v:.2f}, highlighting strong exhaustion among sellers.")
                elif rsi_v > 70:
                    sell_votes += 1
                    reasons.append(f"Overbought Signal: RSI is highly elevated at {rsi_v:.2f}, indicating extreme near-term buyer over-extension.")
                else:
                    reasons.append(f"Neutral Momentum: RSI is holding steady at {rsi_v:.2f} within normal trading thresholds.")
                    
                # Check 3: MACD Line Cross
                if float(latest['MACD']) > float(latest['Signal_Line']):
                    buy_votes += 1
                    reasons.append("Bullish Momentum: The MACD line crossed cleanly over the Signal line, indicating accelerated buying velocity.")
                else:
                    sell_votes += 1
                    reasons.append("Bearish Momentum: The MACD line crossed underneath the Signal line, warning of distribution patterns.")

                # Calculate Signal Output & Strategy Confidence %
                if buy_votes > sell_votes:
                    signal_output = "BUY"
                    confidence_pct = (buy_votes / 3) * 100
                    alert_box = str.success
                elif sell_votes > buy_votes:
                    signal_output = "SELL"
                    confidence_pct = (sell_votes / 3) * 100
                    alert_box = str.error
                else:
                    signal_output = "NEUTRAL"
                    confidence_pct = 50.0
                    alert_box = str.warning

                # Display Results
                str.subheader("🎯 Mathematical Output Matrix")
                res_col1, res_col2, res_col3 = str.columns(3)
                res_col1.metric("Calculated Execution Price", f"${current_p:,.4f}")
                res_col2.markdown(f"### Signal: **{signal_output}**")
                res_col3.metric("Strategy Confidence Rating", f"{confidence_pct:.1f}%")
                
                alert_box(f"**Engine Assessment Verdict: {signal_output}** at a quantitative system confidence weight of {confidence_pct:.1f}%.")
                
                str.markdown("#### 🧠 Structural Reasoning Logs")
                for r in reasons:
                    str.markdown(f"- {r}")

                # Display Visual Chart Component
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                time_column = df['Datetime'] if 'Datetime' in df else df['Date']
                fig.add_trace(go.Candlestick(x=time_column, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market Price"), row=1, col=1)
                fig.add_trace(go.Scatter(x=time_column, y=df['SMA_20'], name="20 SMA"), row=1, col=1)
                fig.add_trace(go.Scatter(x=time_column, y=df['SMA_50'], name="50 SMA"), row=1, col=1)
                fig.add_trace(go.Scatter(x=time_column, y=df['RSI'], name="RSI (14)", line=dict(color='orange')), row=2, col=1)
                fig.update_layout(xaxis_rangeslider_visible=False, height=450, template="simple_white", margin=dict(t=10, b=10))
                str.plotly_chart(fig, use_container_width=True)

                # ==========================================
                # LIVE PAPER TRADING INTERACTION INTERFACE
                # ==========================================
                str.divider()
                str.subheader("💼 Paper Trading Execution Terminal")
                str.write(f"**Available Virtual Liquidity:** `${str.session_state.cash:,.2f} USD`")
                
                trade_col1, trade_col2 = str.columns(2)
                trade_qty = trade_col1.number_input("Transaction Quantity (Units)", min_value=0.01, max_value=1000.0, value=1.00, step=0.1)
                
                # Cache the trading asset information inside temporary data fields to execute safely
                str.session_state['active_price'] = current_p
                str.session_state['active_ticker'] = ticker

                # Paper Trading Purchase Processing
                if trade_col1.button("🟢 Execute Market Buy Order", use_container_width=True):
                    total_cost = trade_qty * current_p
                    if str.session_state.cash >= total_cost:
                        str.session_state.cash -= total_cost
                        str.session_state.portfolio[ticker] = str.session_state.portfolio.get(ticker, 0.0) + trade_qty
                        str.session_state.statement.append({
                            "Timestamp": datetime.now().strftime("%H:%M:%S"),
                            "Asset": ticker,
                            "Type": "BUY",
                            "Quantity": trade_qty,
                            "Execution Price": current_p,
                            "Total Value": total_cost
                        })
                        str.toast(f"Market Buy Order Completed: {trade_qty} {ticker}", icon="✅")
                    else:
                        str.error("Insufficient Cash Capital to clear this asset transaction order.")

                # Paper Trading Short/Sale Processing
                if trade_col2.button("🔴 Execute Market Sell Order", use_container_width=True):
                    if str.session_state.portfolio.get(ticker, 0.0) >= trade_qty:
                        total_revenue = trade_qty * current_p
                        str.session_state.cash += total_revenue
                        str.session_state.portfolio[ticker] -= trade_qty
                        if str.session_state.portfolio[ticker] <= 0:
                            del str.session_state.portfolio[ticker]
                        str.session_state.statement.append({
                            "Timestamp": datetime.now().strftime("%H:%M:%S"),
                            "Asset": ticker,
                            "Type": "SELL",
                            "Quantity": trade_qty,
                            "Execution Price": current_p,
                            "Total Value": total_revenue
                        })
                        str.toast(f"Market Sell Order Completed: {trade_qty} {ticker}", icon="🩸")
                    else:
                        str.error("Transaction Rejected: You do not own enough units of this asset to complete the sale.")
            else:
                str.error("Error reading streaming arrays. Re-execute the engine query request link.")

# ==========================================
# TAB 2: PORTFOLIO & ACCOUNT STATEMENTS
# ==========================================
with tab2:
    str.header("📋 Institutional Portfolio Ledger")
    
    val_col1, val_col2 = str.columns(2)
    val_col1.metric("Cash Balance (USD)", f"${str.session_state.cash:,.2f}")
    
    # Build dynamic open portfolio tracking frame
    if str.session_state.portfolio:
        str.markdown("### Open Capital Holdings")
        portfolio_rows = []
        for hold_ticker, qty in str.session_state.portfolio.items():
            portfolio_rows.append({"Asset Ticker Token": hold_ticker, "Open Allocated Balance (Units)": qty})
        str.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True)
    else:
        str.info("Your active portfolio currently holds zero open transaction positions.")
        
    str.divider()
    str.markdown("### 📜 Account Transaction Statement History")
    if str.session_state.statement:
        str.dataframe(pd.DataFrame(str.session_state.statement), use_container_width=True)
    else:
        str.caption("No trade transactions executed within this active container instance session.")

# ==========================================
# TAB 3: RISK RISK RISK
# ==========================================
with tab3:
    str.header("Regulatory Parameters & System Risk Warning")
    str.warning("""
    Mathematical confidence equations measure strategy alignment and do not reflect factual trading predictions. 
    High-frequency scalping patterns carry catastrophic decay profiles under standard leverage settings. 
    Use this paper trading dashboard exclusively to practice strategic quantitative analysis routines.
    """)
