import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="ISP Pro Manager", layout="wide")

# --- قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL DEFAULT 0, paid_amount REAL DEFAULT 0, last_auto_bill TEXT)''')
conn.commit()

PRICES = {"bronze": 20, "silver": 25, "gold": 30, "platinum": 40, "diamond": 50, "platinum-ise": 60}

def get_price(service_name):
    s = str(service_name).lower()
    for k, v in PRICES.items():
        if k in s: return v
    return 0

def send_whatsapp(phone, message):
    # تنظيف الرقم
    phone = "".join(filter(str.isdigit, str(phone)))
    if not phone.startswith('961'): phone = '961' + phone
    url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
    return url

st.title("📡 نظام الإدارة الذكي - نسخة الاحتراف")

file = st.file_uploader("ارفع ملف Radius")

if file:
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    date_col = 'Expiry Date'
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # --- نظام زيادة الدين التلقائي عند الاستحقاق ---
    today_str = datetime.now().strftime('%Y-%m')
    for _, r in df.iterrows():
        user = str(r['Username'])
        price = get_price(r['Service'])
        exp_date = r[date_col]
        
        c.execute("SELECT debt, last_auto_bill FROM billing WHERE username=?", (user,))
        db_row = c.fetchone() or (0, "")
        
        # إذا استحق التاريخ ولم يتم تسجيل دين لهذا الشهر بعد
        if pd.notna(exp_date) and exp_date <= datetime.now() and db_row[1] != today_str:
            new_debt = db_row[0] + price
            c.execute("INSERT OR REPLACE INTO billing (username, debt, paid_amount, last_auto_bill) VALUES (?, ?, ?, ?)", 
                      (user, new_debt, 0, today_str))
    conn.commit()

    # --- الفلاتر (Filters) ---
    st.sidebar.header("🔍 فلاتر العرض")
    view_type = st.sidebar.radio("عرض حسب الدفع:", ["الكل", "المدفوع فقط", "غير المدفوع (عليه دين)"])

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

        # تطبيق الفلاتر
        if view_type == "المدفوع فقط" and debt > 0: continue
        if view_type == "غير المدفوع (عليه دين)" and debt == 0: continue

        exp = r[date_col]
        status = "🔴" if pd.notna(exp) and exp < now else "🟢"
        
        rows.append({
            "ح": status,
            "المشترك": user,
            "تاريخ": exp.strftime('%d/%m') if pd.notna(exp) else "??",
            "الدين": f"${debt}",
            "الرقم": r.get('Mobile Number', r.get('Phone Number', ''))
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # --- إدارة المشترك والرسائل الـ 4 ---
    st.subheader("⚙️ إدارة المشترك والرسائل")
    target = st.selectbox("اختر مشترك:", [""] + [r['المشترك'] for r in rows])
    
    if target:
        # جلب معلومات المشترك
        row_data = df[df['Username'] == target].iloc[0]
        phone = row_data.get('Mobile Number', row_data.get('Phone Number', ''))
        price = get_price(row_data['Service'])
        c.execute("SELECT debt FROM billing WHERE username=?", (target,))
        curr_debt = c.fetchone()[0]

        st.write(f"الزبون: **{target}** | الدين: **${curr_debt}**")

        # الـ 4 فقسات (الرسائل)
        col1, col2 = st.columns(2)
        with col1:
            # 1. قرب انتهاء الاشتراك
            msg1 = f"مرحباً {target}، نود تذكيرك بأن اشتراكك ينتهي خلال يومين. يرجى التجديد لضمان استمرار الخدمة."
            st.link_button("⏳ قرب الانتهاء (يومين)", send_whatsapp(phone, msg1))

            # 2. انتهاء الاشتراك
            msg2 = f"عزيزي {target}، لقد انتهى اشتراكك اليوم. يرجى التواصل معنا للتجديد."
            st.link_button("🚫 انتهى الاشتراك", send_whatsapp(phone, msg2))

        with col2:
            # 3. تذكير بالدفع
            msg3 = f"تذكير: يرجى تسديد المبلغ المستحق بذمتكم وقدره ${curr_debt} لخدمة الإنترنت."
            st.link_button("💸 تذكير بالدفع", send_whatsapp(phone, msg3))

            # 4. رسالة شحن الحساب
            msg4 = f"تم تجديد حسابك بنجاح. المبلغ المطلوب حالياً هو ${curr_debt}. شكراً لثقتكم."
            st.link_button("✅ تم التشريج (إعلام بالدين)", send_whatsapp(phone, msg4))

        # زر تسجيل دفعة
        if st.button(f"💰 تسجيل قبض ${price} من {target}", type="primary"):
            c.execute("UPDATE billing SET debt = MAX(0, debt - ?), paid_amount = paid_amount + ? WHERE username = ?", (price, price, target))
            conn.commit()
            st.success(f"تم قبض ${price}")
            st.rerun()
