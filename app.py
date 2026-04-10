import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="ISP Pro Manager", layout="wide")

# --- إدارة قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL, last_update TEXT)''')
conn.commit()

# --- الأسعار ---
PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinim": 40, "daymon": 50, "ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("📊 نظام المحاسبة الشامل للديون")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    # تحديد عمود التاريخ وفرز الجدول
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        df[expiry_col] = pd.to_datetime(df[expiry_col], errors='coerce')
        # ترتيب الجدول حسب التاريخ (الأقدم أولاً - يعني المنتهي بيطلع بالوجه)
        df = df.sort_values(by=expiry_col)

    # --- حسابات الداشبورد (قيمة الدين في السوق) ---
    c.execute("SELECT SUM(debt) FROM billing")
    market_debt = c.fetchone()[0] or 0
    
    df['Price'] = df['Service'].apply(get_price)
    
    st.markdown(f"### 💰 إجمالي ديون السوق الحالية: `${market_debt}`")
    st.markdown("---")

    # --- عرض الزبائن ---
    for index, row in df.iterrows():
        user = row['Username']
        price = row['Price']
        expiry = row.get(expiry_col, None)
        
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        current_debt = res[0] if res else 0
        
        # فحص الحالة: خالص تاريخياً وموقف (اللون الرمادي للمنتهي والخالص)
        is_expired = pd.notna(expiry) and expiry < datetime.now()
        
        # تصميم الصف
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
            
            with col1:
                status_icon = "❌" if is_expired else "✅"
                st.markdown(f"{status_icon} **{user}**")
                st.caption(f"الخدمة: {row['Service']} | ينتهي: {expiry.date() if pd.notna(expiry) else '??'}")
            
            with col2:
                st.write(f"السعر: ${price}")
            
            with col3:
                # تلوين الدين
                d_color = "red" if current_debt > 0 else "green"
                st.markdown(f"**إجمالي الدين: :[{d_color}][${current_debt}]**")
                
                # إضافة/خصم يدوي
                amount = st.number_input("تعديل يدوي ($)", key=f"amt_{user}", step=5.0)
                sub_col1, sub_col2 = st.columns(2)
                if sub_col1.button("➕ زيادة", key=f"add_{user}"):
                    c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (user, current_debt + amount, datetime.now().isoformat()))
                    conn.commit()
                    st.rerun()
                if sub_col2.button("➖ خصم", key=f"sub_{user}"):
                    c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (user, max(0, current_debt - amount), datetime.now().isoformat()))
                    conn.commit()
                    st.rerun()

            with col4:
                # زر القبض السريع لسعر الاشتراك
                if st.button("✅ قبض سعر الاشتراك", key=f"btn_{user}"):
                    c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (user, max(0, current_debt - price), datetime.now().isoformat()))
                    conn.commit()
                    st.rerun()
                
                # رابط واتساب
                phone = str(row.get('Mobile Number', ''))
                if phone:
                    msg = f"مرحباً {user}، تذكير بخصوص اشتراكك. إجمالي المبلغ المطلوب: ${current_debt}."
                    wa_url = f"https://wa.me/{phone.replace('+', '')}?text={msg.replace(' ', '%20')}"
                    st.markdown(f"[💬 واتساب]({wa_url})")

    # --- الإجراءات الجماعية ---
    st.sidebar.header("⚙️ الإدارة")
    if st.sidebar.button("🚨 تسجيل اشتراك الشهر الجديد للكل"):
        for _, r in df.iterrows():
            u = r['Username']
            p = get_price(r['Service'])
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            old_d = c.fetchone()
            old_d = old_d[0] if old_d else 0
            c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (u, old_d + p, datetime.now().isoformat()))
        conn.commit()
        st.rerun()
