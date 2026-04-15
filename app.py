import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# 2. جلب اللغة (عربي/إنجليزي) من السايد بار
st.sidebar.markdown("<h4 style='color: #888;'>⚙️ الإعدادات</h4>", unsafe_allow_html=True)
lang = st.sidebar.radio("", ["العربية", "English"], label_visibility="collapsed")

# قاموس النصوص
texts = {
    "العربية": {
        "search": "🔍 ابحث...",
        "package": "الباقة",
        "expiry": "الانتهاء",
        "days": "الأيام",
        "pay": "تم الدفع",
        "extend": "تجديد",
        "whatsapp": "واتساب"
    },
    "English": {
        "search": "🔍 Search...",
        "package": "Pkg",
        "expiry": "Exp",
        "days": "Days",
        "pay": "Paid",
        "extend": "Renew",
        "whatsapp": "WA"
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
    except:
        return pd.DataFrame()

df = load_data()

# --- CSS لتصغير المربعات وجعلها طولية ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    
    /* تصميم الكرت الصغير الطولي */
    .mini-card {{
        background-color: #004aad;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 5px;
        color: white;
        text-align: center;
        min-height: 180px; /* ضمان توحد الطول */
    }}
    
    .user-name {{
        font-size: 1.1rem;
        font-weight: bold;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .mini-info {{
        font-size: 0.85rem;
        margin: 2px 0;
        color: #e0e0e0;
    }}
    
    .status-dot {{
        font-size: 0.75rem;
        background: rgba(255,255,255,0.15);
        padding: 2px 8px;
        border-radius: 10px;
    }}

    /* تصغير حجم أزرار الستريم ليت لتناسب العرض الصغير */
    div.stButton > button {{
        padding: 2px 5px !important;
        font-size: 0.8rem !important;
        height: 30px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# العنوان
st.markdown(f"<h2 style='color: #004aad; text-align: center;'>📡 Future Net</h2>", unsafe_allow_html=True)

if not df.empty:
    search = st.text_input(t["search"], label_visibility="collapsed")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    # --- توزيع الزبائن (2 في كل سطر) ---
    # نستخدم loop بيمشي خطوتين خطوتين
    for i in range(0, len(df), 2):
        cols = st.columns(2) # إنشاء عمودين
        
        for j in range(2):
            if i + j < len(df):
                row = df.iloc[i + j]
                days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else "!!"
                
                with cols[j]:
                    # الكرت الطولي
                    st.markdown(f"""
                        <div class="mini-card">
                            <div class="status-dot">● {row['Status']}</div>
                            <div class="user-name">👤 {row['Username']}</div>
                            <div class="mini-info">📦 {row['Package']}</div>
                            <div class="mini-info">📅 {row['Expiry'].split(' ')[0]}</div>
                            <div class="mini-info">⏳ {t['days']}: {days_left}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار تحكم مصغرة تحت الكرت
                    btn_cols = st.columns(3)
                    with btn_cols[0]: st.button("💰", key=f"p_{i+j}", help=t["pay"])
                    with btn_cols[1]: st.button("🔄", key=f"e_{i+j}", help=t["extend"])
                    with btn_cols[2]: 
                        link = f"https://wa.me/961?text=" + quote(f"Hi {row['Username']}...")
                        st.link_button("📲", link)
else:
    st.info("No Data Found.")
