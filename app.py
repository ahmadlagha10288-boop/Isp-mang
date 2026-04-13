import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net - Cards View", layout="wide")

# تصميم CSS المخصص للبطاقات
st.markdown("""
    <style>
    .user-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #007bff;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    .status-online { color: #2ecc71; font-weight: bold; }
    .status-offline { color: #e74c3c; font-weight: bold; }
    .client-name { font-size: 1.2rem; font-weight: bold; color: #ffffff; }
    .info-label { color: #888888; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    try:
        # قراءة الرابط من Secrets
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الداتا بدون عناوين (لأنك بتبدأ من أول سطر)
        df = pd.read_csv(url, header=None)
        
        # تنظيف الأسطر الفاضية
        df = df.dropna(how='all')
        
        # اختيار الأعمدة بالأرقام حسب صورتك: 
        # 0=A (اليوزر نيم)، 1=B (الحالة)، 2=C (الباقة)، 3=D (التاريخ)، 5=F (التلفون)
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Username', 'Status', 'Service', 'Expiry', 'Phone']
        
        # حذف أي سطر مش يوزر نيم حقيقي (اللي بيطلعوا nan أو Radius)
        df = df[df['Username'].notna()]
        df = df[~df['Username'].astype(str).str.contains('Radius|Action|Name|nan|Total', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net - Clients Portal")

if not df.empty:
    # --- قسم البحث ---
    search = st.text_input("🔍 ابحث عن يوزر نيم:")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    st.write(f"عرض {len(df)} مشترك")

    # --- عرض الزبائن ---
    cols = st.columns(3)
    
    for index, row in df.iterrows():
        with cols[index % 3]:
            # تحديد الحالة
            status_val = str(row['Status']).lower()
            is_online = 'online' in status_val or 'active' in status_val
            status_class = "status-online" if is_online else "status-offline"
            status_text = "🟢 Online" if is_online else "🔴 Expired"
            
            # محتوى البطاقة (باستخدام Username من العمود A)
            st.markdown(f"""
                <div class="user-card">
                    <div class="client-name">{row['Username']}</div>
                    <div class="{status_class}">{status_text}</div>
                    <hr style="margin: 10px 0; border-color: #333;">
                    <div><span class="info-label">Service:</span> {row['Service']}</div>
                    <div><span class="info-label">Expiry:</span> {row['Expiry']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # زر الواتساب
            phone = str(row['Phone']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) > 5:
                clean_phone = phone.replace(' ', '')
                full_num = f"961{clean_phone}" if not clean_phone.startswith('961') else clean_phone
                msg = quote(f"Hello {row['Username']}, your subscription {row['Service']} is {row['Status']}.")
                st.markdown(f'<a href="https://wa.me/{full_num}?text={msg}" target="_blank" style="text-decoration:none;"><button style="width:100%; border-radius:5px; border:none; background:#25D366; color:white; padding:5px; cursor:pointer;">📲 WhatsApp</button></a>', unsafe_allow_html=True)

else:
    st.warning("⚠️ لا توجد بيانات. تأكد من إعدادات الرابط في الـ Secrets.")

# زر التحديث في الجنب
if st.sidebar.button("🔄 Update Data"):
    st.cache_data.clear()
    st.rerun()
