import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import json
import re

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CardIQ – AI Credit Card Optimizer",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

.stApp { background-color: #0a0a0f; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
    margin-bottom: 0.3rem;
}

.hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.1rem;
    color: #9ca3af;
    font-weight: 300;
    margin-bottom: 2rem;
}

.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2d2d4e;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6b7280;
    margin-bottom: 0.3rem;
}

.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff;
}

.metric-value.green { color: #34d399; }
.metric-value.purple { color: #a78bfa; }
.metric-value.blue { color: #60a5fa; }

.insight-card {
    background: #111122;
    border: 1px solid #2d2d4e;
    border-left: 3px solid #a78bfa;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.8rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #d1d5db;
}

.optimizer-card {
    background: linear-gradient(135deg, #0f2027 0%, #1a1a3e 100%);
    border: 1px solid #34d399;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

.optimizer-savings {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #34d399;
}

.chat-msg-user {
    background: #1e1e3a;
    border-radius: 12px 12px 4px 12px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: #e8e8f0;
    text-align: right;
}

.chat-msg-ai {
    background: #111122;
    border: 1px solid #2d2d4e;
    border-radius: 12px 12px 12px 4px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: #d1d5db;
}

.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #ffffff;
    margin: 1.5rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #2d2d4e;
}

.tag {
    display: inline-block;
    background: #1e1e3a;
    border: 1px solid #a78bfa;
    color: #a78bfa;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    margin: 0.2rem;
}

.upload-hint {
    font-size: 0.8rem;
    color: #6b7280;
    margin-top: 0.3rem;
}

div[data-testid="stFileUploader"] {
    background: #111122;
    border: 1px dashed #2d2d4e;
    border-radius: 12px;
    padding: 0.5rem;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7c3aed, #3b82f6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 2rem;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
    transition: opacity 0.2s;
}

div[data-testid="stButton"] > button:hover { opacity: 0.85; }

.stCheckbox > label { color: #d1d5db !important; }

div[data-testid="stTextInput"] input {
    background: #111122 !important;
    border: 1px solid #2d2d4e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Credit card benefits data ─────────────────────────────────────────────────
CARD_BENEFITS = {
    "HDFC Millennia": {
        "categories": {
            "Food Delivery": 5.0,
            "Online Shopping": 5.0,
            "Groceries": 1.0,
            "Travel": 1.0,
            "Entertainment": 1.0,
            "Fuel": 1.0,
            "Utilities": 1.0,
            "Other": 1.0,
        },
        "note": "5% cashback on Amazon, Flipkart, Swiggy, Zomato; 1% elsewhere"
    },
    "Axis Flipkart": {
        "categories": {
            "Online Shopping": 5.0,
            "Food Delivery": 4.0,
            "Travel": 4.0,
            "Groceries": 1.5,
            "Entertainment": 1.5,
            "Fuel": 1.5,
            "Utilities": 1.5,
            "Other": 1.5,
        },
        "note": "5% on Flipkart; 4% on preferred merchants; 1.5% elsewhere"
    },
    "SBI SimplyCLICK": {
        "categories": {
            "Online Shopping": 2.5,
            "Food Delivery": 2.5,
            "Entertainment": 2.5,
            "Travel": 2.5,
            "Groceries": 1.25,
            "Fuel": 1.25,
            "Utilities": 1.25,
            "Other": 1.25,
        },
        "note": "10x points (2.5% value) on partner sites; 5x elsewhere online"
    },
    "ICICI Amazon Pay": {
        "categories": {
            "Online Shopping": 5.0,
            "Food Delivery": 2.0,
            "Groceries": 2.0,
            "Travel": 2.0,
            "Entertainment": 2.0,
            "Fuel": 1.0,
            "Utilities": 1.0,
            "Other": 1.0,
        },
        "note": "5% on Amazon (Prime members); 2% on partner merchants; 1% elsewhere"
    },
    "HDFC Regalia": {
        "categories": {
            "Travel": 4.0,
            "Entertainment": 3.0,
            "Food Delivery": 3.0,
            "Online Shopping": 3.0,
            "Groceries": 2.0,
            "Fuel": 1.0,
            "Utilities": 1.0,
            "Other": 2.0,
        },
        "note": "Premium travel & lifestyle card; 4x on travel, 3x on dining & entertainment"
    },
    "Amex MRCC": {
        "categories": {
            "Online Shopping": 2.0,
            "Food Delivery": 2.0,
            "Groceries": 2.0,
            "Entertainment": 2.0,
            "Travel": 2.0,
            "Fuel": 1.0,
            "Utilities": 1.0,
            "Other": 1.0,
        },
        "note": "5x Membership Rewards points on first ₹1500/month; 1x thereafter"
    },
}

# ── Helper: parse CSV ─────────────────────────────────────────────────────────
def parse_csv(file):
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        # Normalise column names
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if "date" in cl: col_map[c] = "Date"
            elif "desc" in cl or "narr" in cl or "particular" in cl or "detail" in cl: col_map[c] = "Description"
            elif "amount" in cl or "debit" in cl or "credit" in cl or "amt" in cl: col_map[c] = "Amount"
            elif "type" in cl: col_map[c] = "Type"
        df.rename(columns=col_map, inplace=True)
        if "Amount" in df.columns:
            df["Amount"] = pd.to_numeric(df["Amount"].astype(str).str.replace(",", "").str.replace("₹", ""), errors="coerce")
        return df
    except Exception as e:
        st.error(f"Could not parse file: {e}")
        return None

def get_debits(df):
    if df is None: return pd.DataFrame()
    if "Type" in df.columns:
        mask = df["Type"].astype(str).str.upper().str.contains("DEBIT|DR")
        debits = df[mask].copy()
    else:
        debits = df[df["Amount"] < 0].copy()
    debits["Amount"] = debits["Amount"].abs()
    return debits[debits["Amount"] > 0]

# ── AI analysis ───────────────────────────────────────────────────────────────
CATEGORIES = ["Food Delivery", "Groceries", "Online Shopping", "Travel", "Entertainment", "Fuel", "Utilities", "Health", "Other"]

def analyze_with_ai(client, transactions_text, owned_cards):
    card_benefits_text = ""
    for card in owned_cards:
        b = CARD_BENEFITS[card]
        card_benefits_text += f"\n- {card}: {b['note']}"

    prompt = f"""You are a sharp financial analyst. Analyze these transactions and return ONLY a valid JSON object — no markdown, no explanation, no extra text.

TRANSACTIONS:
{transactions_text}

USER'S CREDIT CARDS:{card_benefits_text}

Return exactly this JSON structure:
{{
  "total_spend": <number>,
  "top_category": "<string>",
  "categories": {{
    "Food Delivery": <number>,
    "Groceries": <number>,
    "Online Shopping": <number>,
    "Travel": <number>,
    "Entertainment": <number>,
    "Fuel": <number>,
    "Utilities": <number>,
    "Health": <number>,
    "Other": <number>
  }},
  "subscriptions": [
    {{"name": "<string>", "amount": <number>, "frequency": "monthly"}}
  ],
  "insights": [
    "<insight string 1>",
    "<insight string 2>",
    "<insight string 3>"
  ],
  "card_optimizer": [
    {{
      "category": "<category name>",
      "spend": <number>,
      "card_used": "Unknown",
      "best_card": "<card name from user's cards>",
      "best_rate": <cashback_percentage>,
      "potential_savings": <number>
    }}
  ],
  "total_potential_savings": <number>,
  "top_recommendation": "<one key actionable recommendation>"
}}

Rules:
- Categorize every transaction into one of the 9 categories listed
- For card_optimizer: for each category where spend > 500, identify which card from the user's owned cards gives the best cashback rate, compute potential_savings as (spend * best_rate / 100)
- total_potential_savings is the sum of all potential_savings
- insights should be specific, data-driven, and slightly candid (not generic)
- All amounts in INR
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)

def chat_with_data(client, question, context):
    prompt = f"""You are CardIQ, a witty and sharp AI financial advisor. You have access to a user's full transaction data and analysis. Answer their question in 2-4 sentences, being specific and using actual numbers from the data. Don't be generic.

FINANCIAL CONTEXT:
{context}

USER QUESTION: {question}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

# ── Plotly chart helpers ──────────────────────────────────────────────────────
CHART_COLORS = ["#a78bfa", "#60a5fa", "#34d399", "#f472b6", "#fb923c", "#facc15", "#38bdf8", "#4ade80", "#c084fc"]

def make_donut(categories):
    filtered = {k: v for k, v in categories.items() if v > 0}
    fig = go.Figure(go.Pie(
        labels=list(filtered.keys()),
        values=list(filtered.values()),
        hole=0.65,
        marker=dict(colors=CHART_COLORS, line=dict(color="#0a0a0f", width=2)),
        textfont=dict(family="DM Sans", size=12, color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(font=dict(color="#9ca3af", family="DM Sans"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
    )
    return fig

def make_optimizer_bar(optimizer_data):
    if not optimizer_data: return None
    categories = [d["category"] for d in optimizer_data]
    savings = [d["potential_savings"] for d in optimizer_data]
    best_cards = [d["best_card"] for d in optimizer_data]
    fig = go.Figure(go.Bar(
        x=savings,
        y=categories,
        orientation="h",
        marker=dict(color=CHART_COLORS[:len(categories)], line=dict(color="#0a0a0f", width=1)),
        text=[f"₹{s:,.0f} via {c}" for s, c in zip(savings, best_cards)],
        textposition="outside",
        textfont=dict(color="#9ca3af", size=11),
        hovertemplate="<b>%{y}</b><br>Potential saving: ₹%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#4b5563", tickfont=dict(color="#6b7280")),
        yaxis=dict(showgrid=False, color="#4b5563", tickfont=dict(color="#d1d5db")),
        margin=dict(t=10, b=10, l=10, r=120),
        height=max(200, len(categories) * 50),
    )
    return fig

# ── Session state ─────────────────────────────────────────────────────────────
if "analysis" not in st.session_state: st.session_state.analysis = None
if "context" not in st.session_state: st.session_state.context = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "api_key" not in st.session_state: st.session_state.api_key = ""

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">CardIQ 💳</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Know your spend. Maximize your rewards. Talk to your money.</div>', unsafe_allow_html=True)

# ── API KEY INPUT ─────────────────────────────────────────────────────────────
with st.expander("🔑 Enter your OpenAI API Key", expanded=(not st.session_state.api_key)):
    api_input = st.text_input("API Key", type="password", placeholder="sk-...", value=st.session_state.api_key, label_visibility="collapsed")
    if api_input:
        st.session_state.api_key = api_input
        st.success("✓ API key saved for this session")

st.markdown("---")

# ── INPUT PANEL ───────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-header">📂 Upload Statements</div>', unsafe_allow_html=True)
    bank_file = st.file_uploader("Bank Statement (CSV)", type=["csv"], key="bank")
    st.markdown('<div class="upload-hint">Columns needed: Date, Description, Amount</div>', unsafe_allow_html=True)

    cc_file = st.file_uploader("Credit Card Statement (CSV) — optional", type=["csv"], key="cc")
    st.markdown('<div class="upload-hint">Same format: Date, Description, Amount</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-header">💳 Your Credit Cards</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-hint" style="margin-bottom:0.8rem">Select cards you own — we\'ll show you how to optimize rewards</div>', unsafe_allow_html=True)
    owned_cards = []
    for card in CARD_BENEFITS.keys():
        if st.checkbox(card, key=f"card_{card}"):
            owned_cards.append(card)

st.markdown("")
analyze_btn = st.button("⚡ Analyze My Finances", use_container_width=True)

# ── ANALYSIS ──────────────────────────────────────────────────────────────────
if analyze_btn:
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API key above.")
    elif not bank_file:
        st.error("Please upload at least your bank statement.")
    else:
        with st.spinner("Crunching your numbers with AI..."):
            bank_df = parse_csv(bank_file)
            bank_debits = get_debits(bank_df)

            all_debits = bank_debits.copy()
            if cc_file:
                cc_df = parse_csv(cc_file)
                cc_debits = get_debits(cc_df)
                if not cc_debits.empty:
                    all_debits = pd.concat([all_debits, cc_debits], ignore_index=True)

            if all_debits.empty:
                st.error("No debit transactions found. Check your CSV format.")
            else:
                transactions_text = all_debits[["Date", "Description", "Amount"]].to_string(index=False, max_rows=100)

                if not owned_cards:
                    owned_cards = list(CARD_BENEFITS.keys())[:3]

                try:
                    client = OpenAI(api_key=st.session_state.api_key)
                    result = analyze_with_ai(client, transactions_text, owned_cards)
                    st.session_state.analysis = result
                    st.session_state.context = f"Total spend: ₹{result.get('total_spend',0):,.0f}. Categories: {result.get('categories',{})}. Insights: {result.get('insights',[])}. Card optimizer: {result.get('card_optimizer',[])}. Total potential savings: ₹{result.get('total_potential_savings',0):,.0f}."
                    st.session_state.chat_history = []
                except Exception as e:
                    st.error(f"AI analysis failed: {e}")

# ── RESULTS ───────────────────────────────────────────────────────────────────
if st.session_state.analysis:
    r = st.session_state.analysis

    st.markdown("---")

    # ── Top metrics ──
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Spend</div><div class="metric-value">₹{r.get('total_spend',0):,.0f}</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Top Category</div><div class="metric-value purple">{r.get('top_category','–')}</div></div>""", unsafe_allow_html=True)
    with m3:
        subs = r.get('subscriptions', [])
        sub_total = sum(s.get('amount', 0) for s in subs)
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Subscriptions</div><div class="metric-value blue">₹{sub_total:,.0f}/mo</div></div>""", unsafe_allow_html=True)
    with m4:
        savings = r.get('total_potential_savings', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Missed Rewards</div><div class="metric-value green">₹{savings:,.0f}</div></div>""", unsafe_allow_html=True)

    # ── Spend breakdown + Insights ──
    tab1, tab2, tab3 = st.tabs(["📊  Spend Breakdown", "🔍  Insights", "💳  Card Optimizer"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="section-header">Spending by Category</div>', unsafe_allow_html=True)
            cats = {k: v for k, v in r.get('categories', {}).items() if v > 0}
            if cats:
                st.plotly_chart(make_donut(cats), use_container_width=True)
        with c2:
            st.markdown('<div class="section-header">Breakdown</div>', unsafe_allow_html=True)
            total = max(r.get('total_spend', 1), 1)
            for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
                pct = int(amt / total * 100)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #1f1f3a;">
                    <span style="color:#d1d5db">{cat}</span>
                    <span style="color:#a78bfa;font-family:'Syne',sans-serif;font-weight:600">₹{amt:,.0f} <span style="color:#4b5563;font-size:0.8rem">({pct}%)</span></span>
                </div>""", unsafe_allow_html=True)

        # Subscriptions
        if subs:
            st.markdown('<div class="section-header" style="margin-top:1.5rem">🔁 Recurring Subscriptions Detected</div>', unsafe_allow_html=True)
            sub_cols = st.columns(min(len(subs), 4))
            for i, sub in enumerate(subs):
                with sub_cols[i % 4]:
                    st.markdown(f"""<div class="metric-card" style="padding:1rem"><div class="metric-label">{sub.get('name','?')}</div><div class="metric-value" style="font-size:1.3rem">₹{sub.get('amount',0):,.0f}<span style="font-size:0.75rem;color:#6b7280">/mo</span></div></div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header">AI Insights on Your Spending</div>', unsafe_allow_html=True)
        for insight in r.get('insights', []):
            st.markdown(f'<div class="insight-card">💡 {insight}</div>', unsafe_allow_html=True)

        rec = r.get('top_recommendation', '')
        if rec:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a0533,#0f1d3a);border:1px solid #7c3aed;border-radius:16px;padding:1.4rem 1.6rem;margin-top:1rem">
                <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#7c3aed;margin-bottom:0.5rem">Top Recommendation</div>
                <div style="font-size:1rem;color:#e8e8f0;line-height:1.6">🎯 {rec}</div>
            </div>""", unsafe_allow_html=True)

    with tab3:
        opt = r.get('card_optimizer', [])
        total_savings = r.get('total_potential_savings', 0)

        st.markdown(f"""
        <div class="optimizer-card">
            <div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;color:#34d399;margin-bottom:0.3rem">Total Rewards You Left on the Table</div>
            <div class="optimizer-savings">₹{total_savings:,.0f}</div>
            <div style="color:#6b7280;font-size:0.85rem;margin-top:0.3rem">This month alone. Imagine a year.</div>
        </div>""", unsafe_allow_html=True)

        if opt:
            st.markdown('<div class="section-header">Savings Potential by Category</div>', unsafe_allow_html=True)
            chart = make_optimizer_bar(opt)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

            st.markdown('<div class="section-header">Card-by-Card Recommendations</div>', unsafe_allow_html=True)
            for item in sorted(opt, key=lambda x: -x.get('potential_savings', 0)):
                if item.get('potential_savings', 0) > 0:
                    st.markdown(f"""
                    <div class="insight-card" style="border-left-color:#34d399">
                        <strong style="color:#ffffff">{item['category']}</strong> — You spent <strong style="color:#a78bfa">₹{item['spend']:,.0f}</strong>.
                        Use <strong style="color:#34d399">{item['best_card']}</strong> ({item['best_rate']}% back) →
                        saves you <strong style="color:#34d399">₹{item['potential_savings']:,.0f}</strong> 💸
                    </div>""", unsafe_allow_html=True)

    # ── Chat ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">💬 Ask CardIQ Anything</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-hint" style="margin-bottom:1rem">Ask questions like: "Why am I overspending?" · "Which card should I cancel?" · "How can I save ₹5000 next month?"</div>', unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    user_q = st.text_input("Your question", placeholder="e.g. Am I spending too much on food?", label_visibility="collapsed")
    if user_q:
        with st.spinner("Thinking..."):
            try:
                client = OpenAI(api_key=st.session_state.api_key)
                answer = chat_with_data(client, user_q, st.session_state.context)
                st.session_state.chat_history.append({"role": "user", "content": user_q})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Chat failed: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#374151;font-size:0.8rem;margin-top:3rem;padding-top:1rem;border-top:1px solid #1f1f3a">
    CardIQ · Built with Streamlit + GPT-4o · Your data never leaves your session
</div>""", unsafe_allow_html=True)
