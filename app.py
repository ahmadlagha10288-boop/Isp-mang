import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="Future Net Pro", layout="wide")

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
        # قراءة الملف خام تماماً
        df = pd.read_csv(url, header=None)
        
        # تصفية: حذف أي سطر فيه كلمات تعريفية أو فاضي
        df = df[df[0].notna()]
        df = df[~df[0].astype(str).str.contains('Action|Radius|Name|nan|Uptime|Total', case=False)]
        
        # تثبيت ترتيب الأعمدة: 0=A(الاسم), 1=B(الحالة), 2=C(الخدمة), 3=D(الوقت), 4=E(السعر), 5=F(التلفون)
        return df.reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.error("⚠️ الملف فارغ أو الرابط غير صحيح. تأكد من وجود بيانات في العمود A.")
else:
    # ترتيب حسب تاريخ التشريج (D - Index 3)
    try:
        df[3] = pd.to_datetime(df[3], errors='coerce')
        df = df.sort_values(by=3, ascending=True)
    except:
        pass

    search = st.text_input("🔍 بحث عن مشترك:")
    if search:
        df = df[df[0].astype(str).str.contains(search, case=False)]

    for idx, row in df.iterrows():
        # توزيع البيانات حسب طلبك
        name = str(row[0])    # A
        status = str(row[1])  # B
        service = str(row[2]) # C
        date = str(row[3])    # D
        price = str(row[4])   # E
        phone = str(row[5]).replace('.0', '').strip() # F

        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-line">● <b>الحالة:</b> {status} | 🛠️ <b>الخدمة:</b> {service}</div>
                    <div class="info-line">📅 <b>وقت التشريج:</b> {date}</div>
                    <div class="info-line">💰 <b>السعر:</b> ${price}</div>
            """, unsafe_allow_html=True)
            
            if phone != 'nan' and len(phone) > 5:
                # مفتاح لبنان
                num = f"961{phone}" if not phone.startswith('961') else phone
                m1 = quote(f"تنبيه: اشتراكك ({service}) قارب على الانتهاء.")
                m2 = quote(f"يرجى دفع ${price} للتجديد. شكراً.")
                m3 = quote(f"تحذير: سيتم قطع الخدمة لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{num}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{num}?text={m2}" class="wa-btn btn-2">💸 دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{num}?text={m3}" class="wa-btn btn-3">🚫 إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
