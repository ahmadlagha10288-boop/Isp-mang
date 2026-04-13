import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Ultra Manager", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة من السطر الثاني كما اتفقنا
        df = pd.read_csv(url, header=1)
        df.columns = df.columns.astype(str).str.strip()
        
        # تنظيف البيانات المالية والتواريخ
        if 'Selling Price' in df.columns:
            df['Selling Price'] = pd.to_numeric(df['Selling Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- واجهة المستخدم ---
st.title("⚡ Future Net Ultra Manager")

if not df.empty:
    # 2. الحسابات الذكية
    today = datetime.now().date()
    near_expiry_days = today + timedelta(days=2)
    
    online_df = df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)] if 'Status' in df.columns else pd.DataFrame()
    near_expiry_df = df[(df['Expiry Date'] >= today) & (df['Expiry Date'] <= near_expiry_days)] if 'Expiry Date' in df.columns else pd.DataFrame()
    
    # 3. الداشبورد السريع
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 المشتركين", len(df))
    c2.metric("🟢 أونلاين", len(online_df))
    c3.metric("⏳ قريباً ينتهي", len(near_expiry_df))
    c4.metric("💰 المداخيل", f"${df['Selling Price'].sum():,.0f}" if 'Selling Price' in df.columns else "$0")

    st.divider()

    # 4. القائمة الجانبية
    st.sidebar.header("🛠️ الإدارة")
    menu = st.sidebar.selectbox("القسم الإداري:", 
        ["📋 الإدارة العامة", "💸 قسم المديونين", "📩 مراسلة واتساب", "💾 Backup"])

    if menu == "📋 الإدارة العامة":
        st.subheader("📊 قائمة المشتركين")
        search = st.text_input("🔎 بحث سريع:")
        if search:
            df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]
        st.dataframe(df, use_container_width=True)

    elif menu == "💸 قسم المديونين":
        st.subheader("🔴 المبالغ المستحقة")
        debt_df = df[df['Status'].astype(str).str.contains('Expired|Block', case=False, na=False)] if 'Status' in df.columns else pd.DataFrame()
        if not debt_df.empty:
            st.table(debt_df[['Name', 'Status', 'Selling Price', 'Mobile Number']])
        else:
            st.success("لا يوجد ديون حالياً! ✅")

    elif menu == "📩 مراسلة واتساب":
        st.subheader("💬 مراسلة سريعة")
        user = st.selectbox("اختر الزبون:", df['Name'].tolist())
        u_data = df[df['Name'] == user].iloc[0]
        phone = str(u_data['Mobile Number']).replace('.0', '')
        msg = f"مرحباً {user}، يرجى سداد مستحقات الاشتراك لتجنب الانقطاع."
        wa_link = f"https://wa.me/{phone}?text={quote(msg)}"
        st.markdown(f'[اضغط هنا للإرسال عبر واتساب 📲]({wa_link})')

    elif menu == "💾 Backup":
        st.subheader("📥 حفظ نسخة احتياطية")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Backup", csv, "FutureNet_Backup.csv", "text/csv")

else:
    st.warning("⚠️ لم يتم العثور على بيانات.")

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
