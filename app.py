import os
import re
import json
from io import StringIO
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="CardIQ", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")

# ------------------------------------------------------------
# Config / constants
# ------------------------------------------------------------
BANKS = [
    {"name": "HDFC Bank", "abbr": "HDFC", "color": "#155EEF", "bg": "#EAF2FF"},
    {"name": "ICICI Bank", "abbr": "ICICI", "color": "#F97066", "bg": "#FFF1EF"},
    {"name": "SBI", "abbr": "SBI", "color": "#155EEF", "bg": "#EEF4FF"},
    {"name": "Axis Bank", "abbr": "AXIS", "color": "#C11574", "bg": "#FDF2FA"},
    {"name": "Kotak", "abbr": "KOTAK", "color": "#E04F16", "bg": "#FFF6ED"},
    {"name": "IDFC First", "abbr": "IDFC", "color": "#B42318", "bg": "#FEF3F2"},
]

CARD_BENEFITS = {
    "HDFC Millennia": {"Online Shopping": 5.0, "Food Delivery": 5.0, "Groceries": 1.0, "Travel": 1.0, "Entertainment": 1.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "SBI Cashback": {"Online Shopping": 5.0, "Food Delivery": 5.0, "Groceries": 1.0, "Travel": 1.0, "Entertainment": 1.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "Axis Ace": {"Utilities": 5.0, "Food Delivery": 4.0, "Groceries": 2.0, "Online Shopping": 2.0, "Travel": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Health": 1.0, "Other": 1.0},
    "ICICI Amazon Pay": {"Online Shopping": 5.0, "Food Delivery": 2.0, "Groceries": 2.0, "Travel": 2.0, "Entertainment": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "HDFC Regalia": {"Travel": 4.0, "Entertainment": 3.0, "Food Delivery": 2.5, "Online Shopping": 2.5, "Groceries": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 2.0},
    "Amex MRCC": {"Online Shopping": 2.0, "Food Delivery": 2.0, "Groceries": 2.0, "Travel": 2.0, "Entertainment": 2.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "HSBC Cashback": {"Food Delivery": 10.0, "Groceries": 10.0, "Online Shopping": 1.5, "Travel": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "BPCL SBI Card": {"Fuel": 4.5, "Travel": 1.0, "Food Delivery": 1.0, "Groceries": 1.0, "Online Shopping": 1.0, "Entertainment": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "HDFC Tata Neu": {"Groceries": 5.0, "Online Shopping": 4.0, "Utilities": 3.0, "Food Delivery": 2.0, "Travel": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Health": 2.0, "Other": 1.0},
    "IDFC First Select": {"Travel": 2.5, "Entertainment": 2.0, "Online Shopping": 2.0, "Food Delivery": 2.0, "Groceries": 2.0, "Fuel": 1.5, "Utilities": 1.5, "Health": 1.5, "Other": 1.5},
    "Axis Flipkart": {"Online Shopping": 5.0, "Food Delivery": 4.0, "Travel": 2.0, "Groceries": 1.5, "Entertainment": 1.5, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
    "AU Ixigo": {"Travel": 5.0, "Online Shopping": 2.0, "Entertainment": 2.0, "Food Delivery": 1.5, "Groceries": 1.0, "Fuel": 1.0, "Utilities": 1.0, "Health": 1.0, "Other": 1.0},
}

CATEGORY_ORDER = ["Online Shopping", "Travel", "Food Delivery", "Groceries", "Utilities", "Entertainment", "Fuel", "Health", "Other"]
MONTHS = pd.date_range("2025-10-01", periods=6, freq="MS")

# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown(
    """
<style>
:root {
  --bg: #F6F8FC;
  --surface: #FFFFFF;
  --surface-2: #EEF3FB;
  --text: #101828;
  --muted: #475467;
  --line: #D0D5DD;
  --primary: #155EEF;
  --primary-soft: #EAF2FF;
  --green: #079455;
  --amber: #DC6803;
  --red: #D92D20;
  --violet: #7A5AF8;
}
html, body, [class*="css"], .stApp {background: var(--bg) !important; color: var(--text) !important;}
#MainMenu, header, footer {visibility:hidden;}
.block-container {max-width: 1180px; padding-top: 1.2rem; padding-bottom: 2rem;}
section[data-testid="stSidebar"] {display:none;}
.hero {background: linear-gradient(135deg,#FFFFFF 0%,#EEF4FF 100%); border:1px solid var(--line); border-radius:28px; padding:28px 32px; margin-bottom:18px;}
.hero h1 {margin:0; font-size: 3rem; line-height:1; color:#0B1220;}
.hero p {margin:.6rem 0 0 0; color: var(--muted); font-size:1rem;}
.kicker {font-size:.75rem; text-transform:uppercase; letter-spacing:.18em; color:#667085; font-weight:700; margin-bottom:.75rem;}
.section-title {font-size:.8rem; text-transform:uppercase; letter-spacing:.16em; color:#667085; font-weight:700; margin:8px 0 12px 0;}
.card {background:var(--surface); border:1px solid var(--line); border-radius:22px; padding:18px 20px; box-shadow: 0 1px 2px rgba(16,24,40,.04);}
.metric-value {font-size:2rem; font-weight:700; color:#0B1220;}
.metric-label {font-size:.78rem; color:#667085; text-transform:uppercase; letter-spacing:.12em; font-weight:700;}
.metric-sub {font-size:.92rem; color:#475467; margin-top:.35rem;}
.bank-tile {background:var(--surface); border:1px solid var(--line); border-radius:18px; padding:16px; text-align:center;}
.bank-badge {width:52px; height:52px; margin:0 auto 10px auto; border-radius:14px; display:flex; align-items:center; justify-content:center; font-weight:800;}
.small-note {font-size:.88rem; color:#475467; line-height:1.65;}
.chat-user {background:#0B1220; color:#FFFFFF; padding:12px 14px; border-radius:16px; margin:10px 0 8px auto; max-width:78%; width:fit-content;}
.chat-ai {background:#FFFFFF; border:1px solid var(--line); color:#101828; padding:14px 16px; border-radius:16px; margin:8px 0 16px 0; max-width:86%; line-height:1.6; white-space:pre-wrap;}
.pill {display:inline-block; padding:6px 10px; border-radius:999px; background:#EEF4FF; color:#1849A9; font-size:.82rem; font-weight:600; margin:0 8px 8px 0;}
.op-card {background:#F8FAFC; border:1px dashed #B2CCFF; border-radius:16px; padding:14px; margin-bottom:12px;}
hr {border:none; border-top:1px solid var(--line); margin: 1rem 0 1.25rem 0;}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Helpers / data generation
# ------------------------------------------------------------
def resolve_api_key():
    if st.session_state.get("api_key"):
        return st.session_state.api_key
    try:
        secret = st.secrets.get("OPENAI_API_KEY", "")
        if secret:
            st.session_state.api_key = secret
            return secret
    except Exception:
        pass
    env = os.getenv("OPENAI_API_KEY", "")
    if env:
        st.session_state.api_key = env
        return env
    return ""


def add_row(rows, date, merchant, amount, source="Bank", tx_type="DEBIT"):
    rows.append({"Date": pd.Timestamp(date), "Description": merchant, "Amount": float(amount), "Type": tx_type, "Source": source})


def build_demo_data():
    rows = []
    for idx, month_start in enumerate(MONTHS):
        y, m = month_start.year, month_start.month
        d = lambda day: pd.Timestamp(year=y, month=m, day=day)

        # Income
        add_row(rows, d(1), "Salary Credit", 210000, "Bank", "CREDIT")

        # Recurring bills / bundle story
        add_row(rows, d(2), "Airtel Postpaid Family Plan", -1399 - idx*80)
        add_row(rows, d(3), "Airtel Xstream Fiber", -1499)
        add_row(rows, d(4), "Tata Play DTH", -699)
        add_row(rows, d(4), "Netflix Premium", -649)
        add_row(rows, d(5), "Amazon Prime", -299)
        add_row(rows, d(5), "Disney+ Hotstar", -299)
        add_row(rows, d(6), "Spotify Premium", -119)
        add_row(rows, d(6), "YouTube Premium", -189)
        add_row(rows, d(7), "Cult.fit Membership", -1499)

        # Utilities / essentials
        add_row(rows, d(8), "BESCOM Electricity Bill", -(3600 + idx*220))
        add_row(rows, d(9), "Society Maintenance", -3500)
        add_row(rows, d(10), "Piped Gas Bill", -(650 + idx*25))
        add_row(rows, d(11), "AquaGuard Service", -499 if idx in [2, 5] else 0)

        # Groceries
        add_row(rows, d(8), "DMart Grocery", -(4200 + idx*150))
        add_row(rows, d(16), "Blinkit Grocery", -(1800 + idx*90))
        add_row(rows, d(24), "Zepto Grocery", -(1500 + idx*70))

        # Food delivery
        add_row(rows, d(9), "Swiggy Order", -(720 + idx*20), "Card")
        add_row(rows, d(13), "Zomato Order", -(840 + idx*25), "Card")
        add_row(rows, d(22), "Swiggy Order", -(690 + idx*18), "Card")
        add_row(rows, d(27), "Zomato Order", -(770 + idx*20), "Bank")

        # Fuel / transport
        add_row(rows, d(12), "HPCL Fuel", -(4200 + idx*120), "Card")
        add_row(rows, d(26), "BPCL Fuel", -(2800 + idx*80), "Card")
        add_row(rows, d(14), "Uber Ride", -(580 + idx*15), "Card")
        add_row(rows, d(21), "Ola Ride", -(420 + idx*10), "Card")

        # Entertainment
        add_row(rows, d(18), "PVR Cinemas", -(1200 + idx*50))
        add_row(rows, d(19), "BookMyShow", -(950 + idx*40))

        # Health
        add_row(rows, d(15), "Apollo Pharmacy", -(1500 + idx*60))
        add_row(rows, d(23), "Practo Consultation", -699 if idx in [1, 4] else 0)

        # Shopping trend: rising over time
        shopping_multiplier = [1.0, 1.05, 1.1, 1.25, 1.45, 1.7][idx]
        add_row(rows, d(7), "Amazon Shopping", -(6500 * shopping_multiplier), "Card")
        add_row(rows, d(17), "Myntra Fashion", -(4200 * shopping_multiplier), "Card")
        add_row(rows, d(25), "Flipkart Shopping", -(3500 * shopping_multiplier), "Card")
        add_row(rows, d(20), "Nykaa Beauty", -(2200 * shopping_multiplier), "Card")

        # Travel and one-time spikes
        if idx == 3:
            add_row(rows, d(11), "MakeMyTrip Flight Booking", -28500, "Card")
            add_row(rows, d(12), "Taj Hotel Booking", -16400, "Card")
        if idx == 5:
            add_row(rows, d(14), "Croma Electronics", -68999, "Card")
            add_row(rows, d(20), "Apple Store Purchase", -14999, "Card")
            add_row(rows, d(28), "Annual Car Insurance", -18200, "Bank")

        # Ambiguous UPI / cash-like leakage
        add_row(rows, d(12), f"UPI/9876543210@ybl/{idx}", -(1800 + idx*120))
        add_row(rows, d(19), f"UPI/merchant{idx}@okaxis", -(2200 + idx*140))

    df = pd.DataFrame(rows)
    df = df[df["Amount"] != 0].copy()
    return df.sort_values("Date").reset_index(drop=True)


def categorize(description: str) -> str:
    d = str(description).lower()
    if any(k in d for k in ["swiggy", "zomato"]):
        return "Food Delivery"
    if any(k in d for k in ["dmart", "blinkit", "zepto", "grocery"]):
        return "Groceries"
    if any(k in d for k in ["amazon shopping", "myntra", "flipkart", "nykaa", "croma", "apple store"]):
        return "Online Shopping"
    if any(k in d for k in ["flight", "hotel", "makemytrip", "uber", "ola"]):
        return "Travel"
    if any(k in d for k in ["netflix", "prime", "hotstar", "spotify", "youtube premium", "pvr", "bookmyshow", "tata play"]):
        return "Entertainment"
    if any(k in d for k in ["fuel", "hpcl", "bpcl"]):
        return "Fuel"
    if any(k in d for k in ["airtel", "electricity", "maintenance", "gas bill", "insurance", "aquaguard"]):
        return "Utilities"
    if any(k in d for k in ["apollo", "practo", "cult.fit"]):
        return "Health"
    return "Other"


def classify_service(description: str) -> str:
    d = str(description).lower()
    if "airtel postpaid" in d:
        return "Mobile"
    if "fiber" in d or "broadband" in d:
        return "Broadband"
    if any(k in d for k in ["netflix", "prime", "hotstar", "spotify", "youtube premium"]):
        return "OTT / Streaming"
    if "tata play" in d or "dth" in d:
        return "TV / DTH"
    return ""


def detect_subscriptions(df):
    work = df.copy()
    work["merchant_key"] = work["Description"].str.lower().str.replace(r"/\d+$", "", regex=True)
    grp = work.groupby("merchant_key").agg(name=("Description", "first"), months=("Month", "nunique"), avg_amount=("Amount", "mean"), category=("Category", "first")).reset_index()
    grp = grp[(grp["months"] >= 4) & (grp["avg_amount"] >= 100)]
    grp = grp.sort_values("avg_amount", ascending=False)
    return grp[["name", "avg_amount", "category"]].rename(columns={"avg_amount": "amount"})


def detect_anomalies(df):
    work = df.copy()
    merchant_avg = work.groupby("Description")["Amount"].mean().to_dict()
    counts = work.groupby("Description")["Month"].nunique().to_dict()
    current_month = work["Month"].max()
    current = work[work["Month"] == current_month].copy()
    current["merchant_avg"] = current["Description"].map(merchant_avg)
    current["merchant_months"] = current["Description"].map(counts)
    current["is_one_time"] = current["merchant_months"] == 1
    current["delta_vs_norm"] = current["Amount"] - current["merchant_avg"]
    anomalies = current[(current["Amount"] >= 10000) | (current["is_one_time"]) | (current["delta_vs_norm"] >= 8000)]
    anomalies = anomalies.sort_values("Amount", ascending=False)
    return anomalies[["Description", "Amount", "Category", "is_one_time"]].head(6)


def monthly_category_table(df):
    return df.pivot_table(index="MonthLabel", columns="Category", values="Amount", aggfunc="sum", fill_value=0).reset_index()


def optimize_cards(df, owned_cards):
    current_month = df["Month"] == df["Month"].max()
    cur = df[current_month]
    out = []
    for cat, amt in cur.groupby("Category")["Amount"].sum().items():
        if amt < 500:
            continue
        best_card, best_rate = None, 0
        for card in owned_cards:
            rate = CARD_BENEFITS.get(card, {}).get(cat, 1.0)
            if rate > best_rate:
                best_card, best_rate = card, rate
        savings = round(amt * (best_rate / 100), 0) if best_card else 0
        out.append({"category": cat, "spend": float(amt), "best_card": best_card or "—", "best_rate": best_rate, "potential_savings": float(savings)})
    return sorted(out, key=lambda x: x["potential_savings"], reverse=True)


def detect_opportunities(df, current_month_df):
    ops = []
    recurring = detect_subscriptions(df)
    current = current_month_df

    telecom = current[current["Description"].str.contains("Airtel", case=False, na=False)]["Amount"].sum()
    ott = current[current["Description"].str.contains("Netflix|Prime|Hotstar|Spotify|YouTube", case=False, na=False)]["Amount"].sum()
    dth = current[current["Description"].str.contains("Tata Play|DTH", case=False, na=False)]["Amount"].sum()
    if telecom > 0 and ott > 0:
        ops.append({
            "title": "Bundle / consolidation opportunity",
            "evidence": f"You currently spend about ₹{telecom:,.0f} on telecom+broadband, ₹{ott:,.0f} on OTT, and ₹{dth:,.0f} on DTH this month.",
            "impact": "These are being paid separately. A bundled review could reduce cost and simplify billing."
        })

    streaming = current[current["Description"].str.contains("Netflix|Prime|Hotstar|YouTube|Spotify", case=False, na=False)]["Amount"].sum()
    if len(current[current["Description"].str.contains("Netflix|Prime|Hotstar|YouTube|Spotify", case=False, na=False)]) >= 4:
        ops.append({
            "title": "Streaming overlap",
            "evidence": f"You are paying for multiple streaming services worth roughly ₹{streaming:,.0f} this month.",
            "impact": "There may be overlap between video and music subscriptions; worth reviewing what you actually use."
        })

    shopping = current.groupby("Category")["Amount"].sum().get("Online Shopping", 0)
    if shopping >= 25000:
        ops.append({
            "title": "Shopping-heavy month",
            "evidence": f"Online shopping is ₹{shopping:,.0f} this month and has climbed noticeably over recent months.",
            "impact": "This is the clearest driver of this month's spike and the best area for deeper drill-down."
        })

    return ops[:4]


def build_analysis(df, owned_cards):
    debits = df[df["Type"] == "DEBIT"].copy()
    debits["Amount"] = debits["Amount"].abs()
    debits["Category"] = debits["Description"].apply(categorize)
    debits["ServiceType"] = debits["Description"].apply(classify_service)
    debits["Month"] = debits["Date"].dt.to_period("M").astype(str)
    debits["MonthLabel"] = debits["Date"].dt.strftime("%b %Y")

    monthly = debits.groupby("MonthLabel", as_index=False)["Amount"].sum()
    monthly["MonthOrder"] = pd.to_datetime(monthly["MonthLabel"], format="%b %Y")
    monthly = monthly.sort_values("MonthOrder")
    current_label = monthly.iloc[-1]["MonthLabel"]
    prev_label = monthly.iloc[-2]["MonthLabel"]
    current_total = float(monthly.iloc[-1]["Amount"])
    prev_total = float(monthly.iloc[-2]["Amount"])
    mom_change = current_total - prev_total
    mom_pct = (mom_change / prev_total * 100) if prev_total else 0

    current = debits[debits["MonthLabel"] == current_label].copy()
    prev = debits[debits["MonthLabel"] == prev_label].copy()

    curr_cat = current.groupby("Category")["Amount"].sum().to_dict()
    prev_cat = prev.groupby("Category")["Amount"].sum().to_dict()
    cat_deltas = []
    for cat in CATEGORY_ORDER:
        delta = curr_cat.get(cat, 0) - prev_cat.get(cat, 0)
        if abs(delta) > 0:
            cat_deltas.append((cat, delta, curr_cat.get(cat, 0)))
    cat_deltas = sorted(cat_deltas, key=lambda x: x[1], reverse=True)

    top_drivers = cat_deltas[:3]
    anomalies = detect_anomalies(debits)
    subscriptions = detect_subscriptions(debits)
    card_optimizer = optimize_cards(debits, owned_cards)
    opportunities = detect_opportunities(debits, current)
    recurring_total = float(subscriptions["amount"].sum()) if not subscriptions.empty else 0.0
    insights = [
        f"{current_label} spend is ₹{current_total:,.0f}, up by ₹{mom_change:,.0f} ({mom_pct:.1f}%) versus {prev_label}.",
        f"The biggest increase is {top_drivers[0][0]} at ₹{top_drivers[0][2]:,.0f}, which rose by ₹{top_drivers[0][1]:,.0f} month on month." if top_drivers else "Month-on-month movement is limited.",
        f"Recurring subscriptions and bills average about ₹{recurring_total:,.0f} per month across your tracked services." if recurring_total else "No strong recurring stack detected.",
    ]
    if not anomalies.empty:
        biggest = anomalies.iloc[0]
        insights.append(f"The most unusual current-month spend is {biggest['Description']} at ₹{biggest['Amount']:,.0f}.")

    top_category = max(curr_cat.items(), key=lambda x: x[1])[0] if curr_cat else "—"
    total_savings = sum(x["potential_savings"] for x in card_optimizer)
    monthly_cats = monthly_category_table(debits)

    current_top_merchants = current.groupby(["Description", "Category"], as_index=False)["Amount"].sum().sort_values("Amount", ascending=False).head(10)

    return {
        "df": debits,
        "monthly": monthly,
        "current_month_label": current_label,
        "previous_month_label": prev_label,
        "current_total": current_total,
        "mom_change": mom_change,
        "mom_pct": mom_pct,
        "categories_current": curr_cat,
        "top_category": top_category,
        "top_drivers": top_drivers,
        "subscriptions": subscriptions,
        "anomalies": anomalies,
        "card_optimizer": card_optimizer,
        "total_potential_savings": total_savings,
        "opportunities": opportunities,
        "insights": insights,
        "monthly_categories": monthly_cats,
        "current_top_merchants": current_top_merchants,
        "recurring_total": recurring_total,
    }


def make_line(monthly):
    fig = px.line(monthly, x="MonthLabel", y="Amount", markers=True)
    fig.update_traces(line_color="#155EEF", line_width=3, marker_size=8)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320,
                      xaxis_title=None, yaxis_title=None, font=dict(color="#344054"))
    return fig


def make_bar_current(categories_dict):
    data = pd.DataFrame({"Category": list(categories_dict.keys()), "Amount": list(categories_dict.values())})
    data = data.sort_values("Amount", ascending=True)
    fig = px.bar(data, x="Amount", y="Category", orientation="h")
    fig.update_traces(marker_color="#7A5AF8")
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320,
                      xaxis_title=None, yaxis_title=None, font=dict(color="#344054"))
    return fig


def format_currency(n):
    return f"₹{n:,.0f}"


def build_chat_context(analysis, owned_cards, user_profile):
    cur = analysis["current_month_label"]
    monthly = analysis["monthly"][["MonthLabel", "Amount"]].to_dict(orient="records")
    current_categories = sorted(analysis["categories_current"].items(), key=lambda x: x[1], reverse=True)
    subs = analysis["subscriptions"].head(10).to_dict(orient="records") if not analysis["subscriptions"].empty else []
    anomalies = analysis["anomalies"].head(6).to_dict(orient="records") if not analysis["anomalies"].empty else []
    opportunities = analysis["opportunities"]
    merchants = analysis["current_top_merchants"].to_dict(orient="records")
    optimizer = analysis["card_optimizer"]
    context = {
        "current_month": cur,
        "monthly_totals": monthly,
        "current_month_total": analysis["current_total"],
        "month_on_month_change": analysis["mom_change"],
        "month_on_month_pct": analysis["mom_pct"],
        "current_month_categories": current_categories,
        "top_drivers": analysis["top_drivers"],
        "subscriptions": subs,
        "anomalies": anomalies,
        "opportunities": opportunities,
        "top_merchants_current_month": merchants,
        "card_optimizer": optimizer,
        "owned_cards": owned_cards,
        "user_profile": user_profile,
    }
    return json.dumps(context, default=str, ensure_ascii=False)


def maybe_update_profile(question, answer, profile):
    q = question.lower() + " " + answer.lower()
    pairs = {
        "prioritizes_savings": ["save", "reduce spend", "cut cost"],
        "prioritizes_convenience": ["convenience", "simple", "fewer bills"],
        "cares_about_entertainment": ["movies", "streaming", "ott", "music"],
        "wants_fewer_cards": ["fewer cards", "keep 2 cards", "simplify cards"],
        "won't_cut_fitness": ["fitness", "cult.fit", "gym"],
    }
    for key, needles in pairs.items():
        if any(n in q for n in needles):
            profile[key] = True
    return profile


def ask_copilot(question, context_json, api_key):
    client = OpenAI(api_key=api_key)
    prompt = f"""
You are CardIQ Copilot, an AI personal finance assistant for India.
Use ONLY the supplied data. Do not invent merchants, plans, or exact pricing not present in the data.

Response style rules:
- Always be structured.
- Start with a 1-line direct answer.
- Then use bullets.
- When relevant, use these mini-headings: "What I see", "What changed", "What to do next", "Impact".
- Quote actual INR amounts from the data.
- If the user asks a drill-down question, go deeper into the relevant category or merchant list.
- If the question depends on user preference and the data alone is not enough, ask exactly ONE short clarifying question.
- Do not be generic.
- Keep the answer compact but useful.

DATA:
{context_json}

QUESTION:
{question}
"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()


# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
defaults = {
    "flow_step": "home",
    "selected_bank": None,
    "owned_cards": ["HDFC Millennia", "Axis Ace", "HDFC Regalia"],
    "analysis": None,
    "chat_history": [],
    "api_key": "",
    "user_profile": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
resolve_api_key()

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(
    """
<div class="hero">
  <div class="kicker">AI personal finance copilot</div>
  <h1>CardIQ</h1>
  <p>Track what changed this month, catch non-obvious leaks, and ask the copilot what to do next.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("OpenAI API key"):
    api_input = st.text_input("", type="password", placeholder="sk-...", value=st.session_state.api_key, label_visibility="collapsed")
    if api_input:
        st.session_state.api_key = api_input

# ------------------------------------------------------------
# Flow
# ------------------------------------------------------------
if st.session_state.flow_step == "home":
    st.markdown('<div class="section-title">Get started</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown(
            """
<div class="card">
  <div style="font-size:1.75rem;font-weight:700;color:#0B1220;margin-bottom:.4rem;">Connect your bank account</div>
  <div class="small-note">This prototype simulates a secure account-aggregator style flow and analyzes the last 6 months of transaction history to detect recurring spends, month-on-month shifts, large one-time spikes, card reward leaks, and bundling opportunities.</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="card">
  <div class="section-title">What this demo showcases</div>
  <div class="small-note">• 6-month spend patterns<br>• What went wrong this month<br>• Big one-time spends you might miss<br>• Subscription / bundle opportunities<br>• Card optimization and simplification</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.write("")
    if st.button("Connect bank account", use_container_width=True, type="primary"):
        st.session_state.flow_step = "bank_select"
        st.rerun()

elif st.session_state.flow_step == "bank_select":
    st.markdown('<div class="section-title">Step 1 · Select bank</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, bank in enumerate(BANKS):
        with cols[i % 3]:
            st.markdown(
                f"""
<div class="bank-tile">
  <div class="bank-badge" style="background:{bank['bg']}; color:{bank['color']};">{bank['abbr']}</div>
  <div style="font-weight:700; color:#101828;">{bank['name']}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button(bank["name"], key=f"bank_{bank['name']}", use_container_width=True):
                st.session_state.selected_bank = bank["name"]
                st.session_state.flow_step = "card_select"
                st.rerun()
    if st.button("← Back"):
        st.session_state.flow_step = "home"
        st.rerun()

elif st.session_state.flow_step == "card_select":
    st.markdown('<div class="section-title">Step 2 · Select your cards</div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="small-note">Pick the cards you want CardIQ to optimize against. The demo works best with 3–5 cards selected.</div></div>', unsafe_allow_html=True)
    selected = []
    cols = st.columns(2)
    keys = list(CARD_BENEFITS.keys())
    for i, card in enumerate(keys):
        with cols[i % 2]:
            if st.checkbox(card, value=(card in st.session_state.owned_cards), key=f"card_{card}"):
                selected.append(card)
    st.session_state.owned_cards = selected or ["HDFC Millennia", "Axis Ace", "HDFC Regalia"]
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.flow_step = "bank_select"
            st.rerun()
    with c2:
        if st.button("Approve & connect", use_container_width=True, type="primary"):
            st.session_state.flow_step = "results"
            st.session_state.analysis = build_analysis(build_demo_data(), st.session_state.owned_cards)
            st.session_state.chat_history = []
            st.rerun()

elif st.session_state.flow_step == "results":
    analysis = st.session_state.analysis or build_analysis(build_demo_data(), st.session_state.owned_cards)
    st.session_state.analysis = analysis

    top_cards = " ".join([f'<span class="pill">{c}</span>' for c in st.session_state.owned_cards])
    st.markdown(
        f"""
<div class="card" style="margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;">
    <div>
      <div class="section-title" style="margin-bottom:6px;">Connected</div>
      <div style="font-size:1.15rem;font-weight:700;">{st.session_state.selected_bank or 'Demo bank'} · Last 6 months</div>
    </div>
    <div>{top_cards}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="card"><div class="metric-label">Current month spend</div><div class="metric-value">{format_currency(analysis["current_total"])}</div><div class="metric-sub">{analysis["current_month_label"]}</div></div>', unsafe_allow_html=True)
    with m2:
        delta_sign = "+" if analysis["mom_change"] >= 0 else ""
        st.markdown(f'<div class="card"><div class="metric-label">Month-on-month change</div><div class="metric-value">{delta_sign}{format_currency(analysis["mom_change"])}</div><div class="metric-sub">{analysis["mom_pct"]:.1f}% vs {analysis["previous_month_label"]}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="card"><div class="metric-label">Recurring monthly stack</div><div class="metric-value">{format_currency(analysis["recurring_total"])}</div><div class="metric-sub">Subscriptions + recurring bills</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="card"><div class="metric-label">Rewards left unclaimed</div><div class="metric-value">{format_currency(analysis["total_potential_savings"])}</div><div class="metric-sub">Current month card mismatch estimate</div></div>', unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1.25, 1])
    with c1:
        st.markdown('<div class="card"><div class="section-title">Month-on-month spend</div>', unsafe_allow_html=True)
        st.plotly_chart(make_line(analysis["monthly"]), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="section-title">Current month by category</div>', unsafe_allow_html=True)
        st.plotly_chart(make_bar_current(analysis["categories_current"]), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["What changed", "Recurring stack", "Card optimizer", "Opportunities"])

    with t1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<div class='section-title'>What went wrong in {analysis['current_month_label']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-note'><strong>{analysis['insights'][0]}</strong></div>", unsafe_allow_html=True)
        st.write("")
        for cat, delta, current_amt in analysis["top_drivers"][:4]:
            direction = "up" if delta >= 0 else "down"
            st.markdown(f"<div class='small-note'>• <strong>{cat}</strong>: {format_currency(current_amt)} this month, {direction} by {format_currency(abs(delta))} vs last month.</div>", unsafe_allow_html=True)
        if not analysis["anomalies"].empty:
            st.write("")
            st.markdown("<div class='section-title'>Big / unusual spends</div>", unsafe_allow_html=True)
            for _, row in analysis["anomalies"].iterrows():
                one_time = " · one-time" if row["is_one_time"] else ""
                st.markdown(f"<div class='small-note'>• <strong>{row['Description']}</strong> — {format_currency(row['Amount'])} ({row['Category']}){one_time}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Recurring bills and subscriptions</div>", unsafe_allow_html=True)
        if not analysis["subscriptions"].empty:
            for _, row in analysis["subscriptions"].iterrows():
                st.markdown(f"<span class='pill'>{row['name']} · {format_currency(row['amount'])}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='small-note'>No recurring stack detected.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Where the best card changes the outcome</div>", unsafe_allow_html=True)
        for item in analysis["card_optimizer"][:6]:
            st.markdown(f"<div class='small-note'>• <strong>{item['category']}</strong>: {format_currency(item['spend'])} · Best card: <strong>{item['best_card']}</strong> ({item['best_rate']}%) · Potential value: <strong>{format_currency(item['potential_savings'])}</strong></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with t4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Detected recommendation opportunities</div>", unsafe_allow_html=True)
        for op in analysis["opportunities"]:
            st.markdown(f"<div class='op-card'><div style='font-weight:700;margin-bottom:6px;'>{op['title']}</div><div class='small-note'><strong>What I see:</strong> {op['evidence']}<br><strong>Why it matters:</strong> {op['impact']}</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="section-title">Ask CardIQ Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<div class='small-note'>Ask questions like: <strong>What went wrong this month?</strong> · <strong>Break down online shopping for me.</strong> · <strong>Do I have a bundle opportunity?</strong> · <strong>Which 2 cards should I keep?</strong></div>", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai">{msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        q = st.text_input("", placeholder="Ask about month-on-month changes, one-time spends, categories, bundles, or cards…", label_visibility="collapsed")
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted and q.strip():
        api_key = resolve_api_key()
        if not api_key:
            st.error("Please add your OpenAI API key first.")
        else:
            try:
                context_json = build_chat_context(analysis, st.session_state.owned_cards, st.session_state.user_profile)
                answer = ask_copilot(q.strip(), context_json, api_key)
                st.session_state.user_profile = maybe_update_profile(q.strip(), answer, st.session_state.user_profile)
                st.session_state.chat_history.append({"role": "user", "content": q.strip()})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Chat failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Reconnect flow", use_container_width=True):
            st.session_state.flow_step = "home"
            st.rerun()
    with c2:
        if st.button("Reset chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.user_profile = {}
            st.rerun()
