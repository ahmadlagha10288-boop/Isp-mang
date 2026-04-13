import streamlit as st
import pandas as pd
from datetime import datetime

# 1. إعدادات الواجهة
st.set_page_config(page_title="Future Net Radius", layout="wide")

def load_data():
    try:
        # قراءة الرابط من Secrets
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # قراءة البيانات مع تجاهل الأسطر الفارغة
        df = pd.read_csv(url, skip_blank_lines=True)
        
        # تنظيف الأعمدة (إزالة أي مسافات مخفية أو أحرف غريبة)
        df.columns = df.columns.astype(str).str.strip()
        
        # حذف أي سطر فارغ تماماً من الداتا
        df = df.dropna(how='all')

        # تحويل الأعمدة الأساسية وتأمين وجودها
        if 'Status' in df.columns:
            df['Status'] = df['Status'].astype(str).fillna('Unknown')
        
        if 'Selling Price' in df.columns:
            # تنظيف السعر من أي علامة $ أو حروف وتحويله لرقم
            df['Selling Price'] = pd.to_numeric(df.astype(str)['Selling Price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"⚠️ خطأ في جلب البيانات: {e}")
        return pd.DataFrame()

# تحميل البيانات
df = load_data()

# عنوان التطبيق
st.title("🌐 Future Net Radius Manager")

# اختبار سريع (بيظهر لك فقط إذا الجدول فاضي)
if df.empty:
    st.warning("⚠️ الجدول فارغ حالياً.")
    st.info("تأكد من أن رابط الـ CSV في Secrets صحيح ومن وجود بيانات في ملف Google Sheets.")
    if st.button("🔄 محاولة تحديث"):
        st.cache_data.clear()
        st.rerun()
else:
    # 2. حساب الإحصائيات (الداشبورد)
    total_users = len(df)
    
    # فلترة الحالات (نشط، منتهي، أونلاين)
    active_count = len(df[df['Status'].str.contains('Active|Online', case=False, na=False)])
    expired_count = len(df[df['Status'].str.contains('Expired', case=False, na=False)])
    revenue = df['Selling Price'].sum() if 'Selling Price' in df.columns else 0

    # عرض البطاقات
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي المشتركين", total_users)
    col2.metric("نشط / أونلاين", active_count)
    col3.metric("منتهي", expired_count)
    col4.metric("المداخيل", f"${revenue:,.2f}")

    st.divider()

    # 3. أدوات التحكم الجانبية
    st.sidebar.header("البحث والفلترة")
    search = st.sidebar.text_input("🔎 ابحث عن اسم أو يوزر:")
    
    # تطبيق البحث
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # 4. عرض الجدول النهائي
    st.subheader("📋 قائمة المشتركين")
    
    # اختيار أعمدة العرض الأساسية (بناءً على السطر اللي بعتلي ياه)
    main_cols = ['Name', 'Username', 'Status', 'Expiry Date', 'Selling Price', 'Mobile Number', 'Signal Strength']
    # التأكد من عرض الأعمدة الموجودة فعلياً فقط
    display_cols = [c for c in main_cols if c in df.columns]
    
    if display_cols:
        st.dataframe(df[display_cols], width='stretch')
    else:
        st.dataframe(df, width='stretch') # عرض كل الأعمدة إذا لم يجد العناوين المحددة

    # زر التحميل الاحتياطي
    csv_backup = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 تحميل Backup CSV", csv_backup, "future_net_data.csv", "text/csv")

# زر التحديث في القائمة الجانبية
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
