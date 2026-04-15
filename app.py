import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_config(page_title="Future Net", layout="wide")

# 2. اللغة والفرز (في السايد بار الخافت)
st.sidebar.markdown("<h4 style='color: #888;'>⚙️ Settings / الإعدادات</h4>", unsafe_allow_html=True)
lang = st.sidebar.radio("", ["العربية", "English"], label_visibility="collapsed")
sort_by = st.sidebar.selectbox("الترتيب / Sort", ["Name", "Expiry Date", "Status"])

# زر التحديث
if st.sidebar.button("🔄 Refresh / تحديث"):
    st.rerun()

texts = {
    "العربية": {"search": "🔍 ابحث...", "pkg": "باقة", "exp": "ينتهي", "days": "أيام", "debt": "دين"},
    "English": {"search": "🔍 Search...", "pkg": "Pkg", "exp": "Exp", "days": "Days", "debt": "Debt"}
}
t = texts[lang]

# 3. دالة جلب البيانات (معالجة ذكية للأخطاء)
def load_data():
    try:
        # تأكد أن الرابط في Secrets تحت [connections] واسمه spreadsheet
        url = st.secrets["connections"]["spreadsheet"]
        df = pd.read_csv(url, header=None).dropna(how='all')
        
        # تسمية الأعمدة المتوفرة وتكملة الناقص
        cols = ['Name', 'Status', 'Expiry', 'Package', 'Debt', 'Phone']
        current_cols = len(df.columns)
        df.columns = cols[:current_cols]
        
        for col in cols[current_cols:]: df[col] = 0 # إضافة أعمدة وهمية إذا مش موجودة
        
        df['Name'] = df['Name'].astype(str).str.strip()
        df = df[~df['Name'].str.contains('nan|Username|Radius|Total', case=False)]
        df['Expiry_Date'] = pd.to_datetime(df['Expiry'], errors='coerce')
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"⚠️ مشكلة بالرابط: {e}")
        return pd.DataFrame()

df = load_data()

# --- CSS التصميم البيضاوي والألوان ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .compact-card {{
        background-color: #004aad; border-radius: 12px;
        padding: 10px; margin-bottom: 10px; color: white;
        text-align: {'right' if lang == 'العربية' else 'left'};
        min-height: 140px;
    }}
    .border-green {{ border-{'right' if lang == 'العربية' else 'left'}: 10px solid #2ecc71; }}
    .border-yellow {{ border-{'right' if lang == 'العربية' else 'left'}: 10px solid #f1c40f; }}
    .border-red {{ border-{'right' if lang == 'العربية' else 'left'}: 10px solid #e74c3c; }}
    </style>
""", unsafe_allow_html=True)

if not df.empty:
    # الفرز
    if sort_by == "Name": df = df.sort_values('Name')
    elif sort_by == "Expiry Date": df = df.sort_values('Expiry_Date')

    search = st.text_input(t["search"], label_visibility="collapsed")
    if search: df = df[df['Name'].str.contains(search, case=False)]

    for i in range(0, len(df), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(df):
                row = df.iloc[i + j]
                days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else -1
                
                # تحديد اللون
                color_class = "border-green"
                if days_left < 0: color_class = "border-red"
                elif days_left <= 3: color_class = "border-yellow"

                with cols[j]:
                    st.markdown(f"""
                        <div class="compact-card {color_class}">
                            <div style="font-size: 1.2rem; font-weight: bold;">👤 {row['Name']}</div>
                            <div style="font-size: 0.9rem; color: #ddd;">📦 {row['Package']} | 📅 {str(row['Expiry'])[:10]}</div>
                            <div style="font-size: 0.9rem;">⏳ {t['days']}: {days_left if days_left >= 0 else 'Expired'}</div>
                            <div style="color: #ffb3b3; font-weight: bold;">💰 {t['debt']}: ${row['Debt']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار الواتساب (مصلحة تماماً)
                    phone = str(row['Phone']).replace('.0','') if row['Phone'] != 0 else "961"
                    def wa(msg): return f"https://wa.me/{phone}?text={quote(msg)}"

                    w1, w2, w3, w4 = st.columns(4)
                    w1.link_button("⚠️", wa(f"تذكير: اشتراكك ينتهي خلال 3 أيام."))
                    w2.link_button("✅", wa(f"تم تجديد اشتراكك بنجاح."))
                    w3.link_button("🔔", wa(f"يرجى تسديد الدين المتبقي لتجنب القطع."))
                    w4.link_button("🚫", wa(f"تم قطع الخدمة لعدم السداد."))
else:
    st.warning("⚠️ لا توجد بيانات. تأكد من إعدادات الرابط في الـ Secrets.")
