import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# تصميم CSS: خطوط صغيرة جداً لتناسب الموبايل وتوفير المساحة
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 5px solid #007bff; }
    .client-name { font-size: 0.85rem; font-weight: bold; color: white; margin-bottom: 2px; }
    .status-tag { font-size: 0.7rem; font-weight: bold; padding: 2px 5px; border-radius: 4px; display: inline-block; margin-bottom: 5px; }
    .info-box { background-color: #262626; padding: 6px; border-radius: 5px; color: #bbb; font-size: 0.75rem; line-height: 1.2; border: 1px solid #333; }
    .wa-btn { display: block; width: 100%; padding: 8px; text-align: center; border-radius: 5px; text-decoration: none !important; font-weight: bold; font-size: 0.8rem; color: white !important; margin-top: 4px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الشيت بالكامل
        df_raw = pd.read_csv(url, header=None)
        
        # تصفية البيانات: تجاهل الأسطر التعريفية (Radius, Action, Name) والأسطر الفارغة
        df_clean = df_raw[
            df_raw[0].notna() & 
            ~df_raw[0].astype(str).str.contains('Radius|Action|Name|nan', case=False)
        ].copy()
        
        # توزيع الأعمدة بناءً على طلبك الجديد:
        # A=الاسم(0), B=الحالة(1), C=الخدمة(2), D=تاريخ التسجيل(3), E=السعر(4), F=رقم التلفون(5)
        df_clean = df_clean.iloc[:, :6]
        df_clean.columns = ['Name', 'Status', 'Service', 'RegTime', 'Price', 'Mobile']
        
        # تنظيف وتحويل البيانات
        df_clean['RegTime'] = pd.to_datetime(df_clean['RegTime'], errors='coerce')
        # ترتيب: من الأقدم للأحدث (اللي خالص اشتراكه بيطلع أول واحد)
        df_clean = df_clean.sort_values(by='RegTime', ascending=True)
        
        return df_clean.reset_index(drop=True)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- واجهة التطبيق ---
st.title("📡 رادار فيوتشر نت")

if not df.empty:
    search = st.text_input("🔍 بحث عن مشترك:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    today = datetime.now()
    cols = st.columns(2) # عرض كرتين بجانب بعض لتوفير المساحة
    
    for idx, row in df.iterrows():
        with cols[idx % 2]:
            status = str(row['Status']).upper()
            st_color = "#2ecc71" if "ACT" in status or "ON" in status else "#ff4b4b"
            
            # حساب الأيام المتبقية
            days_str = "N/A"
            if pd.notnull(row['RegTime']):
                days_left = (row['RegTime'] + pd.Timedelta(days=30) - today).days
                days_str = f"باقي {days_left} يوم" if days_left >= 0 else "منتهي 🔴"

            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{row['Name']}</div>
                    <div class="status-tag" style="color:{st_color}; border: 1px solid {st_color};">● {status}</div>
                    <div class="info-box">
                        <b>🛠 {row['Service']}</b> | ⏳ {days_str}<br>
                        <b>💰 الحساب:</b> ${row['Price']} | 📅 {row['RegTime'].strftime('%d/%m') if pd.notnull(row['RegTime']) else 'N/A'}
                    </div>
            """, unsafe_allow_html=True)

            # سحب رقم التلفون من الكولون F (المسمى Mobile هنا)
            phone = str(row['Mobile']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) > 5:
                # إضافة مفتاح لبنان تلقائياً إذا مش موجود
                full_phone = f"961{phone}" if not phone.startswith('961') else phone
                
                m1 = quote(f"تنبيه: اشتراكك ينتهي خلال 3 أيام.")
                m2 = quote(f"يرجى تسديد مبلغ ${row['Price']} لتجديد الخدمة.")
                m3 = quote(f"تحذير: سيتم إيقاف الخدمة لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{full_phone}?text={m3}" class="wa-btn btn-3">🚫 إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# أزرار التحكم الجانبية
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()

csv = df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Backup CSV", csv, "FutureNet_Backup.csv")
