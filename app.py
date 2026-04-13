import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        # أهم خطوة: تنظيف أسماء الأعمدة من أي فراغات خفية أو أحرف غريبة
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🚀 Future Net ISP Manager")

if not df.empty:
    # --- دالة للبحث عن الأعمدة بذكاء ---
    def find_col(possible_names):
        for col in df.columns:
            if col.lower().strip() in [n.lower() for n in possible_names]:
                return col
        return None

    # تحديد الأعمدة الموجودة فعلياً
    status_col = find_col(['Status', 'حالة'])
    price_col = find_col(['Selling Price', 'السعر', 'Price'])
    name_col = find_col(['Name', 'الاسم'])
    
    # حساب الإحصائيات (فقط إذا الأعمدة موجودة)
    total = len(df)
    active = 0
    if status_col:
        active = len(df[df[status_col].astype(str).str.contains('Online|Active', case=False, na=False)])
    
    revenue = 0
    if price_col:
        rev_data = pd.to_numeric(df[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        revenue = rev_data.sum()

    # عرض المربعات
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 إجمالي المشتركين", total)
    c2.metric("🟢 نشط / أونلاين", active)
    c3.metric("💰 المداخيل", f"${revenue:,.2f}")

    st.divider()

    # البحث
    search = st.sidebar.text_input("🔍 بحث سريع:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # عرض الجدول (الأعمدة الأساسية التي وجدها البرنامج)
    # زدت لك ميزة: إذا ما لقى الأعمدة، بيعرض لك أول 10 أعمدة من الجدول عشان ما يضل فاضي
    main_display = [c for c in [name_col, 'Username', status_col, 'Expiry Date', price_col, 'Mobile Number'] if c in df.columns]
    
    st.subheader("📋 قائمة المشتركين")
    if main_display:
        # إضافة الألوان يدوياً فقط لعمود الحالة إذا وجد
        def color_status(val):
            if 'Online' in str(val) or 'Active' in str(val): return 'color: #2ecc71'
            if 'Expired' in str(val) or 'Offline' in str(val): return 'color: #e74c3c'
            return ''

        if status_col:
            st.dataframe(df[main_display].style.applymap(color_status, subset=[status_col]), use_container_width=True)
        else:
            st.dataframe(df[main_display], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True) # عرض كل شيء في حال فشل تحديد الأعمدة

else:
    st.warning("الجدول فارغ. تأكد من رابط الـ CSV.")

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
