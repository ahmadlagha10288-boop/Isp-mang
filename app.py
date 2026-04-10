import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Billing System", layout="wide")

# --- إدارة قاعدة البيانات (لحفظ الديون) ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL)''')
conn.commit()

# --- قائمة الأسعار (عدلها كما تحب) ---
PRICES = {
    "bs-Bronze": 20,
    "bs-silver": 25,
    "bs-Gold": 30,
    "bs-silver+": 35
}

st.title("💰 نظام المحاسبة وتحصيل الديون")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    
    # فلترة البحث
    search = st.text_input("🔍 ابحث عن اسم الزبون:")
    if search:
        df = df[df['Username'].astype(str).str.contains(search, case=False)]

    st.markdown("---")
    
    # رؤوس الجدول
    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 2])
    h1.write("**المشترك / الخدمة**")
    h2.write("**السعر الحالي**")
    h3.write("**إجمالي الدين**")
    h4.write("**الإجراء**")
    h5.write("**تواصل**")

    for index, row in df.iterrows():
        user = row['Username']
        service = row['Service']
        price = PRICES.get(service, 0)
        phone = str(row.get('Mobile Number', row.get('Phone Number', '')))
        
        # جلب الدين من الداتابيز
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        current_debt = res[0] if res else 0
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        
        with col1:
            st.write(f"{user}  \n`{service}`")
        with col2:
            st.write(f"${price}")
        with col3:
            # تلوين الدين بالأحمر إذا كان أكبر من 0
            if current_debt > 0:
                st.error(f"${current_debt}")
            else:
                st.success(f"${current_debt}")
                
        with col4:
            if st.button("✅ دفع", key=f"pay_{user}"):
                new_debt = max(0, current_debt - price)
                c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?)", (user, new_debt))
                conn.commit()
                st.rerun()
                
        with col5:
            if phone:
                msg = f"مرحباً {user}، نود تذكيرك بأن اشتراكك ({service}) قارب على الانتهاء. القيمة المطلوبة: {current_debt}$. شكراً لك."
                wa_url = f"https://wa.me/{phone.replace('+', '')}?text={msg.replace(' ', '%20')}"
                st.markdown(f"[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=flat&logo=whatsapp&logoColor=white)]({wa_url})")
            else:
                st.write("رقم غير موجود")

    # القائمة الجانبية للتحكم الجماعي
    st.sidebar.header("⚙️ إعدادات الإدارة")
    if st.sidebar.button("➕ إضافة اشتراك الشهر الجديد للكل"):
        for index, row in df.iterrows():
            u = row['Username']
            p = PRICES.get(row['Service'], 0)
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            res = c.fetchone()
            d = res[0] if res else 0
            c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?)", (u, d + p))
        conn.commit()
        st.sidebar.success("تمت إضافة الرسوم للجميع")
        st.rerun()

st.info("ملاحظة: اضغط على 'إضافة اشتراك الشهر الجديد' مرة واحدة فقط بداية كل شهر.")
