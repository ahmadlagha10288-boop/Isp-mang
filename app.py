import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

# تصميم الواجهة الاحترافي
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 6px solid #007bff; }
    .client-name { font-size: 1.2rem; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .status-badge { font-size: 0.85rem; padding: 2px 10px; border-radius: 12px; font-weight: bold; }
    .online { color: #2ecc71; background: rgba(46, 204, 113, 0.1); }
    .expired { color: #e74c3c; background: rgba(231, 76, 60, 0.1); }
    .info-row { font-size: 0.95rem; color: #bdc3c7; margin: 4px 0; }
    .wa-btn { display: block; width: 100%; padding: 12px; text-align: center; border-radius: 8px; text-decoration: none !important; font-weight: bold; font-size: 0.95rem; color: white !important; margin-top: 10px; }
    .btn-warn { background-color: #f39c12; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        # الحصول على الرابط وتصحيحه للقراءة كـ CSV
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        if "edit" in raw_url:
            csv_url = raw_url.replace('/edit', '/export?format=csv')
        else:
            csv_url = raw_url
            
        # قراءة البيانات بدون عناوين
        df = pd.read_csv(csv_url, header=None)
        
        # تنظيف أولي للأسطر الفارغة
        df = df.dropna(subset=[0]) 
        
        # توزيع الأعمدة: 0=الاسم، 1=الحالة، 2=الخدمة، 3=تاريخ الانتهاء، 5=التلفون
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Name', 'Status', 'Service', 'Expiry', 'Phone']
        
        # فلترة الكلمات التقنية التي تظهر في الصور (Radius, Action, etc)
        df['Name'] = df['Name'].astype(str)
        df = df[~df['Name'].str.contains('Radius|Action|Name|nan|Uptime|Total', case=False)]
        
        # تحويل التاريخ وترتيبه (المنتهي أولاً)
        df['Expiry'] = pd.to_datetime(df['Expiry'], errors='coerce')
        df = df.sort_values(by='Expiry', ascending=True)
        
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"خطأ في الاتصال بالجوجل شيت: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.info("ℹ️ في انتظار البيانات... تأكد من أن الرابط في `secrets` هو رابط 'Share' العام.")
else:
    search = st.text_input("🔍 بحث عن اسم:")
    if search:
        df = df[df['Name'].str.contains(search, case=False)]

    for _, row in df.iterrows():
        name = row['Name']
        status = str(row['Status'])
        service = str(row['Service'])
        expiry = row['Expiry']
        phone = str(row['Phone']).replace('.0', '').strip()
        
        st_class = "online" if "Online" in status else "expired"
        exp_str = expiry.strftime('%Y-%m-%d') if pd.notnull(expiry) else "N/A"
        
        with st.container():
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="info-row">● الحالة: <span class="status-badge {st_class}">{status}</span></div>
                    <div class="info-row">🛠️ الخدمة: {service}</div>
                    <div class="info-row">📅 تاريخ الانتهاء: {exp_str}</div>
            """, unsafe_allow_html=True)
            
            # زر الواتساب (باستخدام رقم التلفون من العمود F)
            if phone != 'nan' and len(phone) >= 7:
                clean_phone = phone.replace(' ', '').replace('+', '')
                full_phone = f"961{clean_phone}" if not clean_phone.startswith('961') else clean_phone
                msg = quote(f"تنبيه من فيوتشر نت: اشتراكك {service} ينتهي في {exp_str}. يرجى التجديد.")
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={msg}" class="wa-btn btn-warn">⚠️ إرسال تنبيه واتساب</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# زر التحديث
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
