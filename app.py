import streamlit as st
import pandas as pd
from urllib.parse import quote

# إعداد الصفحة
st.set_page_config(page_title="Future Net Radar", layout="wide")

def load_data():
    try:
        # تحويل الرابط لصيغة CSV مباشرة
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        csv_url = raw_url.replace('/edit', '/export?format=csv') if "edit" in raw_url else raw_url
        
        # قراءة الملف مع تجاهل أي تعقيدات في العناوين
        df = pd.read_csv(csv_url, header=None)
        
        # تنظيف: حذف أي سطر فارغ تماماً لتجنب ظهور كلمة nan
        df = df.dropna(how='all')
        
        # إجبار الكود على أخذ الأعمدة حسب الترتيب في صورتك (A, B, C, D, F):
        # 0=A (اليوزر نيم)، 1=B (الحالة)، 2=C (الباقة)، 3=D (تاريخ الانتهاء)، 5=F (الهاتف)
        df = df.iloc[:, [0, 1, 2, 3, 5]]
        df.columns = ['Username', 'Status', 'Package', 'Expiry', 'Phone']
        
        # فلترة: إزالة الأسطر التي تحتوي على عناوين تقنية أو قيم فارغة في الاسم
        df = df[df['Username'].notna()]
        df['Username'] = df['Username'].astype(str).str.strip()
        df = df[~df['Username'].str.contains('Radius|Action|Name|nan|Total', case=False)]
        
        return df.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

st.title("📡 رادار فيوتشر نت")

if df.empty:
    st.warning("⚠️ لم نتمكن من سحب البيانات. تأكد من أن ملف الإكسل يبدأ بالبيانات من الخانة A1.")
else:
    # خانة البحث عن يوزر نيم محدد
    search = st.text_input("🔍 ابحث عن يوزر نيم (مثلاً: abotol):")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    for _, row in df.iterrows():
        # تحديد لون الحالة (Online = أخضر، Expired = أحمر)
        status = str(row['Status']).strip()
        is_online = "Online" in status
        status_color = "#2ecc71" if is_online else "#e74c3c"
        
        with st.container():
            st.markdown(f"""
                <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:12px; border-left:6px solid {status_color};">
                    <h3 style="margin:0; color:white; font-family:sans-serif;">👤 {row['Username']}</h3>
                    <div style="margin-top:8px; color:#bdc3c7; font-size:0.95rem;">
                        <b>📦 الباقة:</b> {row['Package']} <br>
                        <b>📅 الانتهاء:</b> {row['Expiry']} <br>
                        <b>🚦 الحالة:</b> <span style="color:{status_color};">{status}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # معالجة رقم الهاتف (العمود F) لفتح الواتساب
            phone = str(row['Phone']).replace('.0', '').replace(' ', '').strip()
            if phone != 'nan' and len(phone) >= 7:
                # إضافة مفتاح لبنان 961 إذا لم يكن موجوداً
                full_num = f"961{phone}" if not phone.startswith('961') else phone
                msg = quote(f"تنبيه من Future Net: عزيزي المشترك {row['Username']}، نود تذكيرك بموعد تجديد اشتراكك ({row['Package']}).")
                st.link_button(f"💬 مراسلة {row['Username']}", f"https://wa.me/{full_num}?text={msg}")
