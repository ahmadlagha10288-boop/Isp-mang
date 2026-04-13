import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة لتناسب شاشة الموبايل
st.set_page_config(
    page_title="Future Net Manager",
    page_icon="🌐",
    layout="centered"
)

# 2. دالة جلب البيانات من رابط الـ CSV المباشر
def get_data():
    try:
        # بيقرأ الرابط من الـ Secrets اللي حطيناه
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة البيانات مع إلغاء الكاش لضمان تحديث البيانات دايماً
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"خطأ في الاتصال بالبيانات: {e}")
        return pd.DataFrame()

# تحميل البيانات
df = get_data()

# 3. واجهة المستخدم
st.title("📱 Future Net ISP")
st.markdown(f"**عدد المشتركين الكلي:** {len(df)}")

# القائمة الجانبية
menu = ["📊 عرض المشتركين", "🔍 بحث سريع", "ℹ️ معلومات السيرفر"]
choice = st.sidebar.selectbox("القائمة", menu)

if choice == "📊 عرض المشتركين":
    st.subheader("قائمة المشتركين")
    if not df.empty:
        # عرض الجدول بشكل يتناسب مع عرض الشاشة
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("لا توجد بيانات حالياً. تأكد من الرابط في Secrets.")

elif choice == "🔍 بحث سريع":
    st.subheader("البحث عن مشترك")
    search_q = st.text_input("ادخل اسم المشترك أو اليوزر...")
    if search_q:
        # البحث في كل الأعمدة
        mask = df.apply(lambda row: row.astype(str).str.contains(search_q, case=False).any(), axis=1)
        result = df[mask]
        if not result.empty:
            st.success(f"تم إيجاد {len(result)} مشترك")
            st.table(result)
        else:
            st.error("لم يتم العثور على نتائج")

elif choice == "ℹ️ معلومات السيرفر":
    st.info("النظام موصول بـ Google Sheets ويعمل بنظام التحديث التلقائي.")
    if st.button("🔄 تحديث البيانات الآن"):
        st.cache_data.clear()
        st.rerun()

# تذييل الصفحة
st.sidebar.markdown("---")
st.sidebar.write("Developed for Future Net")
