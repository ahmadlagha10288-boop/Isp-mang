import streamlit as st
import pandas as pd
from urllib.parse import quote

# إعدادات الصفحة
st.set_page_config(page_title="Future Net", layout="wide")

def load_data():
    try:
        # الرابط من الـ Secrets
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # تحويل الرابط لـ CSV مباشر (هيدا اللي بيخلي البرنامج يشتغل بدون ما ترفع ملف)
        if "edit" in raw_url:
            csv_url = raw_url.replace('/edit', '/export?format=csv')
        else:
            csv_url = raw_url
            
        # قراءة البيانات - العمود A هو اليوزر نيم
        df = pd.read_csv(csv_url, header=None)
        
        # إذا الملف فيه بيانات، رتب الأعمدة
        if not df.empty:
            # 0=A (Username), 1=B (Status), 2=C (Service), 3=D (Expiry), 5=F (Phone)
            df = df.iloc[:, [0, 1, 2, 3, 5]]
            df.columns = ['Username', 'Status', 'Service', 'Expiry', 'Phone']
            
            # تنظيف من الكلمات التقنية
            df = df[df['Username'].notna()]
            df = df[~df['Username'].astype(str).str.contains('Radius|Action|Name|nan', case=False)]
            return df
        return pd.DataFrame()
    except Exception as e:
        # بدل الشاشة السوداء، رح يطبعلك شو الغلط بالظبط
        st.error(f"مشكلة في الاتصال: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار المشتركين")

if df.empty:
    st.warning("⚠️ لا توجد بيانات حالياً. تأكد من أن رابط الجوجل شيت 'عام' (Anyone with the link).")
else:
    # عرض البيانات ككروت
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"""
                <div style="background:#1a1a1a; padding:15px; border-radius:10px; margin-bottom:10px; border-left:5px solid #007bff;">
                    <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                    <p style="margin:5px 0; color:#ccc;">🛠️ الخدمة: {row['Service']} | 📅 الانتهاء: {row['Expiry']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # زر الواتساب (باستخدام العمود F)
            phone = str(row['Phone']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) > 5:
                num = f"961{phone}" if not phone.startswith('961') else phone
                link = f"https://wa.me/{num}?text=" + quote(f"تنبيه للمشترك {row['Username']}: اشتراكك قارب على الانتهاء.")
                st.link_button(f"💬 مراسلة {row['Username']}", link)
