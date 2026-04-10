import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# --- إعداد الصفحة ---
st.set_page_config(page_title="ISP Pro Ultimate", layout="wide")

# --- قاعدة البيانات (المشتركين + السجل) ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, last_auto_bill TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, time TEXT)''')
conn.commit()

# --- دالة إضافة سجل ---
def add_log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.execute("INSERT INTO logs (action, time) VALUES (?, ?)", (msg, now))
    conn.commit()

# --- دالة الواتساب ---
def send_whatsapp(phone, message):
    phone = "".join(filter(str.isdigit, str(phone)))
    if not phone.startswith('961'): phone = '961' + phone
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinum": 40, "diamond": 50, "platinum-ise": 60}
def get_price(service):
    s = str(service).lower() if pd.notna(service) else ""
    for k, v in PRICES.items():
        if k in s: return v
    return 0

st.title("🚀 النظام الاحترافي المتكامل")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    date_col = 'Expiry Date'
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    now = datetime.now()

    # --- 1. قسم الأولويات (Action Center) ---
    st.subheader("🚨 لوحة الأولويات")
    p_col1, p_col2, p_col3 = st.columns(3)
    
    expired_count = len(df[df[date_col] < now])
    near_expiry = len(df[(df[date_col] >= now) & (df[date_col] < now + timedelta(days=3))])
    
    p_col1.metric("🔴 منتهي الاشتراك", f"{expired_count} زبائن")
    p_col2.metric("🔵 قريب ينتهي (3 أيام)", f"{near_expiry} زبائن")
    
    c.execute("SELECT SUM(debt) FROM billing")
    total_market_debt = c.fetchone()[0] or 0
    p_col3.metric("💰 إجمالي ديون السوق", f"${total_market_debt}")

    st.divider()

    # --- 2. الجدول والفلترة ---
    st.sidebar.header("🔍 التحكم")
    view = st.sidebar.radio("تصفية الجدول:", ["الكل", "عليه دين", "خالصين"])
    
    if st.sidebar.button("🚨 تسجيل شهر جديد للجميع"):
        for _, r in df.iterrows():
            u, p = str(r['Username']), get_price(r['Service'])
            c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (p, u))
        add_log("تم تسجيل شهر جديد لجميع المشتركين")
        conn.commit()
        st.rerun()

    rows = []
    for _, r in df.iterrows():
        u = str(r['Username'])
        c.execute("SELECT debt FROM billing WHERE username=?", (u,))
        debt = (c.fetchone() or (0,))[0]
        if view == "عليه دين" and debt == 0: continue
        if view == "خالصين" and debt > 0: continue
        
        exp = r[date_col]
        status = "🔴" if pd.notna(exp) and exp < now else "🔵" if pd.notna(exp) and exp < (now + timedelta(days=3)) else "🟢"
        rows.append({"ح": status, "المشترك": u, "تاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??", "الدين": f"${debt}"})

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # --- 3. إدارة الزبون والرسائل الذكية ---
    st.divider()
    st.subheader("⚙️ إدارة العمليات")
    target = st.selectbox("اختر اسم الزبون:", [""] + [r['المشترك'] for r in rows])

    if target:
        u_row = df[df['Username'] == target].iloc[0]
        phone = u_row.get('Mobile Number', u_row.get('Phone Number', ''))
        price = get_price(u_row['Service'])
        c.execute("SELECT debt FROM billing WHERE username=?", (target,))
        curr_debt = c.fetchone()[0]

        st.info(f"الزبون: **{target}** | الدين الحالي: **${curr_debt}**")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button(f"✅ قبض ${price}", use_container_width=True):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (price, price, target))
                add_log(f"قبض ${price} من {target}")
                conn.commit()
                st.rerun()
        with c2:
            with st.popover("➕ إضافة دين قديم"):
                amt = st.number_input("المبلغ:", step=1.0)
                if st.button("تأكيد الإضافة"):
                    c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (amt, target))
                    add_log(f"إضافة دين ${amt} لـ {target}")
                    conn.commit()
                    st.rerun()
        with c3:
            if st.button("🗑️ تصفير الدين", use_container_width=True):
                c.execute("UPDATE billing SET debt = 0 WHERE username = ?", (target,))
                add_log(f"تصفير حساب {target}")
                conn.commit()
                st.rerun()

        # أزرار الواتساب الأربعة
        st.write("📲 تنبيهات الواتساب:")
        w1, w2, w3, w4 = st.columns(4)
        w1.link_button("⏳ قرب يخلص", send_whatsapp(phone, f"مرحباً {target}، اشتراكك ينتهي خلال يومين."))
        w2.link_button("🚫 انتهى الاشتراك", send_whatsapp(phone, f"عزيزي {target}، لقد انتهى اشتراكك اليوم."))
        w3.link_button("💸 تذكير بالدفع", send_whatsapp(phone, f"تذكير: المبلغ المستحق بذمتكم هو ${curr_debt}."))
        w4.link_button("✅ تم التشريج", send_whatsapp(phone, f"تم تجديد اشتراكك بنجاح. الحساب الحالي: ${curr_debt}."))

    # --- 4. سجل العمليات (Action Log) ---
    st.divider()
    st.subheader("📜 سجل آخر العمليات")
    log_data = pd.read_sql_query("SELECT action as 'العملية', time as 'الوقت' FROM logs ORDER BY id DESC LIMIT 5", conn)
    st.table(log_data)
