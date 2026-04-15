import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. إعداد الصفحة والستايل
st.set_page_config(page_title="Future Net Ultimate", layout="wide")

# 2. اللغات والترجمة
if 'lang' not in st.session_state: st.session_state.lang = 'العربية'
lang_choice = st.sidebar.radio("🌐 Language / اللغة", ["العربية", "English"])

texts = {
    "العربية": {
        "title": "📡 رادار فيوتشر نت - الإدارة الشاملة",
        "search": "🔍 ابحث عن اسم...",
        "sort": "الترتيب حسب",
        "debt": "دين", "pkg": "باقة", "days": "أيام",
        "pay": "💰 قبض", "ext": "🔄 تجديد",
        "wa_warn": "⚠️ تحذير", "wa_done": "✅ تم", "wa_late": "🔔 تأخير", "wa_cut": "🚫 قطع",
        "expired": "منتهي", "near": "قرب يخلص"
    },
    "English": {
        "title": "📡 Future Net - Ultimate Management",
        "search": "🔍 Search name...",
        "sort": "Sort By",
        "debt": "Debt", "pkg": "Pkg", "days": "Days",
        "pay": "💰 Pay", "ext": "🔄 Renew",
        "wa_warn": "⚠️ Warn", "wa_done": "✅ Done", "wa_late": "🔔 Late", "wa_cut": "🚫 Cut",
        "expired": "Expired", "near": "Near"
    }
}
t = texts[lang_choice]

# 3. جلب البيانات (تأكد من وجود عمود للدين ورقم الهاتف في الشيت)
def load_data():
    try:
        url = st.secrets["connections"]["spreadsheet"]
        df = pd.read_csv(url, header=None).dropna(how='all')
        # الأعمدة: 0:اسم، 1:حالة، 2:تاريخ، 3:باقة، 4:دين، 5:تلفون
        df.columns = ['Name', 'Status', 'Expiry', 'Package', 'Debt', 'Phone']
        df['Expiry_Date'] = pd.to_datetime(df['Expiry'], errors='coerce')
        df['Debt'] = pd.to_numeric(df['Debt'], errors='coerce').fillna(0)
        return df
    except:
        st.error("⚠️ مشكلة بالرابط! تأكد من إعدادات Secrets.")
        return pd.DataFrame()

df = load_data()

# 4. CSS للتحكم بالألوان والخلفية البيضاء
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .card {{
        background: #fdfdfd; border-radius: 10px; padding: 12px; margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: {'right' if lang_choice == 'العربية' else 'left'};
    }}
    /* نظام إشارة السير */
    .border-green {{ border-{'right' if lang_choice == 'العربية' else 'left'}: 10px solid #2ecc71; }}
    .border-yellow {{ border-{'right' if lang_choice == 'العربية' else 'left'}: 10px solid #f1c40f; }}
    .border-red {{ border-{'right' if lang_choice == 'العربية' else 'left'}: 10px solid #e74c3c; }}
    </style>
""", unsafe_allow_html=True)

# 5. الفرز والتحكم
st.sidebar.subheader(t["sort"])
sort_option = st.sidebar.selectbox("", [
    "Name (A-Z)", "Date (Newest)", "Status (Expired First)", "Debt (Highest)", "Package Type"
])

if not df.empty:
    # تطبيق الفرز
    if "Name" in sort_option: df = df.sort_values('Name')
    elif "Date" in sort_option: df = df.sort_values('Expiry_Date', ascending=False)
    elif "Status" in sort_option: df = df.sort_values('Status')
    elif "Debt" in sort_option: df = df.sort_values('Debt', ascending=False)
    elif "Package" in sort_option: df = df.sort_values('Package')

    st.markdown(f"<h2 style='text-align:center; color:#004aad;'>{t['title']}</h2>", unsafe_allow_html=True)
    search = st.text_input(t["search"], label_visibility="collapsed")
    if search: df = df[df['Name'].str.contains(search, case=False)]

    # 6. عرض الزبائن (2 في السطر)
    for i in range(0, len(df), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(df):
                row = df.iloc[i + j]
                days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else -1
                
                # تحديد لون البطاقة
                card_class = "border-green" # شغال
                if days_left < 0: card_class = "border-red" # منتهي
                elif days_left <= 3: card_class = "border-yellow" # قرب يخلص
                
                with cols[j]:
                    st.markdown(f"""
                        <div class="card {card_class}">
                            <div style="font-weight:bold; font-size:1.1rem; color:#333;">👤 {row['Name']}</div>
                            <div style="font-size:0.9rem; color:#666;">📦 {row['Package']} | ⏳ {t['days']}: {days_left if days_left >=0 else t['expired_text']}</div>
                            <div style="color:#e74c3c; font-weight:bold;">💰 {t['debt']}: ${row['Debt']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار الإدارة والواتساب
                    b1, b2, b3 = st.columns([1, 1, 2])
                    with b1: st.button("➕", key=f"add_{i+j}") # زيادة دين
                    with b2: st.button("🔄", key=f"ren_{i+j}") # تجديد
                    
                    with b3:
                        # روابط الواتساب المصلحة
                        def send_wa(msg):
                            phone = str(row['Phone']).replace('.0','')
                            return f"https://wa.me/{phone}?text={quote(msg)}"

                        wa_cols = st.columns(4)
                        # 1. تحذير (قبل بـ 3 أيام)
                        wa_cols[0].link_button("⚠️", send_wa(f"تذكير: اشتراكك ينتهي خلال 3 أيام. يرجى التجديد."))
                        # 2. تم التجديد
                        wa_cols[1].link_button("✅", send_wa(f"تم تجديد اشتراكك بنجاح. شكراً لك."))
                        # 3. تزمير دفع (بعد 3 أيام)
                        wa_cols[2].link_button("🔔", send_wa(f"يرجى تسديد المبلغ المتبقي ${row['Debt']} لتجنب القطع."))
                        # 4. قطع (بعد أسبوع)
                        wa_cols[3].link_button("🚫", send_wa(f"تم قطع الخدمة مؤقتاً لعدم السداد. يرجى التواصل معنا."))
