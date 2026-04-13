import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net - Clean View", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        # تنظيف العناوين من الفراغات
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Manager")

if not df.empty:
    # --- تحديد الأعمدة المطلوبة فقط واستبعاد الباقي ---
    # هول الأسماء لازم يطابقوا اللي بالأكسل عندك
    requested_cols = {
        'Name': 'الاسم',
        'Service': 'نوع الخدمة',
        'Expiry Date': 'التاريخ',
        'Mobile Number': 'رقم الهاتف',
        'Status': 'الحالة'
    }

    # فلترة الأعمدة: بناخد بس اللي موجود بالليست فوق
    available_cols = [c for c in requested_cols.keys() if c in df.columns]
    
    # إنشاء نسخة جديدة من الجدول فيها بس الأعمدة المطلوبة
    final_df = df[available_cols].copy()
    
    # تغيير الأسماء للعربية عشان الترتيب والجمالية
    final_df = final_df.rename(columns=requested_cols)

    # --- الإحصائيات (فوق الجدول) ---
    total = len(final_df)
    # حساب الأونلاين من العمود الأصلي قبل الحذف
    online = 0
    if 'Status' in df.columns:
        online = len(df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)])

    c1, c2 = st.columns(2)
    c1.metric("👥 عدد الزبائن", total)
    c2.metric("🟢 أونلاين", online)

    st.divider()

    # --- البحث ---
    search = st.sidebar.text_input("🔍 بحث سريع:")
    if search:
        final_df = final_df[final_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # --- عرض الجدول المنسق ---
    st.subheader("📋 القائمة المختصرة")

    # دالة الألوان للحالة
    def color_status(val):
        v = str(val).lower()
        if 'online' in v or 'active' in v: return 'background-color: #d4edda; color: #155724; font-weight: bold' # خلفية خضراء فاتحة
        if 'offline' in v or 'expired' in v: return 'background-color: #f8d7da; color: #721c24; font-weight: bold' # خلفية حمراء فاتحة
        return ''

    # تطبيق التنسيق وعرض الجدول
    if 'الحالة' in final_df.columns:
        st.dataframe(final_df.style.applymap(color_status, subset=['الحالة']), use_container_width=True)
    else:
        st.dataframe(final_df, use_container_width=True)

else:
    st.info("الجدول فاضي أو الرابط غلط.")

# زر التحديث
if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
