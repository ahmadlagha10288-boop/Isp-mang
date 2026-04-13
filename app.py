import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Ultra Pro", layout="wide")

# تصميم CSS: تصغير الخطوط وتحسين الواجهة
st.markdown("""
    <style>
    .card { 
        background-color: #262730; 
        border-radius: 12px; 
        padding: 12px; 
        margin-bottom: 10px; 
        border-left: 5px solid #007bff;
    }
    .client-name { 
        font-size: 1.1rem; /* تصغير الخط */
        font-weight: bold; 
        color: #ffffff; 
    }
    .days-tag { 
        font-size: 0.9rem; 
        font-weight: bold; 
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .debt-box { 
        background-color: #343541;
        padding: 10px; 
        border-radius: 8px; 
        color: #e0e0e0; 
        font-size: 0.9rem; /* تصغير خط المعلومات */
        line-height: 1.4;
    }
    .wa-btn { 
        display: block; 
        width: 100%; 
        padding: 8px; 
        text-align: center; 
        border-radius: 6px; 
        text-decoration: none !important; 
        font-weight: bold; 
        font-size: 0.85rem;
        color: white !important;
        margin-top: 5px;
    }
    .btn-1 { background-color: #f39c12; } 
    .btn-2 { background-color: #d35400; } 
    .btn-3 { background-color: #c0392b; } 
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df_raw = pd.read_csv(url, header=None)
        h_idx = 0
        for i, row in df_raw.iterrows():
            if "Name" in row.values:
                h_idx = i
                break
        df = pd.read_csv(url, header=h_idx)
        df.columns = df.columns.astype(str).str.strip()
        df = df[df['Name'].notna()].reset_index(drop=True)
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.title("⭐ Future Net Admin")
menu = st.sidebar.selectbox("القائمة الرئيسية:", ["📱 الرادار والواتساب", "💵 المحاسبة والديون", "📊 التقارير والنسخ الاحتياطي"])

if menu == "📱 الرادار والواتساب":
    st.title("📡 رادار المشتركين")
    
    # فلتر سريع (نصيحة: فرز المنتهيين)
    show_expired_only = st.sidebar.checkbox("عرض المنتهيين فقط 🔴")
    
    search = st.text_input("🔍 ابحث عن اسم:")
    
    today = datetime.now()
    if show_expired_only:
        df = df[df['Expiry Date'] < today]
    if search:
        df = df[df['Name'].str.contains(search, case=False, na=False)]

    cols = st.columns(2)
    for idx, row in df.iterrows():
        with cols[idx % 2]:
            expiry = row.get('Expiry Date')
            days_left = (expiry - today).days if pd.notnull(expiry) else 0
            st_color = "#2ecc71" if days_left > 0 else "#ff4b4b"
            bg_tag = "rgba(46, 204, 113, 0.1)" if days_left > 0 else "rgba(255, 75, 75, 0.1)"
            
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{row['Name']}</div>
                    <div class="days-tag" style="color:{st_color}; background:{bg_tag};">
                        ● باقي {days_left} يوم
                    </div>
                    <div class="debt-box">
                        <b>📞 الهاتف:</b> {row.get('Mobile Number', 'N/A')}<br>
                        <b>💰 الدين:</b> ${row.get('Selling Price', '0')} | 🛠️ {row.get('Service', 'N/A')}
                    </div>
            """, unsafe_allow_html=True)

            phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
            if phone and phone != 'nan':
                m1 = quote(f"تنبيه: اشتراكك ينتهي خلال 3 أيام.")
                m2 = quote(f"نرجو تسديد مبلغ ${row.get('Selling Price')} لتجديد الاشتراك.")
                m3 = quote(f"تنبيه أخير: سيتم إيقاف الخدمة لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💵 المحاسبة والديون":
    st.title("⚖️ إدارة الحسابات (زيادة ونقص)")
    user = st.selectbox("اختر الزبون:", df['Name'].unique())
    u_row = df[df['Name'] == user].iloc[0]
    curr_debt = float(u_row.get('Selling Price', 0))
    
    st.warning(f"الحساب الحالي لـ {user}: **${curr_debt}**")
    
    col1, col2 = st.columns(2)
    with col1:
        plus = st.number_input("إضافة دين (+) $", min_value=0.0, step=1.0)
    with col2:
        minus = st.number_input("قبض مبلغ (-) $", min_value=0.0, step=1.0)
    
    final = curr_debt + plus - minus
    st.subheader(f"الحساب الجديد: :blue[${final}]")
    st.info("قم بتعديل الرقم في الإكسل ليتم الحفظ بشكل دائم.")

elif menu == "📊 التقارير والنسخ الاحتياطي":
    st.title("💾 الإدارة والنسخ الاحتياطي")
    
    # إحصائيات سريعة (نصيحة)
    total_money = df['Selling Price'].astype(float).sum()
    st.metric("إجمالي المبالغ المطلوبة في السوق", f"${total_money:,.2f}")
    
    st.divider()
    st.subheader("📥 تحميل نسخة احتياطية")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV Backup (Excel)",
        data=csv,
        file_name=f"FutureNet_Backup_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
