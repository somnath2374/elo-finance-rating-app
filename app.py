import streamlit as st
import requests
import pandas as pd

# ==============================
# 📌 Alpha Vantage API Key
# ==============================
API_KEY = "2TKMY92M38Z8BGUY"

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

    # RSI (Relative Strength Index)
    url = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
    rsi_data = requests.get(url).json()
    try:
        latest_rsi = list(rsi_data["Technical Analysis: RSI"].values())[0]["RSI"]
        indicators["RSI"] = float(latest_rsi)
    except:
        indicators["RSI"] = 50  # Neutral value

    # MACD (Moving Average Convergence Divergence)
    url = f"https://www.alphavantage.co/query?function=MACD&symbol={symbol}&interval=daily&series_type=close&apikey={API_KEY}"
    macd_data = requests.get(url).json()
    try:
        latest_macd = list(macd_data["Technical Analysis: MACD"].values())[0]
        indicators["MACD"] = float(latest_macd["MACD"])
    except:
        indicators["MACD"] = 0

    # SMA (Simple Moving Average)
    url = f"https://www.alphavantage.co/query?function=SMA&symbol={symbol}&interval=daily&time_period=50&series_type=close&apikey={API_KEY}"
    sma_data = requests.get(url).json()
    try:
        indicators["SMA"] = float(list(sma_data["Technical Analysis: SMA"].values())[0]["SMA"])
    except:
        indicators["SMA"] = 0

    return indicators

# ==============================
# 📌 Compute Stock Score
# ==============================
def compute_stock_score(fundamentals, technicals):
    if not fundamentals or not technicals:
        return 1000  # Default ELO

    # Assign weights (tweak these as needed)
    pe_weight = -5      # Lower P/E is better
    roe_weight = 10     # Higher ROE is better
    eps_weight = 10     # Higher EPS is better
    mc_weight = 0.5     # Higher Market Cap is better
    rsi_weight = 2      # RSI ~50 is neutral, above is bullish
    macd_weight = 10    # Positive MACD is good
    sma_weight = 1      # Price above SMA is bullish

    # Compute Score
    score = (fundamentals["P/E Ratio"] * pe_weight +
             fundamentals["ROE (%)"] * roe_weight +
             fundamentals["EPS"] * eps_weight +
             fundamentals["Market Cap (B)"] * mc_weight +
             technicals["RSI"] * rsi_weight +
             technicals["MACD"] * macd_weight +
             technicals["SMA"] * sma_weight)

    # Normalize score to ELO format
    return round(1000 + score, 2)

# ==============================
# 📌 Streamlit UI
# ==============================
def main():
    st.title("📈 Stock Elo Ranking System")

    stock_names = st.text_area("Enter stock symbols (comma separated)", "AAPL, MSFT, TSLA, GOOG")

    if st.button("Generate Rankings"):
        stock_list = [symbol.strip().upper() for symbol in stock_names.split(",")]

        elo_ratings = []
        for stock in stock_list:
            fundamentals = get_fundamental_data(stock)
            technicals = get_technical_data(stock)
            elo = compute_stock_score(fundamentals, technicals)
            elo_ratings.append({"Stock": stock, "Elo Rating": elo})

        leaderboard = pd.DataFrame(elo_ratings).sort_values(by="Elo Rating", ascending=False)

        st.subheader("🏆 Stock Leaderboard (Sorted by Elo Rating)")
        st.dataframe(leaderboard)

if __name__ == "__main__":
    main()
