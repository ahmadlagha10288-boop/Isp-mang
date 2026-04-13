import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Admin Pro", layout="wide")

# تصميم الألوان والخطوط الصغيرة
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 5px solid #007bff; }
    .client-name { font-size: 0.9rem; font-weight: bold; color: white; margin-bottom: 2px; }
    .status-tag { font-size: 0.7rem; font-weight: bold; padding: 2px 5px; border-radius: 4px; display: inline-block; margin-bottom: 5px; }
    .info-box { background-color: #2b2b2b; padding: 6px; border-radius: 5px; color: #ccc; font-size: 0.8rem; line-height: 1.2; }
    .wa-btn { display: block; width: 100%; padding: 6px; text-align: center; border-radius: 4px; text-decoration: none !important; font-weight: bold; font-size: 0.75rem; color: white !important; margin-top: 3px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة كل الداتا بدون عناوين أولية
        raw_df = pd.read_csv(url, header=None)
        
        # البحث عن السطر اللي فيه أول اسم (تجاهل Radius وأي Unnamed)
        # رح ندور على أول سطر بيحتوي داتا حقيقية في العمود الأول
        start_row = 0
        for i in range(len(raw_df)):
            val = str(raw_df.iloc[i, 0]).lower()
            if val != 'nan' and val != 'radius' and val != 'name':
                start_row = i
                break
        
        # إعادة القراءة وتثبيت الأعمدة A, B, C, D
        df = pd.read_csv(url, skiprows=start_row, header=None)
        
        # تسمية الأعمدة بناءً على طلبك
        # A=0, B=1, C=2, D=3, والبيع رح نعتبره E=4 أو F=5 حسب ملفك
        df = df.iloc[:, :6] # ناخد أول 6 أعمدة للامان
        df.columns = ['Name', 'Status', 'Service', 'Timestamp', 'Mobile', 'Price']
        
        # تنظيف
        df = df[df['Name'].notna()]
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        
        # الترتيب: من الأقدم للأحدث (الخالص أول)
        df = df.sort_values(by='Timestamp', ascending=True)
        return df
    except Exception as e:
        st.error(f"خطأ: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Pro")

if not df.empty:
    search = st.text_input("🔍 بحث سريع:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    today = datetime.now()
    cols = st.columns(2)
    
    for idx, row in df.reset_index(drop=True).iterrows():
        with cols[idx % 2]:
            status = str(row['Status']).strip().upper()
            st_color = "#2ecc71" if "ON" in status or "ACT" in status else "#ff4b4b"
            
            # حساب الأيام المتبقية تقريبياً (إذا الشهر 30 يوم)
            days_left = "N/A"
            if pd.notnull(row['Timestamp']):
                expiry_date = row['Timestamp'] + pd.Timedelta(days=30)
                days_left = (expiry_date - today).days

            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{row['Name']}</div>
                    <div class="status-tag" style="color:{st_color}; border: 1px solid {st_color};">● {status}</div>
                    <div class="info-box">
                        <b>🛠 {row['Service']}</b> | ⏳ باقي: {days_left} يوم<br>
                        <b>💰 الدين:</b> ${row['Price']} | 📅 {row['Timestamp']}
                    </div>
            """, unsafe_allow_html=True)

            phone = str(row['Mobile']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) > 5:
                m1 = quote(f"تنبيه: اشتراكك ينتهي قريباً.")
                m2 = quote(f"يرجى دفع ${row['Price']} لتجديد الخدمة.")
                m3 = quote(f"تنبيه أخير: سيتم قطع الخط لعدم الدفع.")
                st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# أزرار التحديث والنسخ بالجنب
if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

csv = df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Backup CSV", csv, "FutureNet.csv")
