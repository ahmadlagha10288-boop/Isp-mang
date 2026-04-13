import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# ... (دالة load_data بقيت كما هي) ...

df = load_data()

# --- قسم الإحصائيات (KPIs) ---
if not df.empty:
    st.title("📡 رادار المشتركين")
    
    # حساب أرقام سريعة
    total_users = len(df)
    online_users = len(df[df['Status'].str.contains('Online', case=False)])
    expired_users = total_users - online_users
    
    # عرض الإحصائيات في 3 مربعات
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي المشتركين", total_users)
    m2.metric("متصل الآن ✅", online_users)
    m3.metric("منتهي الصلاحية ❌", expired_users)

    # --- خيارات الترتيب والبحث في السايد بار ---
    st.sidebar.header("⚙️ التحكم")
    sort_by = st.sidebar.selectbox("ترتيب حسب:", ["الأحدث", "الاسم", "الحالة"])
    
    if sort_by == "الأحدث":
        df = df.sort_values(by='Expiry', ascending=False)
    elif sort_by == "الاسم":
        df = df.sort_values(by='Username')
    elif sort_by == "الحالة":
        df = df.sort_values(by='Status', ascending=True)

    search = st.text_input("🔍 ابحث عن يوزر نيم أو باقة...")
    if search:
        df = df[df['Username'].str.contains(search, case=False)]

    # --- عرض الكروت الملونة ---
    for _, row in df.iterrows():
        status = str(row['Status']).strip()
        
        # ذكاء الألوان: 
        # أخضر = Online
        # أحمر = Expired
        if "Online" in status:
            card_color = "#2ecc71" 
        else:
            card_color = "#e74c3c"
            
        st.markdown(f"""
            <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:10px; border-left:8px solid {card_color};">
                <div style="display:flex; justify-content:space-between;">
                    <h3 style="margin:0; color:white;">👤 {row['Username']}</h3>
                    <span style="color:{card_color}; font-weight:bold;">{status}</span>
                </div>
                <p style="margin:5px 0; color:#ccc;">📦 الباقة: {row['Package']}</p>
                <p style="margin:0; color:#888; font-size:0.85rem;">📅 تاريخ الانتهاء: {row['Expiry']}</p>
            </div>
        """, unsafe_allow_html=True)

    # --- زر البيك أب (Backup) ---
    st.sidebar.download_button(
        "📥 سحب نسخة (Backup)",
        df.to_csv(index=False).encode('utf-8'),
        "future_net_backup.csv",
        "text/csv"
    )
