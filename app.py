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
            currency = stock.info.get("currency", "INR")  # Default INR
            
            # Convert USD to INR if needed
            if currency == "USD":
                price *= usd_to_inr  
            
            real_time_prices[ticker] = round(price, 2)
        except:
            real_time_prices[ticker] = None

    return real_time_prices

# ==============================
# 📌 Compute Time-Based Elo Score
# ==============================
def compute_time_elo(tickers, time_frame):
    elo_ratings = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=time_frame)["Close"]
            
            if len(data) < 2:
                continue  
            
            price_change = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]) * 100
            base_elo = 1000
            elo_ratings[ticker] = round(base_elo + price_change * 10, 2)  

        except:
            elo_ratings[ticker] = None

    return elo_ratings

# ==============================
# 📌 Compute Fundamental Elo Score
# ==============================
def compute_fundamental_elo(tickers):
    fundamental_scores = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            pe_ratio = info.get("trailingPE", 0)  # Lower P/E is better
            roe = info.get("returnOnEquity", 0) * 100  # Higher is better
            eps = info.get("trailingEps", 0)  # Higher is better
            market_cap = info.get("marketCap", 0) / 1e9  # Convert to billions
            
            base_elo = 1000
            fundamental_elo = base_elo + (-3 * pe_ratio) + (5 * roe) + (2 * eps) + (0.5 * market_cap)
            fundamental_scores[ticker] = round(fundamental_elo, 2)

        except:
            fundamental_scores[ticker] = None

    return fundamental_scores

# ==============================
# 📌 Compute Technical Elo Score
# ==============================
def compute_technical_elo(tickers):
    technical_scores = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="6mo")
            
            if len(data) < 20:
                technical_scores[ticker] = 0  # Not enough data, return 0
                continue
            
            # Compute RSI
            delta = data["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_score = rsi.iloc[-1] if not rsi.isna().iloc[-1] else 50  # Neutral if missing

            # Compute MACD
            ema_12 = data["Close"].ewm(span=12, adjust=False).mean()
            ema_26 = data["Close"].ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            macd_score = macd.iloc[-1] if not macd.isna().iloc[-1] else 0  

            # Compute SMA
            sma_50 = data["Close"].rolling(window=50).mean()
            sma_score = data["Close"].iloc[-1] - sma_50.iloc[-1] if not sma_50.isna().iloc[-1] else 0  

            base_elo = 1000
            technical_elo = base_elo + (rsi_score - 50) + (5 * macd_score) + (0.2 * sma_score)
            technical_scores[ticker] = round(technical_elo, 2)

        except:
            technical_scores[ticker] = None

    return technical_scores

# ==============================
# 📌 Streamlit UI
# ==============================
def main():
    st.title("📈 Stock Elo Ranking System")
    
    stock_names = st.text_area("Enter stock names (comma separated)", "Infosys, Reliance.NS, Apple, Tesla , Tata")

    # Time frame selection
    time_frame = st.selectbox("Select Time Frame", ["1wk", "1mo", "6mo", "1y", "5y"], index=4)  

    if st.button("Generate Rankings"):
        stock_list = [name.strip() for name in stock_names.split(",")]
        tickers = [get_ticker(name) for name in stock_list]
        tickers = [t for t in tickers if t]  

        if not tickers:
            st.error("No valid tickers found. Try entering correct stock names.")
            return

        real_time_prices = fetch_realtime_prices(tickers)
        time_elo = compute_time_elo(tickers, time_frame)
        fundamental_elo = compute_fundamental_elo(tickers)
        technical_elo = compute_technical_elo(tickers)

        leaderboard = pd.DataFrame({
            "Stock": tickers,
            "Current Price (₹)": [real_time_prices[ticker] for ticker in tickers],
            "Time-Based Elo": [time_elo[ticker] for ticker in tickers],
            "Fundamental Elo": [fundamental_elo[ticker] for ticker in tickers],
            "Technical Elo": [technical_elo[ticker] for ticker in tickers],
        })

        leaderboard["Final Elo Score"] = leaderboard[["Time-Based Elo", "Fundamental Elo", "Technical Elo"]].mean(axis=1).round(2)

        leaderboard = leaderboard.sort_values(by="Final Elo Score", ascending=False)

        st.subheader(f"🏆 Stock Leaderboard (Sorted by Final Elo Score) [{time_frame} Data]")
        st.dataframe(leaderboard)

if __name__ == "__main__":
    main()
