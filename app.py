import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم الواجهة لتكون احترافية وسهلة على الموبايل
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 6px solid #007bff; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .client-name { font-size: 1.2rem; font-weight: bold; color: #ffffff; margin-bottom: 8px; text-transform: capitalize; }
    .status-badge { font-size: 0.85rem; padding: 3px 8px; border-radius: 20px; font-weight: bold; }
    .online { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; }
    .expired { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; }
    .info-row { font-size: 0.95rem; color: #bdc3c7; margin: 5px 0; display: flex; align-items: center; }
    .wa-btn { display: block; width: 100%; padding: 12px; text-align: center; border-radius: 8px; text-decoration: none !important; font-weight: bold; font-size: 0.9rem; color: white !important; margin-top: 8px; transition: 0.3s; }
    .btn-warn { background-color: #f39c12; }
    .btn-pay { background-color: #d35400; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف بدون عناوين
        df = pd.read_csv(url, header=None)
        
        # الخطوة الأهم: تجاهل أول سطرين إذا كانت تحتوي على Radius أو Action
        # والبدء من البيانات الحقيقية
        df = df.iloc[1:] # تخطي السطر الأول (العناوين)
        
        # تسمية الأعمدة يدوياً بناءً على الصورة الحقيقية للإكسل
        # A=0(Name), B=1(Status), C=2(Service), D=3(Expiry Date), F=5(Phone)
        df = df.iloc[:, [0, 1, 2, 3, 5]] 
        df.columns = ['Name', 'Status', 'Service', 'Expiry', 'Phone']
        
        # تنظيف الأسماء من القيم الفارغة أو الكلمات التقنية
        df = df[df['Name'].notna()]
        df = df[~df['Name'].astype(str).str.contains('Radius|Action|Name|nan', case=False)]
        
        # تحويل التاريخ وترتيبه (المنتهي أولاً)
        df['Expiry'] = pd.to_datetime(df['Expiry'], errors='coerce')
        df = df.sort_values(by='Expiry', ascending=True)
        
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"حدث خطأ في قراءة الملف: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.error("⚠️ لم نتمكن من عرض البيانات. يرجى التأكد من أن الأسماء تبدأ من العمود A في الجوجل شيت.")
else:
    search = st.text_input("🔍 ابحث عن اسم المشترك:")
    if search:
        df = df[df['Name'].astype(str).str.contains(search, case=False)]

    for _, row in df.iterrows():
        name = str(row['Name'])
        status = str(row['Status'])
        service = str(row['Service'])
        expiry = row['Expiry']
        phone = str(row['Phone']).replace('.0', '').strip()
        
        # تحديد لون الحالة
        st_class = "online" if "Online" in status else "expired"
        exp_str = expiry.strftime('%Y-%m-%d') if pd.notnull(expiry) else "غير محدد"
        
        # عرض الكرت
        st.markdown(f"""
            <div class="card">
                <div class="client-name">{name}</div>
                <div class="info-row">📍 الحالة: <span class="status-badge {st_class}">{status}</span></div>
                <div class="info-row">🛠️ الخدمة: {service}</div>
                <div class="info-row">📅 تاريخ الانتهاء: {exp_str}</div>
        """, unsafe_allow_html=True)
        
        # أزرار التواصل (العمود F)
        if phone != 'nan' and len(phone) > 5:
            full_phone = f"961{phone}" if not phone.startswith('961') else phone
            msg1 = quote(f"تذكير: اشتراكك {service} ينتهي في {exp_str}. لتجنب الانقطاع يرجى التجديد.")
            msg2 = quote(f"طلب دفع: المشترك {name}، يرجى تسديد الحساب لتجديد باقة {service}.")
            
            st.markdown(f'<a href="https://wa.me/{full_phone}?text={msg1}" class="wa-btn btn-warn">⚠️ تنبيه انتهاء</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://wa.me/{full_phone}?text={msg2}" class="wa-btn btn-pay">💸 طلب دفع</a>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# التحديث اليدوي
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
