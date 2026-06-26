import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# Page config
st.set_page_config(page_title="QuantEdge Global Alpha Scanner", layout="wide")

# Persistent Memory Initialization
if "cash" not in st.session_state: st.session_state.cash = 10000.00
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "statement" not in st.session_state: st.session_state.statement = []
if "scan_results" not in st.session_state: st.session_state.scan_results = []
if "last_scan_time" not in st.session_state: st.session_state.last_scan_time = None

# Global Watchlist to Scan
GLOBAL_WATCHLIST = {
    "AAPL": "Apple (Equity)", "NVDA": "Nvidia (Equity)", "SPY": "S&P 500",
    "BTC-USD": "Bitcoin (Crypto)", "ETH-USD": "Ethereum (Crypto)", "SOL-USD": "Solana (Crypto)",
    "EURUSD=X": "EUR/USD (Forex)", "GBPUSD=X": "GBP/USD (Forex)", "JPY=X": "USD/JPY (Forex)",
    "GC=F": "Gold (Commodity)", "CL=F": "Crude Oil (Commodity)"
}

st.sidebar.header("🕹️ Scanner Controls")
timeframe = st.sidebar.selectbox("Scanning Interval", ["5 Minutes", "15 Minutes", "1 Hour", "1 Day"])

interval_map = {"5 Minutes": "5m", "15 Minutes": "15m", "1 Hour": "1h", "1 Day": "1d"}
period_map = {"5 Minutes": "5d", "15 Minutes": "5d", "1 Hour": "60d", "1 Day": "1y"}

# ==========================================
# CORE ALGORITHMIC ENGINE
# ==========================================
def calculate_indicators(df):
    """Calculates all native quantitative indicators needed for the scoring engine."""
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # ATR (Volatility for Stop Loss/Take Profit)
    high_low = df['High'] - df['Low']
    df['ATR'] = high_low.rolling(14).mean()
    
    df.bfill(inplace=True)
    return df

def generate_signal(ticker, df):
    """Evaluates the data and returns a trade recommendation if confidence is high."""
    latest = df.iloc[-1]
    curr_p = float(latest['Close'])
    
    score = 0
    reasons = []
    
    # Trend Logic
    if latest['EMA_9'] > latest['EMA_21']:
        score += 1
        reasons.append("Fast EMA crossed above Slow EMA (Bullish Trend).")
    else:
        score -= 1
        reasons.append("Fast EMA crossed below Slow EMA (Bearish Trend).")
        
    # Momentum Logic
    if latest['RSI'] < 35:
        score += 1.5
        reasons.append(f"RSI is oversold at {latest['RSI']:.1f}, indicating potential bounce.")
    elif latest['RSI'] > 65:
        score -= 1.5
        reasons.append(f"RSI is overbought at {latest['RSI']:.1f}, indicating exhaustion.")
        
    # Velocity Logic
    if latest['MACD'] > latest['Signal']:
        score += 1
        reasons.append("MACD Line is above Signal Line (Accelerating Momentum).")
    else:
        score -= 1
        reasons.append("MACD Line is below Signal Line (Decelerating Momentum).")

    # Risk Management Math
    atr = latest['ATR']
    confidence = min((abs(score) / 3.5) * 100, 99.0)
    
    # Only return a signal if confidence is high enough
    if score >= 2.0:
        return {
            "ticker": ticker, "action": "LONG 🟢", "price": curr_p, "confidence": confidence,
            "tp": curr_p + (atr * 2.5), "sl": curr_p - (atr * 1.5), "reasons": reasons
        }
    elif score <= -2.0:
        return {
            "ticker": ticker, "action": "SHORT 🔴", "price": curr_p, "confidence": confidence,
            "tp": curr_p - (atr * 2.5), "sl": curr_p + (atr * 1.5), "reasons": reasons
        }
    return None

# ==========================================
# TAB NAVIGATION
# ==========================================
tab1, tab2 = st.tabs(["🤖 Auto-Scanner & Execution", "💼 Portfolio Ledger"])

