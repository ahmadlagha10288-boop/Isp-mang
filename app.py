import streamlit as st
import pandas as pd
from urllib.parse import quote

# إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

def load_data():
    try:
        # سحب الرابط وتجهيزه
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        csv_url = raw_url.replace('/edit', '/export?format=csv') if "edit" in raw_url else raw_url
        
        # قراءة البيانات (الإكسل عندك بيبدأ من أول سطر بدون عناوين)
        df = pd.read_csv(csv_url, header=None)
        
        # تحديد الأعمدة بالظبط من الصورة:
        # 0 = العمود A (اليوزر نيم: abotol, khaled3adra...)
        # 1 = العمود B (الحالة: Online/Expired)
        # 2 = العمود C (الخدمة: bs-Gold/Silver)
        # 3 = العمود D (تاريخ الانتهاء)
        # 5 = العمود F (رقم التلفون)
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Username', 'Status', 'Service', 'Expiry', 'Phone']
        
        # تنظيف: حذف أي سطر مش زبون (متل Radius أو Action)
        df['Username'] = df['Username'].astype(str)
        df = df[~df['Username'].str.contains('Radius|Action|Name|nan|Total', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.warning("⚠️ لا توجد بيانات. تأكد من أن الرابط في Secrets صحيح وعام.")
else:
    # خانة البحث
    search = st.text_input("🔍 ابحث عن يوزر نيم:")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    for _, row in df.iterrows():
        # تحديد لون الحالة
        is_online = "Online" in str(row['Status'])
        status_color = "#2ecc71" if is_online else "#e74c3c"
        
        with st.container():
            # عرض اليوزر نيم (العمود A) هو الأساس
            st.markdown(f"""
                <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:12px; border-left:6px solid {status_color};">
                    <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                    <p style="margin:5px 0; color:#ccc;">🛠️ الباقة: {row['Service']} | 📅 الانتهاء: {row['Expiry']}</p>
                    <p style="margin:0; color:{status_color}; font-weight:bold;">● {row['Status']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # زر الواتساب (من العمود F)
            phone = str(row['Phone']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) >= 7:
                clean_phone = phone.replace(' ', '').replace('+', '')
                full_phone = f"961{clean_phone}" if not clean_phone.startswith('961') else clean_phone
                msg = quote(f"تنبيه من Future Net: عزيزي المشترك {row['Username']}، نود إعلامك بأن اشتراكك ينتهي قريباً.")
                st.link_button(f"💬 مراسلة {row['Username']}", f"https://wa.me/{full_phone}?text={msg}")
