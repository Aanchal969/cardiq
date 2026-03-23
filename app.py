import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
import json, re, time
from io import StringIO

st.set_page_config(page_title="CardIQ", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

# ══════════════════════════════════════════════════════════════
# SAMPLE DATA  (UPI transactions added — ambiguous IDs)
# ══════════════════════════════════════════════════════════════
SAMPLE_BANK_CSV = """Date,Description,Amount,Type
2024-03-01,Swiggy Order #SW8821,-450,DEBIT
2024-03-02,Amazon Purchase,-2399,DEBIT
2024-03-02,Salary Credit,85000,CREDIT
2024-03-03,Zomato Order #ZM4421,-380,DEBIT
2024-03-04,UPI/9876543210@ybl,-220,DEBIT
2024-03-04,Netflix Subscription,-649,DEBIT
2024-03-05,Big Bazaar Groceries,-3200,DEBIT
2024-03-06,UPI/PAYTM/QRCODE/7654321,-180,DEBIT
2024-03-07,HDFC Credit Card Bill Payment,-12000,DEBIT
2024-03-08,Zomato Order #ZM5530,-670,DEBIT
2024-03-09,UPI/8765432109@okaxis,-3500,DEBIT
2024-03-09,Spotify Premium,-119,DEBIT
2024-03-10,Flipkart Purchase,-1899,DEBIT
2024-03-11,Apollo Pharmacy,-890,DEBIT
2024-03-11,UPI/GPAY/MERCHANT/4567890,-850,DEBIT
2024-03-12,DMart Groceries,-2750,DEBIT
2024-03-13,Amazon Prime Subscription,-1499,DEBIT
2024-03-13,UPI/7654321098@paytm,-310,DEBIT
2024-03-14,Zomato Order #ZM6621,-590,DEBIT
2024-03-15,Reliance Digital,-4500,DEBIT
2024-03-15,Freelance Payment Received,15000,CREDIT
2024-03-16,UPI/6543210987@ybl,-480,DEBIT
2024-03-17,BookMyShow Movies,-840,DEBIT
2024-03-18,UPI/PHONEPE/TXN/5432109,-260,DEBIT
2024-03-18,Myntra Purchase,-2199,DEBIT
2024-03-19,Swiggy Order #SW0012,-550,DEBIT
2024-03-20,Big Bazaar Groceries,-2900,DEBIT
2024-03-21,UPI/4321098765@oksbi,-1200,DEBIT
2024-03-21,YouTube Premium,-189,DEBIT
2024-03-22,Petrol Pump HPCL,-3500,DEBIT
2024-03-22,UPI/PAYTM/QRCODE/3210987,-430,DEBIT
2024-03-23,Amazon Purchase,-3299,DEBIT
2024-03-24,UPI/2109876543@okicici,-750,DEBIT
2024-03-24,Cult.fit Membership,-999,DEBIT
2024-03-25,Zomato Order #ZM8843,-610,DEBIT
2024-03-26,UPI/GPAY/MERCHANT/1098765,-920,DEBIT
2024-03-27,MakeMyTrip Hotel Booking,-8500,DEBIT
2024-03-28,UPI/9087654321@ybl,-290,DEBIT
2024-03-28,Blinkit Groceries,-1850,DEBIT
2024-03-29,Swiggy Order #SW0678,-470,DEBIT
2024-03-30,Electricity Bill BESCOM,-2200,DEBIT
2024-03-31,Jio Recharge,-299,DEBIT"""

SAMPLE_CC_CSV = """Date,Description,Amount,Type
2024-03-01,Swiggy Order,-380,DEBIT
2024-03-02,Amazon Purchase,-5499,DEBIT
2024-03-04,Zomato Order,-520,DEBIT
2024-03-05,UPI/PHONEPE/TXN/8877665,-340,DEBIT
2024-03-06,Myntra Purchase,-3499,DEBIT
2024-03-08,Swiggy Order,-410,DEBIT
2024-03-09,BookMyShow,-1200,DEBIT
2024-03-10,Amazon Purchase,-2199,DEBIT
2024-03-11,UPI/7766554433@paytm,-480,DEBIT
2024-03-12,Uber Ride,-220,DEBIT
2024-03-13,Nykaa Purchase,-1899,DEBIT
2024-03-14,Swiggy Order,-560,DEBIT
2024-03-15,Petrol Pump BPCL,-4000,DEBIT
2024-03-16,Amazon Purchase,-3799,DEBIT
2024-03-17,UPI/GPAY/MERCHANT/6655443,-390,DEBIT
2024-03-18,Uber Ride,-280,DEBIT
2024-03-19,Swiggy Order,-490,DEBIT
2024-03-20,Flipkart Purchase,-2699,DEBIT
2024-03-21,MakeMyTrip Flight,-12500,DEBIT
2024-03-22,Amazon Purchase,-1599,DEBIT
2024-03-23,UPI/5544332211@okaxis,-440,DEBIT
2024-03-24,Uber Ride,-190,DEBIT
2024-03-25,Swiggy Order,-520,DEBIT
2024-03-26,BigBasket Groceries,-3100,DEBIT
2024-03-27,Amazon Purchase,-4299,DEBIT
2024-03-28,UPI/4433221100@ybl,-610,DEBIT
2024-03-29,Uber Ride,-250,DEBIT
2024-03-30,Swiggy Order,-470,DEBIT
2024-03-31,Ajio Purchase,-2899,DEBIT"""

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════
BANKS = [
    {"name":"HDFC Bank",  "abbr":"HDFC",  "color":"#004C8F","bg":"#001E3C","emoji":"🏦"},
    {"name":"ICICI Bank", "abbr":"ICICI", "color":"#F96B21","bg":"#2D1400","emoji":"🏦"},
    {"name":"SBI",        "abbr":"SBI",   "color":"#2251A3","bg":"#0D1B3E","emoji":"🏦"},
    {"name":"Axis Bank",  "abbr":"AXIS",  "color":"#97144D","bg":"#2D0518","emoji":"🏦"},
    {"name":"Kotak Bank", "abbr":"KOTAK", "color":"#EF4123","bg":"#2D0A00","emoji":"🏦"},
    {"name":"IndusInd",   "abbr":"INDUS", "color":"#00529B","bg":"#001E3C","emoji":"🏦"},
    {"name":"Yes Bank",   "abbr":"YES",   "color":"#00447C","bg":"#001829","emoji":"🏦"},
    {"name":"IDFC First", "abbr":"IDFC",  "color":"#9B1B30","bg":"#2D0810","emoji":"🏦"},
]

CATEGORIES = ["Food Delivery","Groceries","Online Shopping","Travel",
              "Entertainment","Fuel","Utilities","Health","Other"]

CARD_BENEFITS = {
    "HDFC Millennia":  {"categories":{"Food Delivery":5.0,"Online Shopping":5.0,"Groceries":1.0,"Travel":1.0,"Entertainment":1.0,"Fuel":1.0,"Utilities":1.0,"Other":1.0},"note":"5% on Amazon, Flipkart, Swiggy, Zomato · 1% elsewhere"},
    "Axis Flipkart":   {"categories":{"Online Shopping":5.0,"Food Delivery":4.0,"Travel":4.0,"Groceries":1.5,"Entertainment":1.5,"Fuel":1.5,"Utilities":1.5,"Other":1.5},"note":"5% on Flipkart · 4% preferred · 1.5% elsewhere"},
    "SBI SimplyCLICK": {"categories":{"Online Shopping":2.5,"Food Delivery":2.5,"Entertainment":2.5,"Travel":2.5,"Groceries":1.25,"Fuel":1.25,"Utilities":1.25,"Other":1.25},"note":"10x points on partner sites · 5x elsewhere"},
    "ICICI Amazon Pay":{"categories":{"Online Shopping":5.0,"Food Delivery":2.0,"Groceries":2.0,"Travel":2.0,"Entertainment":2.0,"Fuel":1.0,"Utilities":1.0,"Other":1.0},"note":"5% on Amazon (Prime) · 2% partners · 1% elsewhere"},
    "HDFC Regalia":    {"categories":{"Travel":4.0,"Entertainment":3.0,"Food Delivery":3.0,"Online Shopping":3.0,"Groceries":2.0,"Fuel":1.0,"Utilities":1.0,"Other":2.0},"note":"4x travel · 3x dining & entertainment"},
    "Amex MRCC":       {"categories":{"Online Shopping":2.0,"Food Delivery":2.0,"Groceries":2.0,"Entertainment":2.0,"Travel":2.0,"Fuel":1.0,"Utilities":1.0,"Other":1.0},"note":"5x Membership Rewards on first ₹1500/month"},
}

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

/* ── Variables ── */
:root {
  --bg:       #080C14;
  --bg2:      #0D1220;
  --bg3:      #121929;
  --border:   #1E2A3F;
  --border2:  #253450;
  --text:     #E2E8F4;
  --muted:    #4A5A7A;
  --muted2:   #2A3855;
  --accent:   #6C8EF5;
  --green:    #34D399;
  --amber:    #FBBF24;
  --coral:    #F87171;
  --violet:   #A78BFA;
}

*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"],.stApp{background-color:var(--bg)!important;color:var(--text)!important;font-family:'Outfit',sans-serif!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none}

/* ── Typography ── */
.iq-eyebrow{font-size:.6rem;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:var(--muted)}
.iq-hero{font-family:'Playfair Display',serif;font-size:clamp(2.8rem,6vw,4.5rem);font-weight:400;line-height:1;color:var(--text);letter-spacing:-.01em}
.iq-hero em{font-style:italic;color:var(--accent)}
.iq-sub{font-size:.875rem;font-weight:300;color:var(--muted);line-height:1.8}
.iq-label{font-size:.58rem;font-weight:600;letter-spacing:.28em;text-transform:uppercase;color:var(--muted2);margin-bottom:1.25rem;padding-bottom:.6rem;border-bottom:1px solid var(--border)}

/* ── Layout ── */
.iq-hero-wrap{padding:2.5rem 5rem 2rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:flex-end;gap:2rem;position:relative;overflow:hidden}
.iq-hero-wrap::before{content:'';position:absolute;top:-60px;right:5rem;width:360px;height:360px;background:radial-gradient(circle,rgba(108,142,245,.08) 0%,transparent 70%);pointer-events:none}
.iq-body{padding:2rem 5rem}
.iq-divider{height:1px;background:var(--border)}

/* ── Cards ── */
.iq-card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.5rem 1.75rem;position:relative;overflow:hidden}
.iq-card::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--violet))}
.iq-card-label{font-size:.58rem;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin-bottom:.6rem}
.iq-metric{font-family:'Playfair Display',serif;font-size:2.2rem;font-weight:400;color:var(--text);line-height:1}
.iq-metric.green{color:var(--green)}
.iq-metric.amber{color:var(--amber)}
.iq-metric.violet{color:var(--violet)}

