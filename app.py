import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم الواجهة - تصغير الخطوط وترتيب الأزرار
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    .client-name { font-size: 1rem; font-weight: bold; color: white; margin-bottom: 5px; }
    .info-line { font-size: 0.85rem; color: #bbb; margin: 3px 0; }
    .wa-btn { display: block; width: 100%; padding: 8px; text-align: center; border-radius: 6px; text-decoration: none !important; font-weight: bold; font-size: 0.85rem; color: white !important; margin-top: 5px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف بدون عناوين لتجنب الضياع
        df = pd.read_csv(url, header=None)
        
        # تنظيف: حذف الأسطر اللي فيها كلمات تقنية أو فاضية
        df = df[df[0].notna()]
        df = df[~df[0].astype(str).str.contains('Action|Radius|Name|nan|Uptime', case=False)]
        
        # تحديد ترتيب الأعمدة: 0=الاسم، 1=الحالة، 2=الخدمة، 3=الوقت، 4=السعر، 5=التلفون
        df.columns = ['Name', 'Status', 'Service', 'Expiry', 'Price', 'Phone'] + list(df.columns[6:])
        
        # تحويل تاريخ الانتهاء وترتيبه (القديم أولاً يعني اللي بدو تجديد)
        df['Expiry'] = pd.to_datetime(df['Expiry'], errors='coerce')
        df = df.sort_values(by='Expiry', ascending=True)
        
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار المشتركين")

if df.empty:
    st.error("⚠️ لم نجد بيانات حقيقية. تأكد من أن الأسماء تبدأ من العمود A.") #
else:
    search = st.text_input("🔍 بحث سريع عن اسم:")
    if search:
        df = df[df['Name'].astype(str).str.contains(search, case=False)]

    for idx, row in df.iterrows():
        # استخراج البيانات حسب الترتيب الجديد
        name = row['Name']
        status = row['Status']
        service = row['Service']
        expiry_date = row['Expiry']
        price = row['Price']
        phone = str(row['Phone']).replace('.0', '').strip()

        # حساب الأيام المتبقية
        today = datetime.now()
        days_left = (expiry_date - today).days if pd.notnull(expiry_date) else "N/A"
        days_style = "color: #ff4b4b;" if str(days_left) != "N/A" and days_left <= 0 else "color: #2ecc71;"

        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-line">● <b>الحالة:</b> {status} | 🛠️ <b>الخدمة:</b> {service}</div>
                    <div class="info-line">📅 <b>تاريخ الانتهاء:</b> {expiry_date} (<span style="{days_style}">{days_left} يوم</span>)</div>
                    <div class="info-line">💰 <b>السعر المطلوب:</b> ${price}</div>
            """, unsafe_allow_html=True)
            
            # أزرار الواتساب
            if phone != 'nan' and len(phone) > 5:
                full_phone = f"961{phone}" if not phone.startswith('961') else phone
                m1 = quote(f"تنبيه: اشتراكك ({service}) ينتهي قريباً.")
                m2 = quote(f"يرجى تسديد مبلغ ${price} لتجديد الخدمة.")
                m3 = quote(f"تحذير نهائي: سيتم إيقاف الخدمة لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# التحديث اليدوي
if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
