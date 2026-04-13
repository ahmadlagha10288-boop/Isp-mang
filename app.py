import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Manager", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة أول سطر فقط لنعرف العناوين وننظفها
        df = pd.read_csv(url, skip_blank_lines=True)
        # تنظيف شامل لكل العناوين (مسح فراغات وتحويل لحروف صغيرة للمقارنة)
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    # دالة ذكية لإيجاد العمود حتى لو فيه اختلاف بسيط بالتسمية
    def get_col(target_name):
        for col in df.columns:
            if target_name.lower() in col.lower():
                return col
        return None

    # تحديد أسماء الأعمدة الحقيقية الموجودة بالملف
    status_col = get_col('Status')
    price_col = get_col('Selling Price')
    name_col = get_col('Name')
    expiry_col = get_col('Expiry Date')

    # حساب الإحصائيات بأمان (بدون KeyError)
    total_users = len(df)
    
    active_users = 0
    if status_col:
        active_users = len(df[df[status_col].astype(str).str.contains('Active|Online', case=False, na=False)])

    revenue = 0
    if price_col:
        # تحويل السعر لرقم بأمان
        temp_price = pd.to_numeric(df[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        revenue = temp_price.sum()

    # عرض المربعات العلوية
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المشتركين", total_users)
    c2.metric("نشط / أونلاين", active_users)
    c3.metric("إجمالي المبيعات", f"${revenue:,.2f}")

    st.divider()

    # البحث
    search = st.sidebar.text_input("🔍 ابحث هنا:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # عرض الجدول (الأعمدة اللي لاقاها البرنامج بس)
    cols_to_show = [c for c in [name_col, status_col, expiry_col, price_col] if c is not None]
    
    st.subheader("📋 قائمة البيانات")
    if cols_to_show:
        st.dataframe(df[cols_to_show], width='stretch')
    else:
        st.dataframe(df, width='stretch') # إذا ما عرف شي بيعرض كل شي

else:
    st.warning("⚠️ الملف فارغ أو الرابط غير صحيح.")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