/* ── Bank tiles ── */
.bank-tile{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.5rem 1rem;text-align:center;cursor:pointer;transition:all .2s;display:flex;flex-direction:column;align-items:center;gap:.6rem;margin-bottom:.5rem}
.bank-tile:hover{border-color:var(--border2);background:var(--bg3)}
.bank-tile.selected{border-color:var(--accent);background:var(--bg3);box-shadow:0 0 0 1px var(--accent) inset}
.bank-logo{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.75rem;letter-spacing:.05em}
.bank-name-text{font-size:.68rem;font-weight:400;color:var(--muted);letter-spacing:.05em}
.bank-selected-badge{font-size:.55rem;letter-spacing:.15em;color:var(--accent);font-weight:600;text-transform:uppercase}

/* ── Consent ── */
.iq-consent{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:2.5rem;max-width:520px;margin:0 auto;position:relative;overflow:hidden}
.iq-consent::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--green))}
.consent-row{display:flex;gap:1rem;padding:.9rem 0;border-bottom:1px solid var(--border)}
.consent-icon{font-size:.9rem;flex-shrink:0;margin-top:.1rem}
.consent-txt{font-size:.82rem;color:var(--muted);line-height:1.6;font-weight:300}
.consent-txt strong{color:var(--text);font-weight:500}

