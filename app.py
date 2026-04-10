import streamlit as st
import pandas as pd

st.set_page_config(page_title="ISP Manager", layout="wide")
st.title("ISP Manager | مدير الشبكة")

uploaded_file = st.file_uploader("Upload Radius 2.csv / ارفع ملف البيانات")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Data Preview / معاينة البيانات")
    st.dataframe(df.head())
    st.success("File uploaded successfully!")
