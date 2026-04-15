import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# 2. ميزة تبديل اللغة (خافتة في السايد بار)
st.sidebar.markdown("<h4 style='color: #888;'>⚙️ الإعدادات / Settings</h4>", unsafe_allow_html=True)
lang = st.sidebar.radio("", ["العربية", "English"], label_visibility="collapsed")

# 3. زر إعادة تحديث الصفحة (Refresh)
if st.sidebar.button("🔄 تحديث البيانات / Reload"):
    st.rerun()

# قاموس النصوص
texts = {
    "العربية": {
        "title": "📡 رادار فيوتشر نت",
        "search": "🔍 ابحث عن مشترك...",
        "package": "الباقة",
        "expiry": "الانتهاء",
        "status": "الحالة",
        "pay": "تم الدفع",
        "extend": "تجديد",
        "whatsapp": "واتساب",
        "days_left": "الأيام"
    },
    "English": {
        "title": "📡 Future Net Radar",
        "search": "🔍 Search...",
        "package": "Package",
        "expiry": "Expiry",
        "status": "Status",
        "pay": "Paid",
        "extend": "Renew",
        "whatsapp": "WhatsApp",
        "days_left": "Days"
    }
}
t = texts[lang]

# 4. دالة جلب البيانات
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
    except:
        return pd.DataFrame()

df = load_data()

# --- CSS المخصص: خلفية بيضاء + بطاقات زرقاء + نصوص واضحة ---
st.markdown(f"""
    <style>
    /* جعل الخلفية الأساسية بيضاء */
    .stApp {{
        background-color: #ffffff;
    }}
    
    /* جعل السايد بار خافت */
    [data-testid="stSidebar"] {{
        background-color: #f8f9fa;
        opacity: 0.8;
    }}

    /* تصميم البطاقة الزرقاء */
    .card {{
        background-color: #004aad; /* أزرق غامق احترافي */
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: {'right' if lang == 'العربية' else 'left'};
    }}
    
    .client-name {{
        font-size: 1.3rem;
        font-weight: bold;
        color: #ffffff;
        border-bottom: 1px solid #4a90e2;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }}

    .info-text {{
        font-size: 1rem;
        color: #e0e0e0;
        margin: 3px 0;
    }}

    /* ألوان الحالة داخل البطاقة */
    .status-badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 5px;
        font-size: 0.8rem;
        background: rgba(255,255,255,0.2);
        margin-bottom: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"<h1 style='color: #004aad; text-align: center;'>{t['title']}</h1>", unsafe_allow_html=True)

if not df.empty:
    search = st.text_input(t["search"], label_visibility="collapsed")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    for idx, row in df.iterrows():
        days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else "N/A"
        
        # عرض البطاقة الزرقاء
        st.markdown(f"""
            <div class="card">
                <div class="status-badge">● {row['Status']}</div>
                <div class="client-name">👤 {row['Username']}</div>
                <div class="info-text"><b>{t['package']}:</b> {row['Package']}</div>
                <div class="info-text"><b>{t['expiry']}:</b> {row['Expiry']}</div>
                <div class="info-text"><b>{t['days_left']}:</b> {days_left}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # أزرار التحكم
        c1, c2, c3 = st.columns(3)
        with c1: st.button(t["pay"], key=f"p_{idx}", use_container_width=True)
        with c2: st.button(t["extend"], key=f"e_{idx}", use_container_width=True)
        with c3:
            link = f"https://wa.me/961?text=" + quote(f"Hi {row['Username']}...")
            st.link_button(t["whatsapp"], link, use_container_width=True)
else:
    st.error("لم نتمكن من سحب البيانات. تأكد من أن ملف الإكسل يبدأ بالبيانات من الخانة A1.")