/* ── Loading ── */
.loading-wrap{text-align:center;padding:4rem 2rem}
.loading-title{font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:400;color:var(--text);margin-bottom:.4rem}
.loading-sub{font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-top:1.2rem}
@keyframes pulse{0%,100%{opacity:.2}50%{opacity:1}}
.pulse-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin:0 3px;animation:pulse 1.4s ease-in-out infinite}
.pd1{background:var(--accent)}
.pd2{background:var(--violet);animation-delay:.2s}
.pd3{background:var(--green);animation-delay:.4s}
.progress-track{width:220px;height:2px;background:var(--border);border-radius:2px;margin:1.5rem auto 0}
.progress-fill{height:2px;border-radius:2px;background:linear-gradient(90deg,var(--accent),var(--violet));transition:width .5s}

/* ── UPI review ── */
.upi-note{background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:0 8px 8px 0;padding:1rem 1.5rem;margin-bottom:1.5rem;font-size:.83rem;color:var(--muted);line-height:1.6}
.upi-note strong{color:var(--accent);font-weight:500}
.prog-bar{height:3px;background:var(--border);border-radius:2px;margin:.5rem 0 .5rem}
.prog-fill{height:3px;border-radius:2px;background:linear-gradient(90deg,var(--accent),var(--green));transition:width .4s}

/* ── Results ── */
.iq-insight{padding:1.1rem 0 1.1rem 1.4rem;border-bottom:1px solid var(--border);font-size:.875rem;font-weight:300;color:var(--muted);line-height:1.7;position:relative}
.iq-insight::before{content:'';position:absolute;left:0;top:.4rem;bottom:.4rem;width:2px;background:linear-gradient(180deg,var(--accent),var(--violet));border-radius:2px}
.iq-insight strong{color:var(--text);font-weight:500}
.iq-row{display:flex;justify-content:space-between;align-items:center;padding:1rem 0;border-bottom:1px solid var(--border)}
.iq-row-cat{font-size:.82rem;font-weight:400;color:var(--muted);min-width:130px}
.iq-row-card{font-size:.8rem;font-weight:500;color:var(--accent);flex:1;text-align:center;padding:0 1rem}
.iq-row-val{font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:400;color:var(--text);text-align:right;min-width:90px}
.iq-sub-tag{display:inline-flex;align-items:center;gap:.5rem;background:var(--bg2);border:1px solid var(--border);border-radius:20px;padding:.35rem .9rem;margin:.25rem;font-size:.72rem;color:var(--muted)}
.iq-sub-tag span{color:var(--green);font-weight:500}
.iq-chat-user{text-align:right;padding:.6rem 0;font-family:'Playfair Display',serif;font-size:1rem;font-style:italic;color:var(--muted)}
.iq-chat-ai{padding:.9rem 0 .9rem 1.4rem;border-left:2px solid var(--border2);font-size:.875rem;color:var(--muted);line-height:1.75;font-weight:300;margin-bottom:.4rem}
.account-badge{font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);background:rgba(108,142,245,.1);border:1px solid rgba(108,142,245,.25);border-radius:4px;padding:.25rem .65rem}

/* ── Inputs ── */
div[data-testid="stTextInput"] input{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text)!important;font-family:'Outfit',sans-serif!important;font-size:.9rem!important;font-weight:300!important;padding:.65rem 1rem!important;box-shadow:none!important}
div[data-testid="stTextInput"] input:focus{border-color:var(--accent)!important;outline:none!important;box-shadow:0 0 0 3px rgba(108,142,245,.12)!important}
.stCheckbox{margin:.15rem 0!important}
.stCheckbox>label>div{color:var(--muted)!important;font-size:.82rem!important;font-family:'Outfit',sans-serif!important;font-weight:400!important}
div[data-testid="stSelectbox"]>div>div{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text)!important;font-family:'Outfit',sans-serif!important;font-size:.8rem!important}
div[data-testid="stSelectbox"] svg{color:var(--accent)!important}

