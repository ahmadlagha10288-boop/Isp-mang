import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Pro", layout="wide")

# تصميم البطاقات
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-top: 4px solid #007bff; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .name { font-size: 1.2rem; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .status-active { color: #2ecc71; font-weight: bold; font-size: 0.9rem; }
    .status-expired { color: #e74c3c; font-weight: bold; font-size: 0.9rem; }
    .detail { color: #bbbbbb; font-size: 0.85rem; margin-top: 3px; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة الملف ومسح الأسطر الفاضية تماماً
        df = pd.read_csv(url).dropna(how='all')
        
        # البحث عن سطر العناوين الحقيقي (تجنب الـ Unnamed)
        for i in range(min(15, len(df))):
            row_list = df.iloc[i].astype(str).tolist()
            if any('Name' in x or 'Username' in x for x in row_list):
                df.columns = df.iloc[i].astype(str).str.strip()
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        
        df = df.dropna(subset=[df.columns[2]]) if len(df.columns) > 2 else df
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Radius")

if not df.empty:
    # --- دالة مساعدة لجلب البيانات بأمان ---
    def get_val(row, names, default="N/A"):
        for n in names:
            for col in df.columns:
                if n.lower() in col.lower():
                    val = row[col]
                    return str(val) if pd.notna(val) else default
        return default

    # البحث
    search = st.text_input("🔍 ابحث عن مشترك:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # --- عرض البطاقات ---
    cols = st.columns(2)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 2]:
            name = get_val(row, ['Name', 'Customer'])
            status = get_val(row, ['Status', 'State'], "Unknown")
            service = get_val(row, ['Service', 'Plan'])
            expiry = get_val(row, ['Expiry', 'Date', 'التاريخ'])
            price = get_val(row, ['Price', 'Selling', 'السعر'], "0")
            phone = get_val(row, ['Mobile', 'Phone', 'تلفون'], "").replace('.0', '')

            st_class = "status-active" if any(x in status.lower() for x in ['online', 'active']) else "status-expired"
            
            # عرض البطاقة
            st.markdown(f"""
                <div class="card">
                    <div class="name">{name}</div>
                    <div class="{st_class}">● {status}</div>
                    <div class="detail">🛠 {service} | 📅 {expiry}</div>
                    <div class="detail">💰 Price: ${price}</div>
                </div>
            """, unsafe_allow_html=True)

            # زر واتساب
            if phone and phone != "nan" and len(phone) > 5:
                wa_link = f"https://wa.me/{phone}?text={quote('مرحباً ' + name + '، معك Future Net')}"
                st.markdown(f"[📲 WhatsApp]({wa_link})")

else:
    st.warning("⚠️ لا يوجد بيانات لعرضها. تأكد من ملف جوجل شيت.")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
