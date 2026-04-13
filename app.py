import streamlit as st
import pandas as pd

st.set_page_config(page_title="Future Net Manager", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف مع تجاهل الأسطر الفاضية في البداية
        df = pd.read_csv(url, on_bad_lines='skip')
        # تنظيف أسماء الأعمدة
        df.columns = df.columns.astype(str).str.strip()
        # حذف أي صفوف أو أعمدة فارغة تماماً
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        return df
    except Exception as e:
        st.error(f"خطأ: تأكد من رابط الـ CSV في Secrets. {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    # عرض عدد المشتركين الحقيقي
    st.metric("إجمالي المشتركين", len(df))
    
    st.subheader("📋 قائمة البيانات")
    # عرض الجدول كاملاً لنشوف شو الأسماء اللي طلعت
    st.dataframe(df, width='stretch')
else:
    st.info("يرجى التأكد من اختيار بصيغة CSV عند النشر (Publish to web).")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
