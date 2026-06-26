import streamlit as str
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Page config
str.set_page_config(page_title="QuantEdge Pro Trading", layout="wide")

# ==========================================
# 1. INITIALIZE PERSISTENT MEMORY (THE FIX)
# ==========================================
if "cash" not in str.session_state:
    str.session_state.cash = 10000.00  
if "portfolio" not in str.session_state:
    str.session_state.portfolio = {}   
if "statement" not in str.session_state:
    str.session_state.statement = []   
# These three variables stop the app from collapsing on refresh
if "engine_executed" not in str.session_state:
    str.session_state.engine_executed = False
if "current_market_data" not in str.session_state:
    str.session_state.current_market_data = None
if "last_analyzed_ticker" not in str.session_state:
    str.session_state.last_analyzed_ticker = None

# ==========================================
# 2. EXPANDED ASSET INVENTORY
# ==========================================
ASSET_CLASSES = {
    "Equities (Stocks)": {"Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA", "Nvidia (NVDA)": "NVDA", "S&P 500 ETF (SPY)": "SPY"},
    "Cryptocurrency": {"Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (SOL)": "SOL-USD", "Ripple (XRP)": "XRP-USD"},
    "Forex": {"EUR / USD": "EURUSD=X", "GBP / USD": "GBPUSD=X", "USD / JPY": "JPY=X", "AUD / USD": "AUDUSD=X"},
    "Commodities": {"Gold": "GC=F", "Crude Oil": "CL=F", "Silver": "SI=F", "Natural Gas": "NG=F"}
}

# ==========================================
# 3. SIDEBAR & CONTROLS
# ==========================================
str.sidebar.header("🕹️ Terminal Controls")

# Callback to reset the engine if the user changes the asset
def reset_engine():
    str.session_state.engine_executed = False

asset_type = str.sidebar.selectbox("Asset Class", list(ASSET_CLASSES.keys()), on_change=reset_engine)
asset_name = str.sidebar.selectbox("Select Ticker", list(ASSET_CLASSES[asset_type].keys()), on_change=reset_engine)
ticker = ASSET_CLASSES[asset_type][asset_name]

timeframe = str.sidebar.selectbox("Interval Timeframe", ["1 Minute", "5 Minutes", "15 Minutes", "1 Hour"], on_change=reset_engine)
chart_style = str.sidebar.radio("Visual Chart Style", ["Candlestick", "Line Chart"])

interval_mapping = {
    "1 Minute": {"int": "1m", "period": "2d"},
    "5 Minutes": {"int": "5m", "period": "5d"},
    "15 Minutes": {"int": "15m", "period": "5d"},
    "1 Hour": {"int": "1h", "period": "730d"}
}

# ==========================================
# 4. TAB NAVIGATION
# ==========================================
tab1, tab2, tab3 = str.tabs(["⚡ Live Trading Terminal", "💼 Portfolio & Statements", "⚠️ Risk Protocols"])

