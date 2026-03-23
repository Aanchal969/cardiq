import os
import re
import json
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="CardIQ", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

# ---------- THEME ----------
st.markdown(
    """
<style>
:root{
  --bg:#060606;
  --panel:#0d0d0f;
  --panel2:#121216;
  --border:#24242e;
  --text:#f7f7fb;
  --muted:#d6d8e4;
  --soft:#9aa0b5;
  --accent:#8b5cf6;
  --accent2:#22d3ee;
  --accent3:#ff5f6d;
  --gold:#fbbf24;
  --card:#101015;
}
html, body, [class*="css"], .stApp {background: #050507 !important; color:var(--text)!important; font-family: Inter, system-ui, sans-serif !important;}
#MainMenu, footer, header {visibility:hidden;}
.block-container{max-width:1180px; padding: 2.2rem 1.3rem 4rem 1.3rem !important;}
section[data-testid="stSidebar"]{display:none}

.hero{background:linear-gradient(135deg, rgba(18,18,24,0.98) 0%, rgba(22,18,35,0.98) 45%, rgba(8,22,30,0.98) 100%); border:1px solid var(--border); border-radius:26px; padding:28px 38px; box-shadow:0 22px 60px rgba(0,0,0,0.38); position:relative; overflow:hidden;}
.hero:before{content:''; position:absolute; right:-80px; top:-80px; width:320px; height:320px; background:radial-gradient(circle, rgba(139,92,246,.28) 0%, rgba(139,92,246,0) 62%);}
.hero:after{content:''; position:absolute; left:-120px; bottom:-120px; width:300px; height:300px; background:radial-gradient(circle, rgba(34,211,238,.20) 0%, rgba(34,211,238,0) 68%);}
.eyebrow{font-size:.82rem; text-transform:uppercase; letter-spacing:.25em; color:var(--soft); font-weight:700; position:relative; z-index:2;}
.h1{font-size:4rem; font-weight:800; letter-spacing:-.04em; margin:.6rem 0 .35rem 0; color:var(--text); position:relative; z-index:2;}
.brand-accent{background:linear-gradient(135deg,var(--accent),var(--accent2)); -webkit-background-clip:text; background-clip:text; color:transparent}
.sub{font-size:1.14rem; color:var(--muted); line-height:1.65; position:relative; z-index:2}
.section-label{font-size:.84rem; color:var(--soft); letter-spacing:.22em; text-transform:uppercase; font-weight:700; margin:1.8rem 0 .9rem 0;}
.panel{background:linear-gradient(180deg, rgba(18,18,24,0.96) 0%, rgba(11,11,15,0.96) 100%); border:1px solid var(--border); border-radius:20px; padding:22px 24px; box-shadow:0 10px 30px rgba(0,0,0,.22);}
.metric{background:linear-gradient(180deg, rgba(18,18,24,0.96) 0%, rgba(11,11,15,0.96) 100%); border:1px solid var(--border); border-radius:22px; padding:22px 24px; min-height:138px; box-shadow:0 10px 30px rgba(0,0,0,.22);}
.metric-label{font-size:.82rem; color:var(--soft); letter-spacing:.18em; text-transform:uppercase; font-weight:700; margin-bottom:12px;}
.metric-value{font-size:2.6rem; font-weight:800; letter-spacing:-.03em; color:var(--text);}
.metric-sub{font-size:1rem; color:var(--muted); margin-top:6px; line-height:1.55}
.chip{display:inline-flex; align-items:center; padding:8px 14px; border-radius:999px; background:linear-gradient(135deg, rgba(139,92,246,.22), rgba(34,211,238,.12)); border:1px solid rgba(139,92,246,.28); color:#f4f6ff; font-weight:700; margin:0 8px 8px 0;}
.bank-card{background:linear-gradient(180deg, rgba(18,18,24,0.96) 0%, rgba(11,11,15,0.96) 100%); border:1px solid var(--border); border-radius:22px; padding:22px 16px; text-align:center; min-height:162px; display:flex; flex-direction:column; justify-content:center; gap:12px; transition:all .18s ease; cursor:pointer; box-shadow:0 10px 30px rgba(0,0,0,.18);}
.bank-card:hover{transform:translateY(-3px); border-color:rgba(139,92,246,.55); box-shadow:0 16px 40px rgba(0,0,0,.35), 0 0 0 1px rgba(34,211,238,.22) inset;}
.badge{width:62px;height:62px;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:800;margin:0 auto;color:white; box-shadow: inset 0 0 0 1px rgba(255,255,255,.06)}
.helper{font-size:1rem; color:var(--muted); line-height:1.7}
.chat-box{background:linear-gradient(180deg, rgba(18,18,24,0.96) 0%, rgba(11,11,15,0.96) 100%); border:1px solid var(--border); border-radius:22px; padding:22px 24px; box-shadow:0 10px 30px rgba(0,0,0,.22);}
.chat-user{color:#f4f6ff; font-weight:700; margin:12px 0 6px 0;}
.chat-ai{color:#eef2ff; line-height:1.72; padding:14px 16px; background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08); border-radius:16px; margin-bottom:12px}
.big-note{font-size:.98rem; color:var(--muted)}
.cta-line{display:flex; justify-content:space-between; gap:16px; align-items:flex-start}
.small-pill{display:inline-flex; align-items:center; border:1px solid var(--border); background:rgba(255,255,255,.03); padding:8px 12px; border-radius:999px; color:var(--muted); margin:0 8px 8px 0; font-size:.94rem}
[data-testid="stExpander"] details{background:linear-gradient(180deg, rgba(18,18,24,0.96) 0%, rgba(11,11,15,0.96) 100%)!important; border:1px solid var(--border)!important; border-radius:16px!important}
[data-testid="stExpander"] summary{color:var(--text)!important; font-weight:700!important}
button[kind="primary"]{background:linear-gradient(135deg,var(--accent3),var(--accent))!important; border:none!important; color:white!important; box-shadow:0 10px 28px rgba(139,92,246,.22)!important}
.stButton>button{border-radius:14px!important; font-weight:700!important; padding:.72rem 1rem!important; transition:all .16s ease!important}
.stButton>button:hover{transform:translateY(-1px)!important; border-color:rgba(139,92,246,.55)!important; box-shadow:0 10px 26px rgba(0,0,0,.24)!important}
.stButton>button:not([kind="primary"]){background:linear-gradient(180deg, rgba(18,18,24,0.96) 0%, rgba(11,11,15,0.96) 100%)!important; color:var(--text)!important; border:1px solid var(--border)!important}
.stCheckbox label, .stCheckbox div{color:var(--text)!important}
[data-testid="stTextInputRootElement"], [data-testid="stTextInput"]{background:transparent!important}
div[data-testid="stTextInput"] input,
[data-testid="stTextInputRootElement"] input,
input[type="text"], input[type="password"], textarea{
  background:#111318!important;
  background-color:#111318!important;
  color:#f8fbff!important;
  -webkit-text-fill-color:#f8fbff!important;
  caret-color:#f8fbff!important;
  border:1px solid var(--border)!important;
  border-radius:14px!important;
  padding:.82rem 1rem!important;
  font-weight:500!important;
  box-shadow:none!important;
}
div[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextInputRootElement"] input::placeholder,
input[type="text"]::placeholder,
input[type="password"]::placeholder,
textarea::placeholder{
  color:#aeb7cb!important;
  -webkit-text-fill-color:#aeb7cb!important;
  opacity:1!important;
}
div[data-testid="stTextInput"] input:focus,
[data-testid="stTextInputRootElement"] input:focus,
input[type="text"]:focus,
input[type="password"]:focus,
textarea:focus{
  border-color:rgba(139,92,246,.75)!important;
  box-shadow:0 0 0 3px rgba(139,92,246,.16)!important;
  outline:none!important;
}
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
textarea:-webkit-autofill{
  -webkit-text-fill-color:#f8fbff!important;
  -webkit-box-shadow:0 0 0px 1000px #111318 inset!important;
  transition:background-color 9999s ease-in-out 0s!important;
}
div[data-testid="stTextInput"] label, .stTextInput label{color:var(--text)!important}
.note-card{background:rgba(139,92,246,.10); border:1px solid rgba(139,92,246,.24); border-radius:18px; padding:16px 18px; color:var(--muted)}
hr{border:none; height:1px; background:var(--border); margin:1.2rem 0 1.4rem 0}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- DATA ----------
BANKS = [
    {"name": "HDFC Bank", "abbr": "HDFC", "color": "#2d6bff"},
    {"name": "ICICI Bank", "abbr": "ICICI", "color": "#ff7d55"},
    {"name": "SBI", "abbr": "SBI", "color": "#4675ff"},
    {"name": "Axis Bank", "abbr": "AXIS", "color": "#c03c8a"},
    {"name": "Kotak", "abbr": "KOTAK", "color": "#ff7a3d"},
    {"name": "IDFC First", "abbr": "IDFC", "color": "#d24e43"},
]

CARD_BENEFITS = {
    "HDFC Millennia": {"categories": {"Online Shopping": 5.0, "Food Delivery": 5.0, "Groceries": 1.0, "Travel": 1.0, "Entertainment": 1.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Best for online shopping & food delivery"},
    "Axis Ace": {"categories": {"Utilities": 5.0, "Groceries": 2.0, "Online Shopping": 1.5, "Food Delivery": 1.5, "Travel": 1.5, "Entertainment": 1.5, "Fuel": 1.5, "Health": 1.5, "Other": 1.5}, "note": "Strong for bill payments & general cashback"},
    "HDFC Regalia": {"categories": {"Travel": 4.0, "Entertainment": 3.0, "Online Shopping": 3.0, "Food Delivery": 3.0, "Groceries": 2.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 2.0}, "note": "Travel and premium lifestyle"},
    "SBI Cashback": {"categories": {"Online Shopping": 5.0, "Food Delivery": 5.0, "Entertainment": 5.0, "Groceries": 1.0, "Travel": 1.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Broad online cashback"},
    "ICICI Amazon Pay": {"categories": {"Online Shopping": 5.0, "Groceries": 2.0, "Food Delivery": 2.0, "Travel": 2.0, "Entertainment": 2.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Amazon-heavy spending"},
    "Amex MRCC": {"categories": {"Travel": 2.0, "Entertainment": 2.0, "Online Shopping": 2.0, "Food Delivery": 2.0, "Groceries": 2.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Rewards points and travel use"},
    "HSBC Cashback": {"categories": {"Online Shopping": 4.0, "Food Delivery": 4.0, "Groceries": 2.0, "Travel": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Useful backup cashback card"},
    "HDFC Tata Neu": {"categories": {"Online Shopping": 3.0, "Groceries": 3.0, "Food Delivery": 1.5, "Travel": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Neu ecosystem & groceries"},
    "Axis Flipkart": {"categories": {"Online Shopping": 5.0, "Travel": 1.5, "Entertainment": 1.5, "Food Delivery": 1.5, "Groceries": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "E-commerce focused"},
    "BPCL SBI Card": {"categories": {"Fuel": 4.5, "Other": 1.0, "Online Shopping": 1.0, "Food Delivery": 1.0, "Groceries": 1.0, "Travel": 1.0, "Entertainment": 1.0, "Utilities": 1.0, "Health": 1.0}, "note": "Fuel-centric"},
    "IDFC First Select": {"categories": {"Utilities": 2.5, "Online Shopping": 2.0, "Food Delivery": 2.0, "Groceries": 2.0, "Travel": 2.0, "Entertainment": 2.0, "Fuel": 1.5, "Health": 2.0, "Other": 1.5}, "note": "Balanced all-round card"},
    "AU Ixigo": {"categories": {"Travel": 5.0, "Online Shopping": 1.5, "Food Delivery": 1.5, "Groceries": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0}, "note": "Travel-heavy users"},
}

CATEGORY_PATTERNS = [
    (r"swiggy|zomato", "Food Delivery"),
    (r"dmart|blinkit|bigbasket|grocer|big bazaar", "Groceries"),
    (r"amazon|myntra|flipkart|nykaa|ajio|croma|apple store", "Online Shopping"),
    (r"makemytrip|air india|hotel|flight|irctc|uber intercity", "Travel"),
    (r"netflix|spotify|youtube premium|bookmyshow|prime video|hotstar|dth", "Entertainment"),
    (r"hpcl|bpcl|fuel|petrol", "Fuel"),
    (r"airtel|jio fiber|wifi|broadband|electricity|bescom|maintenance|insurance|dth", "Utilities"),
    (r"apollo|pharmacy|health|cult.fit", "Health"),
]

RECURRING_HINTS = ["airtel", "jio fiber", "netflix", "spotify", "youtube premium", "dth", "maintenance", "electricity", "insurance", "cult.fit", "prime"]


def generate_demo_transactions() -> pd.DataFrame:
    rows = []
    months = [
        ("2025-10", {
            "Airtel Postpaid": 899, "Jio Fiber Broadband": 1499, "Netflix Subscription": 649,
            "Spotify Premium": 119, "Tata Play DTH": 699, "Society Maintenance": 3500,
            "BESCOM Electricity Bill": 3450, "DMart Grocery": 5200, "HPCL Fuel": 3000,
            "Swiggy Order": 1900, "Amazon Shopping": 4200, "Myntra Fashion": 2100,
            "BookMyShow Movies": 850, "Cult.fit Membership": 999
        }),
        ("2025-11", {
            "Airtel Postpaid": 899, "Jio Fiber Broadband": 1499, "Netflix Subscription": 649,
            "Spotify Premium": 119, "Tata Play DTH": 699, "Society Maintenance": 3500,
            "BESCOM Electricity Bill": 3580, "DMart Grocery": 4950, "HPCL Fuel": 3200,
            "Swiggy Order": 2100, "Amazon Shopping": 4700, "Myntra Fashion": 2500,
            "YouTube Premium": 189, "Cult.fit Membership": 999
        }),
        ("2025-12", {
            "Airtel Postpaid": 899, "Jio Fiber Broadband": 1499, "Netflix Subscription": 649,
            "Spotify Premium": 119, "Tata Play DTH": 699, "Society Maintenance": 3500,
            "BESCOM Electricity Bill": 3820, "DMart Grocery": 5150, "HPCL Fuel": 4500,
            "Swiggy Order": 2300, "Amazon Shopping": 6900, "Myntra Fashion": 3600,
            "Flipkart Shopping": 4404, "Year-end Travel Booking": 28000,
            "Cult.fit Membership": 999
        }),
        ("2026-01", {
            "Airtel Postpaid": 999, "Jio Fiber Broadband": 1499, "Netflix Subscription": 649,
            "Spotify Premium": 119, "Tata Play DTH": 699, "Society Maintenance": 3500,
            "BESCOM Electricity Bill": 3985, "DMart Grocery": 5300, "HPCL Fuel": 3000,
            "Swiggy Order": 2850, "Amazon Shopping": 9600, "Myntra Fashion": 5285,
            "Nykaa Beauty": 2768, "BookMyShow Movies": 1200,
            "Domestic Flight": 31000, "Cult.fit Membership": 999
        }),
        ("2026-02", {
            "Airtel Postpaid": 999, "Jio Fiber Broadband": 1499, "Netflix Subscription": 649,
            "Spotify Premium": 119, "Tata Play DTH": 699, "Society Maintenance": 3500,
            "BESCOM Electricity Bill": 4150, "DMart Grocery": 4575, "BPCL Fuel": 3000,
            "Blinkit Grocery": 2025, "Swiggy Order": 2335, "Amazon Shopping": 8179,
            "Myntra Fashion": 5285, "YouTube Premium": 189, "Cult.fit Membership": 999,
            "UPI/9876543210@ybl/0": 2100
        }),
        ("2026-03", {
            "Airtel Postpaid": 999, "Jio Fiber Broadband": 1599, "Netflix Subscription": 649,
            "Spotify Premium": 119, "Tata Play DTH": 699, "Society Maintenance": 3500,
            "BESCOM Electricity Bill": 4150, "DMart Grocery": 6050, "HPCL Fuel": 4500,
            "Blinkit Grocery": 3000, "Swiggy Order": 3435, "Amazon Shopping": 11050,
            "Myntra Fashion": 14840, "Croma Electronics": 68999, "Apple Store Purchase": 14999,
            "Annual Car Insurance": 18200, "YouTube Premium": 189, "Cult.fit Membership": 999,
            "UPI/merchants@okaxis": 2900, "UPI/9876543210@ybl/5": 2400
        })
    ]

    for ym, spends in months:
        for desc, amount in spends.items():
            rows.append({"Date": f"{ym}-01", "Description": desc, "Amount": amount})
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def categorize(desc: str) -> str:
    text = str(desc).lower()
    for pat, cat in CATEGORY_PATTERNS:
        if re.search(pat, text):
            return cat
    return "Other"


def compute_analytics(df: pd.DataFrame, selected_cards: list[str]) -> dict:
    work = df.copy()
    work["Category"] = work["Description"].apply(categorize)
    work["Month"] = work["Date"].dt.to_period("M").astype(str)
    work["Merchant"] = work["Description"].str.replace(r"\s*Subscription|\s*Broadband|\s*Shopping|\s*Grocery|\s*Purchase", "", regex=True)

    monthly = work.groupby("Month", as_index=False)["Amount"].sum()
    current_month = monthly.iloc[-1]["Month"]
    prev_month = monthly.iloc[-2]["Month"]
    current_spend = float(monthly.iloc[-1]["Amount"])
    prev_spend = float(monthly.iloc[-2]["Amount"])
    mom_change = current_spend - prev_spend
    mom_pct = (mom_change / prev_spend * 100) if prev_spend else 0

    current_df = work[work["Month"] == current_month].copy()
    current_by_cat = current_df.groupby("Category", as_index=False)["Amount"].sum().sort_values("Amount", ascending=False)

    recurring = work.copy()
    recurring["RecurringKey"] = recurring["Description"].str.lower()
    recurring_summary = recurring.groupby("RecurringKey").agg(
        count=("Amount", "count"),
        avg_amount=("Amount", "mean"),
        latest_description=("Description", "last"),
        category=("Category", "last")
    ).reset_index()
    recurring_summary = recurring_summary[(recurring_summary["count"] >= 2) | (recurring_summary["RecurringKey"].str.contains("|".join(RECURRING_HINTS), regex=True))]
    recurring_summary = recurring_summary.sort_values("avg_amount", ascending=False)
    recurring_monthly_value = float(recurring_summary["avg_amount"].sum()) if not recurring_summary.empty else 0.0

    cat_month = work.groupby(["Month", "Category"], as_index=False)["Amount"].sum()
    curr_cat = cat_month[cat_month["Month"] == current_month].rename(columns={"Amount": "CurrentAmount"})
    prev_cat = cat_month[cat_month["Month"] == prev_month].rename(columns={"Amount": "PrevAmount"})[["Category", "PrevAmount"]]
    cat_compare = curr_cat.merge(prev_cat, on="Category", how="left").fillna(0)
    cat_compare["Delta"] = cat_compare["CurrentAmount"] - cat_compare["PrevAmount"]
    top_drivers = cat_compare.sort_values("Delta", ascending=False).head(3)

    anomalies = current_df.sort_values("Amount", ascending=False).head(6).copy()
    anomalies["OneTime"] = ~anomalies["Description"].str.lower().str.contains("|".join(RECURRING_HINTS), regex=True)

    # Card optimization
    optimizer_rows = []
    missed_rewards = 0.0
    for _, row in current_by_cat.iterrows():
        cat = row["Category"]
        spend = float(row["Amount"])
        best_card, best_rate = None, 0.0
        for card in selected_cards:
            rate = CARD_BENEFITS.get(card, {}).get("categories", {}).get(cat, 0.0)
            if rate > best_rate:
                best_card, best_rate = card, rate
        if best_card and spend >= 1000:
            value = spend * best_rate / 100
            optimizer_rows.append({"category": cat, "spend": spend, "best_card": best_card, "best_rate": best_rate, "potential_value": value})
            missed_rewards += value
    optimizer_rows = sorted(optimizer_rows, key=lambda x: x["potential_value"], reverse=True)

    # Opportunities for chat
    telecom = current_df[current_df["Description"].str.contains("airtel", case=False, na=False)]["Amount"].sum()
    broadband = current_df[current_df["Description"].str.contains("fiber|broadband|wifi", case=False, na=False)]["Amount"].sum()
    ott = current_df[current_df["Description"].str.contains("netflix|spotify|youtube premium|prime", case=False, na=False)]["Amount"].sum()
    dth = current_df[current_df["Description"].str.contains("dth|tata play", case=False, na=False)]["Amount"].sum()

    opportunities = []
    if telecom + broadband + ott + dth > 0:
        opportunities.append({
            "title": "Bundle / consolidation opportunity",
            "what_i_see": f"You currently spend about ₹{telecom + broadband:,.0f} on telecom+broadband, ₹{ott:,.0f} on OTT, and ₹{dth:,.0f} on DTH this month.",
            "why_it_matters": "These are being paid separately. A bundled review could reduce cost and simplify billing.",
        })
    if ott >= 1000:
        opportunities.append({
            "title": "Streaming overlap",
            "what_i_see": f"You are paying for multiple streaming services worth roughly ₹{ott:,.0f} this month.",
            "why_it_matters": "There may be overlap across video and music subscriptions; worth reviewing what you actually use.",
        })
    online_amt = float(current_by_cat[current_by_cat["Category"] == "Online Shopping"]["Amount"].sum())
    if online_amt > 25000:
        opportunities.append({
            "title": "Shopping-heavy month",
            "what_i_see": f"Online shopping is ₹{online_amt:,.0f} this month and has climbed sharply versus last month.",
            "why_it_matters": "This is the clearest driver of the spike and the easiest area for deeper drill-down.",
        })

    context = {
        "current_month": current_month,
        "previous_month": prev_month,
        "monthly_spend": monthly.to_dict("records"),
        "current_month_spend": round(current_spend, 2),
        "mom_change": round(mom_change, 2),
        "mom_pct": round(mom_pct, 1),
        "current_category_breakdown": current_by_cat.to_dict("records"),
        "top_drivers": top_drivers.to_dict("records"),
        "anomalies": anomalies[["Description", "Amount", "Category", "OneTime"]].to_dict("records"),
        "recurring": recurring_summary[["latest_description", "avg_amount", "category"]].head(12).to_dict("records"),
        "opportunities": opportunities,
        "card_optimizer": optimizer_rows,
        "selected_cards": selected_cards,
    }

    return {
        "df": work,
        "monthly": monthly,
        "current_month": current_month,
        "prev_month": prev_month,
        "current_spend": current_spend,
        "mom_change": mom_change,
        "mom_pct": mom_pct,
        "recurring_monthly_value": recurring_monthly_value,
        "missed_rewards": missed_rewards,
        "current_by_cat": current_by_cat,
        "top_drivers": top_drivers,
        "anomalies": anomalies,
        "optimizer": optimizer_rows,
        "opportunities": opportunities,
        "context_json": json.dumps(context, default=str),
    }


def get_api_key() -> str:
    if st.session_state.get("api_key"):
        return st.session_state["api_key"]
    for source in [st.secrets, os.environ]:
        try:
            if "OPENAI_API_KEY" in source and source["OPENAI_API_KEY"]:
                return source["OPENAI_API_KEY"]
        except Exception:
            pass
    return ""


def make_line(monthly_df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_df["Month"], y=monthly_df["Amount"],
        marker=dict(color=['#23232b'] * (len(monthly_df)-1) + ['#8b5cf6']),
        hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(title='', tickfont=dict(color='#d6d8e4'), showgrid=False, zeroline=False),
        yaxis=dict(title='', tickfont=dict(color='#d6d8e4'), gridcolor='rgba(255,255,255,.10)', zeroline=False),
        showlegend=False,
    )
    return fig


def make_donut(cat_df: pd.DataFrame):
    fig = go.Figure(go.Pie(
        labels=cat_df["Category"], values=cat_df["Amount"], hole=0.62,
        marker=dict(colors=['#8b5cf6', '#22d3ee', '#ff5f6d', '#fbbf24', '#9c84ff', '#38bdf8', '#34d399', '#f472b6', '#cbd5e1']),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation='v', font=dict(color='#e8ebf7'), bgcolor='rgba(0,0,0,0)')
    )
    return fig


def ask_copilot(question: str, analytics: dict):
    key = get_api_key()
    if not key:
        return "Add an OpenAI API key to use the copilot.", False

    client = OpenAI(api_key=key)
    prefs = st.session_state.get("user_prefs", {})
    history = st.session_state.get("chat_history", [])[-6:]
    history_text = "\n".join([f"User: {h['q']}\nAssistant: {h['a']}" for h in history])
    prompt = f"""
You are CardIQ, an AI financial copilot for an expense tracking product.
Use only the structured data below. Be practical, specific, and helpful.

RULES:
- Answer in a structured way.
- Start with a 1-line conclusion.
- Then use bullet points.
- Use actual numbers from the data.
- If the user asks a preference-dependent question and preferences are missing, ask exactly one short clarifying question instead of guessing.
- Do not make the whole answer about month-on-month analysis unless the question is about that.
- The product is an expense tracker with AI insights, not a bundle-selling bot.
- Bundle suggestions should only be based on services the user is already paying for.
- Keep answers concise but useful.

CURRENT USER PREFERENCES:
{json.dumps(prefs)}

STRUCTURED DATA:
{analytics['context_json']}

RECENT CHAT:
{history_text}

QUESTION:
{question}
"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
        max_tokens=500,
    )
    answer = resp.choices[0].message.content.strip()

    # simple preference memory
    lower_q = question.lower()
    if any(k in lower_q for k in ["i care", "i want", "i prefer", "don't mind", "do not mind", "keep only", "protect essentials", "fewer cards"]):
        prefs[f"pref_{len(prefs)+1}"] = question
        st.session_state["user_prefs"] = prefs
    return answer, True


