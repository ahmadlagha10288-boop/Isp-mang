import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم الألوان والخطوط
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    .client-name { font-size: 1.1rem; font-weight: bold; color: #fff; margin-bottom: 5px; }
    .info-line { font-size: 0.9rem; color: #bbb; margin: 3px 0; }
    .wa-btn { display: block; width: 100%; padding: 10px; text-align: center; border-radius: 6px; text-decoration: none !important; font-weight: bold; font-size: 0.9rem; color: white !important; margin-top: 5px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف بدون أي مسميات أعمدة
        df = pd.read_csv(url, header=None)
        
        # تنظيف: شيل أي سطر العمود الأول فيه فاضي أو فيه كلمات متل Radius/Action
        df = df[df[0].notna()]
        df = df[~df[0].astype(str).str.contains('Action|Radius|Name|nan|Uptime', case=False)]
        
        # ترتيب يدوي للأعمدة حسب طلبك
        # 0=A, 1=B, 2=C, 3=D, 4=E, 5=F
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار المشتركين")

if df.empty:
    st.error("⚠️ لم نجد بيانات. تأكد من أن الأسماء تبدأ من الخانة A1.")
else:
    search = st.text_input("🔍 بحث عن اسم:")
    if search:
        df = df[df[0].astype(str).str.contains(search, case=False)]

    # الترتيب الزمني (حسب العمود D - Index 3)
    try:
        df[3] = pd.to_datetime(df[3], errors='coerce')
        df = df.sort_values(by=3, ascending=True)
    except:
        pass

    for idx, row in df.iterrows():
        # سحب البيانات بالترتيب الأبجدي للأعمدة
        name = str(row[0])    # A
        status = str(row[1])  # B
        service = str(row[2]) # C
        reg_date = str(row[3]) # D
        price = str(row[4])   # E
        phone = str(row[5]).replace('.0', '').strip() # F

        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-line">● <b>الحالة:</b> {status} | 🛠️ <b>الخدمة:</b> {service}</div>
                    <div class="info-line">📅 <b>تاريخ التشريج:</b> {reg_date}</div>
                    <div class="info-line">💰 <b>السعر:</b> ${price}</div>
            """, unsafe_allow_html=True)
            
            # أزرار الواتساب (باستخدام العمود F)
            if phone != 'nan' and len(phone) > 5:
                # مفتاح لبنان
                full_phone = f"961{phone}" if not phone.startswith('961') else phone
                
                m1 = quote(f"تنبيه: اشتراكك ({service}) قرب يخلص.")
                m2 = quote(f"يرجى دفع مبلغ ${price} للتجديد.")
                m3 = quote(f"تحذير: سيتم قطع الخط اليوم لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# زر التحديث الجانبي
if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
