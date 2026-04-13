import streamlit as st
import pandas as pd
from datetime import datetime

# 1. إعدادات الواجهة
st.set_page_config(page_title="Future Net ISP Manager", layout="wide")

# 2. دالة جلب البيانات
def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        # تنظيف وتحويل التاريخ
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce').dt.date
        # تحويل السعر لرقم
        if 'Selling Price' in df.columns:
            df['Selling Price'] = pd.to_numeric(df['Selling Price'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")
        return pd.DataFrame()

df = load_data()

# 3. الداشبورد الاحترافي (Dashboard)
st.title("🌐 Future Net Radius Manager")

if not df.empty:
    # حساب الإحصائيات
    total_users = len(df)
    active_users = len(df[df['Status'].str.contains('Active|Online', na=False, case=False)])
    expired_users = len(df[df['Status'].str.contains('Expired', na=False, case=False)])
    total_revenue = df['Selling Price'].sum()

    # عرض المربعات العلوية
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي المشتركين", total_users)
    col2.metric("نشط / أونلاين", active_users)
    col3.metric("منتهي الصلاحية", expired_users, delta_color="inverse")
    col4.metric("إجمالي المبيعات", f"${total_revenue:,.2f}")

    st.divider()

    # 4. القائمة الجانبية والفلترة
    st.sidebar.header("لوحة التحكم")
    
    # فلترة حسب الحالة
    if 'Status' in df.columns:
        status_list = df['Status'].unique().tolist()
        selected_status = st.sidebar.multiselect("فلترة حسب الحالة:", status_list, default=status_list)
        df = df[df['Status'].isin(selected_status)]

    # بحث سريع
    search = st.sidebar.text_input("🔍 بحث (اسم، يوزر، هاتف):")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # 5. عرض البيانات المخصصة
    st.subheader("📋 بيانات المشتركين")
    # اختيار الأعمدة المهمة فقط للعرض السريع لتجنب زحمة الشاشة
    display_cols = ['Name', 'Username', 'Status', 'Expiry Date', 'Selling Price', 'Mobile Number', 'Signal Strength']
    available_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(df[available_cols], use_container_width=True)

    # 6. قسم الحسابات المالية
    with st.expander("💰 تفاصيل الحسابات والقطاعات"):
        if 'Sector' in df.columns:
            sector_revenue = df.groupby('Sector')['Selling Price'].sum()
            st.bar_chart(sector_revenue)

    # 7. نسخة احتياطية (Backup)
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 تحميل Backup (CSV)", csv, "future_net_full_backup.csv", "text/csv")

else:
    st.warning("لم يتم العثور على بيانات. تأكد من أن ملف جوجل شيت يحتوي على الأعمدة المذكورة.")

# زر التحديث
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
