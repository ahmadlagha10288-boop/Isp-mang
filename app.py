import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Admin", layout="wide")

# تصميم CSS: تصغير الخطوط وترتيب البطاقات
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 10px; padding: 10px; margin-bottom: 8px; border-left: 5px solid #007bff; }
    .client-name { font-size: 0.9rem; font-weight: bold; color: white; }
    .status-tag { font-size: 0.75rem; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-top: 4px; display: inline-block; }
    .info-box { background-color: #2b2b2b; padding: 8px; border-radius: 6px; color: #ddd; font-size: 0.8rem; line-height: 1.3; margin-top: 5px; }
    .wa-btn { display: block; width: 100%; padding: 7px; text-align: center; border-radius: 5px; text-decoration: none !important; font-weight: bold; font-size: 0.8rem; color: white !important; margin-top: 4px; }
    .btn-1 { background-color: #f39c12; } .btn-2 { background-color: #d35400; } .btn-3 { background-color: #c0392b; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url)
        # تنظيف الداتا من العناوين الفارغة والأسطر الوهمية
        df = df[df.iloc[:, 0].notna()]
        df = df[~df.iloc[:, 0].astype(str).str.contains('Radius|Action|Name|nan', case=False)]
        
        # تحويل عمود التاريخ (تأكد إنه اسمه Expiry Date أو التاريخ بالإكسل)
        for col in df.columns:
            if 'date' in col.lower() or 'expiry' in col.lower() or 'تاريخ' in col:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df.sort_values(by=col, ascending=True) # الترتيب من الخالص للمطوّل
                break
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- الواجهة ---
st.sidebar.title("⭐ Future Net")
menu = st.sidebar.selectbox("القائمة:", ["📱 الرادار", "💵 المحاسبة", "💾 Backup"])

if menu == "📱 الرادار":
    st.title("📡 رادار المشتركين")
    search = st.text_input("🔍 بحث عن اسم أو رقم:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    today = datetime.now()
    cols = st.columns(2)
    
    for idx, row in df.reset_index(drop=True).iterrows():
        with cols[idx % 2]:
            name = row.iloc[0] # عمود A
            status = str(row.iloc[1]) # عمود B
            price = row.get('Selling Price', '0')
            phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
            
            st.markdown(f"""
                <div class="card">
                    <div class="client-name">{name}</div>
                    <div class="status-tag" style="background: rgba(46, 204, 113, 0.2); color: #2ecc71;">● {status}</div>
                    <div class="info-box">
                        💰 <b>الدين:</b> ${price} <br>
                        📞 <b>الهاتف:</b> {phone}
                    </div>
            """, unsafe_allow_html=True)
            
            if len(phone) > 5:
                m1 = quote("تنبيه: اشتراكك ينتهي خلال 3 أيام.")
                m2 = quote(f"يرجى تسديد مبلغ ${price} لتجديد الخدمة.")
                m3 = quote("تنبيه أخير: سيتم إيقاف الخدمة اليوم.")
                st.markdown(f'<a href="https://wa.me/{phone}?text={m1}" class="wa-btn btn-1">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m2}" class="wa-btn btn-2">💸 طلب دفع</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://wa.me/{phone}?text={m3}" class="wa-btn btn-3">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💵 المحاسبة":
    st.title("⚖️ إدارة الحسابات")
    user = st.selectbox("الزبون:", df.iloc[:, 0].unique())
    u_row = df[df.iloc[:, 0] == user].iloc[0]
    curr = float(pd.to_numeric(u_row.get('Selling Price', 0), errors='coerce') or 0)
    st.info(f"الحساب الحالي لـ {user}: **${curr}**")
    p, m = st.columns(2)
    plus = p.number_input("زيادة (+)")
    minus = m.number_input("نقص (-)")
    st.subheader(f"الصافي: ${curr + plus - minus}")

elif menu == "💾 Backup":
    st.title("💾 النسخة الاحتياطية")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 تحميل ملف CSV", csv, "Backup.csv")

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
