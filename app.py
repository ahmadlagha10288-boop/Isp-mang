import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# تصميم CSS: تصغير الخطوط جداً وتحسين الرؤية
st.markdown("""
    <style>
    .card { background-color: #1a1a1a; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 5px solid #007bff; }
    .client-name { font-size: 0.9rem; font-weight: bold; color: white; margin-bottom: 2px; }
    .status-tag { font-size: 0.7rem; font-weight: bold; padding: 2px 5px; border-radius: 4px; display: inline-block; margin-bottom: 5px; }
    .info-box { background-color: #262626; padding: 6px; border-radius: 5px; color: #bbb; font-size: 0.75rem; line-height: 1.2; border: 1px solid #333; }
    .wa-btn { display: block; width: 100%; padding: 8px; text-align: center; border-radius: 5px; text-decoration: none !important; font-weight: bold; font-size: 0.8rem; color: white !important; margin-top: 4px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الشيت الخام
        df_all = pd.read_csv(url, header=None)
        
        # 1. تنظيف الداتا: تخطي أي سطر فيه كلمات متل "Action" أو "Name" أو "Radius"
        # رح ندور على أول سطر العمود التاني فيه مش "None" ومش "Name"
        data_start_idx = 0
        for i, row in df_all.iterrows():
            val_a = str(row[0]).strip().lower() # عمود A
            val_c = str(row[2]).strip().lower() # عمود C (الاسم في حالتك أحياناً بكون هون)
            if val_a != 'nan' and val_a != 'action' and val_a != 'radius' and val_c != 'name':
                data_start_idx = i
                break
        
        # إعادة بناء الجدول من سطر البيانات الحقيقي
        df = df_all.iloc[data_start_idx:].reset_index(drop=True)
        
        # 2. تسمية الأعمدة بناءً على وصفك (A=الاسم، B=الحالة، C=الخدمة، D=التاريخ)
        # رح ناخد أول 6 أعمدة احتياطاً
        df = df.iloc[:, :7] 
        df.columns = ['Name', 'Status', 'Service', 'RegTime', 'Mobile', 'Price', 'Extra']
        
        # تنظيف الأسماء من أي فراغات
        df['Name'] = df['Name'].astype(str).str.strip()
        df = df[df['Name'] != 'nan']
        
        # معالجة التاريخ والترتيب (من الأقدم للأحدث)
        df['RegTime'] = pd.to_datetime(df['RegTime'], errors='coerce')
        df = df.sort_values(by='RegTime', ascending=True)
        
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- واجهة التطبيق ---
st.sidebar.title("⭐ Future Net")
menu = st.sidebar.selectbox("القائمة:", ["📱 الرادار", "💵 المحاسبة", "💾 Backup"])

if menu == "📱 الرادار":
    st.title("📡 رادار المشتركين")
    search = st.text_input("🔍 بحث (اسم، رقم، حالة):")
    
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    today = datetime.now()
    cols = st.columns(2)
    
    for idx, row in df.reset_index(drop=True).iterrows():
        with cols[idx % 2]:
            # تحديد لون الحالة
            status = str(row['Status']).upper()
            st_color = "#2ecc71" if "ON" in status or "ACT" in status else "#ff4b4b"
            
            # حساب الأيام المتبقية (بناءً على 30 يوم من تاريخ التسجيل)
            days_str = "N/A"
            if pd.notnull(row['RegTime']):
                days_left = (row['RegTime'] + pd.Timedelta(days=30) - today).days
                days_str = f"باقي {days_left} يوم" if days_left >= 0 else "منتهي"

            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{row['Name']}</div>
                    <div class="status-tag" style="color:{st_color}; border: 1px solid {st_color};">● {status}</div>
                    <div class="info-box">
                        <b>🛠 {row['Service']}</b> | ⏳ {days_str}<br>
                        <b>💰 الدين:</b> ${row['Price']} | 📅 {row['RegTime'].strftime('%d/%m') if pd.notnull(row['RegTime']) else 'N/A'}
                    </div>
            """, unsafe_allow_html=True)

            # واتساب
            phone = str(row['Mobile']).replace('.0', '').strip()
            if phone != 'nan' and len(phone) > 5:
                m1 = quote(f"تنبيه: اشتراكك ينتهي خلال 3 أيام.")
                m2 = quote(f"يرجى تسديد مبلغ ${row['Price']} لتجديد الخدمة.")
                m3 = quote(f"تحذير: سيتم إيقاف الخدمة لعدم الدفع.")
                st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💵 المحاسبة":
    st.title("⚖️ المحاسبة")
    user = st.selectbox("الزبون:", df['Name'].unique())
    u_row = df[df['Name'] == user].iloc[0]
    curr = float(pd.to_numeric(u_row['Price'], errors='coerce') or 0)
    st.write(f"الحساب الحالي لـ {user}: **${curr}**")
    p, m = st.columns(2)
    with p: plus = st.number_input("زيادة (+)")
    with m: minus = st.number_input("نقص (-)")
    st.subheader(f"الصافي المطلوب: :blue[${curr + plus - minus}]")

elif menu == "💾 Backup":
    st.title("💾 نسخة احتياطية")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 تحميل ملف Excel (CSV)", csv, "FutureNet_Backup.csv")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
