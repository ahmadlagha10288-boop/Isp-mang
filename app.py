import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Pro", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
conn.commit()

# --- قائمة الأسعار ---
PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinim": 40, "daymon": 50, "ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 إدارة الشبكة | وضوح البيانات")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    
    # --- معالجة التاريخ لتوضيحه (قراءة ذكية) ---
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        # يحاول البرنامج قراءة التاريخ بكل الصيغ الممكنة
        df[expiry_col] = pd.to_datetime(df[expiry_col], dayfirst=True, errors='coerce')
        # ترتيب حسب التاريخ (الأقدم فوق)
        df = df.sort_values(by=expiry_col)

    st.markdown("---")

    for index, row in df.iterrows():
        user = row['Username']
        service = row['Service']
        price = get_price(service)
        expiry = row.get(expiry_col, None)
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        debt = res[0] if res else 0
        
        # تحديد حالة الانتهاء واللون
        is_expired = pd.notna(expiry) and expiry < datetime.now()
        date_str = expiry.strftime('%d / %m / %Y') if pd.notna(expiry) else "غير محدد"
        
        # عرض البيانات بشكل مكبّر وواضح
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                # تكبير اسم المشترك وتوضيح التاريخ بلون خلفية
                bg_color = "#ff4b4b" if is_expired else "#2ecc71"
                st.markdown(f"""
                <div style="background-color:{bg_color}; padding:10px; border-radius:10px; color:white;">
                    <h3 style="margin:0;">👤 {user}</h3>
                    <p style="margin:0; font-size:18px; font-weight:bold;">📅 التاريخ: {date_str}</p>
                </div>
                """, unsafe_allow_html=True)
                st.write(f"الخدمة: {service} (${price})")

            with col2:
                st.markdown(f"### 💰 ${debt}")
                if st.button("قبض ✅", key=f"pay_{user}"):
                    c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, (SELECT paid_amount FROM billing WHERE username=?)+?)", (user, max(0, debt - price), user, price))
                    conn.commit()
                    st.rerun()

            with col3:
                # خانة التعديل اليدوي سريعة
                new_val = st.number_input("تعديل دين", key=f"edit_{user}", step=1.0)
                if st.button("تحديث 💾", key=f"up_{user}"):
                    c.execute("INSERT OR REPLACE INTO billing (username, debt) VALUES (?, ?)", (user, new_val))
                    conn.commit()
                    st.rerun()

    # زر تسجيل الديون الجماعي في الجنب
    if st.sidebar.button("🚨 تسجيل ديون شهر جديد للكل"):
        for _, r in df.iterrows():
            u = r['Username']
            p = get_price(r['Service'])
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            d = c.fetchone()[0] if c.fetchone() else 0
            c.execute("INSERT OR REPLACE INTO billing (username, debt) VALUES (?, ?)", (u, d + p))
        conn.commit()
        st.rerun()
