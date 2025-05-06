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
        result = yq.search(company_name, first_quote=True)
        if result and isinstance(result, dict) and "symbol" in result:
            return result["symbol"]
    except:
        pass
    return None

# ==============================
# 📌 Fetch Real-Time Prices & Convert USD to INR
# ==============================
def fetch_realtime_prices(tickers):
    usd_to_inr = get_usd_to_inr()
    real_time_prices = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            price = stock.history(period="1d")["Close"].iloc[-1]
            currency = stock.info.get("currency", "INR")
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
            change = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]) * 100
            base_elo = 1000
            elo_ratings[ticker] = round(base_elo + change * 10, 2)
        except:
            elo_ratings[ticker] = None
    return elo_ratings

# ==============================
# 📌 Compute Fundamental Elo Score
# ==============================
def compute_fundamental_elo(tickers):
    scores = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            pe = info.get("trailingPE", 0)
            roe = info.get("returnOnEquity", 0) * 100
            eps = info.get("trailingEps", 0)
            cap = info.get("marketCap", 0) / 1e9
            base_elo = 1000
            score = base_elo + (-3 * pe) + (5 * roe) + (2 * eps) + (0.5 * cap)
            scores[ticker] = round(score, 2)
        except:
            scores[ticker] = None
    return scores

# ==============================
# 📌 Compute Technical Elo Score
# ==============================
def compute_technical_elo(tickers):
    scores = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="6mo")
            if len(data) < 20:
                scores[ticker] = 0
                continue

            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_score = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

            ema_12 = data["Close"].ewm(span=12, adjust=False).mean()
            ema_26 = data["Close"].ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            macd_score = macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0

            sma_50 = data["Close"].rolling(window=50).mean()
            sma_score = data["Close"].iloc[-1] - sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else 0

            base_elo = 1000
            score = base_elo + (rsi_score - 50) + (5 * macd_score) + (0.2 * sma_score)
            scores[ticker] = round(score, 2)
        except:
            scores[ticker] = None
    return scores

# ==============================
# 📌 Streamlit UI
# ==============================
def main():
    st.title("📈 Stock Elo Ranking System")

    with st.expander("ℹ️ What is Elo Rating?"):
        st.markdown("""
        **Elo rating** is a method originally used in chess to rank players.  
        In this app, we adapt it for stocks by calculating Elo scores based on:
        - 📅 **Time-based performance** (past returns)
        - 📊 **Fundamental metrics** (P/E, EPS, ROE, etc.)
        - 📈 **Technical indicators** (RSI, MACD, SMA)
        These scores are combined to produce a **final ranking** for each stock.
        """)

    stock_names = st.text_area("Enter stock names (comma separated)", "Infosys, Reliance.NS, Apple, Tesla, TataMotors.NS")
    time_frame = st.selectbox("Select Time Frame", ["1wk", "1mo", "6mo", "1y", "5y"], index=3)

    if st.button("Generate Rankings"):
        stock_list = [name.strip() for name in stock_names.split(",")]
        tickers = [get_ticker(name) for name in stock_list]
        tickers = [t for t in tickers if t]

        if not tickers:
            st.error("No valid tickers found. Try entering correct stock names.")
            return

        with st.spinner("🔍 Fetching data and computing scores..."):
            real_time_prices = fetch_realtime_prices(tickers)
            time_elo = compute_time_elo(tickers, time_frame)
            fundamental_elo = compute_fundamental_elo(tickers)
            technical_elo = compute_technical_elo(tickers)

        df = pd.DataFrame({
            "Stock": tickers,
            "Current Price (₹)": [real_time_prices[t] for t in tickers],
            "Time-Based Elo": [time_elo[t] for t in tickers],
            "Fundamental Elo": [fundamental_elo[t] for t in tickers],
            "Technical Elo": [technical_elo[t] for t in tickers],
        })

        df["Final Elo Score"] = df[["Time-Based Elo", "Fundamental Elo", "Technical Elo"]].mean(axis=1).round(2)
        df = df.sort_values(by="Final Elo Score", ascending=False)

        st.subheader(f"🏆 Stock Leaderboard [{time_frame}]")
        st.dataframe(df.reset_index(drop=True))

if __name__ == "__main__":
    main()
