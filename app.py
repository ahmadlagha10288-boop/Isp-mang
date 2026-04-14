import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# 2. ميزة تبديل اللغة
if 'lang' not in st.session_state:
    st.session_state.lang = 'العربية'

lang = st.sidebar.radio("🌐 Language / اللغة", ["العربية", "English"])

# قاموس النصوص
texts = {
    "العربية": {
        "title": "📡 نظام إدارة فيوتشر نت",
        "search": "🔍 ابحث عن مشترك...",
        "total": "إجمالي المشتركين",
        "online": "متصل الآن ✅",
        "expired": "منتهي ❌",
        "package": "الباقة",
        "expiry": "تاريخ الانتهاء",
        "status": "الحالة",
        "pay": "💰 تم الدفع",
        "extend": "🔄 تمديد شهر",
        "whatsapp": "📲 واتساب",
        "days_left": "الأيام المتبقية",
        "expired_text": "منتهي"
    },
    "English": {
        "title": "📡 Future Net Management",
        "search": "🔍 Search for a client...",
        "total": "Total Clients",
        "online": "Online Now ✅",
        "expired": "Expired ❌",
        "package": "Package",
        "expiry": "Expiry Date",
        "status": "Status",
        "pay": "💰 Paid",
        "extend": "🔄 Renew Month",
        "whatsapp": "📲 WhatsApp",
        "days_left": "Days Left",
        "expired_text": "Expired"
    }
}

t = texts[lang]

# 3. دالة جلب البيانات
def load_data():
    try:
        url = st.secrets["connections"]["spreadsheet"]
        df = pd.read_csv(url, header=None)
        df = df.dropna(how='all')
        df = df.iloc[:, [0, 1, 2, 3]]
        df.columns = ['Username', 'Status', 'Expiry', 'Package']
        df['Username'] = df['Username'].astype(str).str.strip()
        df = df[~df['Username'].str.contains('nan|Username|Radius|Total', case=False)]
        df['Expiry_Date'] = pd.to_datetime(df['Expiry'], errors='coerce')
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- التصميم المخصص (CSS) لتحسين القراءة ---
st.markdown(f"""
    <style>
    .card {{
        background-color: #262730;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        border-right: 8px solid; /* سيتم تحديد اللون برمجياً */
        color: white;
    }}
    .client-title {{
        font-size: 1.5rem;
        font-weight: bold;
        color: #ffffff !important;
        margin-bottom: 10px;
    }}
    .info-row {{
        margin: 5px 0;
        font-size: 1.1rem;
        color: #e0e0e0;
    }}
    .status-tag {{
        float: {'left' if lang == 'العربية' else 'right'};
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title(t["title"])

if not df.empty:
    # إحصائيات سريعة
    c1, c2, c3 = st.columns(3)
    c1.metric(t["total"], len(df))
    c2.metric(t["online"], len(df[df['Status'].str.contains('Online', case=False)]))
    c3.metric(t["expired"], len(df[df['Status'].str.contains('Expired|Offline', case=False)]))

    search = st.text_input(t["search"])
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    for idx, row in df.iterrows():
        days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else -1
        
        # تحديد الألوان
        if "Online" in str(row['Status']):
            color = "#2ecc71" # أخضر
        elif days_left <= 3 and days_left >= 0:
            color = "#f1c40f" # أصفر
        else:
            color = "#e74c3c" # أحمر

        # المربع الطولي
        st.markdown(f"""
            <div class="card" style="border-{'right' if lang == 'العربية' else 'left'}: 10px solid {color};">
                <div class="status-tag" style="background: {color}22; color: {color}; border: 1px solid {color};">
                    {row['Status']}
                </div>
                <div class="client-title">👤 {row['Username']}</div>
                <div class="info-row"><b>📦 {t['package']}:</b> {row['Package']}</div>
                <div class="info-row"><b>📅 {t['expiry']}:</b> {row['Expiry']}</div>
                <div class="info-row"><b>⏳ {t['days_left']}:</b> {days_left if days_left >= 0 else t['expired_text']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # أزرار التحكم بشكل أفقي تحت المربع الطولي
        b1, b2, b3 = st.columns(3)
        with b1: st.button(t["pay"], key=f"p_{idx}", use_container_width=True)
        with b2: st.button(t["extend"], key=f"e_{idx}", use_container_width=True)
        with b3:
            link = f"https://wa.me/961?text=" + quote(f"Hello {row['Username']}...")
            st.link_button(t["whatsapp"], link, use_container_width=True)
        st.write("---")
