import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة لتكون مريحة للنظر ومناسبة للموبايل والكمبيوتر
st.set_page_config(page_title="ISP Manager Pro", layout="wide")

# --- إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS billing 
                 (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0)''')
    # إضافة الأعمدة إذا لم تكن موجودة لتجنب الأخطاء
    try: c.execute("ALTER TABLE billing ADD COLUMN paid_amount REAL DEFAULT 0")
    except: pass
    conn.commit()
    return conn, c

conn, c = init_db()

# --- قائمة الأسعار الذكية ---
PRICES = {
    "bronze": 20, "silver": 25, "gold": 30, 
    "platinum": 40, "Diamond": 50, "platinum-lse": 60
}

def get_price(service_name):
    if pd.isna(service_name): return 0
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

def clean_phone(phone):
    p = "".join(filter(str.isdigit, str(phone)))
    if not p: return ""
    if p.startswith("961"): return p
    if len(p) == 8: return "961" + p
    return p

st.title("📡 نظام إدارة وحسابات الشبكة")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    
    # معالجة التاريخ والفرز (الأقدم فوق لتعرف مين خلص اشتراكه)
    expiry_col = 'Expired' if 'Expired' in df.columns else 'Expiration Date'
    if expiry_col in df.columns:
        df[expiry_col] = pd.to_datetime(df[expiry_col], dayfirst=True, errors='coerce')
        df = df.sort_values(by=expiry_col)

    # --- حسابات الإحصائيات (Dashboard) ---
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    res_sums = c.fetchone()
    market_debt = res_sums[0] if res_sums[0] else 0
    total_collected = res_sums[1] if res_sums[1] else 0

    st.markdown("### 📊 لوحة التحكم المالي")
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 ديون في السوق (إلك)", f"${market_debt:.1f}")
    m2.metric("✅ إجمالي الجباية (معك)", f"${total_collected:.1f}")
    m3.metric("👥 عدد الزبائن", len(df))

    st.markdown("---")
    search = st.text_input("🔍 ابحث عن اسم زبون:")

    # --- جدول الزبائن (تصميم مضغوط) ---
    # ترويسة بسيطة
    t1, t2, t3, t4 = st.columns([3, 1, 1, 1])
    t1.write("**المشترك / التاريخ**")
    t2.write("**السعر**")
    t3.write("**الدين**")
    t4.write("**أدوات**")

    for index, row in df.iterrows():
        user = row['Username']
        if search and search.lower() not in user.lower(): continue
        
        price = get_price(row['Service'])
        expiry = row.get(expiry_col, None)
        phone = clean_phone(row.get('Mobile Number', row.get('Phone Number', '')))
        
        c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        debt = res[0] if res else 0
        p_amount = res[1] if res else 0
        
        is_expired = pd.notna(expiry) and expiry < datetime.now()
        date_str = expiry.strftime('%d/%m') if pd.notna(expiry) else "??"

        with st.container():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                color = "#ff4b4b" if is_expired else "#2ecc71"
                st.markdown(f"<b style='color:{color}'>{user}</b> <small>({date_str})</small>", unsafe_allow_html=True)
            with c2:
                st.write(f"${price}")
            with c3:
                d_color = "red" if debt > 0 else "gray"
                st.markdown(f":{d_color}[**${debt}**]")
            with c4:
                # نافذة صغيرة للتحكم ليبقى الجدول مرتباً
                with st.popover("⚙️"):
                    st.write(f"الخدمة: {row['Service']}")
                    if st.button("✅ قبض الاشتراك", key=f"f_{user}"):
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                                  (user, max(0, debt - price), p_amount + price))
                        conn.commit()
                        st.rerun()
                    
                    amt = st.number_input("تعديل يدوي", key=f"edit_{user}", step=1.0)
                    if st.button("➕ زيادة", key=f"add_{user}"):
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (user, debt + amt, p_amount))
                        conn.commit()
                        st.rerun()
                    if st.button("➖ خصم", key=f"sub_{user}"):
                        c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (user, max(0, debt - amt), p_amount + amt))
                        conn.commit()
                        st.rerun()
                        
                    if phone:
                        msg = f"مرحباً {user}، تذكير بخصوص اشتراكك. إجمالي المطلوب: ${debt}."
                        st.markdown(f"[💬 واتساب](https://wa.me/{phone}?text={msg.replace(' ', '%20')})")

    # --- الأوامر الجانبية ---
    st.sidebar.header("⚙️ خيارات الإدارة")
    if st.sidebar.button("🚨 تسجيل اشتراك الشهر الجديد"):
        for _, r in df.iterrows():
            u = r['Username']
            p = get_price(r['Service'])
            c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
            res = c.fetchone()
            d = res[0] if res else 0
            pa = res[1] if res else 0
            c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", (u, d + p, pa))
        conn.commit()
        st.sidebar.success("تم تسجيل الديون!")
        st.rerun()

    if st.sidebar.button("🧹 تصفير الجباية (شهر جديد)"):
        c.execute("UPDATE billing SET paid_amount = 0")
        conn.commit()
        st.sidebar.info("تم تصفير عداد الجباية.")
        st.rerun()
