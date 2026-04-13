import streamlit as st
import pandas as pd
from urllib.parse import quote

# إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

def load_data():
    try:
        # الرابط من Secrets وتصحيحه تلقائياً
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        csv_url = raw_url.replace('/edit', '/export?format=csv') if "edit" in raw_url else raw_url
        
        # قراءة البيانات - الإكسل عندك بيبدأ فوراً بالأسماء
        df = pd.read_csv(csv_url, header=None)
        
        # تنظيف أي سطر فارغ تماماً
        df = df.dropna(how='all')
        
        # ربط الأعمدة يدوياً حسب صورتك:
        # 0=A (abotol, khaled), 1=B (Status), 2=C (Service), 3=D (Expiry), 5=F (Phone)
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Username', 'Status', 'Package', 'Expiry', 'Phone']
        
        # حذف الكلمات التقنية والأسطر الفارغة
        df = df[df['Username'].notna()]
        df['Username'] = df['Username'].astype(str).str.strip()
        df = df[~df['Username'].str.contains('Radius|Action|Name|nan|Total', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.warning("⚠️ تأكد من أن رابط الجوجل شيت 'عام' (Anyone with the link).")
else:
    # عرض المشتركين
    for _, row in df.iterrows():
        # تحديد اللون حسب الحالة
        status = str(row['Status']).strip()
        status_color = "#2ecc71" if "Online" in status else "#e74c3c"
        
        with st.container():
            st.markdown(f"""
                <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:12px; border-left:6px solid {status_color};">
                    <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                    <div style="margin-top:8px; color:#bdc3c7; font-size:0.9rem;">
                        <b>📦 الباقة:</b> {row['Package']} | <b>📅 الانتهاء:</b> {row['Expiry']}
                    </div>
                    <p style="margin:5px 0 0 0; color:{status_color}; font-weight:bold;">● {status}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # زر الواتساب (من العمود F)
            phone = str(row['Phone']).replace('.0', '').replace(' ', '').strip()
            if phone != 'nan' and len(phone) >= 7:
                full_num = f"961{phone}" if not phone.startswith('961') else phone
                msg = quote(f"تنبيه من فيوتشر نت: المشترك {row['Username']}، اشتراكك {row['Package']} قارب على الانتهاء.")
                st.link_button(f"💬 مراسلة {row['Username']}", f"https://wa.me/{full_num}?text={msg}")
