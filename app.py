import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Future Net Admin", layout="wide")

# 2. نظام اللغات (Switch)
if 'lang' not in st.session_state: st.session_state.lang = 'العربية'
lang = st.sidebar.radio("🌐 Language / اللغة", ["العربية", "English"])

texts = {
    "العربية": {
        "title": "📡 لوحة تحكم فيوتشر نت",
        "search": "🔍 بحث عن مشترك...",
        "filter": "تصفية حسب الحالة",
        "sort": "ترتيب حسب",
        "debt": "الدين",
        "renew": "تجديد",
        "wa_remind": "تذكير (3 أيام)",
        "wa_done": "تم التجديد",
        "wa_late": "تأخير دفع",
        "wa_cut": "قطع نهائي",
        "stats": "إحصائيات سريعة"
    },
    "English": {
        "title": "📡 Future Net Admin Panel",
        "search": "🔍 Search client...",
        "filter": "Filter Status",
        "sort": "Sort by",
        "debt": "Debt",
        "renew": "Renew",
        "wa_remind": "Reminder (3d)",
        "wa_done": "Renewed",
        "wa_late": "Late Pay",
        "wa_cut": "Cut Line",
        "stats": "Quick Stats"
    }
}
t = texts[lang]

# 3. دالة جلب البيانات مع دعم "الدين" (بافتراض وجود عمود للدين)
def load_data():
    try:
        url = st.secrets["connections"]["spreadsheet"]
        df = pd.read_csv(url, header=None).dropna(how='all')
        # الأعمدة: 0:اسم، 1:حالة، 2:تاريخ، 3:باقة، 4:دين (اختياري)
        df = df.iloc[:, :5]
        df.columns = ['Name', 'Status', 'Expiry', 'Package', 'Debt'] if len(df.columns) == 5 else ['Name', 'Status', 'Expiry', 'Package']
        if 'Debt' not in df.columns: df['Debt'] = 0
        
        df['Expiry_Date'] = pd.to_datetime(df['Expiry'], errors='coerce')
        return df.fillna(0)
    except: return pd.DataFrame()

df = load_data()

# --- التصميم الجديد (White & Blue) ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { opacity: 0.9; border-right: 1px solid #eee; }
    .user-card { 
        background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 15px; margin-bottom: 10px; border-left: 8px solid #004aad;
    }
    .user-name { color: #004aad; font-size: 1.2rem; font-weight: bold; }
    .debt-tag { color: #e74c3c; font-weight: bold; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# 4. لوحة الإحصائيات (Quick Stats)
if not df.empty:
    st.title(t["title"])
    c1, c2, c3 = st.columns(3)
    c1.metric(t["stats"], len(df))
    c2.metric("Online ✅", len(df[df['Status'] == 'Online']))
    c3.metric("Total Debt 💰", f"${df['Debt'].astype(float).sum()}")

    # 5. الفرز المتقدم (Sorting)
    st.sidebar.subheader("⚙️ " + t["sort"])
    sort_val = st.sidebar.selectbox("", ["Name (A-Z)", "Date (Newest)", "Debt (Highest)", "Package"])
    
    if "Name" in sort_val: df = df.sort_values('Name')
    elif "Date" in sort_val: df = df.sort_values('Expiry_Date', ascending=False)
    elif "Debt" in sort_val: df = df.sort_values('Debt', ascending=False)

    # 6. البحث والتحديد الجماعي
    search = st.text_input(t["search"])
    if search: df = df[df['Name'].str.contains(search, case=False)]
    
    selected_users = st.multiselect("Bulk Action / تحديد جماعي", df['Name'].tolist())
    if selected_users and st.button("⚡ Renew Selected / تجديد المحددين"):
        st.success(f"Done! Processed {len(selected_users)} users.")

    st.divider()

    # 7. عرض المشتركين
    for idx, row in df.iterrows():
        days_left = (row['Expiry_Date'] - datetime.now()).days if pd.notnull(row['Expiry_Date']) else 0
        
        with st.container():
            st.markdown(f"""
            <div class="user-card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="user-name">👤 {row['Name']}</span>
                    <span class="debt-tag">{t['debt']}: ${row['Debt']}</span>
                </div>
                <div style="color:#666; font-size:0.9rem; margin-top:5px;">
                    📦 {row['Package']} | 📅 {row['Expiry']} | ⏳ {days_left} Days
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # صف الأزرار (إدارة + واتساب)
            col_admin, col_wa = st.columns([1, 2])
            
            with col_admin:
                sub_c1, sub_c2 = st.columns(2)
                sub_c1.button("➕", key=f"add_{idx}", help="زيادة دين")
                sub_c2.button("➖", key=f"sub_{idx}", help="إنقاص دين")
            
            with col_wa:
                # منطق رسائل الواتساب
                def get_wa_link(msg_type):
                    messages = {
                        "remind": f"تذكير: مشتركنا {row['Name']}، اشتراكك ينتهي خلال 3 أيام. يرجى التجديد.",
                        "done": f"تم بنجاح تجديد اشتراكك {row['Package']}. شكراً لثقتكم.",
                        "late": f"تنبيه: يوجد رصيد غير مدفوع بقيمة ${row['Debt']}. يرجى السداد لتجنب القطع.",
                        "cut": f"نأسف لإبلاغك بأنه تم قطع الخدمة لعدم السداد. يرجى التواصل معنا."
                    }
                    phone = "961XXXXXXXX" # هنا يجب ربط رقم الهاتف من الشيت
                    return f"https://wa.me/{phone}?text={quote(messages[msg_type])}"

                wa_c1, wa_c2, wa_c3, wa_c4 = st.columns(4)
                wa_c1.link_button("⏰", get_wa_link("remind"), help=t["wa_remind"])
                wa_c2.link_button("✅", get_wa_link("done"), help=t["wa_done"])
                wa_c3.link_button("⚠️", get_wa_link("late"), help=t["wa_late"])
                wa_c4.link_button("🚫", get_wa_link("cut"), help=t["wa_cut"])
            st.write("---")

else:
    st.warning("No Data Found.")
