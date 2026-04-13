import streamlit as st
import pandas as pd

st.set_page_config(page_title="Future Net Radius", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # الحل السحري: نخبره أن العناوين في السطر الثاني (header=1)
        df = pd.read_csv(url, header=1)
        # تنظيف العناوين
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    # --- اختيار الـ 5 أعمدة اللي طلبتهم بالضبط ---
    # تأكدت من أسمائهم من الصورة اللي بعتها
    requested_cols = ['Name', 'Service', 'Expiry Date', 'Mobile Number', 'Status']
    
    # فحص الأعمدة المتوفرة فعلياً
    available = [c for c in requested_cols if c in df.columns]
    
    if available:
        # عرض الـ 5 أعمدة فقط
        display_df = df[available].copy()
        
        # تحسين شكل العناوين للعرض فقط
        #Mobile Number -> Phone | Expiry Date -> Expiry
        display_df.columns = [c.replace('Mobile Number', 'Phone').replace('Expiry Date', 'Expiry') for c in display_df.columns]

        # الإحصائيات (Total Customers)
        st.metric("Total Customers", len(df))
        
        # حساب الأونلاين (Status)
        if 'Status' in display_df.columns:
            online_count = len(display_df[display_df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)])
            st.metric("Online Now", online_count)

        st.divider()

        # دالة تلوين الحالة (Status)
        def style_status(val):
            v = str(val).lower()
            if 'online' in v or 'active' in v:
                return 'background-color: #d4edda; color: #155724; font-weight: bold'
            if 'offline' in v or 'expired' in v:
                return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
            return ''

        # البحث
        search = st.sidebar.text_input("🔍 Search Customers:")
        if search:
            display_df = display_df[display_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

        # عرض الجدول
        if 'Status' in display_df.columns:
            st.dataframe(display_df.style.applymap(style_status, subset=['Status']), use_container_width=True)
        else:
            st.dataframe(display_df, use_container_width=True)
            
    else:
        # إذا ما لقى الأسماء، بيعرض كل شي عشان ما يختفوا
        st.warning("Column names didn't match. Showing all data:")
        st.dataframe(df, use_container_width=True)

else:
    st.info("The sheet is empty or the CSV URL is wrong.")

# زر التحديث في القائمة الجانبية
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
