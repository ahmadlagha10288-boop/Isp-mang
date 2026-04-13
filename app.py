import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Admin", layout="wide")

# تصميم CSS بسيط وواضح
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 5px solid #007bff; border-bottom: 1px solid #333; }
    .client-name { font-size: 1.1rem; font-weight: bold; color: #fff; }
    .info-line { font-size: 0.9rem; color: #ccc; margin: 4px 0; }
    .wa-btn { display: block; width: 100%; padding: 8px; text-align: center; border-radius: 5px; text-decoration: none !important; font-weight: bold; font-size: 0.85rem; color: white !important; margin-top: 5px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الشيت "خام" (Raw) بدون أسماء أعمدة
        df = pd.read_csv(url, header=None)
        
        # حذف الأسطر اللي كلها فاضية
        df = df.dropna(how='all').reset_index(drop=True)
        
        # فلترة ذكية: تجاهل الأسطر اللي فيها كلمات "Action" أو "Radius"
        # هيدي بتنظف العناوين اللي طالعة بالصور عندك
        df = df[~df.iloc[:, 0].astype(str).str.contains('Action|Radius|Name|nan', case=False)]
        
        # ترتيب حسب التاريخ (العمود الرابع D - Index 3)
        # من الخالص (القديم) للجديد
        try:
            df[3] = pd.to_datetime(df[3], errors='coerce')
            df = df.sort_values(by=3, ascending=True)
        except:
            pass
            
        return df
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار المشتركين")

if df.empty:
    st.warning("⚠️ لم يتم العثور على بيانات. تأكد من تحديث ملف الجوجل شيت.")
else:
    search = st.text_input("🔍 بحث عن اسم أو رقم:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # عرض البيانات
    for idx, row in df.iterrows():
        # A=0 (الاسم), B=1 (الحالة), C=2 (الخدمة), D=3 (التاريخ), E=4 (السعر), F=5 (التلفون)
        name = str(row[0])
        status = str(row[1])
        service = str(row[2])
        date_val = str(row[3])
        price = str(row[4])
        phone = str(row[5]).replace('.0', '').strip()

        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-line">🟢 الحالة: {status} | 🛠️ الخدمة: {service}</div>
                    <div class="info-line">💰 السعر: ${price} | 📅 التاريخ: {date_val}</div>
            """, unsafe_allow_html=True)
            
            # أزرار الواتساب
            if phone != 'nan' and len(phone) > 5:
                # التأكد من مفتاح لبنان
                full_phone = f"961{phone}" if not phone.startswith('961') else phone
                
                m1 = quote(f"تنبيه: اشتراكك ({service}) ينتهي قريباً.")
                m2 = quote(f"يرجى تسديد مبلغ ${price} لتجديد الخدمة.")
                m3 = quote(f"تحذير: سيتم إيقاف الخدمة لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# أزرار جانبية
if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
