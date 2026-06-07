import streamlit as st
import pandas as pd

st.title("📱 Kiểm kê Trạm - HYN")
st.write("Dữ liệu kiểm kê:")

# Đảm bảo link này là link Sếp copy từ thanh địa chỉ trình duyệt sau khi đã nhấn Share "Anyone with the link"
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit?usp=sharing"
csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')

try:
    df = pd.read_csv(csv_url)
    st.dataframe(df) # Dữ liệu sẽ hiện ra ở đây
except Exception as e:
    st.error("Không thể đọc được dữ liệu. Sếp kiểm tra lại link đã Share công khai chưa nhé!")