import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# --- إعداد الصفحة ---
st.set_page_config(page_title="ISP Pro Ultimate System", layout="wide")

# --- تنسيق CSS لتحسين المظهر ---
st.markdown("""
    <style>
    div.stMetric { background-color: #0e1117; padding: 10px; border-radius: 10px; border: 1px solid #333; }
    .stTextArea textarea { color: #2ecc71 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, last_auto_bill TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, time TEXT)''')
conn.commit()

# --- دالات المساعدة ---
def add_log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.execute("INSERT INTO logs (action, time) VALUES (?, ?)", (msg, now))
    conn.commit()

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

# --- واجهة البرنامج ---
st.title("📡 نظام إدارة الشبكة الاحترافي")

file = st.file_uploader("ارفع ملف الـ Radius 2.csv الأحدث")

if file:
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    date_col = 'Expiry Date'
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    now = datetime.now()

    # --- القائمة الجانبية (Sidebar) ---
    st.sidebar.header("🛠 العمليات الجماعية")
    
    # 1. زر التأسيس (مرة واحدة في الشهر)
    if st.sidebar.button("🚨 زيادة شهر للكل (تأسيس الحسابات)"):
        count = 0
        for _, r in df.iterrows():
            u, p = str(r['Username']), get_price(r['Service'])
            c.execute("SELECT debt, paid_amount FROM billing WHERE username=?", (u,))
            res = c.fetchone() or (0,0)
            c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount) VALUES (?, ?, ?)", 
                      (u, res[0] + p, res[1]))
            count += 1
        conn.commit()
        add_log(f"تأسيس: تم زيادة شهر لجميع المشتركين ({count} مشترك)")
        st.sidebar.success(f"تمت العملية لـ {count} مشترك!")
        st.rerun()

    st.sidebar.divider()
    
    # 2. ميزة الرسائل الجماعية للجروب
    st.sidebar.subheader("📢 رسائل الجروب الجماعية")
    
    # تجميع بيانات الديون
    c.execute("SELECT username, debt FROM billing WHERE debt > 0")
    debtors = c.fetchall()
    if st.sidebar.button("📝 نص قائمة الديون للجروب"):
        if debtors:
            msg = "💸 قائمة الذمم المالية المطلوبة (يرجى التسديد):\n" + "\n".join([f"- {d[0]}: ${d[1]}" for d in debtors])
            st.sidebar.text_area("انسخ النص وابعته للجروب:", msg, height=200)
        else:
            st.sidebar.info("لا يوجد ديون حالياً.")

    # تجميع المنتهيين
    expired_list = df[df[date_col] < now]['Username'].tolist()
    if st.sidebar.button("📝 نص المنتهية اشتراكاتهم"):
        if expired_list:
            msg = "🚫 المشتركين المنتهية صلاحيتهم (الإنترنت مقطوع):\n" + "\n".join([f"- {u}" for u in expired_list])
            st.sidebar.text_area("انسخ النص وابعته للجروب:", msg, height=150)
        else:
            st.sidebar.info("لا يوجد اشتراكات منتهية.")

    st.sidebar.divider()
    view = st.sidebar.radio("تصفية الجدول حسب:", ["الكل", "عليه دين فقط", "خالصين"])

    # --- لوحة الأولويات (فوق الجدول) ---
    st.subheader("🚨 نظرة عامة على الشبكة")
    p_col1, p_col2, p_col3 = st.columns(3)
    
    expired_num = len(df[df[date_col] < now])
    near_expiry_num = len(df[(df[date_col] >= now) & (df[date_col] < now + timedelta(days=3))])
    c.execute("SELECT SUM(debt) FROM billing")
    total_market_debt = c.fetchone()[0] or 0
    
    p_col1.metric("🔴 منتهي حالياً", f"{expired_num}")
    p_col2.metric("🔵 بينتهي قريباً", f"{near_expiry_num}")
    p_col3.metric("💰 ديونك بالسوق", f"${total_market_debt}")

    st.divider()

    # --- جدول البيانات ---
    rows = []
    for _, r in df.iterrows():
        u = str(r['Username'])
        c.execute("SELECT debt FROM billing WHERE username=?", (u,))
        debt = (c.fetchone() or (0,))[0]
        
        if view == "عليه دين فقط" and debt == 0: continue
        if view == "خالصين" and debt > 0: continue
        
        exp = r[date_col]
        status = "🔴" if pd.notna(exp) and exp < now else "🔵" if pd.notna(exp) and exp < (now + timedelta(days=3)) else "🟢"
        rows.append({"ح": status, "المشترك": u, "تاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??", "الدين": f"${debt}"})
    
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # --- إدارة المشترك الفردي ---
    st.divider()
    st.subheader("⚙️ إدارة المشترك المحدد")
    target = st.selectbox("اختر اسم المشترك للتعامل معه:", [""] + [r['المشترك'] for r in rows])

    if target:
        u_row = df[df['Username'] == target].iloc[0]
        phone = u_row.get('Mobile Number', u_row.get('Phone Number', ''))
        price = get_price(u_row['Service'])
        c.execute("SELECT debt FROM billing WHERE username=?", (target,))
        curr_debt = c.fetchone()[0]

        st.info(f"المشترك: **{target}** | الخدمة: **{u_row['Service']}** | الحساب الحالي: **${curr_debt}**")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(f"✅ تسجيل قبض ${price}", type="primary", use_container_width=True):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (price, price, target))
                add_log(f"قبض ${price} من {target}")
                conn.commit()
                st.rerun()
        with c2:
            with st.popover("➕ إضافة دين قديم/سابق"):
                old_val = st.number_input("المبلغ:", step=1.0)
                if st.button("تأكيد الإضافة"):
                    c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (old_val, target))
                    add_log(f"إضافة مبلغ {old_val} لحساب {target}")
                    conn.commit()
                    st.rerun()
        with c3:
            if st.button("🗑️ تصفير الحساب تماماً", use_container_width=True):
                c.execute("UPDATE billing SET debt = 0 WHERE username = ?", (target,))
                add_log(f"تصفير حساب {target}")
                conn.commit()
                st.rerun()

        # أزرار الواتساب
        st.write("📲 مراسلة فورية:")
        w1, w2, w3, w4 = st.columns(4)
        w1.link_button("⏳ قرب الانتهاء", send_whatsapp(phone, f"مرحباً {target}، اشتراكك بيخلص خلال يومين."))
        w2.link_button("🚫 انتهى الاشتراك", send_whatsapp(phone, f"عزيزي {target}، انتهى اشتراكك اليوم. يرجى التجديد."))
        w3.link_button("💸 تذكير بالدفع", send_whatsapp(phone, f"تذكير: المبلغ المستحق بذمتكم هو ${curr_debt}."))
        w4.link_button("✅ تم التشريج", send_whatsapp(phone, f"تم تجديد حسابك. الحساب الحالي المطلوبة: ${curr_debt}."))

    # --- سجل العمليات ---
    st.divider()
    st.subheader("📜 آخر التحركات في السيستم")
    log_df = pd.read_sql_query("SELECT action as 'العملية', time as 'الوقت' FROM logs ORDER BY id DESC LIMIT 5", conn)
    st.table(log_df)
else:
    st.info("يرجى رفع ملف Radius 2.csv للبدء.")