# ---------- STATE ----------
defaults = {
    "step": "home",
    "api_key": "",
    "selected_bank": None,
    "selected_cards": [],
    "analytics": None,
    "chat_history": [],
    "user_prefs": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------- HERO ----------
st.markdown(
    """
<div class="hero">
  <div class="eyebrow">AI Personal Finance Copilot</div>
  <div class="cta-line">
    <div>
      <div class="h1">Card<span class="brand-accent">IQ</span></div>
      <div class="sub">AI-powered expense tracking and financial copilot.<br>Understand your spending, optimize your cards, uncover smarter savings, and ask CardIQ what to do next.</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("OpenAI API key"):
    fallback = get_api_key()
    api_value = st.text_input("API key", value="" if fallback else st.session_state.get("api_key", ""), type="password", placeholder="sk-...", label_visibility="collapsed")
    if api_value:
        st.session_state["api_key"] = api_value
        st.caption("API key saved for this session.")
    elif fallback:
        st.caption("API key loaded securely from secrets or environment.")


# ---------- FLOW ----------
if st.session_state.step == "home":
    st.markdown('<div class="section-label">Get started</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.45, 1])
    with c1:
        st.markdown(
            """
<div class="panel">
  <div style="font-size:2rem; font-weight:800; margin-bottom:10px; color:var(--text)">Connect your bank account</div>
  <div class="helper">This prototype simulates an account-aggregator style flow and analyzes the last 6 months of spend history to power expense tracking, card optimization, recurring-spend detection, and AI chat-based insights.</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="panel">
  <div class="section-label" style="margin:0 0 10px 0">What this demo includes</div>
  <div class="helper">• Expense tracking across 6 months<br>• Month-on-month spend view<br>• Spend breakdown and recurring stack<br>• Card optimization and smarter savings insights<br>• AI copilot for follow-up questions</div>
</div>
""",
            unsafe_allow_html=True,
        )
    if st.button("Connect bank account", type="primary", use_container_width=True):
        st.session_state.step = "bank"
        st.rerun()

elif st.session_state.step == "bank":
    st.markdown('<div class="section-label">Step 1 · Select bank</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, bank in enumerate(BANKS):
        with cols[i % 3]:
            st.markdown(
                f"""
<div class="bank-card">
  <div class="badge" style="background:{bank['color']}22; color:{bank['color']}">{bank['abbr']}</div>
  <div style="font-size:1.65rem; font-weight:800">{bank['name']}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button(bank["name"], key=f"bank_{bank['name']}", use_container_width=True):
                st.session_state.selected_bank = bank["name"]
                st.session_state.step = "cards"
                st.rerun()
    if st.button("← Back"):
        st.session_state.step = "home"
        st.rerun()

elif st.session_state.step == "cards":
    st.markdown('<div class="section-label">Step 2 · Select your cards</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="helper">Pick the cards you want CardIQ to optimize against. Nothing is pre-selected.</div></div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    selected = []
    cards = list(CARD_BENEFITS.keys())
    for i, card in enumerate(cards):
        with (left if i % 2 == 0 else right):
            if st.checkbox(card, value=(card in st.session_state.selected_cards), key=f"card_{card}"):
                selected.append(card)
    st.session_state.selected_cards = selected
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "bank"
            st.rerun()
    with c2:
        if st.button("Approve & connect", type="primary", use_container_width=True):
            st.session_state.analytics = compute_analytics(generate_demo_transactions(), st.session_state.selected_cards)
            st.session_state.chat_history = []
            st.session_state.user_prefs = {}
            st.session_state.step = "dashboard"
            st.rerun()

elif st.session_state.step == "dashboard":
    analytics = st.session_state.analytics
    st.markdown(
        f"""
<div class="panel" style="margin-bottom:18px">
  <div class="cta-line">
    <div>
      <div class="section-label" style="margin:0 0 8px 0">Connected</div>
      <div style="font-size:2rem; font-weight:800">{st.session_state.selected_bank} · Last 6 months</div>
    </div>
    <div>{''.join([f'<span class="chip">{c}</span>' for c in st.session_state.selected_cards])}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric"><div class="metric-label">Current month spend</div><div class="metric-value">₹{analytics["current_spend"]:,.0f}</div><div class="metric-sub">{analytics["current_month"]}</div></div>', unsafe_allow_html=True)
    with m2:
        sign = "+" if analytics["mom_change"] >= 0 else "-"
        st.markdown(f'<div class="metric"><div class="metric-label">Month-on-month change</div><div class="metric-value">{sign}₹{abs(analytics["mom_change"]):,.0f}</div><div class="metric-sub">{abs(analytics["mom_pct"]):.1f}% vs {analytics["prev_month"]}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric"><div class="metric-label">Recurring monthly stack</div><div class="metric-value">₹{analytics["recurring_monthly_value"]:,.0f}</div><div class="metric-sub">Subscriptions + recurring bills</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric"><div class="metric-label">Rewards opportunity</div><div class="metric-value">₹{analytics["missed_rewards"]:,.0f}</div><div class="metric-sub">Potential current-month value</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.15, 0.95])
    with c1:
        st.markdown('<div class="panel"><div class="section-label" style="margin:0 0 .7rem 0">Month-on-month spend</div></div>', unsafe_allow_html=True)
        st.plotly_chart(make_line(analytics["monthly"]), use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.markdown('<div class="panel"><div class="section-label" style="margin:0 0 .7rem 0">Spend breakdown</div></div>', unsafe_allow_html=True)
        st.plotly_chart(make_donut(analytics["current_by_cat"]), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-label">Ask CardIQ copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    st.markdown('<div class="big-note">Try questions like: <strong>What changed this month?</strong> · <strong>Break down online shopping for me.</strong> · <strong>Do I have a bundle opportunity?</strong> · <strong>Which 2 cards should I keep?</strong></div>', unsafe_allow_html=True)
    question = st.text_input("Ask CardIQ", placeholder="Ask about spending patterns, recurring bills, subscriptions, cards, or savings...", label_visibility="collapsed")
    if st.button("Ask", type="primary") and question:
        answer, ok = ask_copilot(question, analytics)
        st.session_state.chat_history.append({"q": question, "a": answer})
        st.rerun()

    for item in reversed(st.session_state.chat_history[-6:]):
        st.markdown(f'<div class="chat-user">{item["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-ai">{item["a"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    r1, r2 = st.columns(2)
    with r1:
        if st.button("Reconnect flow", use_container_width=True):
            st.session_state.step = "home"
            st.session_state.selected_bank = None
            st.session_state.selected_cards = []
            st.session_state.analytics = None
            st.session_state.chat_history = []
            st.rerun()
    with r2:
        if st.button("Reset chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.user_prefs = {}
            st.rerun()
