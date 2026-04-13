import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# تصميم البطاقات المعدل
st.markdown("""
    <style>
    .card { 
        background-color: #1e1e1e; 
        border-radius: 15px; 
        padding: 20px; 
        margin-bottom: 20px; 
        border-top: 5px solid #007bff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .name { font-size: 1.3rem; font-weight: bold; color: #ffffff; margin-bottom: 10px; }
    .status-active { color: #2ecc71; font-weight: bold; }
    .status-expired { color: #e74c3c; font-weight: bold; }
    .info-row { color: #cccccc; font-size: 0.95rem; margin-top: 8px; display: flex; align-items: center; }
    .wa-btn { 
        display: inline-block; 
        padding: 8px 15px; 
        background-color: #25d366; 
        color: white !important; 
        border-radius: 8px; 
        text-decoration: none; 
        font-weight: bold; 
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df_raw = pd.read_csv(url, header=None)
        
        # تحديد السطر الصحيح للعناوين
        header_index = 0
        for i, row in df_raw.iterrows():
            if "Name" in row.values:
                header_index = i
                break
        
        df = pd.read_csv(url, header=header_index)
        df.columns = df.columns.astype(str).str.strip()
        df = df[df['Name'].notna()]
        df = df[df['Name'] != 'Name']
        return df
    except:
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    search = st.text_input("🔍 بحث عن مشترك:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # عرض البطاقات
    cols = st.columns(2)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 2]:
            name = str(row.get('Name', 'Unknown'))
            # تصليح قراءة الحالة
            status_val = str(row.get('Status', 'Offline'))
            is_online = any(x in status_val.lower() for x in ['online', 'active', 'up'])
            
            st_color = "status-active" if is_online else "status-expired"
            st_icon = "🟢" if is_online else "🔴"
            
            # عرض الكرت
            st.markdown(f"""
                <div class="card">
                    <div class="name">{name}</div>
                    <div class="{st_color}">{st_icon} {status_val}</div>
                    <div class="info-row">🛠️ <b style="margin-left:5px;">Service:</b> {row.get('Service', 'N/A')}</div>
                    <div class="info-row">📅 <b style="margin-left:5px;">Expiry:</b> {row.get('Expiry Date', 'N/A')}</div>
                    <div class="info-row">💰 <b style="margin-left:5px;">Price:</b> ${row.get('Selling Price', '0')}</div>
            """, unsafe_allow_html=True)

            # تصليح زر الواتساب ليظهر كزر نظيف
            phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
            if phone and phone != 'nan' and len(phone) > 5:
                wa_msg = quote(f"مرحباً سيد {name}، معك Future Net. بخصوص اشتراكك {row.get('Service', '')}...")
                st.markdown(f'<a href="https://wa.me/{phone}?text={wa_msg}" class="wa-btn">📲 WhatsApp Message</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("⚠️ بانتظار البيانات...")

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
