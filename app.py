import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Admin Pro", layout="wide")

# --- تنسيق CSS لإرجاع الشكل القديم المريح ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 25px; }
    div.stInfo { background-color: #e3f2fd; color: #0d47a1; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
conn.commit()

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinum": 40, "diamond": 50, "platinum-ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 نظام الإدارة المحاسبي")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    
    # --- الحل الذكي للتاريخ: قراءة التنسيق (السنة-الشهر-اليوم) ---
    if expiry_col in df.columns:
        # بنحكي للبرنامج يقرأ السنة أولاً، وهذا التعديل اللي بيحل مشكلة الـ ??
        df[expiry_col] = pd.to_datetime(df[expiry_col], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        # ترتيب: المنتهي أولاً
        df = df.sort_values(by=expiry_col)

    # الإحصائيات باللون الأزرق المريح (نفس الصورة الأولى)
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    totals = c.fetchone()
    st.info(f"💰 ديون السوق: **${totals[0] or 0}** | ✅ جباية الكاش: **${totals[1] or 0}**")

    st.markdown("---")
    search = st.text_input("🔍 ابحث عن اسم:")

    # --- تجهيز الجدول بلمحة وحدة (نفس التصميم الأصلي) ---
    rows = []
    for index, row in df.iterrows():
        user = row['Username']
        if search and search.lower() not in user.lower(): continue
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        debt = (c.fetchone() or (0,))[0]
        
        # تنسيق التاريخ ليظهر بشكل (يوم/شهر)
        exp_date = row[expiry_col]
        date_display = exp_date.strftime('%d/%m') if pd.notna(exp_date) else "??"
        
        rows.append({
            "المشترك": user,
            "تاريخ": date_display,
            "الخدمة": row['Service'],
            "السعر": f"${get_price(row['Service'])}",
            "الدين": f"${debt}"
        })

    # عرض الجدول الموحد
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # --- إدارة سريعة تحت الجدول (كبسات القبض والتعديل) ---
    st.subheader("⚙️ إدارة حساب")
    target = st.selectbox("اختر زبون للإجراء:", [""] + df['Username'].tolist())
    if target:
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (target,))
        u_data = c.fetchone() or (0,0)
        p_val = get_price(df[df['Username']==target]['Service'].values[0])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ قبض ${p_val} من {target}"):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (p_val, p_val, target))
                conn.commit()
                st.rerun()
        with col2:
            new_v = st.number_input("تعديل يدوي للدين", value=float(u_data[0]), step=1.0)
            if st.button("حفظ التعديل"):
                c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (target, new_v, u_data[1]))
                conn.commit()
                st.rerun()

# القائمة الجانبية
if st.sidebar.button("🚨 تسجيل شهر جديد للكل"):
    for _, r in df.iterrows():
        u = r['Username']; p = get_price(r['Service'])
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
        res = c.fetchone() or (0,0)
        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (u, res[0] + p, res[1]))
    conn.commit()
    st.rerun()
