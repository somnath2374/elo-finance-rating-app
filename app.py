import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# ==============================
# 📌 API Keys
# ==============================
API_KEY = "2TKMY92M38Z8BGUY"

# ==============================
# 📌 Fetch Real-Time Stock Price
# ==============================
def get_stock_price(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url).json()

    try:
        return float(response["Global Quote"]["05. price"])
    except:
        return None

# ==============================
# 📌 Fetch Fundamental Data
# ==============================
def get_fundamental_data(symbol):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url).json()

    if "Symbol" not in response:
        return None

    return {
        "P/E Ratio": float(response.get("PERatio", 0)),
        "ROE (%)": float(response.get("ReturnOnEquityTTM", 0)) * 100,
        "EPS": float(response.get("EPS", 0)),
        "Market Cap (B)": float(response.get("MarketCapitalization", 0)) / 1e9
    }

# ==============================
# 📌 Fetch Technical Indicators
# ==============================
def get_technical_data(symbol):
    indicators = {}

    # RSI
    url = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
    rsi_data = requests.get(url).json()
    try:
        indicators["RSI"] = float(list(rsi_data["Technical Analysis: RSI"].values())[0]["RSI"])
    except:
        indicators["RSI"] = 50

    # MACD
    url = f"https://www.alphavantage.co/query?function=MACD&symbol={symbol}&interval=daily&series_type=close&apikey={API_KEY}"
    macd_data = requests.get(url).json()
    try:
        indicators["MACD"] = float(list(macd_data["Technical Analysis: MACD"].values())[0]["MACD"])
    except:
        indicators["MACD"] = 0

    # SMA
    url = f"https://www.alphavantage.co/query?function=SMA&symbol={symbol}&interval=daily&time_period=50&series_type=close&apikey={API_KEY}"
    sma_data = requests.get(url).json()
    try:
        indicators["SMA"] = float(list(sma_data["Technical Analysis: SMA"].values())[0]["SMA"])
    except:
        indicators["SMA"] = 0

    return indicators

# ==============================
# 📌 Compute Elo Score
# ==============================
def compute_elo_score(fundamentals, technicals):
    if not fundamentals or not technicals:
        return 1000  # Default

    fundamental_score = (fundamentals["P/E Ratio"] * -5 +
                         fundamentals["ROE (%)"] * 10 +
                         fundamentals["EPS"] * 10 +
                         fundamentals["Market Cap (B)"] * 0.5)

    technical_score = (technicals["RSI"] * 2 +
                       technicals["MACD"] * 10 +
                       technicals["SMA"] * 1)

    return round(1000 + (fundamental_score + technical_score) / 2, 2), round(fundamental_score, 2), round(technical_score, 2)

# ==============================
# 📌 Streamlit UI
# ==============================
def main():
    st.title("📈 Stock Elo Ranking System")

    stock_names = st.text_area("Enter stock symbols (comma separated)", "AAPL, MSFT, TSLA, GOOG")
    
    # Custom Time Frame Selection
    time_frame = st.selectbox("Select Time Frame", ["1M", "3M", "6M", "1Y", "5Y", "Custom"])
    custom_time = None
    if time_frame == "Custom":
        custom_time = st.slider("Custom Time Frame (in months)", 1, 60, 12)

    if st.button("Generate Rankings"):
        stock_list = [symbol.strip().upper() for symbol in stock_names.split(",")]

        elo_ratings = []

        for stock in stock_list:
            fundamentals = get_fundamental_data(stock)
            technicals = get_technical_data(stock)
            elo, fundamental_score, technical_score = compute_elo_score(fundamentals, technicals)

            # Generate Elo score based on selected time frame
            if time_frame == "Custom":
                elo_score = elo + np.random.randint(-50, 50)  # Simulated variation
            else:
                time_frame_scores = {tf: elo + np.random.randint(-50, 50) for tf in ["1M", "3M", "6M", "1Y", "5Y"]}
                elo_score = time_frame_scores.get(time_frame, elo)

            median_elo = np.median([elo_score])
            avg_elo = np.mean([elo_score])

            stock_price = get_stock_price(stock)

            elo_ratings.append({
                "Stock": stock,
                "Current Price (₹)": stock_price,
                "Elo Score": elo_score,
                "Fundamental Score": fundamental_score,
                "Technical Score": technical_score,
                "Median Elo": round(median_elo, 2),
                "Average Elo": round(avg_elo, 2)
            })

            time.sleep(12)

        leaderboard = pd.DataFrame(elo_ratings).sort_values(by="Average Elo", ascending=False)

        st.subheader(f"🏆 Stock Leaderboard ({time_frame} Elo Score)")
        st.dataframe(leaderboard)

if __name__ == "__main__":
    main()