/* ── Buttons ── */
div[data-testid="stButton"]>button{background:linear-gradient(135deg,var(--accent),var(--violet))!important;border:none!important;color:#fff!important;border-radius:8px!important;padding:.75rem 2.5rem!important;font-family:'Outfit',sans-serif!important;font-size:.72rem!important;font-weight:600!important;letter-spacing:.15em!important;text-transform:uppercase!important;width:auto!important;transition:all .25s!important;box-shadow:0 4px 15px rgba(108,142,245,.25)!important}
div[data-testid="stButton"]>button:hover{opacity:.85!important;box-shadow:0 4px 20px rgba(108,142,245,.4)!important}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid var(--border)!important;gap:.5rem!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;font-size:.7rem!important;letter-spacing:.18em!important;text-transform:uppercase!important;font-family:'Outfit',sans-serif!important;font-weight:500!important;padding:.75rem 1.5rem!important;border:none!important;border-radius:0!important}
.stTabs [aria-selected="true"]{color:var(--accent)!important;border-bottom:2px solid var(--accent)!important}
.stTabs [data-baseweb="tab-panel"]{background:transparent!important;padding:1.5rem 0!important}

/* ── Expander ── */
details{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:10px!important;padding:0 5rem!important;margin:.5rem 0!important}
details summary{font-size:.65rem!important;letter-spacing:.2em!important;text-transform:uppercase!important;color:var(--muted)!important;font-family:'Outfit',sans-serif!important;padding:.8rem 0!important;cursor:pointer!important}
details>div{background:var(--bg2)!important;padding:.25rem 0 .75rem!important}

.stSpinner>div{border-top-color:var(--accent)!important}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
div[data-testid="stForm"]{background:transparent!important;border:none!important;padding:0!important}
div[data-testid="stFileUploader"]{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:10px!important}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def parse_csv_string(csv_string):
    df = pd.read_csv(StringIO(csv_string))
    df.columns = [c.strip() for c in df.columns]
    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"].astype(str).str.replace(",","").str.replace("₹",""), errors="coerce")
    return df

def get_debits(df):
    if df is None or df.empty: return pd.DataFrame()
    if "Type" in df.columns:
        debits = df[df["Type"].astype(str).str.upper().str.contains("DEBIT|DR")].copy()
    else:
        debits = df[df["Amount"] < 0].copy()
    debits["Amount"] = debits["Amount"].abs()
    return debits[debits["Amount"] > 0]

def is_upi(description):
    """Detect UPI transactions that lack a merchant name."""
    desc = str(description).upper()
    if "UPI" not in desc:
        return False
    # If it contains a recognisable merchant name, don't flag it
    known = ["SWIGGY","ZOMATO","AMAZON","FLIPKART","NETFLIX","SPOTIFY","BOOKMYSHOW",
             "MYNTRA","DMART","BIGBAZAAR","BLINKIT","MAKEMYTRIP","IRCTC","UBER","OLA",
             "PETROL","HPCL","BPCL","BESCOM","JIO","CULT","APOLLO","NYKAA","AJIO","YOUTUBE"]
    return not any(k in desc for k in known)

def extract_upi_display(description):
    """Return a short human-readable version of a UPI ID."""
    desc = str(description)
    # Try to isolate the VPA (virtual payment address)
    parts = [p for p in re.split(r"[/\-_]", desc) if "@" in p]
    if parts:
        return parts[0]
    # Fallback: last meaningful segment
    segments = [s for s in desc.split("/") if s and s.upper() not in ["UPI","IMPS","NEFT"]]
    return segments[-1] if segments else desc

def analyze_with_ai(client, tx_text, owned_cards):
    card_text = "\n".join([f"- {c}: {CARD_BENEFITS[c]['note']}" for c in owned_cards])
    prompt = f"""You are a sharp financial analyst. Analyze these transactions and return ONLY valid JSON — no markdown.

TRANSACTIONS:
{tx_text}

USER'S CREDIT CARDS:
{card_text}

Return exactly this structure:
{{
  "total_spend": <number>,
  "top_category": "<string>",
  "categories": {{"Food Delivery":<n>,"Groceries":<n>,"Online Shopping":<n>,"Travel":<n>,"Entertainment":<n>,"Fuel":<n>,"Utilities":<n>,"Health":<n>,"Other":<n>}},
  "subscriptions": [{{"name":"<string>","amount":<n>}}],
  "insights": ["<string>","<string>","<string>"],
  "card_optimizer": [{{"category":"<string>","spend":<n>,"best_card":"<string>","best_rate":<n>,"potential_savings":<n>}}],
  "total_potential_savings": <number>,
  "top_recommendation": "<string>"
}}
Rules: categorize every transaction, optimizer only for spend > 500, insights must cite actual numbers, all amounts in INR. Note: UPI transactions in the data already have a Category column — treat those as ground truth and don't re-categorize them."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3, max_tokens=2000,
    )
    raw = re.sub(r"```json\s*|\s*```", "", response.choices[0].message.content.strip()).strip()
    return json.loads(raw)

def chat_with_data(client, question, context):
    prompt = f"""You are CardIQ — precise, direct, never generic. 2-3 sentences, actual numbers only. No filler.
DATA: {context}
QUESTION: {question}"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0.4, max_tokens=250,
    )
    return response.choices[0].message.content.strip()

