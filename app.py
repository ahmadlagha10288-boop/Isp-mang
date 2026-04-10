import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

st.set_page_config(page_title="ISP Manager Final", layout="wide")

# --- تحسين المظهر ---
st.markdown("""
    <style>
    div.stInfo { background-color: #0e1117; color: #00ff00; border: 1px solid #00ff00; border-radius: 10px; }
    [data-testid="stMetricValue"] { color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
conn.commit()

# الأسعار
PRICES = {
    "bronze": 20, "silver": 25, "gold": 30,
    "platinum": 40, "diamond": 50, "platinum-ise": 60
}

def get_price(service_name):
    if pd.isna(service_name): return 0
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 نظام إدارة المشتركين")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    # قراءة الملف مع تنظيف أسماء الأعمدة
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    
    # اسم العمود من اللي بعتته بالظبط
    date_col = 'Expiry Date'
    
    if date_col in df.columns:
        # تحويل التاريخ (فهم التنسيق اللي بالملف)
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(by=date_col)

    # الإحصائيات
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    totals = c.fetchone()
    st.info(f"💰 ديون السوق: **${totals[0] or 0}** | ✅ جباية الكاش: **${totals[1] or 0}**")

    search = st.text_input("🔍 ابحث عن اسم (Username):")

    rows = []
    now = datetime.now()

    for _, r in df.iterrows():
        user = str(r['Username'])
        if search and search.lower() not in user.lower(): continue
        
        # جلب الدين من القاعدة
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        debt = res[0] if res else 0
        
        # تحديد الألوان حسب التاريخ
        exp = r[date_col]
        if pd.isna(exp):
            status = "⚪"
        elif exp < now:
            status = "🔴" # منتهي
        elif exp < (now + timedelta(days=3)):
            status = "🔵" # قريب يخلص
        else:
            status = "🟢" # شغال

        rows.append({
            "ح": status,
            "المشترك": user,
            "تاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??",
            "الخدمة": r['Service'],
            "السعر": f"${get_price(r['Service'])}",
            "الدين": f"${debt}"
        })

    # عرض الجدول
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # قسم الإدارة
    target = st.selectbox("🎯 اختر مشترك للقبض:", [""] + df['Username'].astype(str).tolist())
    if target:
        price_val = get_price(df[df['Username']==target]['Service'].values[0])
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ قبض ${price_val}"):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (price_val, price_val, target))
                conn.commit()
                st.rerun()
        with col2:
            new_debt = st.number_input("تعديل يدوي للدين:", step=1.0)
            if st.button("💾 حفظ"):
                c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, (SELECT paid_amount FROM billing WHERE username=?))", (target, new_debt, target))
                conn.commit()
                st.rerun()

# تسجيل شهر جديد
if st.sidebar.button("🚨 تسجيل شهر جديد للكل"):
    for _, r in df.iterrows():
        u = str(r['Username']); p = get_price(r['Service'])
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
        res = c.fetchone() or (0,0)
        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (u, res[0] + p, res[1]))
    conn.commit()
    st.rerun()
