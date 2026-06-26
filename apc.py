import streamlit as str
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import datetime
import pandas as pd

# Page Configuration
str.set_page_config(page_title="Short-Term Stock Forecaster", layout="wide")
str.title("📈 Short-Term Stock Price Forecaster")
str.write("Predicting stock movements over days and months using 5 years of historical data.")

# 1. Sidebar Inputs
str.sidebar.header("Configuration")
ticker = str.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, GOOGL, MSFT)", value="AAPL").upper()

# Dropdown for short-term horizon
horizon_type = str.sidebar.selectbox("Forecast Horizon Type", ["Days", "Months"])
if horizon_type == "Days":
    horizon = str.sidebar.slider("Number of Days to Forecast", min_value=1, max_value=90, value=30)
    period_letter = 'D'
else:
    horizon = str.sidebar.slider("Number of Months to Forecast", min_value=1, max_value=12, value=3)
    period_letter = 'M'

# Calculate 5 years lookback
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5*365)

# 2. Data Fetching
@str.cache_data(ttl=3600)
def load_data(stock_ticker, start, end):
    try:
        data = yf.download(stock_ticker, start=start, end=end)
        if data.empty:
            return None
        data.reset_index(inplace=True)
        return data
    except Exception as e:
        return None

if ticker:
    with str.spinner(f"Fetching 5 years of data for {ticker}..."):
        df = load_data(ticker, start_date, end_date)
    
    if df is not None:
        str.success(f"Successfully loaded data for {ticker}!")
        
        # Display raw historical metrics
        latest_price = df['Close'].iloc[-1].values[0] if isinstance(df['Close'], pd.DataFrame) else df['Close'].iloc[-1]
        str.metric(label=f"Latest Closing Price ({df['Date'].iloc[-1].strftime('%Y-%m-%d')})", value=f"${latest_price:.2f}")
        
        # 3. Data Preparation for Prophet
        # Prophet requires columns named 'ds' (date) and 'y' (value)
        df_prophet = pd.DataFrame()
        df_prophet['ds'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        
        # Handle potential multi-index column from yfinance
        if isinstance(df['Close'], pd.DataFrame):
            df_prophet['y'] = df['Close'].iloc[:, 0]
        else:
            df_prophet['y'] = df['Close']

        # 4. Model Training and Forecasting
        # Tuned parameters specifically for short-term flexibility
        model = Prophet(
            daily_seasonality=False,   # Stock data is daily, intra-day seasonality not needed
            weekly_seasonality=True,   # Captures day-of-the-week effects (e.g., Friday sell-offs)
            yearly_seasonality=True,   # Captures annual cyclical trends
            changepoint_prior_scale=0.05 # Controls model flexibility (higher = more sensitive to recent changes)
        )
        
        with str.spinner("Training model and generating short-term forecast..."):
            model.fit(df_prophet)
            
            # Determine periods based on user selection
            if horizon_type == "Months":
                # Convert months to approximate days for the forecast step
                forecast_periods = horizon * 30
            else:
                forecast_periods = horizon
                
            future = model.make_future_dataframe(periods=forecast_periods)
            # Remove weekends from future dataframe since stock markets are closed
            future = future[future['ds'].dt.dayofweek < 5]
            
            forecast = model.predict(future)

        # 5. Visualizing the Results
        str.subheader(f"Short-Term Forecast Analysis for next {horizon} {horizon_type.lower()}")
        
        # Plotly chart showing historical + forecast + uncertainty intervals
        fig = plot_plotly(model, forecast)
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Stock Price ($)",
            template="plotly_white",
            hovermode="x unified"
        )
        str.plotly_chart(fig, use_container_width=True)
        
        # Forecast components (trends, weekly, yearly patterns)
        with str.expander("View Forecast Under-the-Hood Components"):
            str.write("These charts break down the underlying patterns the model detected over the 5-year period:")
            components_fig = model.plot_components(forecast)
            str.pyplot(components_fig)
            
        # Display raw forecast table
        str.subheader("Forecast Data Table")
        forecast_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_periods)
        forecast_display.columns = ['Date', 'Predicted Price', 'Pessimistic Bound (Lower)', 'Optimistic Bound (Upper)']
        str.dataframe(forecast_display.style.format({
            'Predicted Price': '${:.2f}', 
            'Pessimistic Bound (Lower)': '${:.2f}', 
            'Optimistic Bound (Upper)': '${:.2f}'
        }))

    else:
        str.error("Could not fetch data. Please check if the ticker symbol is valid.")
