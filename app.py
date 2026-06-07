import streamlit as st
import pandas as pd

st.title("📱 Kiểm kê Trạm - HYN")
st.write("Dữ liệu kiểm kê:")

# Link gốc của Sếp
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"

# Cách xử lý link "chắc chắn thắng"
# Nếu link có /edit, ta thay bằng /export?format=csv
csv_url = sheet_url.replace('/edit', '/export?format=csv')

try:
    df = pd.read_csv(csv_url)
    st.dataframe(df)
except Exception as e:
    st.error(f"Lỗi đọc dữ liệu: {e}")
    st.write("Sếp kiểm tra lại: File Google Sheet đã được để chế độ 'Anyone with the link' chưa?")