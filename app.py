import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد الصفحة لتكون بوضعية "عريضة" وأجمل
st.set_page_config(page_title="ISP Total Management", layout="wide", initial_sidebar_state="expanded")

# --- تنسيق CSS مخصص لتجميل الواجهة بالألوان ---
st.markdown("""
<style>
    /* ألوان الخلفية والعناوين */
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* تنسيق الكروت العلوية (Dashboard) */
    div[data-testid="stMetricValue"] { color: #3498db !important; font-size: 36px; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #7f8c8d !important; font-size: 16px; }
    .css-1r6slb0 { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }

    /* تنسيق أزرار الواتساب */
    .wa-btn {
        background-color: #25D366; color: white; border-radius: 5px; padding: 8px 15px;
        text-decoration: none; display: inline-flex; align-items: center; font-weight: bold;
        transition: background 0.3s;
    }
    .wa-btn:hover { background-color: #1ebe57; color: white; }
    
    /* تنسيق جدول البيانات */
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 8px; background: white; }
</style>
""", unsafe_allow_html=True)

# --- إدارة قاعدة البيانات ---
conn = sqlite3.connect('isp_debts.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS billing 
             (username TEXT PRIMARY KEY, debt REAL, last_update TEXT)''')
conn.commit()

# --- قائمة الأسعار الرسمية (تأكد من مطابقة الكلمات الصغيرة) ---
PRICES = {
    "bronse": 20, "bronze": 20, # حل مشكلة الاسم بـ s أو z
    "silver": 25, "gold": 30, 
    "platinim": 40, "platinum": 40,
    "daymon": 50, "diamond": 50,
    "ise": 60, "platinium-ise": 60
}

# وظيفة ذكية لجلب السعر بناءً على جزء من الكلمة
def get_price(service_name):
    if pd.isna(service_name): return 0
    service_lower = str(service_name).lower()
    for key, value in PRICES.items():
        if key in service_lower: return value
    return 0 # إذا لم يجد السعر

st.title("📊 لوحة تحكم ISP الاحترافية للمحاسبة")

file = st.file_uploader("ارفع ملف Radius 2.csv", type=['csv'])

if file:
    df = pd.read_csv(file)
    
    # تحضير عمود الأسعار بالاعتماد على الوظيفة الذكية
    df['Price'] = df['Service'].apply(get_price)

    # --- حسابات السوق Dashboard (الألوان والجمال) ---
    c.execute("SELECT SUM(debt) FROM billing")
    market_debt = c.fetchone()[0] or 0
    
    expected_month_income = df['Price'].sum()

    st.markdown("### 📈 إحصائيات سريعة")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("💰 إجمالي الديون في السوق", f"${market_debt}", help="المبالغ التي لم يتم تحصيلها بعد")
    with col_m2:
        st.metric("📈 متوقع قبوله هذا الشهر", f"${expected_month_income}", help="مجموع أسعار خدمات المشتركين حالياً")
    with col_m3:
        st.metric("👥 المشتركين النشطين", len(df), help="عدد المشتركين في الملف الحالي")

    st.markdown("---")

    # --- قسم البحث والفلترة الذكي ---
    st.markdown("### 🔎 إدارة المشتركين")
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        search_t = st.text_input("ابحث عن اسم المشترك:", placeholder="اكتب الاسم هنا...")
    with f_col2:
        f_status = st.selectbox("حالة الدفع:", ["الكل", "عليه دين 🚨", "خالص ✅"])

    # تجهيز قائمة المشتركين للعرض
    st.markdown("---")
    
    # ترويسة الجدول (أجمل)
    t1, t2, t3, t4, t5 = st.columns([2, 1, 1, 1, 2])
    t1.markdown("**المشترك / الخدمة**")
    t2.markdown("**السعر**")
    t3.markdown("**الدين**")
    t4.markdown("**الإجراء**")
    t5.markdown("**تنبيهات الواتساب**")

    for index, row in df.iterrows():
        user = row['Username']
        service = row['Service']
        price = row['Price']
        # جلب الرقم مع حماية من الأرقام الفارغة
        phone = row.get('Mobile Number', row.get('Phone Number', ''))
        phone_str = str(phone) if not pd.isna(phone) else ''
        
        # جلب الدين
        c.execute("SELECT debt FROM billing WHERE username=?", (user,))
        res = c.fetchone()
        debt = res[0] if res else 0
        
        # فلترة البحث والحالة
        if search_t and search_t.lower() not in user.lower(): continue
        if f_status == "عليه دين 🚨" and debt == 0: continue
        if f_status == "خالص ✅" and debt > 0: continue

        # عرض البيانات بصفوف ملونة
        r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([2, 1, 1, 1, 2])
        
        with r_col1:
            color = "#e74c3c" if debt > 0 else "#27ae60" # تلوين الاسم أحمر/أخضر
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{user}</span><br><small>{service}</small>", unsafe_allow_html=True)
        with r_col2:
            st.write(f"${price}")
        with r_col3:
            if debt > 0:
                st.markdown(f"<span style='color:#e74c3c; font-weight:bold;'>${debt}</span>", unsafe_allow_html=True)
            else:
                st.write(f"${debt}")
                
        with r_col4:
            if st.button("قبض ✅", key=f"pay_{user}"):
                new_debt = max(0, debt - price)
                c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (user, new_debt, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.rerun()
                
        with r_col5:
            # نظام الإنذارات والواتساب الذكي
            if phone_str and phone_str != 'nan':
                # منطق الرسائل بناءً على الدين
                if debt >= (price * 3): # عليه 3 أشهر أو أكثر
                    msg = f"🆘 إنذار نهائي: خطك سيقطع نهائياً. إجمالي الدين: ${debt}. يرجى الدفع فوراً."
                    btn_text = "🆘 إنذار قطع نهائي"
                    btn_color = "#c0392b" # أحمر غامق
                elif debt > 0: # عليه دين (شهر واحد)
                    msg = f"⚠️ تذكير: قرب يخلص شهرك، معك 3 أيام للدفع وتجنب القطع. المبلغ: ${debt}$."
                    btn_text = "⚠️ تذكير 3 أيام"
                    btn_color = "#f39c12" # برتقالي
                else: # خالص
                    msg = f"✅ شكراً لالتزامك. اشتراكك {service} فعال وصالح لهذا الشهر."
                    btn_text = "✅ شكراً"
                    btn_color = "#27ae60" # أخضر

                wa_url = f"https://wa.me/{phone_str.replace('+', '')}?text={msg.replace(' ', '%20')}"
                
                # تصميم زر الواتساب الملون
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn" style="background-color:{btn_color};">💬 {btn_text}</a>', unsafe_allow_html=True)
            else:
                st.write("<small>رقم غير موجود</small>", unsafe_allow_html=True)

    # --- القائمة الجانبية (Sidebar) ---
    st.sidebar.markdown("### ⚙️ إدارة الديون")
    if st.sidebar.button("➕ إضافة شهر جديد للجميع"):
        for index, row in df.iterrows():
            u = row['Username']
            p = row['Price']
            c.execute("SELECT debt FROM billing WHERE username=?", (u,))
            res = c.fetchone()
            d = res[0] if res else 0
            # إضافة سعر الخدمة فوق الدين القديم
            c.execute("INSERT OR REPLACE INTO billing VALUES (?, ?, ?)", (u, d + p, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        st.sidebar.success("تم تحديث الديون")
        st.rerun()

st.divider()
st.caption("نظام إدارة ISP - تصميم حصري وذكي")
