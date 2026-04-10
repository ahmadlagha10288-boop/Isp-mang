import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة لتناسب عرض الموبايل والكمبيوتر
st.set_page_config(page_title="ISP Manager Pro", layout="wide")

# --- تنسيق CSS لجعل الجدول مضغوط وشكله احترافي ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 25px; }
    .main .block-container { padding-top: 2rem; }
    div.stButton > button { width: 100%; padding: 5px; height: 35px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
conn.commit()

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinim": 40, "daymon": 50, "ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 لوحة المشتركين الموحدة")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        df[expiry_col] = pd.to_datetime(df[expiry_col], dayfirst=True, errors='coerce')
        df = df.sort_values(by=expiry_col)

    # --- الإحصائيات (الداشبورد) ---
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    res = c.fetchone()
    market_debt = res[0] or 0
    collected = res[1] or 0
    
    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("💰 ديون السوق", f"${market_debt:.1f}")
    col_stat2.metric("✅ جباية الكاش", f"${collected:.1f}")

    st.markdown("---")
    
    # --- محرك البحث ---
    search = st.text_input("🔍 ابحث عن اسم:")

    # --- عرض الجدول بطريقة "قائمة ذكية" ---
    # بنعمل ترويسة وحدة بس فوق
    h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
    h1.write("**المشترك**")
    h2.write("**السعر**")
    h3.write("**الدين**")
    h4.write("**إدارة**")

    for index, row in df.iterrows():
        user = row['Username']
        if search and search.lower() not in user.lower(): continue
        
        service = row['Service']
        price = get_price(service)
        expiry = row.get(expiry_col, None)
        
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (user,))
        res_db = c.fetchone()
        debt = res_db[0] if res_db else 0
        p_amt = res_db[1] if res_db else 0
        
        is_expired = pd.notna(expiry) and expiry < datetime.now()
        date_str = expiry.strftime('%d/%m') if pd.notna(expiry) else "??"

        # عرض سطر واحد بسيط جداً
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                color = "red" if is_expired else "green"
                st.markdown(f":{color}[{user}] <small>({date_str})</small>", unsafe_allow_html=True)
            with c2:
                st.write(f"${price}")
            with c3:
                st.write(f"${debt}")
            with c4:
                # زر "خيارات" يفتح قائمة منسدلة صغيرة (Popover) عشان ما تخرب الشكل
                with st.popover("⚙️"):
                    st.write(f"الخدمة: {service}")
                    if st.button("✅ قبض الاشتراك", key=f"pay_{user}"):
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                                  (user, max(0, debt - price), p_amt + price))
                        conn.commit()
                        st.rerun()
                    
                    amt = st.number_input("مبلغ يدوي", key=f"amt_{user}", step=5.0)
                    if st.button("➕ زيادة دين", key=f"add_{user}"):
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (user, debt + amt, p_amt))
                        conn.commit()
                        st.rerun()
                    
                    phone = str(row.get('Mobile Number', ''))
                    if phone:
                        wa_url = f"https://wa.me/{phone}?text=مرحباً {user}، مطلوب منك ${debt}"
                        st.markdown(f"[💬 واتساب]({wa_url})")

    # --- القائمة الجانبية ---
    st.sidebar.button("🚨 تسجيل اشتراك شهر جديد", on_click=lambda: [c.execute("UPDATE billing SET debt = debt + ?", (get_price(r['Service']),)) for _,r in df.iterrows()])
