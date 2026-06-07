import streamlit as st
import pandas as pd

# 1. Thiết lập cấu hình trang cho di động
st.set_page_config(page_title="Kiểm kê HYN", layout="wide")

st.title("📱 Kiểm kê Trạm - HYN")

# 2. Sử dụng ô tìm kiếm để lọc trạm (cực kỳ hữu ích trên điện thoại)
query = st.text_input("🔍 Tìm kiếm tên trạm...")

sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(csv_url)

try:
    df = load_data()
    
    # 3. Lọc dữ liệu theo từ khóa tìm kiếm
    if query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
    
    # 4. Hiển thị bảng gọn gàng hơn
    st.write(f"Đang hiển thị {len(df)} dòng dữ liệu:")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error("Chưa tải được dữ liệu, Sếp kiểm tra lại kết nối!")