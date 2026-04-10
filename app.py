import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import os

# --- إعداد الصفحة ---
st.set_page_config(page_title="ISP Pro - Final Edition", layout="wide")

# --- قاعدة البيانات (حفظ دائم) ---
DB_FILE = 'isp_debts.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, 
              service TEXT, expiry_date TEXT, phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, time TEXT)''')
conn.commit()

# --- دالات المساعدة ---
def add_log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.execute("INSERT INTO logs (action, time) VALUES (?, ?)", (msg, now))
    conn.commit()

def send_whatsapp(phone, message):
    phone = "".join(filter(str.isdigit, str(phone))) if phone else ""
    if not phone.startswith('961') and phone != "": phone = '961' + phone
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinum": 40, "diamond": 50, "platinum-ise": 60}
def get_price(service):
    s = str(service).lower() if service else ""
    for k, v in PRICES.items():
        if k in s: return v
    return 0

# --- واجهة البرنامج ---
st.title("📡 نظام الإدارة المتكامل (الحفظ الدائم)")

# 1. رفع الملف للتحديث (اختياري)
file = st.file_uploader("ارفع ملف Radius 2.csv لتحديث الأسماء والتواريخ")

if file:
    df_upload = pd.read_csv(file)
    df_upload.columns = [col.strip() for col in df_upload.columns]
    date_col = 'Expiry Date'
    phone_col = 'Mobile Number' if 'Mobile Number' in df_upload.columns else 'Phone Number'
    
    for _, r in df_upload.iterrows():
        u = str(r['Username'])
        s = str(r['Service'])
        e = str(r[date_col])
        p = str(r[phone_col]) if phone_col in df_upload.columns else ""
        
        # تحديث البيانات (ON CONFLICT لإبقاء الدين القديم كما هو)
        c.execute('''INSERT INTO billing (username, service, expiry_date, phone) VALUES (?, ?, ?, ?)
                     ON CONFLICT(username) DO UPDATE SET service=excluded.service, expiry_date=excluded.expiry_date, phone=excluded.phone''', (u, s, e, p))
    conn.commit()
    st.success("✅ تم تحديث قاعدة البيانات من الملف!")

# 2. جلب البيانات المخزنة
db_df = pd.read_sql_query("SELECT * FROM billing", conn)

if not db_df.empty:
    db_df['expiry_date'] = pd.to_datetime(db_df['expiry_date'], errors='coerce')
    now = datetime.now()

    # --- القائمة الجانبية (Sidebar) ---
    st.sidebar.header("💾 الأمان والعمليات")
    
    # زر البيك اب (Backup)
    with open(DB_FILE, "rb") as fp:
        st.sidebar.download_button(
            label="📥 تحميل نسخة احتياطية (Backup)",
            data=fp,
            file_name=f"ISP_Backup_{datetime.now().strftime('%Y-%m-%d')}.db",
            mime="application/x-sqlite3"
        )
    
    st.sidebar.divider()
    
    if st.sidebar.button("🚨 زيادة شهر للكل"):
        for _, r in db_df.iterrows():
            price = get_price(r['service'])
            c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (price, r['username']))
        conn.commit()
        add_log("زيادة شهر لجميع المشتركين")
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("📢 رسائل جماعية")
    c.execute("SELECT username, debt FROM billing WHERE debt > 0")
    debtors = c.fetchall()
    if st.sidebar.button("📝 نص الديون للجروب"):
        msg = "💸 قائمة الذمم المالية:\n" + "\n".join([f"- {d[0]}: ${d[1]}" for d in debtors])
        st.sidebar.text_area("انسخ النص:", msg, height=150)

    # --- الإحصائيات ---
    st.subheader("📊 إحصائيات السوق")
    c1, c2, c3 = st.columns(3)
    c.execute("SELECT SUM(debt) FROM billing")
    total_debt = c.fetchone()[0] or 0
    c1.metric("💰 إجمالي الديون", f"${total_debt}")
    c2.metric("🔴 منتهي", len(db_df[db_df['expiry_date'] < now]))
    c3.metric("🟢 شغال", len(db_df[db_df['expiry_date'] >= now]))

    # --- الجدول ---
    rows = []
    for _, r in db_df.iterrows():
        u, debt, exp = r['username'], r['debt'], r['expiry_date']
        status = "🔴" if pd.notna(exp) and exp < now else "🟢"
        rows.append({"ح": status, "المشترك": u, "تاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??", "الدين": f"${debt}"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # --- إدارة المشترك ---
    st.divider()
    target = st.selectbox("إدارة مشترك محدد:", [""] + [r['المشترك'] for r in rows])

    if target:
        c.execute("SELECT * FROM billing WHERE username=?", (target,))
        u_data = c.fetchone()
        curr_debt, service, phone = u_data[1], u_data[3], u_data[5]
        price = get_price(service)

        st.info(f"الزبون: **{target}** | الدين الحالي: **${curr_debt}**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"✅ قبض ${price}", type="primary"):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?) WHERE username = ?", (price, target))
                add_log(f"قبض {price} من {target}")
                conn.commit()
                st.rerun()
        with col2:
            with st.popover("➕ إضافة دين"):
                val = st.number_input("المبلغ:", step=1.0)
                if st.button("تأكيد"):
                    c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (val, target))
                    conn.commit()
                    st.rerun()
        with col3:
            if st.button("🗑️ تصفير"):
                c.execute("UPDATE billing SET debt = 0 WHERE username = ?", (target,))
                conn.commit()
                st.rerun()

        st.write("📲 واتساب سريع:")
        w1, w2 = st.columns(2)
        w1.link_button("💸 تذكير بالدين", send_whatsapp(phone, f"تذكير: المبلغ المطلوب هو ${curr_debt}"))
        w2.link_button("✅ تم التجديد", send_whatsapp(phone, f"تم تجديد اشتراكك. الحساب: ${curr_debt}"))

    # --- السجل ---
    st.divider()
    st.subheader("📜 آخر العمليات")
    st.table(pd.read_sql_query("SELECT action as 'العملية', time as 'الوقت' FROM logs ORDER BY id DESC LIMIT 5", conn))

else:
    st.warning("البرنامج فارغ. يرجى رفع ملف CSV لأول مرة لتخزين البيانات.")
