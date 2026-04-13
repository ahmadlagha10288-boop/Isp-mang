import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم CSS لتحسين المظهر على الموبايل
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #007bff; }
    .client-name { font-size: 1.2rem; font-weight: bold; color: #fff; margin-bottom: 5px; }
    .status-online { color: #2ecc71; font-weight: bold; }
    .status-expired { color: #e74c3c; font-weight: bold; }
    .info-line { font-size: 0.95rem; color: #ccc; margin: 4px 0; }
    .wa-btn { display: block; width: 100%; padding: 10px; text-align: center; border-radius: 8px; text-decoration: none !important; font-weight: bold; font-size: 1rem; color: white !important; margin-top: 8px; }
    .btn-warn { background-color: #f39c12; } .btn-pay { background-color: #d35400; } .btn-stop { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        # قراءة الرابط من Secrets
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة بدون عناوين (header=None) لأن ملفك يبدأ بالبيانات فوراً
        df = pd.read_csv(url, header=None)
        
        # تسمية الأعمدة بناءً على الصورة المرسلة
        # A=0, B=1, C=2, D=3, E=4, F=5
        df = df.iloc[:, :7] # نأخذ أول 7 أعمدة
        df.columns = ['Name', 'Status', 'Service', 'Expiry', 'Speed', 'Phone', 'Extra']
        
        # تنظيف البيانات
        df = df.dropna(subset=['Name'])
        
        # تحويل التاريخ للترتيب (العمود D)
        df['Expiry'] = pd.to_datetime(df['Expiry'], errors='coerce')
        # ترتيب: المنتهي أولاً (الأقدم تاريخاً)
        df = df.sort_values(by='Expiry', ascending=True)
        
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.warning("⚠️ لم يتم العثور على بيانات. تأكد من رابط الجوجل شيت في الإعدادات.")
else:
    search = st.text_input("🔍 ابحث عن اسم الزبون:")
    if search:
        df = df[df['Name'].astype(str).str.contains(search, case=False)]

    for idx, row in df.iterrows():
        name = str(row['Name'])
        status = str(row['Status'])
        service = str(row['Service'])
        expiry = row['Expiry']
        phone = str(row['Phone']).replace('.0', '').strip()
        
        # تنسيق التاريخ والحالة
        expiry_str = expiry.strftime('%Y-%m-%d') if pd.notnull(expiry) else "N/A"
        status_class = "status-online" if "Online" in status else "status-expired"
        
        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-line">● الحالة: <span class="{status_class}">{status}</span></div>
                    <div class="info-line">🛠️ الخدمة: {service}</div>
                    <div class="info-line">📅 تاريخ الانتهاء: {expiry_str}</div>
            """, unsafe_allow_html=True)
            
            # أزرار الواتساب (تستخدم العمود F)
            if phone != 'nan' and len(phone) > 5:
                # إضافة مفتاح لبنان 961
                clean_phone = phone.replace(' ', '').replace('+', '')
                full_phone = f"961{clean_phone}" if not clean_phone.startswith('961') else clean_phone
                
                msg1 = quote(f"عزيزي {name}، اشتراكك {service} ينتهي بتاريخ {expiry_str}. يرجى التجديد.")
                msg2 = quote(f"تذكير بالدفع للمشترك {name}. القيمة المطلوبة لتجديد باقة {service}.")
                
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={msg1}" class="wa-btn btn-warn">⚠️ تنبيه اقتراب انتهاء</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={msg2}" class="wa-btn btn-pay">💸 طلب دفع فوري</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# زر التحديث في الجانب
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
