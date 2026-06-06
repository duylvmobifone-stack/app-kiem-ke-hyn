import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Cấu hình giao diện Mobile
st.set_page_config(page_title="Kiểm kê MobiFone", layout="centered")

st.title("📱 Kiểm kê Trạm HYN")

# Kết nối Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Đọc dữ liệu (Tải về và hiển thị)
try:
    df = conn.read(worksheet="Chi tiết") # Tên tab trong file Excel của Sếp
    
    # 1. Chọn trạm để làm việc
    ma_tram = st.selectbox("📍 Chọn Mã trạm cần kiểm kê:", df['Ma_tram'].unique())
    
    # 2. Lọc dữ liệu trạm đó
    tram_data = df[df['Ma_tram'] == ma_tram]
    
    # 3. Giao diện chỉnh sửa
    st.write(f"### Dữ liệu của: {ma_tram}")
    edited_df = st.data_editor(tram_data, num_rows="fixed")
    
    # 4. Nút lưu
    if st.button("💾 Lưu dữ liệu vào Google Sheets"):
        # Cập nhật lại vào Google Sheets
        conn.update(worksheet="Chi tiết", data=edited_df)
        st.success("✅ Đã cập nhật thành công!")
        st.balloons()

except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.info("💡 Sếp nhớ chia sẻ quyền truy cập file Google Sheets cho email: gs-connections@streamlit-gsheets.iam.gserviceaccount.com")