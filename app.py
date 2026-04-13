import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Ultra 2026", layout="wide")

# تصميم CSS لتحسين شكل الأزرار والبطاقات
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 15px; padding: 20px; margin-bottom: 10px; border-left: 6px solid #007bff; }
    .wa-container { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
    .wa-btn { 
        display: block; 
        width: 100%; 
        padding: 12px; 
        text-align: center; 
        border-radius: 8px; 
        text-decoration: none; 
        font-weight: bold; 
        font-size: 0.9rem;
        color: white !important;
    }
    .btn-1 { background-color: #f39c12; } /* تنبيه 3 أيام */
    .btn-2 { background-color: #d35400; } /* طلب دفع */
    .btn-3 { background-color: #c0392b; } /* تحذير إيقاف */
    .debt-box { background: #2c3e50; padding: 10px; border-radius: 8px; margin-top: 5px; border: 1px solid #34495e; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # تنظيف الداتا من السطور الزائدة
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

# --- القسم 1: الرادار والواتساب ---
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
        
        # عرض البطاقة
        st.markdown(f"""
            <div class="card">
                <div style="font-size:1.4rem; font-weight:bold;">{row['Name']}</div>
                <div style="color:{st_color}; font-weight:bold;">● باقي {days_left} يوم</div>
                <div class="debt-box">
                    📞 {row.get('Mobile Number', 'N/A')} | 💰 الدين: ${row.get('Selling Price', '0')}
                </div>
                <div class="wa-container">
        """, unsafe_allow_html=True)

        # تجهيز رسائل الواتساب
        phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
        if phone and phone != 'nan':
            m1 = quote(f"عزيزي {row['Name']}، تنبيه من فيوتشر نت: اشتراكك ينتهي خلال 3 أيام.")
            m2 = quote(f"عزيزي {row['Name']}، نرجو تسديد مبلغ ${row.get('Selling Price')} لتجديد اشتراكك اليوم.")
            m3 = quote(f"تنبيه أخير {row['Name']}، يرجى الدفع لتجنب إيقاف الخدمة خلال ساعات.")
            
            st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع فوري</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير نهائي وإيقاف</a>', unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)

# --- القسم 2: المحاسبة والديون ---
elif menu == "💵 المحاسبة والديون":
    st.title("⚖️ إدارة الديون (مدين / دائن)")
    user = st.selectbox("اختر الزبون:", df['Name'].unique())
    u_row = df[df['Name'] == user].iloc[0]
    current_price = float(u_row.get('Selling Price', 0))
    
    st.info(f"الحساب الحالي للسيد {user} هو: **${current_price}**")
    
    col1, col2 = st.columns(2)
    with col1:
        add_debt = st.number_input("زيادة دين (+):", min_value=0.0)
    with col2:
        sub_debt = st.number_input("قبض مبلغ (-):", min_value=0.0)
    
    new_total = current_price + add_debt - sub_debt
    
    if st.button("احسب الحساب الجديد"):
        st.success(f"الحساب الجديد: **${new_total}**")
        st.write("👉 يرجى تعديل السعر في ملف الإكسل بهذا الرقم.")

# --- القسم 3: التشريج الشهري ---
elif menu == "🗓️ التشريج الشهري":
    st.title("📅 نظام التشريج الجماعي")
    st.write("اضغط الزر لتجهيز قائمة بأسماء كل المشتركين لتبدأ شهر جديد.")
    
    if st.button("تجهيز قائمة الشهر الجديد"):
        recharge_df = df[['Name', 'Service', 'Selling Price', 'Mobile Number']]
        st.dataframe(recharge_df)
        csv = recharge_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 تحميل القائمة للطباعة (Excel)", csv, "FutureNet_Recharge.csv")

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
