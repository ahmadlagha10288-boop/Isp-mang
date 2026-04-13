import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة والهوية
st.set_page_config(page_title="Future Net Pro Manager", layout="wide")

# دالة لتنسيق الألوان في الجدول
def color_status(val):
    color = 'white'
    if 'Online' in str(val) or 'Active' in str(val):
        color = '#2ecc71' # أخضر
    elif 'Expired' in str(val) or 'Offline' in str(val):
        color = '#e74c3c' # أحمر
    elif 'Near Expiry' in str(val):
        color = '#f1c40f' # أصفر
    return f'color: {color}; font-weight: bold'

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        df.columns = df.columns.astype(str).str.strip()
        df = df.dropna(how='all', axis=0)
        return df
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return pd.DataFrame()

df = load_data()

# --- التصميم العلوي ---
st.title("🚀 Future Net Professional Dashboard")
st.markdown("---")

if not df.empty:
    # 2. الحسابات الذكية
    total_users = len(df)
    active_users = len(df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)]) if 'Status' in df.columns else 0
    expired_users = len(df[df['Status'].astype(str).str.contains('Expired', case=False, na=False)]) if 'Status' in df.columns else 0
    
    # حساب المداخيل مع تنظيف العملة
    revenue = 0
    if 'Selling Price' in df.columns:
        revenue = pd.to_numeric(df['Selling Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()

    # عرض البطاقات الملونة (Metrics)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 إجمالي المشتركين", total_users)
    c2.metric("🟢 نشط / أونلاين", active_users)
    c3.metric("🔴 منتهي الصلاحية", expired_users)
    c4.metric("💰 المداخيل الكلية", f"${revenue:,.2f}")

    st.markdown("---")

    # 3. الفلاتر الجانبية (الأدوات)
    st.sidebar.header("🛠️ أدوات التحكم")
    
    # فلترة حسب القطاع (Sector)
    if 'Sector' in df.columns:
        sectors = ['الكل'] + sorted(df['Sector'].dropna().unique().tolist())
        selected_sector = st.sidebar.selectbox("اختار القطاع / المنطقة:", sectors)
        if selected_sector != 'الكل':
            df = df[df['Sector'] == selected_sector]

    # بحث سريع
    search = st.sidebar.text_input("🔍 بحث (اسم، يوزر، رقم):")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # 4. عرض الجدول مع التنسيق اللوني (Styling)
    st.subheader("📋 إدارة بيانات المشتركين")
    
    # تحديد الأعمدة المراد عرضها فقط
    cols_to_show = ['Name', 'Username', 'Status', 'Expiry Date', 'Selling Price', 'Mobile Number', 'Sector', 'Signal Strength']
    available_cols = [c for c in cols_to_show if c in df.columns]

    # تطبيق الألوان على عمود الحالة
    if 'Status' in available_cols:
        styled_df = df[available_cols].style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.dataframe(df[available_cols], use_container_width=True)

    # 5. تنبيهات الإشارة الضعيفة (Signal Alert)
    if 'Signal Strength' in df.columns:
        with st.expander("⚠️ تنبيهات الإشارة الضعيفة"):
            low_signal = df[df['Signal Strength'].astype(str).str.contains(r'-[89]\d', regex=True, na=False)]
            if not low_signal.empty:
                st.warning(f"يوجد {len(low_signal)} مشتركين يعانون من إشارة ضعيفة (أقل من -80)")
                st.table(low_signal[['Name', 'Username', 'Signal Strength']])
            else:
                st.success("جميع الإشارات ضمن النطاق الجيد ✅")

else:
    st.warning("يرجى التأكد من أن رابط الـ CSV في Secrets يعمل وأن الملف يحتوي على بيانات.")

# زر التحديث
if st.sidebar.button("🔄 تحديث شامل للبيانات"):
    st.cache_data.clear()
    st.rerun()
