import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

st.set_page_config(page_title="ISP Ultimate Manager", layout="wide")

# --- قاعدة بيانات ذكية ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
try:
    c.execute("ALTER TABLE billing ADD COLUMN paid_amount REAL DEFAULT 0")
except: pass
conn.commit()

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

st.title("🚀 الإدارة الذكية (النسخة النهائية)")

file = st.file_uploader("ارفع ملف الـ CSV")

if file:
    df = pd.read_csv(file)
    
    # --- ميزة البحث التلقائي عن عمود التاريخ ---
    date_col = None
    possible_names = ['Expired', 'Expiration Date', 'Date', 'تاريخ', 'End Date']
    for col in df.columns:
        if any(name.lower() in col.lower() for name in possible_names):
            date_col = col
            break
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(by=date_col)

    # حسابات سريعة
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    totals = c.fetchone()
    st.info(f"💰 ديون السوق: **${totals[0] or 0}** | ✅ جباية الكاش: **${totals[1] or 0}**")

    # عرض البيانات بجدول احترافي
    rows = []
    now = datetime.now()
    for _, r in df.iterrows():
        user = r['Username']
        exp = r[date_col] if date_col else None
        
        # منطق الألوان الثلاثي
        if pd.isna(exp): status = "⚪"
        elif exp < now: status = "🔴"
        elif exp < (now + timedelta(days=3)): status = "🔵"
        else: status = "🟢"

        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        d = c.fetchone()
        debt = d[0] if d else 0
        
        rows.append({
            "ح": status,
            "المشترك": user,
            "التاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??",
            "الدين": f"${debt}"
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # التحكم
    st.markdown("---")
    target = st.selectbox("🎯 اختر زبون للإجراء:", [""] + df['Username'].tolist())
    if target:
        p_val = get_price(df[df['Username']==target]['Service'].values[0])
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ قبض ${p_val} (اشتراك)"):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (p_val, p_val, target))
                conn.commit()
                st.rerun()
        with col2:
            new_val = st.number_input("تعديل يدوي للدين:", step=1.0)
            if st.button("💾 حفظ التعديل"):
                c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, (SELECT paid_amount FROM billing WHERE username=?))", (target, new_val, target))
                conn.commit()
                st.rerun()

# --- المشروع القادم: نتفلكس ---
st.sidebar.markdown("---")
st.sidebar.subheader("🆕 المشروع القادم")
if st.sidebar.button("ابدأ إعداد نظام نتفلكس"):
    st.sidebar.success("تم تسجيل الطلب! دعنا ننهي برنامج الشبكة أولاً.")
