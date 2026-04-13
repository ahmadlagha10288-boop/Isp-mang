import streamlit as st
import pandas as pd
from urllib.parse import quote

# 1. إعداد الصفحة
st.set_page_config(page_title="Future Net Manager", layout="wide")

# تصميم البطاقات (Cards)
st.markdown("""
    <style>
    .card { background-color: #1e1e1e; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    .status-online { color: #2ecc71; font-weight: bold; }
    .status-offline { color: #e74c3c; font-weight: bold; }
    .name-text { font-size: 1.1rem; font-weight: bold; color: white; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # قراءة أولية للملف
        raw_df = pd.read_csv(url)
        
        # البحث عن السطر اللي فيه العناوين الحقيقية (مثل Name أو Username)
        header_row = 0
        for i in range(min(10, len(raw_df))):
            row_values = raw_df.iloc[i].astype(str).tolist()
            if any('Name' in val or 'Username' in val for val in row_values):
                header_row = i + 1
                break
        
        # إعادة قراءة الملف من السطر الصحيح
        df = pd.read_csv(url, header=header_row)
        df.columns = df.columns.astype(str).str.strip()
        # حذف الأسطر الفاضية
        df = df.dropna(subset=[df.columns[2]], thresh=1) if len(df.columns) > 2 else df.dropna(how='all')
        return df
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Future Net Dashboard")

if not df.empty:
    # --- الإحصائيات (تأمين الحسابات لتجنب الأخطاء) ---
    total = len(df)
    
    # دالة ذكية لإيجاد الأعمدة حتى لو تغير اسمها
    def get_col(names):
        for n in names:
            for col in df.columns:
                if n.lower() in col.lower(): return col
        return None

    name_col = get_col(['Name', 'Customer'])
    status_col = get_col(['Status', 'State'])
    phone_col = get_col(['Mobile', 'Phone', 'تلفون'])
    price_col = get_col(['Price', 'Selling'])

    # حساب الأونلاين
    online = 0
    if status_col:
        online = len(df[df[status_col].astype(str).str.contains('Online|Active', case=False, na=False)])

    c1, c2 = st.columns(2)
    c1.metric("إجمالي الزبائن", total)
    c2.metric("نشط حالياً", online)

    st.divider()

    # --- البحث ---
    search = st.text_input("🔍 ابحث عن زبون:")
    if search:
        df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # --- عرض البطاقات ---
    cols = st.columns(2)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 2]:
            # جلب البيانات بأمان
            c_name = row[name_col] if name_col else "بدون اسم"
            c_status = str(row[status_col]) if status_col else "Unknown"
            c_phone = str(row[phone_col]).replace('.0', '') if phone_col else ""
            
            st_class = "status-online" if "Online" in c_status or "Active" in c_status else "status-offline"
            
            st.markdown(f"""
                <div class="card">
                    <div class="name-text">{c_name}</div>
                    <div class="{st_class}">{c_status}</div>
                    <div style="font-size:0.9rem; margin-top:5px; color:#aaa;">
                        Price: ${row.get(price_col, '0')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # زر واتساب
            if c_phone and c_phone != 'nan':
                wa_msg = quote(f"مرحباً {c_name}، معك Future Net...")
                st.markdown(f"[📲 مراسلة واتساب](https://wa.me/{c_phone}?text={wa_msg})")

else:
    st.warning("⚠️ لم يتم العثور على بيانات بالجدول. تأكد من أن ملف جوجل شيت يحتوي على أسماء.")

if st.sidebar.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()
