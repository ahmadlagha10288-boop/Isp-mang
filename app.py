import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Manager", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
conn.commit()

# --- الأسعار الدقيقة حسب طلبك ---
PRICES = {
    "bronze": 20,
    "silver": 25,
    "gold": 30,
    "platinum": 40,
    "diamond": 50,
    "platinum-ise": 60
}

def get_price(service_name):
    if pd.isna(service_name): return 0
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📡 نظام المحاسبة الموحد")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    
    # --- معالجة التاريخ (تحويل النص إلى تاريخ حقيقي) ---
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        # تحويل التاريخ مع مراعاة التنسيق اللي بعتلي ياه
        df[expiry_col] = pd.to_datetime(df[expiry_col], errors='coerce')
        # ترتيب: المنتهي أولاً
        df = df.sort_values(by=expiry_col)

    # --- حساب الإحصائيات ---
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    totals = c.fetchone()
    m_debt = totals[0] or 0
    collected = totals[1] or 0
    
    st.info(f"💰 ديون السوق: **${m_debt:.1f}** | ✅ جباية الكاش: **${collected:.1f}**")

    # --- تجهيز بيانات الجدول للعرض ---
    table_list = []
    for index, row in df.iterrows():
        user = row['Username']
        service = row['Service']
        price = get_price(service)
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        u_debt = res[0] if res else 0
        
        # تنسيق التاريخ ليظهر بشكل واضح (يوم-شهر)
        expiry_dt = row[expiry_col]
        if pd.notna(expiry_dt):
            display_date = expiry_dt.strftime('%d/%m')
            status = "🔴" if expiry_dt < datetime.now() else "🟢"
        else:
            display_date = "??"
            status = "⚪"
            
        table_list.append({
            "ح": status,
            "المشترك": user,
            "تاريخ": display_date,
            "الخدمة": service,
            "السعر": f"${price}",
            "الدين": f"${u_debt}"
        })

    # --- عرض الجدول الموحد ---
    st.dataframe(pd.DataFrame(table_list), use_container_width=True, hide_index=True)

    st.divider()

    # --- الإدارة (التحكم) ---
    st.subheader("⚙️ إدارة الحساب")
    target = st.selectbox("اختر اسم الزبون:", [""] + df['Username'].tolist())
    
    if target:
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (target,))
        u_data = c.fetchone()
        curr_debt = u_data[0] if u_data else 0
        curr_paid = u_data[1] if u_data else 0
        p_val = get_price(df[df['Username']==target]['Service'].values[0])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ قبض ${p_val} من {target}"):
                c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                          (target, max(0, curr_debt - p_val), curr_paid + p_val))
                conn.commit()
                st.success("تم تسجيل الدفعة")
                st.rerun()
        
        with col2:
            new_val = st.number_input("تعديل يدوي للدين ($):", value=float(curr_debt))
            if st.button("تحديث المبلغ 💾"):
                c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                          (target, new_val, curr_paid))
                conn.commit()
                st.rerun()

    # --- الأوامر الجانبية ---
    if st.sidebar.button("🚨 تسجيل شهر جديد للجميع"):
        for _, r in df.iterrows():
            u = r['Username']
            p = get_price(r['Service'])
            c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
            res = c.fetchone()
            d = res[0] if res else 0
            pa = res[1] if res else 0
            c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (u, d + p, pa))
        conn.commit()
        st.rerun()
