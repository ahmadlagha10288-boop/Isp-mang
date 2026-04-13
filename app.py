import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. إعداد واجهة التطبيق للأيفون
st.set_page_config(page_title="Future Net ISP", page_icon="🌐", layout="centered")

st.title("📱 Future Net Manager")
st.markdown("---")

# 2. الربط مع قاعدة البيانات (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

# دالة لجلب البيانات وتحديثها
def get_data():
    return conn.read(worksheet="Sheet1", ttl=0)

df = get_data()

# 3. القائمة الجانبية للتنقل
menu = ["📊 عرض المشتركين", "➕ إضافة مشترك", "🔍 بحث سريع"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

if choice == "📊 عرض المشتركين":
    st.subheader("قائمة المشتركين الحالية")
    st.dataframe(df, use_container_width=True)
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

elif choice == "➕ إضافة مشترك":
    st.subheader("إضافة مشترك جديد للسحابة")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("اسم المشترك")
        phone = st.text_input("رقم الهاتف")
        expiry = st.date_input("تاريخ الانتهاء")
        price = st.number_input("المبلغ المدفوع", min_value=0)
        
        if st.form_submit_button("حفظ وإرسال"):
            if name:
                # تجهيز السطر الجديد
                new_row = pd.DataFrame([{
                    "Name": name,
                    "Phone": phone,
                    "Expiry_Date": str(expiry),
                    "Price": price,
                    "Status": "Active"
                }])
                # دمج السطر الجديد مع البيانات القديمة
                updated_df = pd.concat([df, new_row], ignore_index=True)
                # تحديث ملف جوجل شيت
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success(f"تم حفظ {name} بنجاح!")
                st.balloons()
            else:
                st.error("الرجاء إدخال اسم المشترك")

elif choice == "🔍 بحث سريع":
    st.subheader("البحث عن مشترك")
    search_q = st.text_input("اكتب الاسم هنا...")
    if search_q:
        result = df[df['Name'].str.contains(search_q, case=False, na=False)]
        if not result.empty:
            st.table(result)
        else:
            st.warning("لا يوجد مشترك بهذا الاسم")
