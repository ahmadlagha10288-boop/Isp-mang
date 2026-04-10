import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Management System", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL, paid_amount REAL DEFAULT 0)''')
conn.commit()

# --- الأسعار ---
PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinim": 40, "daymon": 50, "ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

# وظيفة تنظيف رقم الهاتف
def clean_phone(phone):
    p = "".join(filter(str.isdigit, str(phone)))
    if not p: return ""
    if p.startswith("961"): return p
    if len(p) == 8: return "961" + p
    return p

st.title("🚀 نظام إدارة وحسابات الشبكة")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        df[expiry_col] = pd.to_datetime(df[expiry_col], errors='coerce')
        df = df.sort_values(by=expiry_col)

    # --- معالجة البيانات ---
    total_expected = 0
    total_collected = 0
    not_paid_count = 0
    paid_count = 0
    
    for index, row in df.iterrows():
        u = row['Username']
        p = get_price(row['Service'])
        total_expected += p
        
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
        res = c.fetchone()
        debt = res[0] if res else 0
        collected = res[1] if res else 0
        
        total_collected += collected
        if debt > 0: not_paid_count += 1
        else: paid_count += 1

    # --- لوحة التحكم Dashboard (أول الصفحة) ---
    st.markdown("### 📊 إحصائيات الحسابات")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👥 زبائن دافعة", paid_count)
    m2.metric("🚫 زبائن لم تدفع", not_paid_count)
    m3.metric("💰 مصاري بالسوق", f"${total_expected - total_collected:.2f}")
    m4.metric("✅ إجمالي ما تم جبايته", f"${total_collected:.2f}")
    st.markdown("---")

    # --- ميزة الراديوس (Radius Link) ---
    st.sidebar.header("🔗 ربط الراديوس")
    radius_url = st.sidebar.text_input("رابط صفحة الراديوس:", "http://your-radius-ip/admin")
    st.sidebar.info("يمكنك فتح الرابط للمقارنة اليدوية حالياً.")
    if st.sidebar.button("فتح الراديوس"):
        st.sidebar.markdown(f"[اضغط هنا لفتح الراديوس]({radius_url})")

    # --- عرض الجدول المرتّب ---
    for index, row in df.iterrows():
        user = row['Username']
        price = get_price(row['Service'])
        expiry = row.get(expiry_col, None)
        phone = clean_phone(row.get('Mobile Number', row.get('Phone Number', '')))
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        debt = res[0] if res else 0
        
        is_expired = pd.notna(expiry) and expiry < datetime.now()
        
        with st.expander(f"{'❌' if is_expired else '✅'} {user} | ينتهي: {expiry.date() if pd.notna(expiry) else '??'} | دين: ${debt}", expanded=debt > 0):
            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                st.write(f"**الخدمة:** {row['Service']} (${price})")
                if is_expired: st.error("⚠️ الاشتراك منتهي!")
            
            with c2:
                amt = st.number_input("تعديل ($)", key=f"n_{user}", step=1.0)
                if st.button("➕ إضافة دين", key=f"a_{user}"):
                    c.execute("INSERT OR REPLACE INTO billing (username, debt) VALUES (?, ?)", (user, debt + amt))
                    conn.commit()
                    st.rerun()
                if st.button("➖ خصم/دفع", key=f"s_{user}"):
                    # تحديث الدين والمبلغ المحصل
                    new_debt = max(0, debt - amt)
                    c.execute("SELECT paid_amount FROM billing WHERE username=?", (user,))
                    old_paid = c.fetchone()[1] if c.fetchone() else 0
                    c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (user, new_debt, old_paid + amt))
                    conn.commit()
                    st.rerun()

            with c3:
                if phone:
                    msg = f"مرحباً {user}، تذكير من إدارة الشبكة. إجمالي المطلوب: ${debt}. شكراً."
                    st.markdown(f"[💬 واتساب لـ {user}](https://wa.me/{phone}?text={msg})")
