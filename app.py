import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import os

# --- 1. إعداد الصفحة الأساسي ---
st.set_page_config(page_title="ISP Ultimate Manager", layout="wide")

# --- 2. إعداد قاعدة البيانات ---
DB_FILE = 'isp_debts.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, 
              service TEXT, expiry_date TEXT, phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, time TEXT)''')
conn.commit()

# --- 3. نظام اللغات (Translations) ---
LANG = {
    "ar": {
        "title": "📡 نظام إدارة الشبكة الاحترافي",
        "upload": "ارفع ملف Radius 2.csv لتحديث البيانات",
        "sidebar_head": "📂 القائمة الرئيسية",
        "filter": "تصفية الجدول حسب:",
        "filter_all": "الكل", "filter_debt": "عليه دين فقط", "filter_paid": "خالصين",
        "ops": "⚙️ عمليات جماعية",
        "add_month": "🚨 زيادة شهر للكل (تأسيس)",
        "group_msgs": "📢 رسائل الجروب الجماعية",
        "debt_msg_btn": "📝 نص قائمة الديون",
        "exp_msg_btn": "📝 نص المنتهيين",
        "safety": "💾 الأمان والنسخ الاحتياطي",
        "backup_btn": "📥 تحميل نسخة احتياطية (Backup)",
        "stats_head": "📊 خلاصة حالة الشبكة",
        "stat_debt": "💰 ديون السوق", "stat_exp": "🔴 منتهي", "stat_active": "🟢 شغال",
        "table_status": "ح", "table_user": "المشترك", "table_date": "تاريخ", "table_debt": "الدين",
        "manage_user": "⚙️ إدارة العمليات لمشترك محدد",
        "select_user": "اختر مشترك من القائمة:",
        "debt_info": "الدين الحالي للزبون:",
        "pay_btn": "✅ تسجيل قبض اشتراك",
        "add_debt_btn": "➕ إضافة دين/حساب سابق",
        "reset_btn": "🗑️ تصفير الحساب تماماً",
        "wa_remind": "💸 تذكير بالدين", "wa_done": "✅ تم التجديد",
        "logs_head": "📜 سجل آخر التحركات",
        "no_data": "قاعدة البيانات فارغة حالياً. يرجى رفع ملف CSV لأول مرة لتأسيس البيانات."
    },
    "en": {
        "title": "📡 Professional ISP Management System",
        "upload": "Upload Radius 2.csv to update/sync data",
        "sidebar_head": "📂 Main Menu",
        "filter": "Filter Table By:",
        "filter_all": "All", "filter_debt": "Debt Only", "filter_paid": "Clear",
        "ops": "⚙️ Bulk Operations",
        "add_month": "🚨 Add Month to Everyone",
        "group_msgs": "📢 Group Messages",
        "debt_msg_btn": "📝 Copy Debt List",
        "exp_msg_btn": "📝 Copy Expired List",
        "safety": "💾 Security & Backup",
        "backup_btn": "📥 Download Database Backup",
        "stats_head": "📊 Network Dashboard",
        "stat_debt": "💰 Total Market Debt", "stat_exp": "🔴 Expired", "stat_active": "🟢 Active",
        "table_status": "S", "table_user": "Username", "table_date": "Date", "table_debt": "Debt",
        "manage_user": "⚙️ Specific User Management",
        "select_user": "Select a user from list:",
        "debt_info": "Customer's Current Debt:",
        "pay_btn": "✅ Record Subscription Payment",
        "add_debt_btn": "➕ Add Previous Debt",
        "reset_btn": "🗑️ Reset Account to $0",
        "wa_remind": "💸 Debt Reminder", "wa_done": "✅ Renewal Sent",
        "logs_head": "📜 System Action Logs",
        "no_data": "Database is empty. Please upload a CSV to initialize."
    }
}

# --- 4. إعدادات القائمة الجانبية ---
st.sidebar.subheader("🌐 Language / اللغة")
lang_choice = st.sidebar.selectbox("Select Language", ["Arabic", "English"])
ln = "ar" if lang_choice == "Arabic" else "en"
t = LANG[ln]

# --- 5. دالات المساعدة (Helper Functions) ---
def add_log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.execute("INSERT INTO logs (action, time) VALUES (?, ?)", (msg, now))
    conn.commit()

def send_whatsapp(phone, message):
    phone = "".join(filter(str.isdigit, str(phone))) if phone else ""
    if phone and not phone.startswith('961'): phone = '961' + phone
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinum": 40, "diamond": 50, "platinum-ise": 60}
def get_price(service):
    s = str(service).lower() if service else ""
    for k, v in PRICES.items():
        if k in s: return v
    return 0

# --- 6. واجهة المستخدم الرئيسية ---
st.title(t["title"])

# رفع الملف للتحديث
file = st.file_uploader(t["upload"])
if file:
    df_upload = pd.read_csv(file)
    df_upload.columns = [col.strip() for col in df_upload.columns]
    date_col = 'Expiry Date'
    phone_col = 'Mobile Number' if 'Mobile Number' in df_upload.columns else 'Phone Number'
    
    for _, r in df_upload.iterrows():
        u, s, e = str(r['Username']), str(r['Service']), str(r[date_col])
        p = str(r[phone_col]) if phone_col in df_upload.columns else ""
        c.execute('''INSERT INTO billing (username, service, expiry_date, phone) VALUES (?, ?, ?, ?)
                     ON CONFLICT(username) DO UPDATE SET service=excluded.service, expiry_date=excluded.expiry_date, phone=excluded.phone''', (u, s, e, p))
    conn.commit()
    st.success("✅ Database Synced Successfully / تم تحديث قاعدة البيانات بنجاح")

# جلب البيانات من الداتابيز
db_df = pd.read_sql_query("SELECT * FROM billing", conn)

if not db_df.empty:
    db_df['expiry_date'] = pd.to_datetime(db_df['expiry_date'], errors='coerce')
    now = datetime.now()

    # --- القائمة الجانبية ---
    st.sidebar.divider()
    st.sidebar.header(t["sidebar_head"])
    
    # فلتر التصفية
    view_filter = st.sidebar.radio(t["filter"], [t["filter_all"], t["filter_debt"], t["filter_paid"]])
    
    st.sidebar.divider()
    
    # عمليات جماعية
    st.sidebar.subheader(t["ops"])
    if st.sidebar.button(t["add_month"]):
        for _, r in db_df.iterrows():
            p = get_price(r['service'])
            c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (p, r['username']))
        conn.commit()
        add_log(f"Added month to all ({len(db_df)} users)")
        st.sidebar.success("Done / تم")
        st.rerun()

    st.sidebar.divider()

    # رسائل الجروب
    st.sidebar.subheader(t["group_msgs"])
    c.execute("SELECT username, debt FROM billing WHERE debt > 0")
    debtors = c.fetchall()
    if st.sidebar.button(t["debt_msg_btn"]):
        msg = f"💸 {t['stat_debt']}:\n" + "\n".join([f"- {d[0]}: ${d[1]}" for d in debtors])
        st.sidebar.text_area("Copy this:", msg, height=150)

    expired_names = db_df[db_df['expiry_date'] < now]['username'].tolist()
    if st.sidebar.button(t["exp_msg_btn"]):
        msg = f"🚫 {t['stat_exp']}:\n" + "\n".join([f"- {un}" for un in expired_names])
        st.sidebar.text_area("Copy this:", msg, height=150)

    st.sidebar.divider()

    # البيك أب
    st.sidebar.subheader(t["safety"])
    with open(DB_FILE, "rb") as fp:
        st.sidebar.download_button(t["backup_btn"], data=fp, file_name=f"Backup_{datetime.now().strftime('%Y-%m-%d')}.db")

    # --- الإحصائيات الفوقية ---
    st.subheader(t["stats_head"])
    col1, col2, col3 = st.columns(3)
    c.execute("SELECT SUM(debt) FROM billing")
    total_debt = c.fetchone()[0] or 0
    col1.metric(t["stat_debt"], f"${total_debt}")
    col2.metric(t["stat_exp"], len(db_df[db_df['expiry_date'] < now]))
    col3.metric(t["stat_active"], len(db_df[db_df['expiry_date'] >= now]))

    # --- الجدول الرئيسي ---
    rows = []
    for _, r in db_df.iterrows():
        u, debt, exp = r['username'], r['debt'], r['expiry_date']
        if view_filter == t["filter_debt"] and debt <= 0: continue
        if view_filter == t["filter_paid"] and debt > 0: continue
        status = "🔴" if pd.notna(exp) and exp < now else "🟢"
        rows.append({t["table_status"]: status, t["table_user"]: u, t["table_date"]: exp.strftime('%d/%m') if pd.notna(exp) else "??", t["table_debt"]: f"${debt}"})
    
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # --- إدارة المشترك الفردي ---
    st.divider()
    st.subheader(t["manage_user"])
    target = st.selectbox(t["select_user"], [""] + [r[t["table_user"]] for r in rows])

    if target:
        c.execute("SELECT * FROM billing WHERE username=?", (target,))
        u_data = c.fetchone()
        # Columns: username(0), debt(1), paid(2), service(3), expiry(4), phone(5)
        curr_debt, service, phone = u_data[1], u_data[3], u_data[5]
        price = get_price(service)
        st.info(f"👤 {t['table_user']}: {target} | 💰 {t['debt_info']} ${curr_debt}")
        
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button(t["pay_btn"], type="primary", use_container_width=True):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?) WHERE username = ?", (price, target))
                add_log(f"Paid ${price} from {target}")
                conn.commit(); st.rerun()
        with b2:
            with st.popover(t["add_debt_btn"], use_container_width=True):
                val = st.number_input("Amount / المبلغ", step=1.0)
                if st.button("Confirm / تأكيد"):
                    c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (val, target))
                    add_log(f"Added ${val} debt to {target}")
                    conn.commit(); st.rerun()
        with b3:
            if st.button(t["reset_btn"], use_container_width=True):
                c.execute("UPDATE billing SET debt = 0 WHERE username = ?", (target))
                add_log(f"Reset {target} account")
                conn.commit(); st.rerun()

        st.write("📲 WhatsApp Notifications:")
        w1, w2 = st.columns(2)
        w1.link_button(t["wa_remind"], send_whatsapp(phone, f"تذكير: الحساب المطلوب هو ${curr_debt}"))
        w2.link_button(t["wa_done"], send_whatsapp(phone, f"تم تجديد اشتراكك بنجاح. الحساب الحالي: ${curr_debt}"))

    # --- سجل العمليات ---
    st.divider()
    st.subheader(t["logs_head"])
    st.table(pd.read_sql_query("SELECT action, time FROM logs ORDER BY id DESC LIMIT 5", conn))

else:
    st.warning(t["no_data"])
