import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# 2. خيارات السايد بار (خافتة)
st.sidebar.markdown("<h4 style='color: #888;'>⚙️ Settings</h4>", unsafe_allow_html=True)
lang = st.sidebar.radio("", ["العربية", "English"], label_visibility="collapsed")
if st.sidebar.button("🔄 Refresh"):
    st.rerun()

# قاموس النصوص
texts = {
    "العربية": {"search": "🔍 ابحث...", "pkg": "باقة", "exp": "ينتهي", "days": "أيام"},
    "English": {"search": "🔍 Search...", "pkg": "Pkg", "exp": "Exp", "days": "Days"}
}
t = texts[lang]

# 3. جلب البيانات
def load_data():
    try:
        url = st.secrets["connections"]["spreadsheet"]
        df = pd.read_csv(url, header=None).dropna(how='all')
        df = df.iloc[:, [0, 1, 2, 3]]
        df.columns = ['Username', 'Status', 'Expiry', 'Package']
        df['Username'] = df['Username'].astype(str).str.strip()
        df = df[~df['Username'].str.contains('nan|Username|Radius|Total', case=False)]
        df['Expiry_Date'] = pd.to_datetime(df['Expiry'], errors='coerce')
        return df.reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_data()

# --- CSS لتصغير حجم المربع (البوكس) والحفاظ على وضوح الخط ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    
    /* تصغير المربع وضغطه */
    .compact-card {{
        background-color: #004aad;
        border-radius: 8px;
        padding: 8px 12px; /* تقليل المسافات الداخلية */
        margin-bottom: 5px;
        color: white;
        border-right: 6px solid #4a90e2;
        min-height: 130px; /* طول معتدل للمربع */
    }}
    
    .user-title {{
        font-size: 1.15rem; /* حجم خط واضح */
        font-weight: bold;
        margin-bottom: 4px;
        color: #ffffff;
    }}
    
    .info-line {{
        font-size: 0.95rem; /* خط المعلومات الأساسي */
        margin: 1px 0;
        color: #e0e0e0;
    }}
    
    .status-label {{
        font-size: 0.75rem;
        background: rgba(255,255,255,0.2);
        padding: 1px 6px;
        border-radius: 4px;
        float: {'left' if lang == 'العربية' else 'right'};
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"<h3 style='color: #004aad; text-align: center;'>📡 Future Net Radar</h3>", unsafe_allow_html=True)

if not df.empty:
    search = st.text_input(t["search"], label_visibility="collapsed")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    # عرض زبونين في كل سطر
    for i in range(0, len(df), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(df):
                row = df.iloc[i + j]
                days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else "!!"
                
                with cols[j]:
                    # تصميم المربع المضغوط
                    st.markdown(f"""
                        <div class="compact-card">
                            <div class="status-label">{row['Status']}</div>
                            <div class="user-title">👤 {row['Username']}</div>
                            <div class="info-line">📦 {t['pkg']}: {row['Package']}</div>
                            <div class="info-line">📅 {t['exp']}: {row['Expiry'].split(' ')[0]}</div>
                            <div class="info-line">⏳ {t['days']}: {days_left}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار التحكم (💰, 🔄, 📲) بجانب بعضها تحت المربع مباشرة
                    b_col = st.columns(3)
                    with b_col[0]: st.button("💰", key=f"p_{i+j}", use_container_width=True)
                    with b_col[1]: st.button("🔄", key=f"e_{i+j}", use_container_width=True)
                    with b_col[2]: 
                        wa_link = f"https://wa.me/961?text=Hi {row['Username']}"
                        st.link_button("📲", wa_link, use_container_width=True)
else:
    st.info("No Data.")
