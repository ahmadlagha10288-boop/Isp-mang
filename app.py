import streamlit as st
import pandas as pd

# هيدا التعديل بخلي البرنامج يقرأ اليوزر نيم (العمود A) فوراً
def get_csv_url(url):
    # تحويل رابط الشيت العادي لرابط "داتا" CSV
    if "edit" in url:
        return url.replace('/edit', '/export?format=csv')
    return url

# استدعاء الرابط من الـ Secrets
sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
data_url = get_csv_url(sheet_url)

# قراءة الداتا (البرنامج رح يشوفها CSV متل ما طلب)
df = pd.read_csv(data_url, header=None)

# تحديد العمود 0 لليوزر نيم (العمود A) والعمود 5 للتلفون (F)
df = df.iloc[:, [0, 1, 2, 3, 5]]
df.columns = ['Username', 'Status', 'Service', 'Expiry', 'Phone']
