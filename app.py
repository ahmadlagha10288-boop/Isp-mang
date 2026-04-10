import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# --- إعداد الصفحة ---
st.set_page_config(page_title="ISP Pro Ultimate", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, last_auto_bill TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, time TEXT)''')
conn.commit()

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

st.title("🚀 النظام الاحترافي - مرحلة التأسيس")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    date_col = 'Expiry Date'
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    now = datetime.now()

    # --- القائمة الجانبية (الأزرار) ---
    st.sidebar.header("🛠 إعدادات الشهر الحالي")
    
    # الزر اللي بدك ياه هلق (لزيادة شهر للكل مرة واحدة)
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

    view = st.sidebar.radio("تصفية الجدول:", ["الكل", "عليه دين", "خالصين"])

    # --- الإحصائيات ---
    st.subheader("🚨 لوحة الأولويات")
    p_col1, p_col2, p_col3 = st.columns(3)
    expired_count = len(df[df[date_col] < now])
    near_expiry = len(df[(df[date_col] >= now) & (df[date_col] < now + timedelta(days=3))])
    c.execute("SELECT SUM(debt) FROM billing")
    total_market_debt = c.fetchone()[0] or 0
    p_col1.metric("🔴 منتهي الاشتراك", f"{expired_count}")
    p_col2.metric("🔵 قريب ينتهي", f"{near_expiry}")
    p_col3.metric("💰 ديون السوق", f"${total_market_debt}")

    st.divider()

    # --- الجدول ---
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

    # --- إدارة العمليات ---
    st.divider()
    st.subheader("⚙️ إدارة العمليات")
    target = st.selectbox("اختر الزبون لتسديد دفعة أو زيادة دين سابق:", [""] + [r['المشترك'] for r in rows])

    if target:
        u_row = df[df['Username'] == target].iloc[0]
        phone = u_row.get('Mobile Number', u_row.get('Phone Number', ''))
        price = get_price(u_row['Service'])
        c.execute("SELECT debt FROM billing WHERE username=?", (target,))
        curr_debt = c.fetchone()[0]

        st.info(f"الزبون: **{target}** | الحساب المطلوب: **${curr_debt}**")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(f"✅ تسجيل قبض ${price}", type="primary"):
                c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (price, price, target))
                add_log(f"قبض ${price} من {target}")
                conn.commit()
                st.rerun()
        with c2:
            with st.popover("➕ إضافة حساب سابق"):
                amt = st.number_input("المبلغ:", step=1.0)
                if st.button("تأكيد"):
                    c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (amt, target))
                    add_log(f"إضافة دين قديم ${amt} لـ {target}")
                    conn.commit()
                    st.rerun()
        with c3:
            if st.button("🗑️ تصفير الحساب"):
                c.execute("UPDATE billing SET debt = 0 WHERE username = ?", (target,))
                add_log(f"تصفير حساب {target}")
                conn.commit()
                st.rerun()

        st.write("📲 تنبيهات الواتساب:")
        w1, w2, w3, w4 = st.columns(4)
        w1.link_button("⏳ قرب يخلص", send_whatsapp(phone, f"مرحباً {target}، اشتراكك بيخلص خلال يومين."))
        w2.link_button("🚫 انتهى", send_whatsapp(phone, f"عزيزي {target}، انتهى اشتراكك اليوم."))
        w3.link_button("💸 تذكير دين", send_whatsapp(phone, f"تذكير: المبلغ المستحق بذمتكم هو ${curr_debt}."))
        w4.link_button("✅ تم التشريج", send_whatsapp(phone, f"تم تجديد حسابك. المبلغ المطلوب: ${curr_debt}."))

    st.divider()
    st.subheader("📜 سجل آخر العمليات")
    log_data = pd.read_sql_query("SELECT action as 'العملية', time as 'الوقت' FROM logs ORDER BY id DESC LIMIT 5", conn)
    st.table(log_data)
