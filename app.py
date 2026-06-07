import streamlit as st
import pandas as pd

# 1. Cấu hình trang tối ưu hiển thị Mobile
st.set_page_config(page_title="Kiểm Kê Tài Sản HYN", layout="centered", initial_sidebar_state="collapsed")

# CSS để giao diện hiển thị dạng Thẻ (Card) bo góc đẹp mắt trên điện thoại
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stCheckbox { background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #e9ecef; }
    .station-title { background-color: #007bff; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_width=True)

st.title("📱 Kiểm kê Trạm - HYN")

# Link dữ liệu của Sếp
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')

@st.cache_data(ttl=30)  # Giảm cache xuống 30s để cập nhật nhanh hơn
def load_data():
    df = pd.read_csv(csv_url)
    # Loại bỏ dòng header phụ nếu có (dòng chứa 't', 'Tên trạm'...)
    df = df[df['Tên trạm'] != 'Tên trạm']
    return df

try:
    df_source = load_data()
    
    # BƯỚC 1: TÌM KIẾM VÀ CHỌN TRẠM (Rất tiện trên điện thoại)
    st.write("### 🔍 Bước 1: Chọn Trạm Kiểm Kê")
    search_keyword = st.text_input("Gõ tên trạm cần tìm (Ví dụ: AN_THI, BAI_SAY...):", "")
    
    # Lọc danh sách trạm theo từ khóa
    if search_keyword:
        filtered_stations = df_source[df_source['Tên trạm'].str.contains(search_keyword, case=False, na=False)]['Tên trạm'].unique()
    else:
        filtered_stations = df_source['Tên trạm'].unique()
        
    selected_station = st.selectbox("Chọn chính xác trạm từ danh sách:", filtered_stations)

    if selected_station:
        # Lấy dữ liệu hiện tại của trạm đã chọn
        row_data = df_source[df_source['Tên trạm'] == selected_station].iloc[0]
        
        st.markdown(f"<div class='station-title'>🏠 ĐANG KIỂM KÊ: {selected_station}</div>", unsafe_allow_width=True)
        st.write(f"📅 *Ngày kiểm gần nhất: {row_data.get('Ngày Kiểm', 'Chưa rõ')}*")
        
        # BƯỚC 2: TÍCH CHỌN KIỂM KÊ THEO TỪNG DANH MỤC
        st.write("### 📑 Bước 2: Tích chọn trạng thái hạng mục")
        
        # Tạo các tab phân nhóm để không bị dài màn hình khi cuộn bằng điện thoại
        tab1, tab2, tab3 = st.tabs(["🏗️ Hạ tầng", "⚡ Điện & Nguồn", "❄️ Điều hòa & Thiết bị"])
        
        with tab1:
            st.subheader("Cơ sở hạ tầng Trạm")
            # Kiểm tra trạng thái cũ từ file để tích sẵn nếu đã "Hoạt động" hoặc "Tốt"
            infra_1 = st.checkbox("🏷️ Biển tên trạm (Có/Tốt)", value=(row_data.get('Biển tên trạm') in ['Có', 'Tốt']))
            infra_2 = st.checkbox("🔥 Tiêu lệnh PCCC (Có/Tốt)", value=(row_data.get('Tiêu lệnh PCCC') in ['Có', 'Tốt']))
            infra_3 = st.checkbox("🚪 Phòng máy (Shelter/Nhà xây tốt)", value=(row_data.get('Phòng máy') in ['Shelter', 'Nhà xây']))
            infra_4 = st.checkbox("🗼 Cột anten (An toàn/Tốt)", value=(row_data.get('Cột anten') not in ['Hỏng', 'Yếu']))

        with tab2:
            st.subheader("Hệ thống Nguồn điện")
            power_1 = st.checkbox("🔌 Thiết bị nguồn AC (Hoạt động tốt)", value=(row_data.get('Thiết bị nguồn AC') == 'Hoạt động' or row_data.get('Thiết bị nguồn AC') == 'Tốt'))
            power_2 = st.checkbox("🔋 Tủ nguồn 1 (Đạt tiêu chuẩn)", value=(row_data.get('Tủ nguồn 1') not in ['Hỏng', 'Lỗi']))
            power_3 = st.checkbox("🏎️ Máy phát điện (Sẵn sàng chạy)", value=(row_data.get('Máy phát điện') in ['Có', 'Tốt', 'Hoạt động']))
            power_4 = st.checkbox("⚡ Cắt lọc sét (Hoạt động)", value=(row_data.get('Cắt lọc sét') in ['Có', 'Tốt']))

        with tab3:
            st.subheader("Hệ thống Điều hòa & Vận hành")
            ac_1 = st.checkbox("❄️ Điều hoà 1 (Chạy tốt)", value=(row_data.get('Điều hoà 1') in ['Tốt', 'Hoạt động']))
            ac_2 = st.checkbox("❄️ Điều hoà 2 (Chạy tốt)", value=(row_data.get('Điều hoà 2') in ['Tốt', 'Hoạt động']))
            ac_3 = st.checkbox("🚨 Cảnh báo ngoài (Hoạt động)", value=(row_data.get('Cảnh báo ngoài') in ['Có', 'Tốt']))

        # BƯỚC 3: NÚT XÁC NHẬN KIỂM KÊ
        st.write("---")
        notes = st.text_area("📝 Ghi chú hoặc đề xuất sửa chữa (nếu có):", placeholder="Nhập tình trạng hỏng hóc thực tế tại trạm...")
        
        if st.button("💾 Ghi nhận kết quả kiểm kê", use_container_width=True, type="primary"):
            st.success(f"🎉 Đã ghi nhận tích chọn kiểm kê cho trạm {selected_station} thành công trên giao diện!")
            st.balloons()
            
except Exception as e:
    st.error(f"Lỗi cấu trúc dữ liệu: {e}")