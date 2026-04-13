import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide", initial_sidebar_state="expanded")

# 2. دالة جلب البيانات (مصححة)
def load_data():
    try:
        # تأكد أن اسم المفتاح في Secrets هو 'spreadsheet' تحت [connections]
        url = st.secrets["connections"]["spreadsheet"]
        df = pd.read_csv(url, header=None)
        df = df.dropna(how='all')
        
        # ربط الأعمدة حسب ملفك الجديد (4 أعمدة)
        df = df.iloc[:, [0, 1, 2, 3]]
        df.columns = ['Username', 'Status', 'Expiry', 'Package']
        
        # تنظيف البيانات
        df['Username'] = df['Username'].astype(str).str.strip()
        df = df[~df['Username'].str.contains('nan|Username|Radius|Total', case=False)]
        
        # تحويل التاريخ لنوع تاريخ كرمال الترتيب والجدولة
        df['Expiry_Date'] = pd.to_datetime(df['Expiry'], errors='coerce')
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بالقاعدة: {e}")
        return pd.DataFrame()

# استدعاء البيانات
df = load_data()

# --- واجهة المستخدم الرئيسية ---
st.title("📡 Future Net Management System")

if not df.empty:
    # --- قسم الإحصائيات الذكية ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي المشتركين", len(df))
    with col2:
        online_count = len(df[df['Status'].str.contains('Online', case=False)])
        st.metric("متصل الآن ✅", online_count)
    with col3:
        expired_count = len(df[df['Status'].str.contains('Expired|Offline', case=False)])
        st.metric("منتهي ❌", expired_count)
    with col4:
        # حساب المشتركين اللي رح يخلصوا خلال 3 أيام
        near_expiry = len(df[(df['Expiry_Date'] - datetime.now()).dt.days <= 3])
        st.metric("قرب يخلص ⚠️", near_expiry)

    st.divider()

    # --- لوحة التحكم الجانبية ---
    st.sidebar.header("🛠️ أدوات الإدارة")
    
    # 1. التحكم بالترتيب (طلبك: المتوقف إلى المشرج حديثاً)
    sort_order = st.sidebar.selectbox("نظام العرض:", ["حسب الحالة (Expired أولاً)", "حسب التاريخ (الأقرب للانتهاء)", "أبجدي (A-Z)"])
    
    if sort_order == "حسب الحالة (Expired أولاً)":
        df = df.sort_values(by=['Status', 'Expiry_Date'], ascending=[True, True])
    elif sort_order == "حسب التاريخ (الأقرب للانتهاء)":
        df = df.sort_values(by='Expiry_Date')
    
    # 2. التشريج الجماعي (محاكاة - لإظهار التكلفة والجدولة)
    if st.sidebar.button("⚡ تشريج شهر كامل للجميع"):
        st.sidebar.success(f"تمت جدولة {len(df)} مشترك لتمديد 30 يوم!")
        st.sidebar.info("ملاحظة: يتطلب gspread لتعديل الشيت مباشرة.")

    # 3. بيك اب (Backup)
    st.sidebar.download_button("📥 سحب نسخة احتياطية", df.to_csv(index=False).encode('utf-8'), "FutureNet_Backup.csv")

    # --- خانة البحث ودافع/مش دافع ---
    search = st.text_input("🔍 ابحث عن مشترك...")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    # --- عرض بطاقات المشتركين ---
    for idx, row in df.iterrows():
        # تحديد لون البطاقة حسب الحالة والوقت
        days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else -1
        
        card_border = "#2ecc71" # أخضر
        if "Online" not in str(row['Status']):
            card_border = "#e74c3c" # أحمر
        elif days_left <= 3:
            card_border = "#f1c40f" # أصفر (تنبيه)

        with st.container():
            st.markdown(f"""
                <div style="background:#1a1a1a; padding:15px; border-radius:10px; border-left:8px solid {card_border}; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between;">
                        <h4 style="margin:0;">👤 {row['Username']}</h4>
                        <span style="color:{card_border};">● {row['Status']}</span>
                    </div>
                    <div style="font-size:0.9rem; color:#bbb; margin-top:5px;">
                        📦 الباقة: {row['Package']} | ⏳ الأيام المتبقية: {days_left if days_left >= 0 else 'منتهي'}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # أزرار الإدارة السريعة
            c1, c2, c3 = st.columns(3)
            with c1:
                st.button("💰 تم الدفع", key=f"pay_{idx}")
            with c2:
                st.button("🔄 تمديد شهر", key=f"ext_{idx}")
            with c3:
                link = f"https://wa.me/961?text=" + quote(f"عزيزي {row['Username']}، اشتراكك {row['Package']} سينتهي بتاريخ {row['Expiry']}.")
                st.link_button("📲 واتساب", link)

else:
    st.warning("⚠️ لم نتمكن من سحب البيانات. تأكد من إعدادات الرابط في الـ Secrets.")
