import streamlit as st
import yahooquery as yq
import yfinance as yf
import pandas as pd
import requests

# ==============================
# 📌 Fetch Real-Time USD to INR Exchange Rate
# ==============================
def get_usd_to_inr():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return data["rates"]["INR"]
    except:
        return 83.0  # Default value

# ==============================
# 📌 Get Ticker Symbol from Company Name
# ==============================
def get_ticker(company_name):
    try:
        search_result = yq.search(company_name)
        if search_result and "quotes" in search_result:
            return search_result["quotes"][0]["symbol"]
    except:
        return None

# ==============================
# 📌 Fetch Real-Time Prices & Convert USD to INR
# ==============================
def fetch_realtime_prices(tickers):
    usd_to_inr = get_usd_to_inr()  # Get latest exchange rate
    real_time_prices = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            price = stock.history(period="1d")["Close"].iloc[-1]  # Latest price
            
            # Detect currency
            currency = stock.info.get("currency", "INR")  # Default INR
            
            # Convert USD to INR if needed
            if currency == "USD":
                price *= usd_to_inr  
            
            real_time_prices[ticker] = round(price, 2)
        except:
            real_time_prices[ticker] = None

    return real_time_prices

# ==============================
# 📌 Compute ELO Rating Based on Time Frame
# ==============================
def compute_elo_ratings(tickers, time_frame):
    elo_ratings = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=time_frame)["Close"]
            
            if len(data) < 2:
                continue  # Skip if not enough data
            
            # Calculate % change over time frame
            price_change = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]) * 100
            
            # Convert % change to Elo Rating (higher % change = higher Elo)
            base_elo = 1000
            elo_ratings[ticker] = round(base_elo + price_change * 10, 2)  # Adjust multiplier as needed

        except:
            elo_ratings[ticker] = None

    return elo_ratings

# ==============================
# 📌 Streamlit UI
# ==============================
def main():
    st.title("📈 Stock Elo Ranking System")
    
    stock_names = st.text_area("Enter stock names (comma separated)", "Infosys, Reliance,Tata")

    # Time frame selection
    time_frame = st.selectbox("Select Time Frame", ["1d", "1wk", "1mo", "6mo", "1y", "5y"], index=4)  

    if st.button("Generate Rankings"):
        stock_list = [name.strip() for name in stock_names.split(",")]
        tickers = [get_ticker(name) for name in stock_list]
        tickers = [t for t in tickers if t]  # Remove None values

        if not tickers:
            st.error("No valid tickers found. Try entering correct stock names.")
            return

        real_time_prices = fetch_realtime_prices(tickers)
        elo_ratings = compute_elo_ratings(tickers, time_frame)

        leaderboard = pd.DataFrame({
            "Stock": tickers,
            "Elo Rating": [elo_ratings[ticker] for ticker in tickers],
            "Current Price (₹)": [real_time_prices[ticker] for ticker in tickers]
        }).sort_values(by="Elo Rating", ascending=False)

        st.subheader(f"🏆 Stock Leaderboard (Sorted by Elo Rating) [{time_frame} Data]")
        st.dataframe(leaderboard)

if __name__ == "__main__":
    main()
