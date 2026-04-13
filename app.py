import streamlit as st
import pandas as pd

st.set_page_config(page_title="Future Net - Clean View", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        # تنظيف العناوين من أي فراغات خفية
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"خطأ: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Manager")

if not df.empty:
    # --- دالة ذكية لإيجاد الأعمدة حتى لو في اختلاف بسيط بالاسم ---
    def find_column(options):
        for col in df.columns:
            if any(opt.lower() in col.lower() for opt in options):
                return col
        return None

    # منحدد الأعمدة بناءً على اللي طلبته
    target_cols = {
        'الاسم': find_column(['Name', 'الاسم', 'Customer']),
        'نوع الخدمة': find_column(['Service', 'الخدمة', 'Plan']),
        'التاريخ': find_column(['Expiry Date', 'تاريخ', 'End Date']),
        'رقم الهاتف': find_column(['Mobile Number', 'Phone', 'تلفون']),
        'الحالة': find_column(['Status', 'حالة', 'Online'])
    }

    # منشيل الـ None (الأعمدة اللي ما لاقاها)
    existing_cols = {v: k for k, v in target_cols.items() if v is not None}
    
    if existing_cols:
        # منعمل جدول جديد فيه بس اللي لاقيناه
        display_df = df[list(existing_cols.keys())].copy()
        # منغير الأسماء للعربي
        display_df = display_df.rename(columns=existing_cols)

        # إحصائيات سريعة
        c1, c2 = st.columns(2)
        c1.metric("👥 عدد الزبائن", len(df))
        
        # عرض الجدول مع تلوين الحالة إذا موجودة
        def color_status(val):
            v = str(val).lower()
            if 'online' in v or 'active' in v: return 'background-color: #d4edda; color: #155724'
            if 'offline' in v or 'expired' in v: return 'background-color: #f8d7da; color: #721c24'
            return ''

        st.subheader("📋 القائمة المطلوبة")
        if 'الحالة' in display_df.columns:
            st.dataframe(display_df.style.applymap(color_status, subset=['الحالة']), use_container_width=True)
        else:
            st.dataframe(display_df, use_container_width=True)
    else:
        # إذا فشل الكود بمعرفة الأسماء، بيعرض الجدول كامل عشان ما يختفوا الزباين
        st.warning("⚠️ لم أستطع تحديد الأعمدة المطلوبة بدقة، إليك الجدول الكامل:")
        st.dataframe(df, use_container_width=True)

else:
    st.info("الجدول فارغ أو الرابط غير صحيح.")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
