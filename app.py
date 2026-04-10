import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="ISP Manager Pro", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
conn.commit()

# --- الأسعار ---
PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinim": 40, "daymon": 50, "ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 نظام إدارة الشبكة والحسابات")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    # معالجة التاريخ والفرز (الأقدم فوق)
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        df[expiry_col] = pd.to_datetime(df[expiry_col], dayfirst=True, errors='coerce')
        df = df.sort_values(by=expiry_col)

    # --- الحسابات المالية ---
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    res = c.fetchone()
    total_market_debt = res[0] if res[0] else 0
    total_collected = res[1] if res[1] else 0

    # عرض الأرقام الأساسية
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("💰 ديون السوق (إلك مع الناس)", f"${total_market_debt:.1f}")
    col_b.metric("✅ إجمالي اللي جبيناه", f"${total_collected:.1f}")
    col_c.metric("👥 عدد المشتركين", len(df))

    st.markdown("---")

    # --- محرك البحث ---
    search = st.text_input("🔍 ابحث عن زبون:")

    # --- عرض الجدول المنسق ---
    # ترويسة الجدول
    h1, h2, h3, h4 = st.columns([3, 1, 1, 2])
    h1.write("**المشترك (تاريخ الانتهاء)**")
    h2.write("**السعر**")
    h3.write("**الدين**")
    h4.write("**إجراءات**")

    for index, row in df.iterrows():
        user = row['Username']
        if search and search.lower() not in user.lower(): continue
        
        service = row['Service']
        price = get_price(service)
        expiry = row.get(expiry_col, None)
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        r_debt = c.fetchone()
        debt = r_debt[0] if r_debt else 0
        
        is_expired = pd.notna(expiry) and expiry < datetime.now()
        date_str = expiry.strftime('%d/%m') if pd.notna(expiry) else "??"

        # عرض سطر واحد لكل زبون لتقليل الحجم
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
            
            with c1:
                color = "red" if is_expired else "green"
                st.markdown(f":{color}[**{user}**] | ({date_str})")
            
            with c2:
                st.write(f"${price}")
            
            with c3:
                d_color = "red" if debt > 0 else "gray"
                st.markdown(f":{d_color}[**${debt}**]")
            
            with c4:
                # زر صغير لفتح التفاصيل
                with st.popover("خيارات ⚙️"):
                    st.write(f"الخدمة: {service}")
                    if st.button("✅ قبض الاشتراك", key=f"f_{user}"):
                        c.execute("SELECT paid_amount FROM billing WHERE username=?", (user,))
                        old_p = c.fetchone()[1] if c.fetchone() else 0
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                                  (user, max(0, debt - price), old_paid + price))
                        conn.commit()
                        st.rerun()
                    
                    # تعديل يدوي
                    amt = st.number_input("تعديل مبلغ", key=f"n_{user}", step=1.0)
                    if st.button("➕ زيادة دين", key=f"add_{user}"):
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, (SELECT paid_amount FROM billing WHERE username=?))", (user, debt + amt, user))
                        conn.commit()
                        st.rerun()
                    
                    # واتساب
                    phone = str(row.get('Mobile Number', ''))
                    if phone:
                        wa_url = f"https://wa.me/{phone}?text=تذكير: إجمالي دينك هو ${debt}"
                        st.markdown(f"[💬 واتساب]({wa_url})")

    # --- القائمة الجانبية ---
    st.sidebar.header("⚙️ الإدارة")
    if st.sidebar.button("🚨 تسجيل شهر جديد للكل"):
        for _, r in df.iterrows():
            u = r['Username']
            p = get_price(r['Service'])
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            d = c.fetchone()[0] if c.fetchone() else 0
            c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, (SELECT paid_amount FROM billing WHERE username=?))", (u, d + p, u))
        conn.commit()
        st.rerun()

    if st.sidebar.button("🧹 تصفير الجباية"):
        c.execute("UPDATE billing SET paid_amount = 0")
        conn.commit()
        st.rerun()