with tab1:
    str.title("⚡ QuantEdge Live Trading Terminal")
    
    # Execute Button
    if str.button("🔄 Pull Market Data & Execute Signal Scan", use_container_width=True):
        with str.spinner("Querying market feeds..."):
            chosen_int = interval_mapping[timeframe]["int"]
            chosen_per = interval_mapping[timeframe]["period"]
            
            # Fetch data and store it in session state
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
                
                # Save to persistent memory
                str.session_state.current_market_data = df
                str.session_state.engine_executed = True
                str.session_state.last_analyzed_ticker = ticker
            else:
                str.error("Failed to retrieve sufficient data. The market may be closed, or the API blocked the request.")
                str.session_state.engine_executed = False

    str.divider()

    # ==========================================
    # 5. PERSISTENT RENDER LOGIC
    # ==========================================
    # This block ensures the UI stays open even after you click "Buy" or "Sell"
    if str.session_state.engine_executed and str.session_state.current_market_data is not None:
        df = str.session_state.current_market_data
        latest = df.iloc[-1]
        current_p = float(latest['Close'])
        
        # Re-calculate verdict logic for display
        buy_votes, sell_votes = 0, 0
        reasons = []
        
        if float(latest['SMA_20']) > float(latest['SMA_50']):
            buy_votes += 1
            reasons.append("Bullish Bias: The 20 SMA is riding above the 50 SMA.")
        else:
            sell_votes += 1
            reasons.append("Bearish Bias: The 20 SMA is tracking below the 50 SMA.")
            
        rsi_v = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
        if rsi_v < 30:
            buy_votes += 1
            reasons.append(f"Oversold Signal: RSI is depressed at {rsi_v:.2f}.")
        elif rsi_v > 70:
            sell_votes += 1
            reasons.append(f"Overbought Signal: RSI is elevated at {rsi_v:.2f}.")
        else:
            reasons.append(f"Neutral Momentum: RSI is holding steady at {rsi_v:.2f}.")
            
        if float(latest['MACD']) > float(latest['Signal_Line']):
            buy_votes += 1
            reasons.append("Bullish Momentum: MACD line crossed over the Signal line.")
        else:
            sell_votes += 1
            reasons.append("Bearish Momentum: MACD line crossed underneath the Signal line.")

        if buy_votes > sell_votes:
            signal_output, confidence_pct, alert_box = "BUY", (buy_votes / 3) * 100, str.success
        elif sell_votes > buy_votes:
            signal_output, confidence_pct, alert_box = "SELL", (sell_votes / 3) * 100, str.error
        else:
            signal_output, confidence_pct, alert_box = "NEUTRAL", 50.0, str.warning

        # Display Metrics
        res_col1, res_col2, res_col3 = str.columns(3)
        res_col1.metric(f"Execution Price ({str.session_state.last_analyzed_ticker})", f"${current_p:,.4f}")
        res_col2.markdown(f"### Signal: **{signal_output}**")
        res_col3.metric("Strategy Confidence Rating", f"{confidence_pct:.1f}%")
        
        alert_box(f"**Engine Assessment Verdict: {signal_output}** at a quantitative confidence of {confidence_pct:.1f}%.")
        with str.expander("View Verdict Reasoning"):
            for r in reasons:
                str.write(f"- {r}")

        # Display Dynamic Charts
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        time_column = df['Datetime'] if 'Datetime' in df else df['Date']
        
        # Toggle between Candlestick and Line
        if chart_style == "Candlestick":
            fig.add_trace(go.Candlestick(x=time_column, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market Price"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=time_column, y=df['Close'], name="Market Price (Line)", line=dict(color='blue', width=2)), row=1, col=1)
            
        fig.add_trace(go.Scatter(x=time_column, y=df['SMA_20'], name="20 SMA", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_column, y=df['SMA_50'], name="50 SMA", line=dict(color='purple')), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=time_column, y=df['RSI'], name="RSI (14)", line=dict(color='gray')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="simple_white", margin=dict(t=10, b=10))
        str.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # 6. PAPER TRADING EXECUTION
        # ==========================================
        str.divider()
        str.subheader("💼 Paper Trading Execution Terminal")
        str.write(f"**Available Virtual Liquidity:** `${str.session_state.cash:,.2f} USD`")
        
        trade_col1, trade_col2 = str.columns(2)
        trade_qty = trade_col1.number_input("Transaction Quantity (Units)", min_value=0.01, max_value=1000.0, value=1.00, step=0.1)
        
        active_ticker = str.session_state.last_analyzed_ticker

        if trade_col1.button("🟢 Execute Market Buy Order", use_container_width=True):
            total_cost = trade_qty * current_p
            if str.session_state.cash >= total_cost:
                str.session_state.cash -= total_cost
                str.session_state.portfolio[active_ticker] = str.session_state.portfolio.get(active_ticker, 0.0) + trade_qty
                str.session_state.statement.append({
                    "Timestamp": datetime.now().strftime("%H:%M:%S"),
                    "Asset": active_ticker,
                    "Type": "BUY",
                    "Quantity": trade_qty,
                    "Price": current_p,
                    "Total Value": total_cost
                })
                str.success(f"Bought {trade_qty} {active_ticker} at ${current_p:.2f}")
            else:
                str.error("Insufficient Capital.")

        if trade_col2.button("🔴 Execute Market Sell Order", use_container_width=True):
            if str.session_state.portfolio.get(active_ticker, 0.0) >= trade_qty:
                total_revenue = trade_qty * current_p
                str.session_state.cash += total_revenue
                str.session_state.portfolio[active_ticker] -= trade_qty
                if str.session_state.portfolio[active_ticker] <= 0:
                    del str.session_state.portfolio[active_ticker]
                str.session_state.statement.append({
                    "Timestamp": datetime.now().strftime("%H:%M:%S"),
                    "Asset": active_ticker,
                    "Type": "SELL",
                    "Quantity": trade_qty,
                    "Price": current_p,
                    "Total Value": total_revenue
                })
                str.success(f"Sold {trade_qty} {active_ticker} at ${current_p:.2f}")
            else:
                str.error("You do not own enough units to sell.")
    else:
        str.info("Select an asset and click 'Pull Market Data' to begin.")

# ==========================================
# PORTFOLIO TAB
# ==========================================
with tab2:
    str.header("📋 Portfolio Ledger")
    str.metric("Cash Balance (USD)", f"${str.session_state.cash:,.2f}")
    
    if str.session_state.portfolio:
        str.markdown("### Open Positions")
        str.dataframe(pd.DataFrame([{"Asset": k, "Units": v} for k, v in str.session_state.portfolio.items()]), use_container_width=True)
    
    if str.session_state.statement:
        str.markdown("### Transaction History")
        str.dataframe(pd.DataFrame(str.session_state.statement), use_container_width=True)

with tab3:
    str.warning("Paper trading environment only. Mathematical models do not guarantee real-world returns.")
