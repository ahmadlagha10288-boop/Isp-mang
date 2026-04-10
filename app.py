import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# إعداد الصفحة
st.set_page_config(page_title="ISP Manager Pro", layout="wide")

# --- إدارة قاعدة البيانات ---
def get_db():
    conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS billing 
                 (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
    try: c.execute("ALTER TABLE billing ADD COLUMN paid_amount REAL DEFAULT 0")
    except: pass
    conn.commit()
    return conn, c

conn, c = get_db()

# --- الأسعار ---
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

st.title("📡 نظام المتابعة الذكي بالألوان")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file is not None:
    try:
        df = pd.read_csv(file)
        expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
        
        if expiry_col in df.columns:
            # تحويل التاريخ ومعالجة الأخطاء
            df[expiry_col] = pd.to_datetime(df[expiry_col], errors='coerce')
            # ترتيب: المنتهي أولاً ثم القريب ينتهي
            df = df.sort_values(by=expiry_col)

        # الإحصائيات
        c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
        res = c.fetchone()
        st.info(f"💰 ديون السوق: **${res[0] or 0}** | ✅ جباية الكاش: **${res[1] or 0}**")

        table_rows = []
        now = datetime.now()

        for _, row in df.iterrows():
            user = row['Username']
            exp_date = row[expiry_col]
            
            # --- منطق الألوان الذكي ---
            if pd.isna(exp_date):
                color_icon = "⚪" # تاريخ غير معروف
                status_text = "غير محدد"
            elif exp_date < now:
                color_icon = "🔴" # منتهي
                status_text = "منتهي"
            elif exp_date < (now + timedelta(days=3)):
                color_icon = "🔵" # قريب يخلص (باقي أقل من 3 أيام)
                status_text = "قريب ينتهي"
            else:
                color_icon = "🟢" # شغال تمام
                status_text = "شغال"

            c.execute("SELECT debt FROM billing WHERE username=?", (user,))
            d_res = c.fetchone()
            debt = d_res[0] if d_res else 0
            
            date_display = exp_date.strftime('%d/%m') if pd.notna(exp_date) else "??"
            
            table_rows.append({
                "الحالة": color_icon,
                "الوضع": status_text,
                "المشترك": user,
                "التاريخ": date_display,
                "الدين": f"${debt}"
            })

        # عرض الجدول
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        st.divider()
        
        # إدارة سريعة
        st.subheader("⚙️ إدارة زبون")
        target = st.selectbox("اختر الاسم:", [""] + df['Username'].tolist())
        if target:
            # (نفس أكواد القبض والتعديل السابقة)
            p_val = get_price(df[df['Username']==target]['Service'].values[0])
            if st.button(f"✅ قبض ${p_val} من {target}"):
                c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (target,))
                u_d = c.fetchone() or (0,0)
                c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                          (target, max(0, u_d[0] - p_val), u_d[1] + p_val))
                conn.commit()
                st.rerun()

    except Exception as e:
        st.error(f"خطأ: {e}")

# الزر الجانبي
if st.sidebar.button("🚨 تسجيل شهر جديد للكل"):
    for _, r in df.iterrows():
        u = r['Username']; p = get_price(r['Service'])
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
        res = c.fetchone() or (0,0)
        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (u, res[0] + p, res[1]))
    conn.commit()
    st.rerun()
