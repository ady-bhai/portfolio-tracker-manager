import streamlit as st
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
import plotly.graph_objects as go

# Alpha Vantage API setup
def get_stock_data(ticker):
    api_key = 'YL85DT3REYG0T7SR'
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, _ = ts.get_daily(symbol=ticker, outputsize='compact')
    data = data[['4. close']]  # Use 'close' price
    data.columns = ['Close']  # Rename the column to 'Close'
    data.index = pd.to_datetime(data.index)  # Ensure the index is datetime format
    return data

# Portfolio Data
def create_portfolio_dataframe(tickers_list, quantity_list):
    stock_data = {}
    for ticker in tickers_list:
        data = get_stock_data(ticker)
        if data is not None:
            stock_data[ticker] = data['Close']
    
    # Create the portfolio data frame, multiplying the stock data by the quantities
    portfolio_data = pd.DataFrame(stock_data)
    portfolio_value = portfolio_data * quantity_list
    portfolio_value["Total Value"] = portfolio_value.sum(axis=1)
    return portfolio_value

# Portfolio Insights
def portfolio_insights(portfolio_df):
    total_value = portfolio_df["Total Value"].iloc[-1]
    st.subheader("Portfolio Insights")
    st.write(f"**Total Portfolio Value:** ${total_value:,.2f}")
    
    # Daily Returns
    daily_returns = portfolio_df.pct_change().dropna()
    st.write(f"**Daily Returns (Last 5 Days):**")
    st.write(daily_returns.tail())

    # Volatility (Standard Deviation)
    volatility = daily_returns.std().mean() * np.sqrt(252)  # Annualized volatility (252 trading days)
    st.write(f"**Annualized Volatility:** {volatility:.2%}")
    
    # Portfolio Diversification (correlation matrix)
    correlation = daily_returns.corr()
    st.write("**Portfolio Diversification (Correlation Matrix):**")
    st.dataframe(correlation)

# Sharpe Ratio Calculation
def calculate_sharpe_ratio(daily_returns):
    # Calculate Sharpe Ratio: (Mean Return - Risk-Free Rate) / Standard Deviation
    risk_free_rate = 0.0  # Assuming no risk-free rate for simplicity
    mean_return = daily_returns.mean() * 252  # Annualized mean return
    volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
    sharpe_ratio = (mean_return - risk_free_rate) / volatility
    return sharpe_ratio

# Recommendation System
def recommend_stocks(portfolio_df, tickers_list):
    daily_returns = portfolio_df.pct_change().dropna()

    # Calculate the Sharpe Ratio for each stock
    sharpe_ratios = {}
    for ticker in tickers_list:
        sharpe_ratios[ticker] = calculate_sharpe_ratio(daily_returns[ticker])
    
    # Sort by Sharpe Ratio (high to low)
    sorted_sharpe = sorted(sharpe_ratios.items(), key=lambda x: x[1], reverse=True)

    st.write("**Stocks with the Highest Sharpe Ratios:**")
    st.write(sorted_sharpe)
    
    # Suggest new stock based on correlation with the current portfolio (low correlation for diversification)
    st.write("**Stocks with Low Correlation to Current Portfolio:**")
    correlation = daily_returns.corr()
    
    # Find the top 3 stocks with the lowest average correlation with the portfolio
    avg_correlation = correlation.mean()
    low_corr_stocks = avg_correlation.sort_values().head(3)
    st.write(low_corr_stocks)

# Initialize Streamlit App Layout
st.title("Portfolio Management System")

# Sidebar for stock tickers and quantities
st.sidebar.header("Portfolio Management")

# Initialize session state if it doesn't exist
if 'tickers_list' not in st.session_state:
    st.session_state['tickers_list'] = ['AAPL']  # Default to one stock as the starting point
    st.session_state['quantity_list'] = [10]     # Default quantity

# Function to display dynamic stock inputs
def display_stock_inputs():
    tickers_input = []
    quantities_input = []
    
    # Iterate over the tickers in session state to create the inputs
    for i, ticker in enumerate(st.session_state['tickers_list']):
        tickers_input.append(st.sidebar.text_input(f"Stock Ticker {i+1}", ticker))
        quantities_input.append(st.sidebar.number_input(f"Quantity of {ticker}", min_value=1, value=st.session_state['quantity_list'][i]))

    # Add new stock input fields
    if st.sidebar.button("Add More Stocks"):
        # Add a new stock field to the list in session state
        st.session_state['tickers_list'].append('')
        st.session_state['quantity_list'].append(1)

    return tickers_input, quantities_input

# Get tickers and quantities from session state and input fields
tickers_input, quantities_input = display_stock_inputs()

# Update session state with the new values from the inputs
st.session_state['tickers_list'] = tickers_input
st.session_state['quantity_list'] = quantities_input

# Create portfolio dataframe based on user input
portfolio_df = create_portfolio_dataframe(st.session_state['tickers_list'], st.session_state['quantity_list'])

# Portfolio Insights
portfolio_insights(portfolio_df)

# Plot Portfolio Value Over Time
fig = go.Figure()
fig.add_trace(go.Scatter(x=portfolio_df.index, y=portfolio_df["Total Value"], mode="lines", name="Total Portfolio Value"))
fig.update_layout(title="Portfolio Value Over Time",
                  xaxis_title="Date",
                  yaxis_title="Portfolio Value (USD)",
                  template="plotly_dark")
st.plotly_chart(fig)

# Recommend Stocks based on Sharpe Ratio and Correlation
recommend_stocks(portfolio_df, st.session_state['tickers_list'])
