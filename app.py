import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم CSS لتحسين العرض على الموبايل
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #007bff; }
    .client-name { font-size: 1.15rem; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .status-badge { font-size: 0.85rem; padding: 2px 8px; border-radius: 10px; font-weight: bold; }
    .online { color: #2ecc71; } .expired { color: #e74c3c; }
    .info-row { font-size: 0.9rem; color: #bdc3c7; margin: 4px 0; }
    .wa-btn { display: block; width: 100%; padding: 10px; text-align: center; border-radius: 8px; text-decoration: none !important; font-weight: bold; font-size: 0.9rem; color: white !important; margin-top: 8px; }
    .btn-warn { background-color: #f39c12; } .btn-pay { background-color: #d35400; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف من السطر الأول وبدون عناوين نهائياً
        df = pd.read_csv(url, header=None)
        
        # تنظيف: حذف الأسطر الفاضية بالكامل
        df = df.dropna(how='all')
        
        # تسمية الأعمدة يدوياً حسب ترتيب الإكسل (A, B, C, D, E, F)
        # 0=الاسم، 1=الحالة، 2=الخدمة، 3=تاريخ الانتهاء، 5=التلفون
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Name', 'Status', 'Service', 'Expiry', 'Phone']
        
        # أهم خطوة: حذف الأسطر اللي فيها كلمات Radius أو Action أو nan في خانة الاسم
        df = df[df['Name'].notna()]
        df['Name'] = df['Name'].astype(str)
        df = df[~df['Name'].str.contains('Radius|Action|Name|nan|Uptime', case=False)]
        
        # تحويل التاريخ للترتيب (المنتهي أولاً)
        df['Expiry'] = pd.to_datetime(df['Expiry'], errors='coerce')
        df = df.sort_values(by='Expiry', ascending=True)
        
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"خطأ: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.warning("⚠️ لم يتم العثور على زبائن. تأكد من تحديث الجوجل شيت.")
else:
    search = st.text_input("🔍 بحث عن اسم:")
    if search:
        df = df[df['Name'].str.contains(search, case=False)]

    for _, row in df.iterrows():
        name = row['Name']
        status = str(row['Status'])
        service = str(row['Service'])
        expiry = row['Expiry']
        phone = str(row['Phone']).replace('.0', '').replace(' ', '').strip()
        
        st_class = "online" if "Online" in status else "expired"
        exp_str = expiry.strftime('%Y-%m-%d') if pd.notnull(expiry) else "غير محدد"
        
        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-row">● الحالة: <span class="{st_class}">{status}</span></div>
                    <div class="info-row">🛠️ الخدمة: {service}</div>
                    <div class="info-row">📅 تاريخ الانتهاء: {exp_str}</div>
            """, unsafe_allow_html=True)
            
            # أزرار الواتساب (باستخدام العمود F)
            if phone != 'nan' and len(phone) >= 7:
                full_phone = f"961{phone}" if not phone.startswith('961') else phone
                msg = quote(f"تذكير: اشتراكك {service} ينتهي في {exp_str}. يرجى التجديد.")
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={msg}" class="wa-btn btn-warn">⚠️ تنبيه انتهاء</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# زر التحديث
if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
