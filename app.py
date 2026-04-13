import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

def load_data():
    try:
        # الرابط من Secrets وتصحيحه ليصبح رابط تحميل CSV
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        csv_url = raw_url.replace('/edit', '/export?format=csv') if "edit" in raw_url else raw_url
        
        # قراءة البيانات بدون عناوين (لأن بياناتك تبدأ فوراً من السطر الأول)
        df = pd.read_csv(csv_url, header=None)
        
        # اختيار الأعمدة بناءً على ملفك الحقيقي (الذي يظهر في صورة الإكسل)
        # العمود 0 هو (A) وهو "اليوزر نيم" مثل abotol و khaled3adra
        # العمود 1 هو (B) وهو الحالة
        # العمود 2 هو (C) وهو نوع الخدمة
        # العمود 3 هو (D) وهو تاريخ الانتهاء
        # العمود 5 هو (F) وهو رقم الهاتف
        
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Username', 'Status', 'Service', 'Expiry', 'Phone']
        
        # تنظيف البيانات من الأسطر التقنية (مثل Radius أو Action)
        df = df[df['Username'].notna()]
        df = df[~df['Username'].astype(str).str.contains('Radius|Action|Name|nan', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame() # إرجاع جدول فارغ عند الخطأ لتجنب الشاشة السوداء

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    # رسالة تنبيه واضحة بدلاً من الشاشة السوداء
    st.warning("⚠️ لا توجد بيانات. تأكد من أن رابط الجوجل شيت 'عام' للجميع.")
else:
    # عرض البيانات ككروت مع التركيز على اليوزر نيم
    for _, row in df.iterrows():
        with st.container():
            # استخدام Username (العمود A) كعنوان للكرت
            st.markdown(f"""
                <div style="background:#1a1a1a; padding:15px; border-radius:10px; margin-bottom:10px; border-left:5px solid #007bff;">
                    <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                    <p style="margin:5px 0; color:#ccc;">🛠️ باقة: {row['Service']} | 📅 الانتهاء: {row['Expiry']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # إعداد رقم الهاتف للواتساب
            phone = str(row['Phone']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) >= 7:
                full_num = f"961{phone}" if not phone.startswith('961') else phone
                msg = quote(f"تنبيه من فيوتشر نت: المشترك {row['Username']}، اشتراكك قارب على الانتهاء.")
                st.link_button(f"💬 مراسلة {row['Username']} عبر واتساب", f"https://wa.me/{full_num}?text={msg}")
