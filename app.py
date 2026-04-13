import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Ultra 2026", layout="wide")

# تصميم CSS محسن للرؤية الواضحة
st.markdown("""
    <style>
    .card { 
        background-color: #262730; 
        border-radius: 15px; 
        padding: 20px; 
        margin-bottom: 15px; 
        border-left: 8px solid #007bff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .client-name { 
        font-size: 1.5rem; 
        font-weight: bold; 
        color: #ffffff; 
        margin-bottom: 10px;
    }
    .days-tag { 
        font-size: 1.2rem; 
        font-weight: bold; 
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
        margin-bottom: 15px;
    }
    .debt-box { 
        background-color: #3d3f4b; /* رمادي أفتح ليتضح الخط */
        padding: 15px; 
        border-radius: 10px; 
        margin-top: 10px; 
        color: #ffffff !important; /* خط أبيض ناصع */
        font-size: 1.1rem;
        border: 1px solid #555;
    }
    .wa-container { display: flex; flex-direction: column; gap: 10px; margin-top: 15px; }
    .wa-btn { 
        display: block; 
        width: 100%; 
        padding: 15px; 
        text-align: center; 
        border-radius: 10px; 
        text-decoration: none !important; 
        font-weight: bold; 
        font-size: 1rem;
        color: white !important;
    }
    .btn-1 { background-color: #f39c12; } 
    .btn-2 { background-color: #d35400; } 
    .btn-3 { background-color: #c0392b; } 
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df_raw = pd.read_csv(url, header=None)
        h_idx = 0
        for i, row in df_raw.iterrows():
            if "Name" in row.values:
                h_idx = i
                break
        df = pd.read_csv(url, header=h_idx)
        df.columns = df.columns.astype(str).str.strip()
        df = df[df['Name'].notna()].reset_index(drop=True)
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- القائمة الجانبية ---
st.sidebar.title("⭐ Future Net Panel")
menu = st.sidebar.selectbox("اختر المهمة:", ["📱 الرادار والواتساب", "💵 المحاسبة والديون", "🗓️ التشريج الشهري"])

if menu == "📱 الرادار والواتساب":
    st.title("📡 رادار المشتركين")
    search = st.text_input("🔍 ابحث عن اسم الزبون:")
    if search:
        df = df[df['Name'].str.contains(search, case=False, na=False)]

    today = datetime.now()
    for idx, row in df.iterrows():
        expiry = row.get('Expiry Date')
        days_left = (expiry - today).days if pd.notnull(expiry) else 0
        st_color = "#2ecc71" if days_left > 0 else "#e74c3c"
        bg_tag = "rgba(46, 204, 113, 0.2)" if days_left > 0 else "rgba(231, 76, 60, 0.2)"
        
        # عرض البطاقة مع تحسين الألوان
        st.markdown(f"""
            <div class="card">
                <div class="client-name">{row['Name']}</div>
                <div class="days-tag" style="color:{st_color}; background:{bg_tag};">
                    ● باقي {days_left} يوم
                </div>
                <div class="debt-box">
                    <b style="color:#00d4ff;">📞 الهاتف:</b> {row.get('Mobile Number', 'N/A')}<br>
                    <b style="color:#ffcc00;">💰 الدين المستحق:</b> ${row.get('Selling Price', '0')}
                </div>
                <div class="wa-container">
        """, unsafe_allow_html=True)

        phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
        if phone and phone != 'nan':
            m1 = quote(f"عزيزي {row['Name']}، تنبيه من فيوتشر نت: اشتراكك ينتهي خلال 3 أيام.")
            m2 = quote(f"عزيزي {row['Name']}، نرجو تسديد مبلغ ${row.get('Selling Price')} لتجديد اشتراكك اليوم.")
            m3 = quote(f"تنبيه أخير {row['Name']}، يرجى الدفع لتجنب إيقاف الخدمة خلال ساعات.")
            
            st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع فوري</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير نهائي وإيقاف</a>', unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)

# بقية الأقسام (المحاسبة والتشريج) تبقى كما هي في الكود السابق...
elif menu == "💵 المحاسبة والديون":
    st.title("⚖️ إدارة الديون")
    # ... نفس كود المحاسبة السابق ...
    user = st.selectbox("اختر الزبون:", df['Name'].unique())
    u_row = df[df['Name'] == user].iloc[0]
    current_price = float(u_row.get('Selling Price', 0))
    st.info(f"الحساب الحالي للسيد {user} هو: **${current_price}**")
    col1, col2 = st.columns(2)
    with col1: add_debt = st.number_input("زيادة دين (+):", min_value=0.0)
    with col2: sub_debt = st.number_input("قبض مبلغ (-):", min_value=0.0)
    new_total = current_price + add_debt - sub_debt
    if st.button("احسب الحساب الجديد"):
        st.success(f"الحساب الجديد: **${new_total}**")

elif menu == "🗓️ التشريج الشهري":
    st.title("📅 التشريج الجماعي")
    if st.button("تجهيز القائمة"):
        st.dataframe(df[['Name', 'Service', 'Selling Price']])

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
