import streamlit as st
import pandas as pd
from urllib.parse import quote

st.set_page_config(page_title="Future Net Radar", layout="wide")

def load_data():
    try:
        # قراءة الرابط من السيكرتس
        url = st.secrets["connections"]["spreadsheet"]
        # قراءة الداتا وتجاهل أول سطرين (عشان الـ nan اللي بالصور)
        df = pd.read_csv(url, header=None)
        
        # ربط الأعمدة: 0=الاسم، 1=الحالة، 2=الباقة، 3=التاريخ، 5=الهاتف
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Username', 'Status', 'Package', 'Expiry', 'Phone']
        
        # --- الفلتر القوي ---
        df = df.dropna(subset=['Username']) # حذف الأسطر الفاضية
        df['Username'] = df['Username'].astype(str).str.strip()
        # حذف أي سطر فيه nan أو Radius أو عناوين
        df = df[~df['Username'].str.contains('nan|Radius|Action|Name|Total', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"⚠️ مشكلة بالرابط: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.info("🔄 جاري سحب البيانات... تأكد من حفظ الـ Secrets وعمل Refresh.")
else:
    # عرض البيانات ككروت نظيفة
    for _, row in df.iterrows():
        status = str(row['Status']).strip()
        color = "#2ecc71" if "Online" in status else "#e74c3c"
        
        st.markdown(f"""
            <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:10px; border-left:6px solid {color};">
                <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                <p style="margin:5px 0; color:#ccc;">📦 {row['Package']} | 📅 {row['Expiry']}</p>
                <p style="margin:0; color:{color}; font-weight:bold;">● {status}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # زر الواتساب
        phone = str(row['Phone']).replace('.0', '').strip()
        if phone != 'nan' and len(phone) > 5:
            num = f"961{phone}" if not phone.startswith('961') else phone
            link = f"https://wa.me/{num}?text=" + quote(f"تنبيه للمشترك {row['Username']}: اشتراكك قارب على الانتهاء.")
            st.link_button(f"💬 مراسلة {row['Username']}", link)
