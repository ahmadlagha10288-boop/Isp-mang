import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Admin Pro", layout="wide")

# تصميم CSS: تحسين الألوان وتصغير الخطوط للرؤية السريعة
st.markdown("""
    <style>
    .card { 
        background-color: #262730; 
        border-radius: 12px; 
        padding: 12px; 
        margin-bottom: 10px; 
        border-left: 5px solid #007bff;
    }
    .client-name { font-size: 1.1rem; font-weight: bold; color: #ffffff; }
    .days-tag { font-size: 0.85rem; font-weight: bold; padding: 2px 8px; border-radius: 4px; margin-bottom: 8px; display: inline-block; }
    .debt-box { background-color: #343541; padding: 10px; border-radius: 8px; color: #e0e0e0; font-size: 0.9rem; line-height: 1.4; }
    .wa-btn { 
        display: block; width: 100%; padding: 8px; text-align: center; border-radius: 6px; 
        text-decoration: none !important; font-weight: bold; font-size: 0.8rem; color: white !important; margin-top: 4px;
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
            # تحويل التاريخ وترتيب الداتا (من الأقدم للأحدث)
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce')
            df = df.sort_values(by='Expiry Date', ascending=True) # الترتيب المطلوب
            
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- القائمة الجانبية ---
st.sidebar.title("⭐ Future Net Admin")
menu = st.sidebar.selectbox("القائمة الرئيسية:", ["📱 الرادار والواتساب", "💵 المحاسبة والديون", "📊 التقارير والنسخ الاحتياطي"])

if menu == "📱 الرادار والواتساب":
    st.title("📡 رادار المشتركين (مرتب حسب الانتهاء)")
    
    search = st.text_input("🔍 ابحث عن اسم أو رقم تلفون:")
    today = datetime.now()

    if search:
        # البحث في الاسم أو رقم التلفون
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    cols = st.columns(2)
    for idx, row in df.iterrows():
        with cols[idx % 2]:
            expiry = row.get('Expiry Date')
            days_left = (expiry - today).days if pd.notnull(expiry) else 0
            
            # تحديد اللون حسب الحالة
            st_color = "#ff4b4b" if days_left <= 0 else ("#f39c12" if days_left <= 3 else "#2ecc71")
            bg_tag = "rgba(255, 75, 75, 0.1)" if days_left <= 0 else "rgba(46, 204, 113, 0.1)"
            
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{row['Name']}</div>
                    <div class="days-tag" style="color:{st_color}; background:{bg_tag};">
                        ● {"منتهي الصلاحية" if days_left < 0 else f"باقي {days_left} يوم"}
                    </div>
                    <div class="debt-box">
                        <b>📞 الهاتف:</b> {str(row.get('Mobile Number', 'N/A')).replace('.0', '')}<br>
                        <b>💰 الدين:</b> ${row.get('Selling Price', '0')} | 🛠️ {row.get('Service', 'N/A')}
                    </div>
            """, unsafe_allow_html=True)

            phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
            if phone and phone != 'nan':
                m1 = quote(f"تنبيه من Future Net: اشتراكك ينتهي خلال 3 أيام.")
                m2 = quote(f"يرجى تسديد مبلغ ${row.get('Selling Price')} لتجديد الاشتراك.")
                m3 = quote(f"تنبيه أخير: سيتم إيقاف الخدمة اليوم لعدم الدفع.")
                
                st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💵 المحاسبة والديون":
    st.title("⚖️ إدارة الحسابات")
    user = st.selectbox("اختر الزبون:", df['Name'].unique())
    u_row = df[df['Name'] == user].iloc[0]
    curr_debt = float(pd.to_numeric(u_row.get('Selling Price', 0), errors='coerce') or 0)
    
    st.info(f"الحساب الحالي لـ {user}: **${curr_debt}**")
    
    col1, col2 = st.columns(2)
    with col1: plus = st.number_input("إضافة دين (+) $", min_value=0.0)
    with col2: minus = st.number_input("قبض مبلغ (-) $", min_value=0.0)
    
    final = curr_debt + plus - minus
    st.subheader(f"الحساب الجديد: :blue[${final}]")
    st.write("👉 عدّل الرقم في الإكسل ليتم الحفظ.")

elif menu == "📊 التقارير والنسخ الاحتياطي":
    st.title("💾 الإدارة والنسخ")
    total_money = pd.to_numeric(df['Selling Price'], errors='coerce').sum()
    st.metric("إجمالي المبالغ المطلوبة بالسوق", f"${total_money:,.2f}")
    
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 تحميل نسخة احتياطية (Backup)", csv, f"FutureNet_{datetime.now().date()}.csv", "text/csv")

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
