import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# تصميم البطاقات الاحترافي
st.markdown("""
    <style>
    .card { 
        background-color: #1e1e1e; 
        border-radius: 15px; 
        padding: 20px; 
        margin-bottom: 15px; 
        border-top: 5px solid #007bff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .name { font-size: 1.3rem; font-weight: bold; color: #ffffff; }
    .status-active { color: #2ecc71; font-weight: bold; }
    .status-expired { color: #e74c3c; font-weight: bold; }
    .info-row { color: #cccccc; font-size: 0.9rem; margin-top: 5px; }
    .label { color: #777777; font-weight: normal; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف بدون عناوين أولية لنحدد وين العناوين الصح
        df_raw = pd.read_csv(url, header=None)
        
        # البحث عن السطر اللي فيه كلمة "Name"
        header_index = 0
        for i, row in df_raw.iterrows():
            if "Name" in row.values:
                header_index = i
                break
        
        # إعادة قراءة الملف من السطر الصحيح
        df = pd.read_csv(url, header=header_index)
        df.columns = df.columns.astype(str).str.strip()
        # حذف الأسطر الفاضية تماماً والأسطر اللي فيها Names مكررة
        df = df[df['Name'].notna()]
        df = df[df['Name'] != 'Name']
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    # --- الإحصائيات الفوق ---
    total = len(df)
    online = 0
    if 'Status' in df.columns:
        online = len(df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)])

    c1, c2 = st.columns(2)
    c1.metric("👥 المشتركين", total)
    c2.metric("🟢 أونلاين", online)

    st.divider()

    # --- البحث ---
    search = st.text_input("🔍 ابحث عن اسم، يوزر، أو رقم:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # --- عرض البطاقات ---
    cols = st.columns(2) # كرتين بكل سطر للموبايل
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 2]:
            name = str(row.get('Name', 'Unknown'))
            status = str(row.get('Status', 'N/A'))
            service = str(row.get('Service', 'N/A'))
            expiry = str(row.get('Expiry Date', 'N/A'))
            price = str(row.get('Selling Price', '0'))
            phone = str(row.get('Mobile Number', '')).replace('.0', '')

            is_online = any(x in status.lower() for x in ['online', 'active'])
            st_color = "status-active" if is_online else "status-expired"
            st_icon = "🟢" if is_online else "🔴"

            # تصميم الكرت
            st.markdown(f"""
                <div class="card">
                    <div class="name">{name}</div>
                    <div class="{st_color}">{st_icon} {status}</div>
                    <div class="info-row"><span class="label">🛠 Service:</span> {service}</div>
                    <div class="info-row"><span class="label">📅 Expiry:</span> {expiry}</div>
                    <div class="info-row"><span class="label">💰 Price:</span> ${price}</div>
                </div>
            """, unsafe_allow_html=True)

            # زر واتساب
            if phone and phone != 'nan' and len(phone) > 5:
                wa_msg = quote(f"مرحباً {name}، اشتراكك {service} هو {status}. فيوتشر نت بخدمتك.")
                st.markdown(f"[📲 WhatsApp](https://wa.me/{phone}?text={wa_msg})")

else:
    st.info("⚠️ بانتظار تحميل البيانات... تأكد من رابط الـ CSV.")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
