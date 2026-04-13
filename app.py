import streamlit as st
import pandas as pd
from datetime import datetime

# 1. إعدادات الواجهة
st.set_page_config(page_title="Future Net Radius", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        
        # أهم خطوة: تنظيف أسماء الأعمدة من أي مسافات زائدة
        df.columns = df.columns.str.strip()
        
        # التأكد من تحويل العمود لنص لتجنب أخطاء البحث
        if 'Status' in df.columns:
            df['Status'] = df['Status'].astype(str).fillna('')
        if 'Selling Price' in df.columns:
            df['Selling Price'] = pd.to_numeric(df['Selling Price'], errors='coerce').fillna(0)
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius Manager")

if not df.empty:
    # التحقق من وجود الأعمدة المطلوبة قبل الحساب
    has_status = 'Status' in df.columns
    has_price = 'Selling Price' in df.columns

    # حساب الإحصائيات مع التأكد من وجود الأعمدة
    total_users = len(df)
    
    active_users = len(df[df['Status'].str.contains('Active|Online', case=False, na=False)]) if has_status else 0
    expired_users = len(df[df['Status'].str.contains('Expired', case=False, na=False)]) if has_status else 0
    total_revenue = df['Selling Price'].sum() if has_price else 0

    # عرض المربعات العلوية
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي المشتركين", total_users)
    col2.metric("نشط / أونلاين", active_users)
    col3.metric("منتهي الصلاحية", expired_users)
    col4.metric("إجمالي المبيعات", f"${total_revenue:,.2f}")

    st.divider()

    # القائمة الجانبية للبحث والفلترة
    search = st.sidebar.text_input("🔍 بحث سريع:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # عرض الجدول (الأعمدة المتاحة فقط)
    important_cols = ['Name', 'Username', 'Status', 'Expiry Date', 'Selling Price', 'Mobile Number']
    display_cols = [c for c in important_cols if c in df.columns]
    
    st.subheader("📋 قائمة المشتركين")
    st.dataframe(df[display_cols], width='stretch')

else:
    st.error("⚠️ لم نتمكن من قراءة البيانات. تأكد من 'الرابط' في السيكرتس ومن أن الملف يحتوي على بيانات.")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
