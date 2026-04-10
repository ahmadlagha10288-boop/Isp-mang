import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Management", layout="wide")

# قاعدة البيانات
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing (username TEXT PRIMARY KEY, debt REAL)''')
conn.commit()

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinim": 40, "daymon": 50, "ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 لوحة التحكم الذكية")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    # تحويل التاريخ للتنسيق الصحيح (تأكد من اسم العمود في ملفك)
    # إذا كان اسم العمود 'Expired' أو 'Expiration Date'
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        df[expiry_col] = pd.to_datetime(df[expiry_col], errors='coerce')

    # حسابات الداشبورد
    c.execute("SELECT SUM(debt) FROM billing")
    market_debt = c.fetchone()[0] or 0
    
    # حساب المتوقع
    df['Price'] = df['Service'].apply(get_price)
    expected = df['Price'].sum()

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("💰 ديون السوق حالياً", f"${market_debt}")
    col_m2.metric("📈 متوقع التحصيل (قيمة الملف)", f"${expected}")

    st.divider()

    for index, row in df.iterrows():
        user = row['Username']
        price = row['Price']
        expiry = row.get(expiry_col, None)
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        debt = res[0] if res else 0
        
        # فحص الانتهاء
        is_expired = False
        if pd.notna(expiry) and expiry < datetime.now():
            is_expired = True

        c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
        with c1:
            if is_expired:
                st.markdown(f"❌ **{user}** <span style='color:red'>(منتهي الصلاحية!)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"✅ **{user}**", unsafe_allow_html=True)
            st.caption(f"الخدمة: {row['Service']} | ينتهي في: {expiry.date() if pd.notna(expiry) else '??'}")
        
        with c2:
            st.write(f"${price}")
        
        with c3:
            st.markdown(f"**دين: :{'red' if debt > 0 else 'green'}[${debt}]**")
            
        with c4:
            if st.button("قبض 💰", key=f"btn_{user}"):
                c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?)", (user, max(0, debt - price)))
                conn.commit()
                st.rerun()

    # القائمة الجانبية للإدارة
    st.sidebar.warning("إجراءات بداية الشهر")
    if st.sidebar.button("🚨 تسجيل ديون الملف الحالي"):
        for _, r in df.iterrows():
            u = r['Username']
            p = get_price(r['Service'])
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            old_d = c.fetchone()
            old_d = old_d[0] if old_d else 0
            c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?)", (u, old_d + p))
        conn.commit()
        st.rerun()
