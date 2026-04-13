import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

def load_data():
    try:
        # جلب الرابط من Secrets
        url = st.secrets["connections"]["spreadsheet"]
        # قراءة الملف (بدون header لأن البيانات تبدأ فوراً)
        df = pd.read_csv(url, header=None)
        
        # تنظيف الأسطر الفاضية
        df = df.dropna(how='all')
        
        # بما أن لديك 4 أعمدة فقط الآن:
        # 0=Username, 1=Status, 2=Date, 3=Package
        df = df.iloc[:, [0, 1, 2, 3]]
        df.columns = ['Username', 'Status', 'Expiry', 'Package']
        
        # فلترة الأسماء (حذف nan وأي كلمات تقنية)
        df['Username'] = df['Username'].astype(str).str.strip()
        df = df[~df['Username'].str.contains('nan|Username|Radius|Total', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"⚠️ خطأ في القراءة: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.info("🔄 جاري مزامنة البيانات... تأكد من عمل Refresh.")
else:
    # عرض البيانات كبطاقات
    for _, row in df.iterrows():
        # تحديد لون الحالة
        status = str(row['Status']).strip()
        color = "#2ecc71" if "Online" in status else "#e74c3c"
        
        st.markdown(f"""
            <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:10px; border-left:6px solid {color}; shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                <p style="margin:5px 0; color:#ccc; font-size:0.9rem;">
                    📦 <b>الباقة:</b> {row['Package']} <br>
                    📅 <b>الانتهاء:</b> {row['Expiry']}
                </p>
                <p style="margin:0; color:{color}; font-weight:bold;">● {status}</p>
            </div>
        """, unsafe_allow_html=True)

# زر التحديث
if st.sidebar.button("🔄 تحديث البيانات"):
    st.rerun()
