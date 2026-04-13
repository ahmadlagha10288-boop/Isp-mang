import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net - Cards View", layout="wide")

# تصميم CSS مخصص للبطاقات
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
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url, header=1)
        df.columns = df.columns.astype(str).str.strip()
        if 'Selling Price' in df.columns:
            df['Selling Price'] = pd.to_numeric(df['Selling Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net - Clients Portal")

if not df.empty:
    # --- قسم البحث ---
    search = st.text_input("🔍 ابحث عن زبون بالاسم أو الرقم:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    st.write(f"عرض {len(df)} مشترك")

    # --- عرض الزبائن على شكل كولوم (Columns) وبطاقات ---
    # منعمل 3 أعمدة بكل سطر
    cols = st.columns(3)
    
    for index, row in df.iterrows():
        # توزيع البطاقات على الأعمدة الثلاثة
        with cols[index % 3]:
            status = str(row['Status']).lower() if 'Status' in df.columns else ""
            status_class = "status-online" if 'online' in status or 'active' in status else "status-offline"
            status_text = "🟢 Online" if 'online' in status or 'active' in status else "🔴 Offline"
            
            phone = str(row['Mobile Number']).replace('.0', '') if 'Mobile Number' in df.columns else ""
            
            # محتوى البطاقة
            st.markdown(f"""
                <div class="user-card">
                    <div class="client-name">{row['Name'] if 'Name' in df.columns else 'Unknown'}</div>
                    <div class="{status_class}">{status_text}</div>
                    <hr style="margin: 10px 0; border-color: #333;">
                    <div><span class="info-label">Service:</span> {row['Service'] if 'Service' in df.columns else 'N/A'}</div>
                    <div><span class="info-label">Expiry:</span> {row['Expiry Date'] if 'Expiry Date' in df.columns else 'N/A'}</div>
                    <div><span class="info-label">Price:</span> ${row['Selling Price'] if 'Selling Price' in df.columns else '0'}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # أزرار التفاعل تحت كل بطاقة
            c1, c2 = st.columns(2)
            with c1:
                if phone:
                    msg = quote(f"Hello {row['Name']}, your subscription is {row['Status']}. Please contact us for any help.")
                    st.markdown(f"[📲 WhatsApp](https://wa.me/{phone}?text={msg})")
            with c2:
                if st.button(f"Details", key=f"btn_{index}"):
                    st.info(f"Full Data for {row['Name']}: \n\n {row.to_dict()}")

else:
    st.warning("No data found in the spreadsheet.")

# زر التحديث
if st.sidebar.button("🔄 Update Data"):
    st.cache_data.clear()
    st.rerun()
