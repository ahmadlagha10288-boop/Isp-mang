import streamlit as st
import pandas as pd

st.set_page_config(page_title="ISP Manager", layout="wide")

# تصميم العناوين
st.title("📡 نظام إدارة مشتركين ISP")
st.markdown("---")

uploaded_file = st.file_uploader("ارفع ملف Radius 2.csv")

if uploaded_file:
    # قراءة الملف
    df = pd.read_csv(uploaded_file)
    
    # قائمة بالأعمدة اللي بدك ياها (تأكد إن الأسماء مطابقة للملف عندك)
    cols_to_show = ['Username', 'Status', 'Service', 'Current Speed', 'Expired']
    
    # التأكد أن الأعمدة موجودة فعلياً في الملف لتجنب الأخطاء
    existing_cols = [c for c in cols_to_show if c in df.columns]
    df_filtered = df[existing_cols]

    # قسم البحث
    st.subheader("🔍 البحث السريع")
    search_term = st.text_input("ابحث عن مشترك (Username):")
    
    if search_term:
        df_filtered = df_filtered[df_filtered['Username'].astype(str).str.contains(search_term, case=False, na=False)]

    # عرض البيانات
    st.write(f"عرض {len(df_filtered)} مشترك")
    st.dataframe(df_filtered, use_container_width=True)

    # تنبيه للمشتركين المنتهيين (Expired)
    if 'Expired' in df_filtered.columns:
        st.sidebar.warning("مشتركين قاربوا على الانتهاء أو انتهوا")
        # هنا يمكن إضافة فلترة للمنتهيين لاحقاً
