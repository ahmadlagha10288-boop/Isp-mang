import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم CSS لترتيب الكروت وتصغير الخط
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    .client-name { font-size: 1.1rem; font-weight: bold; color: white; margin-bottom: 5px; }
    .info-line { font-size: 0.85rem; color: #bbb; margin: 3px 0; }
    .wa-btn { display: block; width: 100%; padding: 10px; text-align: center; border-radius: 6px; text-decoration: none !important; font-weight: bold; font-size: 0.9rem; color: white !important; margin-top: 5px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الداتا بدون الاعتماد على أي عناوين موجودة بالشيت
        df = pd.read_csv(url, header=None)
        
        # تنظيف: حذف الأسطر اللي فيها كلمات "Action" أو "Radius" أو "Name"
        # هيدا السطر هو اللي بيمنع "الخربطة" اللي شفتها بالصورة
        df = df[~df.iloc[:, 0].astype(str).str.contains('Action|Radius|Name|nan', case=False)]
        df = df[df.iloc[:, 0].notna()] # حذف الأسطر الفاضية
        
        # تحويل التاريخ (العمود الرابع - Index 3) للترتيب
        try:
            df[3] = pd.to_datetime(df[3], errors='coerce')
            df = df.sort_values(by=3, ascending=True)
        except:
            pass
            
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار المشتركين")

if df.empty:
    st.warning("⚠️ لا يوجد بيانات لعرضها. تأكد من ملف الجوجل شيت.")
else:
    search = st.text_input("🔍 بحث سريع:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    for idx, row in df.iterrows():
        # الترتيب حسب طلبك:
        name = str(row[0])      # العمود A
        status = str(row[1])    # العمود B
        service = str(row[2])   # العمود C
        reg_date = str(row[3])  # العمود D
        price = str(row[4])     # العمود E
        phone = str(row[5]).replace('.0', '').strip() # العمود F

        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-line">● <b>الحالة:</b> {status} | 🛠️ <b>الخدمة:</b> {service}</div>
                    <div class="info-line">📅 <b>وقت التشريج:</b> {reg_date}</div>
                    <div class="info-line">💰 <b>السعر:</b> ${price}</div>
            """, unsafe_allow_html=True)
            
            # أزرار الواتساب باستخدام رقم التلفون من كولون F
            if phone != 'nan' and len(phone) > 5:
                # إضافة مفتاح لبنان إذا مش موجود
                full_phone = f"961{phone}" if not phone.startswith('961') else phone
                
                m1 = quote(f"تنبيه: اشتراكك ({service}) قارب على الانتهاء.")
                m2 = quote(f"يرجى تسديد مبلغ ${price} لتجديد الخدمة.")
                m3 = quote(f"تحذير نهائي: سيتم إيقاف الخدمة لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# أزرار التحديث والنسخ الجانبية
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

csv = df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Backup (CSV)", csv, "FutureNet_Backup.csv")
