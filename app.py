import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Admin Pro", layout="wide")

# تصميم CSS: تصغير الخطوط، تحسين المربعات، وألوان واضحة للحالات
st.markdown("""
    <style>
    .card { 
        background-color: #1e1e1e; 
        border-radius: 10px; 
        padding: 10px; 
        margin-bottom: 8px; 
        border-left: 5px solid #007bff;
    }
    .client-name { font-size: 0.95rem; font-weight: bold; color: #ffffff; margin-bottom: 2px; }
    .status-tag { font-size: 0.75rem; font-weight: bold; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 6px; }
    .info-box { background-color: #2b2b2b; padding: 6px; border-radius: 6px; color: #d0d0d0; font-size: 0.8rem; line-height: 1.3; }
    .wa-btn { 
        display: block; width: 100%; padding: 6px; text-align: center; border-radius: 5px; 
        text-decoration: none !important; font-weight: bold; font-size: 0.75rem; color: white !important; margin-top: 4px;
    }
    .btn-alert { background-color: #f39c12; } 
    .btn-pay { background-color: #d35400; } 
    .btn-stop { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة البيانات مع تحديد أسماء الأعمدة يدوياً بناءً على طلبك
        df = pd.read_csv(url)
        
        # إعادة تسمية الأعمدة بناءً على الترتيب (A, B, C, D...)
        new_cols = {
            df.columns[0]: 'Name',      # كولون A
            df.columns[1]: 'Status',    # كولون B
            df.columns[2]: 'Service',   # كولون C
            df.columns[3]: 'Timestamp'  # كولون D (وقت التشريج)
        }
        df.rename(columns=new_cols, inplace=True)
        
        # تنظيف البيانات
        df = df[df['Name'].notna()].reset_index(drop=True)
        
        # معالجة التاريخ (كولون D) لترتيب المشتركين
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            # ترتيب من الأقدم للأحدث (اللي شحن من زمان بيطلع أول شي لأنه قرب يخلص)
            df = df.sort_values(by='Timestamp', ascending=True)
            
        return df
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

df = load_data()

# --- القائمة الجانبية ---
st.sidebar.title("⭐ Future Net")
menu = st.sidebar.selectbox("القائمة:", ["📱 الرادار", "💵 المحاسبة", "💾 النسخ والتقارير"])

if menu == "📱 الرادار":
    st.title("📡 رادار المشتركين")
    search = st.text_input("🔍 بحث عن اسم، خدمة أو حالة:")
    
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    cols = st.columns(2)
    for idx, row in df.iterrows():
        with cols[idx % 2]:
            status = str(row.get('Status', 'Offline')).strip().lower()
            
            # تحديد لون الحالة بناءً على كولون B
            color_map = {
                'online': '#2ecc71',
                'active': '#2ecc71',
                'blocked': '#95a5a6',
                'expired': '#ff4b4b',
                'offline': '#e67e22'
            }
            current_color = color_map.get(status, '#ffffff')
            
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{row['Name']}</div>
                    <div class="status-tag" style="color:{current_color}; border: 1px solid {current_color};">
                        ● {status.upper()}
                    </div>
                    <div class="info-box">
                        <b>🛠 الخدمة:</b> {row.get('Service', 'N/A')}<br>
                        <b>📅 آخر تشريج:</b> {row.get('Timestamp', 'N/A')}<br>
                        <b>💰 السعر:</b> ${row.get('Selling Price', '0')}
                    </div>
            """, unsafe_allow_html=True)

            # أزرار الواتساب المختصرة
            phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
            if phone and phone != 'nan':
                m1 = quote(f"تنبيه من فيوتشر نت: اشتراكك ({row.get('Service')}) قارب على الانتهاء.")
                m2 = quote(f"يرجى تسديد الحساب لتجديد الخدمة. شكراً.")
                m3 = quote(f"سيتم إيقاف الخدمة حالاً لعدم تسديد المستحقات.")
                
                st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-alert">⚠️ تنبيه</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-pay">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-stop">🚫 إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💵 المحاسبة":
    st.title("⚖️ إدارة الديون")
    user = st.selectbox("اختر الزبون:", df['Name'].unique())
    u_row = df[df['Name'] == user].iloc[0]
    
    # استخراج السعر الحالي من الكولون المناسب
    curr_debt = float(pd.to_numeric(u_row.get('Selling Price', 0), errors='coerce') or 0)
    
    st.info(f"الزبون: **{user}** | الحساب الحالي: **${curr_debt}**")
    
    c1, c2 = st.columns(2)
    with c1: plus = st.number_input("زيادة (+)", min_value=0.0)
    with c2: minus = st.number_input("نقص (-)", min_value=0.0)
    
    st.subheader(f"الحساب الجديد: :green[${curr_debt + plus - minus}]")
    st.caption("ملاحظة: عدّل الرقم النهائي في ملف الإكسل.")

elif menu == "💾 النسخ والتقارير":
    st.title("💾 النسخ الاحتياطي")
    total = pd.to_numeric(df['Selling Price'], errors='coerce').sum()
    st.metric("إجمالي المبالغ المطلوبة", f"${total:,.2f}")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 تحميل نسخة إكسل (Backup)", csv, f"FutureNet_{datetime.now().date()}.csv")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