with tab1:
    st.title("🤖 Global Alpha Scanner")
    st.write("Scans global equities, forex, crypto, and commodities to identify high-probability setups.")
    
    if st.button("🚀 Run Global Alpha Scan", use_container_width=True):
        with st.spinner(f"Scanning {len(GLOBAL_WATCHLIST)} global assets..."):
            found_trades = []
            for ticker, name in GLOBAL_WATCHLIST.items():
                try:
                    df = yf.download(ticker, period=period_map[timeframe], interval=interval_map[timeframe], progress=False)
                    if not df.empty and len(df) > 30:
                        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                        df.reset_index(inplace=True)
                        df = calculate_indicators(df)
                        signal = generate_signal(ticker, df)
                        
                        if signal:
                            signal['name'] = name
                            found_trades.append(signal)
                except Exception as e:
                    pass # Skip failed downloads gracefully
            
            # Sort by highest confidence
            found_trades.sort(key=lambda x: x['confidence'], reverse=True)
            st.session_state.scan_results = found_trades
            st.session_state.last_scan_time = datetime.now().strftime("%H:%M:%S")

    # Display Scan Results
    if st.session_state.scan_results:
        st.success(f"Scan complete at {st.session_state.last_scan_time}. Found {len(st.session_state.scan_results)} high-probability setups.")
        
        for trade in st.session_state.scan_results:
            with st.container():
                st.markdown(f"### {trade['name']} ({trade['ticker']}) - {trade['action']}")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Live Entry Price", f"${trade['price']:,.4f}")
                col2.metric("Algorithm Confidence", f"{trade['confidence']:.1f}%")
                col3.metric("Take Profit (Target)", f"${trade['tp']:,.4f}")
                col4.metric("Stop Loss", f"${trade['sl']:,.4f}")
                
                with st.expander(f"View Quantitative Reasoning for {trade['ticker']}"):
                    for r in trade['reasons']:
                        st.write(f"- {r}")
                
                # Execution Form
                with st.form(f"execute_{trade['ticker']}"):
                    st.write(f"**Execute {trade['action']} on {trade['ticker']}**")
                    t_qty = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.1, key=f"qty_{trade['ticker']}")
                    
                    if st.form_submit_button("⚡ Execute Trade Automatically"):
                        cost = t_qty * trade['price']
                        
                        # Note: In a real environment, SHORTING requires margin. For this paper ledger, 
                        # we will treat a SHORT as creating a negative quantity position.
                        actual_qty = t_qty if "LONG" in trade['action'] else -t_qty
                        
                        if "LONG" in trade['action'] and st.session_state.cash < cost:
                            st.error("Insufficient Capital for Long Position.")
                        else:
                            if "LONG" in trade['action']:
                                st.session_state.cash -= cost
                            else:
                                st.session_state.cash += cost # Receiving cash for short sale
                                
                            st.session_state.portfolio[trade['ticker']] = {
                                'qty': actual_qty, 'avg_entry': trade['price'], 
                                'tp': trade['tp'], 'sl': trade['sl'], 'type': trade['action']
                            }
                            st.session_state.statement.append({
                                "Time": datetime.now().strftime("%H:%M:%S"), "Asset": trade['ticker'], 
                                "Action": trade['action'], "Qty": actual_qty, "Price": trade['price'], "Cost": cost
                            })
                            st.success(f"Position secured for {trade['ticker']}!")
                            time.sleep(1)
                            st.rerun()
                st.divider()
    elif st.session_state.last_scan_time:
        st.info(f"Scan complete at {st.session_state.last_scan_time}. The algorithm did not find any setups meeting the minimum confidence threshold in current market conditions. Try changing the timeframe.")

with tab2:
    st.header("📈 Active Risk Ledger")
    st.metric("Liquid Cash Balance", f"${st.session_state.cash:,.2f}")
    
    if st.session_state.portfolio:
        st.subheader("Open Positions")
        p_data = []
        for port_t, d in st.session_state.portfolio.items():
            # Get live price to calculate P&L
            try:
                live_p = float(yf.Ticker(port_t).history(period="1d")['Close'].iloc[-1])
            except:
                live_p = d['avg_entry']
                
            qty = d['qty']
            entry = d['avg_entry']
            
            # P&L Math changes depending on if it's a Long or Short position
            if qty > 0: # Long
                pl_dollars = (live_p - entry) * qty
            else: # Short (Negative qty)
                pl_dollars = (entry - live_p) * abs(qty)
                
            p_data.append({
                "Asset": port_t, "Type": d['type'], "Units": abs(qty), "Entry": f"${entry:,.4f}",
                "TP": f"${d['tp']:,.4f}", "SL": f"${d['sl']:,.4f}", "Live P&L": f"${pl_dollars:,.2f}"
            })
        st.dataframe(pd.DataFrame(p_data), use_container_width=True)
        
        # Manual Close Out Option
        st.subheader("Manage Open Positions")
        close_ticker = st.selectbox("Select Asset to Close", list(st.session_state.portfolio.keys()))
        if st.button("Close Selected Position"):
            pos = st.session_state.portfolio[close_ticker]
            try:
                close_p = float(yf.Ticker(close_ticker).history(period="1d")['Close'].iloc[-1])
            except:
                close_p = pos['avg_entry']
            
            if pos['qty'] > 0: # Closing a Long
                st.session_state.cash += (pos['qty'] * close_p)
            else: # Closing a Short
                st.session_state.cash -= (abs(pos['qty']) * close_p)
                
            st.session_state.statement.append({
                "Time": datetime.now().strftime("%H:%M:%S"), "Asset": close_ticker, 
                "Action": "CLOSED", "Qty": pos['qty'], "Price": close_p, "Cost": 0
            })
            del st.session_state.portfolio[close_ticker]
            st.success(f"Position closed for {close_ticker}.")
            time.sleep(1)
            st.rerun()
            
    else: st.info("No open positions.")
        
    if st.session_state.statement:
        st.subheader("Execution History")
        st.dataframe(pd.DataFrame(st.session_state.statement).iloc[::-1], use_container_width=True)
