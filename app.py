import streamlit as st
import pandas as pd

st.set_page_config(page_title="Future Net Manager", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        # تنظيف العناوين
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    # --- اختيار الأعمدة حسب الأسماء الإنجليزية اللي بعتتها ---
    # هول الـ 5 اللي طلبتهم بالضبط
    target_english = ['Name', 'Service', 'Expiry Date', 'Mobile Number', 'Status']
    
    # فحص الأعمدة الموجودة فعلياً
    available = [c for c in target_english if c in df.columns]
    
    if len(available) > 0:
        # عرض فقط الأعمدة الـ 5
        display_df = df[available].copy()
        
        # تحسين شكل العناوين للعرض فقط
        display_df.columns = [c.replace('Mobile Number', 'Phone').replace('Expiry Date', 'Expiry') for c in display_df.columns]

        # الإحصائيات
        c1, c2 = st.columns(2)
        c1.metric("Total Customers", len(df))
        
        # حساب الأونلاين
        online_count = 0
        if 'Status' in df.columns:
            online_count = len(df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)])
        c2.metric("Online Now", online_count)

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
        search = st.sidebar.text_input("🔍 Search:")
        if search:
            display_df = display_df[display_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

        # عرض الجدول
        if 'Status' in display_df.columns:
            st.dataframe(display_df.style.applymap(style_status, subset=['Status']), use_container_width=True)
        else:
            st.dataframe(display_df, use_container_width=True)
            
    else:
        # إذا ما لقى الأسماء الإنجليزية، بيعرض كل شي عشان ما يختفوا
        st.warning("Column names didn't match. Showing all data:")
        st.dataframe(df, use_container_width=True)

else:
    st.info("The sheet is empty or the URL is wrong.")

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
