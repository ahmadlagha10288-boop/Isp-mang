import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Manager", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة البيانات وتنظيف أسماء الأعمدة فوراً
        df = pd.read_csv(url)
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Dashboard")

if not df.empty:
    # --- تحديد الـ 5 أعمدة اللي طلبتهم بالضبط ---
    # ملاحظة: استخدمت الأسماء اللي بعتلي ياها بأول سطر
    cols_map = {
        'Name': 'الاسم',
        'Service': 'نوع الخدمة',
        'Expiry Date': 'تاريخ الانتهاء',
        'Mobile Number': 'رقم الهاتف',
        'Status': 'الحالة (Online/Offline)'
    }

    # فحص أي أعمدة موجودة فعلياً في ملفك لتجنب أي خطأ
    available_cols = [c for c in cols_map.keys() if c in df.columns]
    
    # --- الإحصائيات العلوية ---
    total = len(df)
    online = 0
    if 'Status' in df.columns:
        online = len(df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)])

    col1, col2 = st.columns(2)
    col1.metric("👥 إجمالي الزبائن", total)
    col2.metric("🟢 أونلاين حالياً", online)

    st.divider()

    # --- البحث والجدول ---
    search = st.sidebar.text_input("🔍 بحث عن زبون:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    st.subheader("📋 قائمة المشتركين المختصرة")
    
    if available_cols:
        # عرض الـ 5 أعمدة فقط مع إعادة تسميتهم للعربية لتسهيل القراءة
        display_df = df[available_cols].rename(columns=cols_map)
        
        # إضافة ألوان لعمود الحالة (أخضر للأونلاين وأحمر للأوفلاين)
        def color_status(val):
            v = str(val).lower()
            if 'online' in v or 'active' in v: return 'color: #2ecc71; font-weight: bold'
            if 'offline' in v or 'expired' in v: return 'color: #e74c3c; font-weight: bold'
            return ''

        # إذا كان عمود الحالة موجود، نطبق عليه الألوان
        status_ar = cols_map.get('Status')
        if status_ar in display_df.columns:
            st.dataframe(display_df.style.applymap(color_status, subset=[status_ar]), use_container_width=True)
        else:
            st.dataframe(display_df, use_container_width=True)
    else:
        # إذا ما لقى الأسماء بالضبط، بيعرض لك الجدول كما هو عشان ما يختفي شي
        st.warning("⚠️ لم يتم العثور على الأعمدة بالأسماء المطلوبة، عرض الجدول الكامل:")
        st.dataframe(df, use_container_width=True)

else:
    st.info("الجدول فارغ، تأكد من الرابط في Secrets.")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
