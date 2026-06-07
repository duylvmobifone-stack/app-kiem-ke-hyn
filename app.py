import streamlit as st
import pandas as pd

st.title("📱 Kiểm kê Trạm - HYN")

# Thay đường link của Sếp vào đây
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit?usp=sharing"
csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')

# Đọc dữ liệu
@st.cache_data(ttl=60) # Tự cập nhật lại dữ liệu mỗi 60 giây
def load_data():
    return pd.read_csv(csv_url)

try:
    df = load_data()
    st.write("### Dữ liệu kiểm kê:")
    st.dataframe(df) # Hiển thị bảng
except Exception as e:
    st.error("Chưa đọc được dữ liệu. Sếp nhớ check link Google Sheets đã để ở chế độ 'Anyone with the link' chưa nhé!")