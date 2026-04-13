import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="Future Net Automation", layout="wide")

# تصميم البطاقات والأزرار
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 15px; padding: 20px; margin-bottom: 20px; border-top: 5px solid #007bff; }
    .status-active { color: #2ecc71; font-weight: bold; }
    .status-expired { color: #e74c3c; font-weight: bold; }
    .wa-btn { display: inline-block; padding: 6px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 0.8rem; margin: 2px; }
    .btn-alert { background-color: #f39c12; color: white; }
    .btn-pay { background-color: #e67e22; color: white; }
    .btn-stop { background-color: #c0392b; color: white; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df_raw = pd.read_csv(url, header=None)
        header_index = 0
        for i, row in df_raw.iterrows():
            if "Name" in row.values:
                header_index = i
                break
        df = pd.read_csv(url, header=header_index)
        df.columns = df.columns.astype(str).str.strip()
        df = df[df['Name'].notna()].reset_index(drop=True)
        # تحويل التاريخ لنوع تاريخ حقيقي للحسابات
        if 'Expiry Date' in df.columns:
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- القائمة الجانبية ---
st.sidebar.title("🛠️ إدارة Future Net")
menu = st.sidebar.radio("العمليات:", ["📱 رادار المشتركين", "💰 تعديل الحسابات", "📅 التشريج الشهري"])

# --- 1. رادار المشتركين (مع نظام الواتساب 3 مراحل) ---
if menu == "📱 رادار المشتركين":
    st.title("📡 رادار المشتركين والرسائل")
    search = st.text_input("🔍 بحث عن مشترك:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    today = datetime.now()
    cols = st.columns(2)
    
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 2]:
            expiry = row.get('Expiry Date')
            days_left = (expiry - today).days if pd.notnull(expiry) else -99
            
            status_text = "Active" if days_left > 0 else "Expired"
            st_color = "status-active" if days_left > 0 else "status-expired"
            
            st.markdown(f"""
                <div class="card">
                    <div style="font-size:1.2rem; font-weight:bold;">{row['Name']}</div>
                    <div class="{st_color}">● {status_text} (باقي {days_left} يوم)</div>
                    <div style="color:#aaa; font-size:0.9rem; margin-top:5px;">
                        📞 {row.get('Mobile Number', 'N/A')} | 💰 الدين: ${row.get('Selling Price', '0')}
                    </div>
            """, unsafe_allow_html=True)

            # --- نظام الواتساب بـ 3 مراحل ---
            phone = str(row.get('Mobile Number', '')).replace('.0', '').strip()
            if phone and phone != 'nan':
                # المرحلة 1: تنبيه قبل 3 أيام
                msg1 = quote(f"عزيزي {row['Name']}، نود تنبيهك أن اشتراكك ينتهي خلال 3 أيام. شكراً لاختيارك Future Net.")
                # المرحلة 2: طلب دفع (يوم الانتهاء)
                msg2 = quote(f"عزيزي {row['Name']}، ينتهي اشتراكك اليوم. يرجى تسديد مبلغ ${row.get('Selling Price')} لتجديد الخدمة.")
                # المرحلة 3: تحذير إيقاف
                msg3 = quote(f"تذكير أخير للسيد {row['Name']}، لم يتم استلام الدفعة. سيتم إيقاف الخط خلال ساعات في حال عدم الدفع.")
                
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f'<a href="https://wa.me/{phone}?text={msg1}" class="wa-btn btn-alert">⚠️ تنبيه 3 أيام</a>', unsafe_allow_html=True)
                with c2: st.markdown(f'<a href="https://wa.me/{phone}?text={msg2}" class="wa-btn btn-pay">💸 طلب دفع</a>', unsafe_allow_html=True)
                with c3: st.markdown(f'<a href="https://wa.me/{phone}?text={msg3}" class="wa-btn btn-stop">🚫 تحذير إيقاف</a>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# --- 2. تعديل الحسابات (دين زاد أو نقص) ---
elif menu == "💰 تعديل الحسابات":
    st.title("⚖️ إدارة الديون والأرصدة")
    user_select = st.selectbox("اختر الزبون لتعديل حسابه:", df['Name'].tolist())
    user_row = df[df['Name'] == user_select].iloc[0]
    
    current_debt = float(user_row.get('Selling Price', 0))
    st.info(f"الدين الحالي للسيد {user_select} هو: ${current_debt}")
    
    amount = st.number_input("المبلغ (بالدولار):", min_value=0.0)
    action = st.radio("العملية:", ["إضافة للدين (+)", "خصم من الدين (-)"])
    
    new_debt = current_debt + amount if action == "إضافة للدين (+)" else current_debt - amount
    
    if st.button("اعتماد الحساب الجديد"):
        st.success(f"تم الحساب! المبلغ الجديد الذي يجب وضعه في الإكسل هو: ${new_debt}")
        st.warning("ملاحظة: يرجى تحديث هذا الرقم يدوياً في ملف Google Sheets ليتم حفظه.")

# --- 3. التشريج الشهري ---
elif menu == "📅 التشريج الشهري":
    st.title("🗓️ نظام التشريج الجماعي")
    st.write("هذا القسم يساعدك على تجهيز حسابات الشهر الجديد لكل المشتركين.")
    
    if st.button("🚀 توليد قائمة التشريج لهذا الشهر"):
        recharge_list = df[['Name', 'Service', 'Selling Price', 'Mobile Number']]
        st.write("القائمة الجاهزة للتشريج:")
        st.dataframe(recharge_list)
        
        csv = recharge_list.to_csv(index=False).encode('utf-8')
        st.download_button("📥 تحميل قائمة التشريج (Excel)", csv, "monthly_recharge.csv", "text/csv")

if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()