def make_donut(categories):
    filtered = {k:v for k,v in categories.items() if v > 0}
    # Vibrant, distinct palette
    palette = ["#6C8EF5","#34D399","#F87171","#FBBF24","#A78BFA","#38BDF8","#FB923C","#4ADE80","#F472B6"]
    fig = go.Figure(go.Pie(
        labels=list(filtered.keys()), values=list(filtered.values()), hole=0.68,
        marker=dict(colors=palette[:len(filtered)], line=dict(color="#080C14",width=3)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} · %{percent}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=True,
        legend=dict(font=dict(color="#4A5A7A",family="Outfit",size=11),bgcolor="rgba(0,0,0,0)",
                    itemclick=False, orientation="v"),
        margin=dict(t=10,b=10,l=10,r=10), height=300,
    )
    return fig

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
defaults = {
    "flow_step": "home",
    "selected_bank": None,
    "owned_cards": [],
    "all_debits": None,         # full DataFrame after loading
    "upi_rows": None,           # DataFrame of ambiguous UPI rows
    "upi_categories": {},       # {index: category} user assignments
    "analysis": None,
    "context": "",
    "chat_history": [],
    "api_key": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="iq-hero-wrap">
    <div>
        <div class="iq-eyebrow" style="margin-bottom:1rem">AI · Finance · India</div>
        <div class="iq-hero">Card<em>IQ</em></div>
    </div>
    <div style="padding-bottom:.4rem">
        <div class="iq-sub">Know where your money goes.<br>Know what you're leaving behind.</div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("✦  CONNECT  —  Enter OpenAI API Key"):
    api_input = st.text_input("", type="password", placeholder="sk-...", value=st.session_state.api_key, label_visibility="collapsed")
    if api_input: st.session_state.api_key = api_input
st.markdown('<div class="iq-divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: HOME
# ══════════════════════════════════════════════════════════════
if st.session_state.flow_step == "home":
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Get Started</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:2rem">
        <div style="font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:300;color:#E2E8F4;margin-bottom:.5rem">Connect your bank account.</div>
        <div class="iq-sub">We use India's Account Aggregator framework to securely fetch your transactions.<br>Read-only access. No credentials stored. Disconnect anytime.</div>
    </div>
    """, unsafe_allow_html=True)
    _, c_btn, _ = st.columns([1,1.5,1])
    with c_btn:
        if st.button("CONNECT BANK ACCOUNT"):
            st.session_state.flow_step = "bank_select"
            st.rerun()
    st.markdown("""
    <div style="margin-top:2rem;display:flex;gap:3rem">
        <div style="display:flex;align-items:center;gap:.75rem"><span style="color:#6C8EF5;font-size:.75rem">✦</span><span class="iq-sub" style="font-size:.72rem">256-bit encryption</span></div>
        <div style="display:flex;align-items:center;gap:.75rem"><span style="color:#6C8EF5;font-size:.75rem">✦</span><span class="iq-sub" style="font-size:.72rem">Read-only access</span></div>
        <div style="display:flex;align-items:center;gap:.75rem"><span style="color:#6C8EF5;font-size:.75rem">✦</span><span class="iq-sub" style="font-size:.72rem">RBI Account Aggregator framework</span></div>
        <div style="display:flex;align-items:center;gap:.75rem"><span style="color:#6C8EF5;font-size:.75rem">✦</span><span class="iq-sub" style="font-size:.72rem">Data never stored</span></div>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: BANK SELECT
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "bank_select":
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Step 1 of 3 &nbsp;·&nbsp; Select Bank</div>', unsafe_allow_html=True)
    st.markdown("""<div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:300;color:#E2E8F4;margin-bottom:.5rem">Which bank are you with?</div>
    <div class="iq-sub" style="margin-bottom:2rem">Select your primary bank to fetch account and card statements.</div>""", unsafe_allow_html=True)

    cols = st.columns(4)
    for i, bank in enumerate(BANKS):
        with cols[i % 4]:
            is_sel = st.session_state.selected_bank == bank["name"]
            sel_badge = f'<div class="bank-selected-badge">✓ Selected</div>' if is_sel else ""
            sel_class = "selected" if is_sel else ""
            st.markdown(f"""
            <div class="bank-tile {sel_class}">
                <div class="bank-logo" style="background:{bank['bg']};color:{bank['color']};border:1px solid {bank['color']}33">
                    {bank['abbr']}
                </div>
                <div class="bank-name-text">{bank['name']}</div>
                {sel_badge}
            </div>""", unsafe_allow_html=True)
            if st.button(bank["name"], key=f"bank_{bank['name']}", use_container_width=True):
                st.session_state.selected_bank = bank["name"]
                st.rerun()

    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)
    c1, c2, _ = st.columns([1,1,3])
    with c1:
        if st.button("← BACK"):
            st.session_state.flow_step = "home"; st.rerun()
    with c2:
        if st.session_state.selected_bank:
            if st.button("CONTINUE →"):
                st.session_state.flow_step = "card_select"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: CARD SELECT
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "card_select":
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Step 2 of 3 &nbsp;·&nbsp; Your Credit Cards</div>', unsafe_allow_html=True)
    st.markdown(f"""<div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:300;color:#E2E8F4;margin-bottom:.5rem">Which cards do you use?</div>
    <div class="iq-sub" style="margin-bottom:2rem">Connected to <span style="color:#6C8EF5">{st.session_state.selected_bank}</span>. Select your credit cards for reward optimization.</div>""", unsafe_allow_html=True)

    owned = []
    c1, c2 = st.columns(2)
    for i, card in enumerate(CARD_BENEFITS.keys()):
        with (c1 if i % 2 == 0 else c2):
            if st.checkbox(card, key=f"card_{card}", value=(card in st.session_state.owned_cards)):
                owned.append(card)
                st.markdown(f'<div class="iq-sub" style="font-size:.68rem;margin:-.4rem 0 .6rem 1.8rem;color:#4A3728">{CARD_BENEFITS[card]["note"]}</div>', unsafe_allow_html=True)
    st.session_state.owned_cards = owned

    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)
    cb1, cb2, _ = st.columns([1,1,3])
    with cb1:
        if st.button("← BACK"): st.session_state.flow_step = "bank_select"; st.rerun()
    with cb2:
        if st.button("CONTINUE →"): st.session_state.flow_step = "consent"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: CONSENT
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "consent":
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Step 3 of 3 &nbsp;·&nbsp; Review & Consent</div>', unsafe_allow_html=True)
    _, c_mid, _ = st.columns([.5,3,.5])
    with c_mid:
        st.markdown(f"""<div class="iq-consent">
            <div class="iq-eyebrow" style="color:#6C8EF5;margin-bottom:1.5rem">{st.session_state.selected_bank} &nbsp;·&nbsp; Account Aggregator Consent</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:300;color:#E2E8F4;margin-bottom:1.5rem;line-height:1.3">CardIQ is requesting<br>read-only access to your data.</div>
            <div class="consent-row"><span class="consent-icon">✦</span><div class="consent-txt"><strong>Transaction history</strong> — Last 90 days of debits and credits from your linked account.</div></div>
            <div class="consent-row"><span class="consent-icon">✦</span><div class="consent-txt"><strong>Credit card statements</strong> — Monthly statement data for selected cards only.</div></div>
            <div class="consent-row"><span class="consent-icon">✦</span><div class="consent-txt"><strong>No credentials shared</strong> — CardIQ never sees your PIN, password, or OTP.</div></div>
            <div class="consent-row" style="border:none"><span class="consent-icon">✦</span><div class="consent-txt"><strong>One-time consent</strong> — Access expires after this session. Revoke anytime from your bank app.</div></div>
            <div style="margin-top:1.5rem;padding:1rem;background:#080C14;border:1px solid #1E2A3F">
                <div class="iq-sub" style="font-size:.68rem;color:#2A3855">This consent is governed by the RBI Account Aggregator framework under NBFC-AA regulations. CardIQ is a registered Financial Information User (FIU).</div>
            </div></div>""", unsafe_allow_html=True)
        st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button("← BACK"): st.session_state.flow_step = "card_select"; st.rerun()
        with cb2:
            if st.button("APPROVE & CONNECT"): st.session_state.flow_step = "connecting"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: CONNECTING
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "connecting":
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    placeholder = st.empty()
    loading_steps = [
        f"Connecting to {st.session_state.selected_bank}",
        "Verifying consent token",
        "Fetching account transactions",
        "Fetching credit card statements",
        "Preparing your data",
    ]
    for i, step in enumerate(loading_steps):
        dots = '<span class="pulse-dot pd1"></span><span class="pulse-dot pd2"></span><span class="pulse-dot pd3"></span>'
        pct = int((i+1)/len(loading_steps)*100)
        placeholder.markdown(f"""<div class="loading-wrap">
            <div class="iq-eyebrow" style="margin-bottom:1rem">{st.session_state.selected_bank}</div>
            <div class="loading-title">{step}</div>
            <div style="margin-top:1.5rem">{dots}</div>
            <div class="loading-sub">{i+1} of {len(loading_steps)}</div>
            <div style="margin-top:2rem;width:200px;margin-left:auto;margin-right:auto">
                <div class="progress-track"><div class="progress-fill" style="width:{pct}%"></div></div>
            </div></div>""", unsafe_allow_html=True)
        time.sleep(0.7)

    # Load and detect UPI
    bank_debits = get_debits(parse_csv_string(SAMPLE_BANK_CSV))
    cc_debits   = get_debits(parse_csv_string(SAMPLE_CC_CSV))
    all_debits  = pd.concat([bank_debits, cc_debits], ignore_index=True)

    upi_mask = all_debits["Description"].apply(is_upi)
    upi_rows = all_debits[upi_mask].copy()

    st.session_state.all_debits    = all_debits
    st.session_state.upi_rows      = upi_rows
    st.session_state.upi_categories = {}

    placeholder.empty()
    if len(upi_rows) > 0:
        st.session_state.flow_step = "upi_review"
    else:
        st.session_state.flow_step = "analysing"
    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: UPI REVIEW  ← the new step
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "upi_review":
    upi_rows = st.session_state.upi_rows
    n = len(upi_rows)
    done = sum(1 for v in st.session_state.upi_categories.values() if v != "— Skip —")
    pct = int(done/n*100) if n else 100

    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Quick Review &nbsp;·&nbsp; UPI Transactions</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:300;color:#E2E8F4;margin-bottom:.5rem">
        We found <em>{n}</em> UPI payments we couldn't identify.
    </div>
    <div class="progress-track" style="margin:1rem 0 0">
        <div class="progress-fill" style="width:{pct}%"></div>
    </div>
    <div class="iq-sub" style="font-size:.68rem;margin-bottom:1.5rem">{done} of {n} categorized</div>
    <div class="upi-note">
        UPI transactions show only a payment ID — we can't tell if <strong>9876543210@ybl</strong> is your local grocery store, 
        a restaurant, or a friend. Tag them once and your analysis will be precise. 
        Not sure? Select <strong>Other</strong> or skip.
    </div>
    """, unsafe_allow_html=True)

    # Column headers
    st.markdown("""<div class="upi-row" style="border-bottom:1px solid #1A1410">
        <span style="font-size:.58rem;letter-spacing:.25em;text-transform:uppercase;color:#2A3855">UPI ID &nbsp;·&nbsp; Date</span>
        <span style="font-size:.58rem;letter-spacing:.25em;text-transform:uppercase;color:#2A3855;text-align:right">Amount</span>
        <span style="font-size:.58rem;letter-spacing:.25em;text-transform:uppercase;color:#2A3855">Category</span>
    </div>""", unsafe_allow_html=True)

    # One row per UPI transaction
    for idx, row in upi_rows.iterrows():
        display_id = extract_upi_display(row["Description"])
        date_str   = str(row.get("Date",""))
        amt        = row["Amount"]
        current    = st.session_state.upi_categories.get(idx, "— Skip —")

        col_id, col_amt, col_cat = st.columns([2, 1.2, 1])

        with col_id:
            st.markdown(f"""<div style="padding:.9rem 0">
                <div class="upi-id">{display_id}
                    <span>{date_str}</span>
                </div></div>""", unsafe_allow_html=True)

        with col_amt:
            st.markdown(f'<div class="upi-amt" style="padding:.9rem 0">₹{amt:,.0f}</div>', unsafe_allow_html=True)

        with col_cat:
            options = ["— Skip —"] + CATEGORIES
            sel = st.selectbox(
                label=" ", options=options,
                index=options.index(current) if current in options else 0,
                key=f"upi_cat_{idx}", label_visibility="collapsed"
            )
            st.session_state.upi_categories[idx] = sel

    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)

    tagged = sum(1 for v in st.session_state.upi_categories.values() if v != "— Skip —")
    skipped = n - tagged

    st.markdown(f'<div class="iq-sub" style="font-size:.72rem;margin-bottom:1.5rem">✦ &nbsp; {tagged} tagged &nbsp;·&nbsp; {skipped} will be auto-categorized as <span style="color:#6C8EF5">Other</span></div>', unsafe_allow_html=True)

    cb1, cb2, _ = st.columns([1,1.5,3])
    with cb1:
        if st.button("← BACK"):
            st.session_state.flow_step = "consent"; st.rerun()
    with cb2:
        btn_label = "LOOKS GOOD →" if tagged > 0 else "SKIP ALL →"
        if st.button(btn_label):
            st.session_state.flow_step = "analysing"; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: ANALYSING  (apply UPI tags + call AI)
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "analysing":
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    placeholder = st.empty()
    placeholder.markdown("""<div class="loading-wrap">
        <div class="iq-eyebrow" style="margin-bottom:1rem">GPT-4o</div>
        <div class="loading-title">Analysing your finances</div>
        <div style="margin-top:1.5rem"><span class="pulse-dot pd1"></span><span class="pulse-dot pd2"></span><span class="pulse-dot pd3"></span></div>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.api_key:
        placeholder.error("Please enter your OpenAI API key above first.")
        st.session_state.flow_step = "consent"
    else:
        try:
            all_debits = st.session_state.all_debits.copy()

            # Apply user-tagged UPI categories as a new column hint for the AI
            upi_cats = st.session_state.upi_categories
            all_debits["Category"] = ""
            for idx, cat in upi_cats.items():
                if cat != "— Skip —":
                    all_debits.at[idx, "Category"] = cat

            # Build transaction text — include Category column so AI respects tags
            tx_text = all_debits[["Date","Description","Amount","Category"]].to_string(index=False, max_rows=120)

            cards_to_use = st.session_state.owned_cards if st.session_state.owned_cards else list(CARD_BENEFITS.keys())[:3]
            client = OpenAI(api_key=st.session_state.api_key)
            result = analyze_with_ai(client, tx_text, cards_to_use)

            st.session_state.analysis     = result
            st.session_state.chat_history = []
            st.session_state.context      = f"Spend: ₹{result.get('total_spend',0):,.0f}. Categories: {result.get('categories',{})}. Insights: {result.get('insights',[])}. Optimizer: {result.get('card_optimizer',[])}. Savings: ₹{result.get('total_potential_savings',0):,.0f}."
            st.session_state.flow_step    = "results"
            st.rerun()
        except Exception as e:
            placeholder.error(f"Analysis failed: {e}")
            st.session_state.flow_step = "upi_review"
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# STEP: RESULTS
# ══════════════════════════════════════════════════════════════
elif st.session_state.flow_step == "results":
    r = st.session_state.analysis

    tagged_count = sum(1 for v in st.session_state.upi_categories.values() if v != "— Skip —")

    st.markdown(f"""<div style="padding:1rem 6rem;background:#0D1220;border-bottom:1px solid #1E2A3F;display:flex;justify-content:space-between;align-items:center">
        <div class="iq-eyebrow">Connected &nbsp;·&nbsp; {st.session_state.selected_bank}</div>
        <div style="display:flex;gap:1.5rem;align-items:center">
            {"".join([f'<span class="account-badge">{c}</span>' for c in (st.session_state.owned_cards or ["No cards"])])}
        </div>
        <div class="iq-eyebrow" style="color:#2A3855">{tagged_count} UPI payments tagged &nbsp;·&nbsp; March 2024</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Overview</div>', unsafe_allow_html=True)

    subs = r.get("subscriptions",[])
    sub_total = sum(s.get("amount",0) for s in subs)
    savings   = r.get("total_potential_savings",0)

    m1,m2,m3,m4 = st.columns(4)
    with m1: st.markdown(f'<div class="iq-card"><div class="iq-card-label">Total Spend</div><div class="iq-metric">₹{r.get("total_spend",0):,.0f}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="iq-card"><div class="iq-card-label">Top Category</div><div class="iq-metric" style="font-size:1.5rem">{r.get("top_category","—")}</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="iq-card"><div class="iq-card-label">Subscriptions / mo</div><div class="iq-metric">₹{sub_total:,.0f}</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="iq-card"><div class="iq-card-label">Rewards Unclaimed</div><div class="iq-metric green">₹{savings:,.0f}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="iq-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Spend Breakdown","Insights","Card Optimizer"])

    with tab1:
        cats = {k:v for k,v in r.get("categories",{}).items() if v > 0}
        c1,_,c2 = st.columns([1.3,.2,1.8])
        with c1:
            st.markdown('<div class="iq-label">By Category</div>', unsafe_allow_html=True)
            if cats: st.plotly_chart(make_donut(cats), use_container_width=True, config={"displayModeBar":False})
        with c2:
            st.markdown('<div class="iq-label">Breakdown</div>', unsafe_allow_html=True)
            total = max(r.get("total_spend",1),1)
            for cat,amt in sorted(cats.items(), key=lambda x:-x[1]):
                pct = int(amt/total*100)
                st.markdown(f"""<div class="iq-row">
                    <span class="iq-row-cat">{cat}</span>
                    <span style="font-family:'Playfair Display',serif;font-size:1.1rem;color:#2A3855">{pct}%</span>
                    <span class="iq-row-val">₹{amt:,.0f}</span></div>""", unsafe_allow_html=True)
        if subs:
            st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)
            st.markdown('<div class="iq-label">Recurring Charges</div>', unsafe_allow_html=True)
            st.markdown("".join([f'<div class="iq-sub-tag">{s.get("name","?")} <span>₹{s.get("amount",0):,.0f}/mo</span></div>' for s in subs]), unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="iq-label">Observations</div>', unsafe_allow_html=True)
        for insight in r.get("insights",[]):
            st.markdown(f'<div class="iq-insight">{insight}</div>', unsafe_allow_html=True)
        rec = r.get("top_recommendation","")
        if rec:
            st.markdown(f"""<div style="margin-top:2.5rem;padding:2rem 2.5rem;border:1px solid rgba(201,169,110,.15);background:#0D1220">
                <div class="iq-eyebrow" style="color:#6C8EF5;margin-bottom:1rem">Primary Recommendation</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:300;color:#C8D4F0;line-height:1.6">{rec}</div></div>""", unsafe_allow_html=True)

    with tab3:
        opt = r.get("card_optimizer",[])
        total_s = r.get("total_potential_savings",0)
        st.markdown(f"""<div style="padding:2rem 0 2.5rem">
            <div class="iq-eyebrow" style="color:#2A3855;margin-bottom:.6rem">This month, you left unclaimed</div>
            <div style="font-family:'Playfair Display',serif;font-size:4.5rem;font-weight:300;color:#6C8EF5;line-height:1">₹{total_s:,.0f}</div>
            <div class="iq-sub" style="margin-top:.6rem">Annualised — ₹{int(total_s*12):,.0f} in rewards you never received.</div></div>""", unsafe_allow_html=True)
        if opt:
            st.markdown('<div class="iq-label">By Category</div>', unsafe_allow_html=True)
            st.markdown("""<div class="iq-row">
                <span class="iq-row-cat" style="color:#2A3855;font-size:.58rem;letter-spacing:.2em;text-transform:uppercase">Category</span>
                <span class="iq-row-card" style="color:#2A3855;font-size:.58rem;letter-spacing:.2em;text-transform:uppercase">Optimal Card</span>
                <span class="iq-row-val" style="color:#2A3855;font-size:.58rem;letter-spacing:.2em;text-transform:uppercase">You Save</span></div>""", unsafe_allow_html=True)
            for item in sorted(opt, key=lambda x:-x.get("potential_savings",0)):
                if item.get("potential_savings",0) > 0:
                    st.markdown(f"""<div class="iq-row">
                        <span class="iq-row-cat">{item['category']}<br><span style="font-size:.68rem;color:#2A3855">₹{item['spend']:,.0f} spent</span></span>
                        <span class="iq-row-card">{item['best_card']}<br><span style="font-size:.68rem;color:#4A5A7A">{item['best_rate']}% cashback</span></span>
                        <span class="iq-row-val">₹{item['potential_savings']:,.0f}</span></div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="iq-divider"></div>', unsafe_allow_html=True)

    # Chat
    st.markdown('<div class="iq-body">', unsafe_allow_html=True)
    st.markdown('<div class="iq-label">Ask CardIQ</div>', unsafe_allow_html=True)
    st.markdown('<div class="iq-sub" style="margin-bottom:2rem">Your data. Your questions. Ask anything.</div>', unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="iq-chat-user">&ldquo;{msg["content"]}&rdquo;</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="iq-chat-ai">{msg["content"]}</div>', unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        user_q = st.text_input("", placeholder="e.g.  Which card should I cancel?   ·   Where did I overspend?", label_visibility="collapsed")
        submitted = st.form_submit_button("ASK →")

    if submitted and user_q.strip():
        with st.spinner(""):
            try:
                client = OpenAI(api_key=st.session_state.api_key)
                answer = chat_with_data(client, user_q.strip(), st.session_state.context)
                st.session_state.chat_history.append({"role":"user","content":user_q.strip()})
                st.session_state.chat_history.append({"role":"assistant","content":answer})
                st.rerun()
            except Exception as e:
                st.error(f"Chat failed: {e}")

    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)
    _,c_disc,_ = st.columns([1,1,1])
    with c_disc:
        if st.button("DISCONNECT ACCOUNT"):
            for k,v in defaults.items(): st.session_state[k] = v
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="iq-divider"></div>
<div style="padding:2rem 6rem;display:flex;justify-content:space-between">
    <div class="iq-eyebrow">CardIQ &nbsp;·&nbsp; 2024</div>
    <div class="iq-sub" style="font-size:.6rem">Your data never leaves your session</div>
    <div class="iq-eyebrow">GPT-4o &nbsp;·&nbsp; Streamlit</div>
</div>
""", unsafe_allow_html=True)
