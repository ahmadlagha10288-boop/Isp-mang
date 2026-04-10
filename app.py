import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# إعداد الصفحة
st.set_page_config(page_title="ISP Pro Manager", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, last_auto_bill TEXT)''')
conn.commit()

# قائمة الأسعار الثابتة
PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinum": 40, "diamond": 50, "platinum-ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

def send_whatsapp(phone, message):
    phone = "".join(filter(str.isdigit, str(phone)))
    if not phone.startswith('961'): phone = '961' + phone
    url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
    return url

st.title("📡 نظام الإدارة الشامل")

file = st.file_uploader("ارفع ملف Radius 2.csv")

if file:
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    date_col = 'Expiry Date'
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # --- نظام زيادة الدين التلقائي شهرياً ---
    today_str = datetime.now().strftime('%Y-%m')
    for _, r in df.iterrows():
        user = str(r['Username'])
        price = get_price(r['Service'])
        exp_date = r[date_col]
        c.execute("SELECT debt, last_auto_bill FROM billing WHERE username=?", (user,))
        db_row = c.fetchone() or (0, "")
        if pd.notna(exp_date) and exp_date <= datetime.now() and db_row[1] != today_str:
            c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount, last_auto_bill) VALUES (?, ?, ?, ?)", 
                      (user, db_row[0] + price, 0, today_str))
    conn.commit()

    # --- الفلاتر ---
    st.sidebar.header("🔍 فلاتر العرض")
    view_type = st.sidebar.radio("عرض حسب الدفع:", ["الكل", "المدفوع فقط", "عليه دين"])

    # الإحصائيات
    c.execute("SELECT SUM(debt), SUM(paid_amount) FROM billing")
    totals = c.fetchone()
    st.info(f"💰 ديون السوق: **${totals[0] or 0}** | ✅ جباية الكاش: **${totals[1] or 0}**")

    rows = []
    now = datetime.now()
    for _, r in df.iterrows():
        user = str(r['Username'])
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        debt = (c.fetchone() or (0,))[0]
        if view_type == "المدفوع فقط" and debt > 0: continue
        if view_type == "عليه دين" and debt == 0: continue
        
        exp = r[date_col]
        status = "🔴" if pd.notna(exp) and exp < now else "🔵" if pd.notna(exp) and exp < (now + timedelta(days=3)) else "🟢"
        
        rows.append({"ح": status, "المشترك": user, "تاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??", "الدين": f"${debt}"})

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # --- إدارة المشترك والديون القديمة ---
    st.subheader("⚙️ إدارة المشترك والرسائل")
    target = st.selectbox("اختر اسم الزبون لتعديل حسابه:", [""] + [r['المشترك'] for r in rows])
    
    if target:
        row_data = df[df['Username'] == target].iloc[0]
        phone = row_data.get('Mobile Number', row_data.get('Phone Number', ''))
        price = get_price(row_data['Service'])
        c.execute("SELECT debt FROM billing WHERE username=?", (target,))
        curr_debt = c.fetchone()[0]

        st.warning(f"الزبون: **{target}** | الحساب الحالي: **${curr_debt}**")

        # ميزة زيادة الحساب القديم (اللي سألت عنها)
        with st.expander("➕ إضافة مبلغ قديم / دين سابق"):
            old_amt = st.number_input("ادخل المبلغ القديم لزيادته:", min_value=0.0, step=1.0)
            if st.button("تأكيد إضافة المبلغ"):
                c.execute("UPDATE billing SET debt = debt + ? WHERE username = ?", (old_amt, target))
                conn.commit()
                st.success(f"تمت إضافة ${old_amt} لحساب {target}")
                st.rerun()

        # أزرار الواتساب الأربعة
        st.markdown("---")
        st.write("📲 أزرار التواصل:")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.link_button("⏳ قرب ينتهي", send_whatsapp(phone, f"مرحباً {target}، اشتراكك بيخلص خلال يومين."))
        with col2: st.link_button("🚫 انتهى", send_whatsapp(phone, f"عزيزي {target}، انتهى اشتراكك اليوم."))
        with col3: st.link_button("💸 تذكير دين", send_whatsapp(phone, f"تذكير: المبلغ المستحق بذمتكم هو ${curr_debt}."))
        with col4: st.link_button("✅ تم التشريج", send_whatsapp(phone, f"تم تجديد حسابك. المبلغ الإجمالي: ${curr_debt}."))

        # زر القبض السريع
        if st.button(f"💰 تسجيل قبض ${price} حالياً", type="primary"):
            c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (price, price, target))
            conn.commit()
            st.rerun()
