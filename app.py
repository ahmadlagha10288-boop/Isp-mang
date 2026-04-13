import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Ultra Manager", layout="wide")

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة من السطر الثاني كما اتفقنا
        df = pd.read_csv(url, header=1)
        df.columns = df.columns.astype(str).str.strip()
        
        # تنظيف البيانات المالية والتواريخ
        if 'Selling Price' in df.columns:
            df['Selling Price'] = pd.to_numeric(df['Selling Price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- واجهة المستخدم ---
st.title("⚡ Future Net Ultra Manager 2026")

if not df.empty:
    # 2. الحسابات الذكية (Logic)
    today = datetime.now().date()
    near_expiry_days = today + timedelta(days=2)
    
    # فلاتر ذكية
    online_df = df[df['Status'].astype(str).str.contains('Online|Active', case=False, na=False)]
    expired_df = df[df['Status'].astype(str).str.contains('Expired|Offline', case=False, na=False)]
    near_expiry_df = df[(df['Expiry Date'] >= today) & (df['Expiry Date'] <= near_expiry_days)]
    
    # 3. الداشبورد السريع (Top Metrics)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 المشتركين", len(df))
    c2.metric("🟢 أونلاين", len(online_df))
    c3.metric("⏳ قريباً ينتهي", len(near_expiry_df))
    c4.metric("💰 المداخيل", f"${df['Selling Price'].sum():,.0f}")

    st.divider()

    # 4. القائمة الجانبية المتقدمة
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/906/906343.png", width=100)
    menu = st.sidebar.selectbox("القسم الإداري:", 
        ["📋 الإدارة العامة", "💸 قسم المديونين", "📡 تحليل الشبكة (Sectors)", "📩 مراسلة واتساب", "💾 Backup"])

    # --- القسم 1: الإدارة العامة ---
    if menu == "📋 الإدارة العامة":
        st.subheader("📊 قائمة المشتركين")
        
        # فلاتر سريعة
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            search = st.text_input("🔎 بحث سريع:")
        with col_f2:
            if 'Service' in df.columns:
                service_filter = st.multiselect("فلترة بالخدمة:", df['Service'].unique())
                if service_filter:
                    df = df[df['Service'].isin(service_filter)]

        if search:
            df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

        # عرض الجدول بتنسيق لوني
        def color_rows(val):
            if 'Online' in str(val): return 'color: #2ecc71; font-weight: bold'
            if 'Expired' in str(val): return 'color: #e74c3c; font-weight: bold'
            return ''

        st.dataframe(df.style.applymap(color_rows, subset=['Status'] if 'Status' in df.columns else []), use_container_width=True)

    # --- القسم 2: المديونين ---
    elif menu == "💸 قسم المديونين":
        st.subheader("🔴 المبالغ المستحقة")
        debt_df = df[df['Status'].astype(str).str.contains('Expired|Block', case=False, na=False)]
        if not debt_df.empty:
            st.warning(f"إجمالي ديون السوق: ${debt_df['Selling Price'].sum():,.2f}")
            st.table(debt_df[['Name', 'Status', 'Selling Price', 'Mobile Number']])
        else:
            st.success("السوق نظيف! لا يوجد ديون ✅")

    # --- القسم 3: تحليل الشبكة ---
    elif menu == "📡 تحليل الشبكة (Sectors)":
        st.subheader("📍 توزيع المشتركين حسب القطاع والبرج")
        if 'Sector' in df.columns:
            sector_counts = df['Sector'].value_counts()
            st.bar_chart(sector_counts)
            
            # تفاصيل الإشارة
            if 'Signal Strength' in df.columns:
                st.write("⚠️ المشتركين بإشارة ضعيفة (أقل من -80):")
                weak_signal = df[df['Signal Strength'].astype(str).str.contains(r'-[89]\d', regex=True, na=False)]
                st.dataframe(weak_signal[['Name', 'Sector', 'Signal Strength']])

    # --- القسم 4: واتساب ---
    elif menu == "📩 مراسلة واتساب":
        st.subheader("💬 مراسلة سريعة")
        user = st.selectbox("اختر الزبون:", df['Name'].tolist())
        u_data = df[df['Name'] == user].iloc[0]
        
        msg_type = st.radio("نوع الرسالة:", ["تذكير دفع", "تنبيه قرب انتهاء", "رسالة ترحيب"])
        
        messages = {
            "تذكير دفع": f"عزيزي {user}، يرجى سداد مبلغ ${u_data['Selling Price']} لتجنب انقطاع الخدمة.",
            "تنبيه قرب انتهاء": f"عزيزي {user}، اشتراكك {u_data['Service']} ينتهي بتاريخ {u_data['Expiry Date']}. يرجى التجديد.",
            "رسالة ترحيب": f"شكراً لاختيارك Future Net! نحن في خدمتك دائماً."
        }
        
        final_msg = messages[msg_type]
        phone = str(u_data['Mobile Number']).replace('.0', '')
        wa_link = f"https://wa.me/{phone}?text={quote(final_msg)}"
        
        st.info(f"نص الرسالة: {final_msg}")
        st.markdown(f'[اضغط هنا للإرسال عبر واتساب 📲]({wa_link})')

    # --- القسم 5: Backup ---
    elif menu == "💾 Backup":
        st.subheader("📥 حفظ نسخة احتياطية")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Backup", csv, "FutureNet_Backup.csv", "text/csv")

else:
    st.error("لم نتمكن من العثور على بيانات. تأكد من أن Google Sheet منشورة بصيغة CSV.")

# زر التحديث
if st.sidebar.button("🔄 Refresh System"):
    st.cache_data.clear()
    st.rerun()
 as st
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
