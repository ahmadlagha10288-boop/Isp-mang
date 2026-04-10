import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

st.set_page_config(page_title="ISP Total Control", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL, last_update TEXT)''')
conn.commit()

# --- الأسعار ---
PRICES = {
    "Bronse": 20, "Silver": 25, "Gold": 30, 
    "Platinim": 40, "Daymon": 50, "Platinium-ise": 60
}

st.title("📊 لوحة تحكم المحاسبة والديون")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    
    # --- حسابات السوق (Dashboard) ---
    c.execute("SELECT SUM(debt) FROM billing")
    total_market_debt = c.fetchone()[0] or 0
    
    # حساب "كم لازم أقبض" (سعر خدمات كل المشتركين بالملف)
    df['expected_price'] = df['Service'].map(PRICES).fillna(0)
    total_expected = df['expected_price'].sum()

    # عرض الأرقام الكبيرة
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 إجمالي ديون السوق (إلي معك)", f"${total_market_debt}")
    m2.metric("📈 لازم تقبض (هذا الشهر)", f"${total_expected}")
    m3.metric("👥 عدد المشتركين", len(df))

    st.markdown("---")

    # --- فلترة البحث وحالة الدفع ---
    filter_status = st.radio("عرض حسب الحالة:", ["الكل", "مش دافع (عليه دين)", "دافع (خالص)"], horizontal=True)
    search = st.text_input("🔍 بحث عن اسم:")

    # تجهيز البيانات للعرض
    display_data = []
    for _, row in df.iterrows():
        user = row['Username']
        service = row['Service']
        price = PRICES.get(service, 0)
        phone = str(row.get('Mobile Number', row.get('Phone Number', '')))
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        current_debt = res[0] if res else 0
        
        # منطق الفلترة
        if filter_status == "مش دافع (عليه دين)" and current_debt == 0: continue
        if filter_status == "دافع (خالص)" and current_debt > 0: continue
        if search and search.lower() not in user.lower(): continue

        # تحديد نوع التنبيه بناءً على حالة الدفع (افتراضياً 3 أيام قبل نهاية الشهر)
        # ملاحظة: يمكنك تطوير منطق التاريخ لاحقاً
        warning_msg = ""
        if current_debt > 0:
            warning_msg = f"⚠️ إنذار: يرجى الدفع قبل قطع الخط"
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        
        with col1:
            color = "red" if current_debt > 0 else "green"
            st.markdown(f":{color}[**{user}**]  \n({service})")
        with col2:
            st.write(f"${price}")
        with col3:
            st.write(f"**${current_debt}**")
        with col4:
            if st.button("✅ قبض", key=f"p_{user}"):
                new_debt = max(0, current_debt - price)
                c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (user, new_debt, datetime.now().isoformat()))
                conn.commit()
                st.rerun()
        with col5:
            # نظام الإنذارات الذكي
            if phone and phone != 'nan':
                if current_debt > price: # عليه أكتر من شهر
                    msg = f"🚨 إنذار نهائي: خطك سيقطع خلال 24 ساعة. إجمالي الدين المتراكم: ${current_debt}"
                elif current_debt > 0: # عليه شهر واحد
                    msg = f"⚠️ تذكير: قرب يخلص شهرك، معك 3 أيام للدفع. المبلغ: ${current_debt}"
                else:
                    msg = f"✅ شكراً لالتزامك. اشتراكك {service} فعال."
                
                wa_url = f"https://wa.me/{phone.replace('+', '')}?text={msg.replace(' ', '%20')}"
                st.markdown(f"[📲 إرسال إنذار]({wa_url})")

    # --- القائمة الجانبية ---
    st.sidebar.header("⚙️ الإجراءات")
    if st.sidebar.button("➕ إضافة رسوم شهر جديد"):
        for _, row in df.iterrows():
            u = row['Username']
            p = PRICES.get(row['Service'], 0)
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            res = c.fetchone()
            d = res[0] if res else 0
            c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (u, d + p, datetime.now().isoformat()))
        conn.commit()
        st.sidebar.success("تم تحديث الديون")
        st.rerun()
