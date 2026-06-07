import streamlit as st
import pandas as pd

# 1. Cấu hình trang tối ưu hiển thị trên giao diện Mobile
st.set_page_config(
    page_title="Kiểm Kê Tài Sản HYN", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. Định dạng CSS để tối ưu nút bấm và các ô tích chọn (Checkbox) to, rõ trên điện thoại
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stCheckbox { background-color: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 6px; border: 1px solid #e9ecef; }
    .station-title { background-color: #007bff; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 Kiểm kê Trạm - HYN")

# Link dữ liệu Google Sheets gốc của Sếp
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')

# 3. Hàm tải và làm sạch dữ liệu tự động
@st.cache_data(ttl=30)  # Tự động xóa bộ nhớ đệm sau 30 giây để cập nhật dữ liệu mới từ Sheets
def load_data():
    # SỬA LỖI ĐỘT PHÁ: Thêm header=1 để ép Pandas lấy dòng số 2 (chứa 'Tên trạm') làm tiêu đề cột
    df = pd.read_csv(csv_url, dtype=str, header=1)
    
    # Xóa bỏ khoảng trắng thừa ở đầu/cuối của tất cả tên cột
    df.columns = df.columns.str.strip()
    
    # Loại bỏ dòng tiêu đề lặp lại nếu có trong file
    if 'Tên trạm' in df.columns:
        df = df[df['Tên trạm'] != 'Tên trạm']
    return df

try:
    df_source = load_data()
    
    # Kiểm tra bảo hiểm nếu cấu hình link Sheets có vấn đề
    if 'Tên trạm' not in df_source.columns:
        st.error(f"❌ Vẫn chưa tìm thấy cột 'Tên trạm'. Các cột hiện tại sau khi bỏ dòng đầu là: {list(df_source.columns)[:5]}")
    else:
        # ----------------------------------------------------
        # BƯỚC 1: TÌM KIẾM VÀ CHỌN TRẠM KHU VỰC HƯNG YÊN
        # ----------------------------------------------------
        st.write("### 🔍 Bước 1: Chọn Trạm Kiểm Kê")
        search_keyword = st.text_input("Gõ tên trạm cần tìm (Ví dụ: AN_THI, BAI_SAY, BAC_SON...):", "")
        
        # Làm sạch cột Tên trạm để phục vụ tìm kiếm không bị lỗi
        df_source['Tên trạm'] = df_source['Tên trạm'].fillna('').astype(str).str.strip()
        
        # Lọc danh sách trạm hiển thị dựa trên từ khóa gõ vào
        if search_keyword:
            filtered_stations = df_source[df_source['Tên trạm'].str.contains(search_keyword, case=False, na=False)]['Tên trạm'].unique()
        else:
            filtered_stations = df_source['Tên trạm'].unique()
            
        selected_station = st.selectbox("Chạm để chọn chính xác trạm từ danh sách:", filtered_stations)

        # ----------------------------------------------------
        # BƯỚC 2: HIỂN THỊ CHI TIẾT VÀ TÍCH CHỌN KIỂM KÊ
        # ----------------------------------------------------
        if selected_station:
            # Trích xuất 1 dòng dữ liệu duy nhất của trạm đang chọn
            row_data = df_source[df_source['Tên trạm'] == selected_station].iloc[0]
            
            # Hiển thị tên trạm dạng Card nổi bật
            st.markdown(f"<div class='station-title'>🏠 ĐANG KIỂM KÊ: {selected_station}</div>", unsafe_allow_html=True)
            st.write(f"📅 *Ngày kiểm gần nhất trong file: {str(row_data.get('Ngày Kiểm', 'Chưa rõ'))}*")
            
            st.write("### 📑 Bước 2: Tích chọn trạng thái hạng mục")
            
            # Chia thành 3 Tabs trên di động giúp màn hình ngắn gọn, dễ cuộn bằng ngón tay
            tab1, tab2, tab3 = st.tabs(["🏗️ Hạ tầng", "⚡ Điện & Nguồn", "❄️ Điều hòa & Thiết bị"])
            
            with tab1:
                st.subheader("Cơ sở hạ tầng Trạm")
                # Tự động TÍCH SẴN nếu trạng thái hiện tại trong Sheets là "Có" hoặc "Tốt"
                infra_1 = st.checkbox("🏷️ Biển tên trạm (Có/Tốt)", value=(str(row_data.get('Biển tên trạm')).strip() in ['Có', 'Tốt']))
                infra_2 = st.checkbox("🔥 Tiêu lệnh PCCC (Có/Tốt)", value=(str(row_data.get('Tiêu lệnh PCCC')).strip() in ['Có', 'Tốt']))
                infra_3 = st.checkbox("🚪 Phòng máy (Shelter/Nhà xây tốt)", value=(str(row_data.get('Phòng máy')).strip() in ['Shelter', 'Nhà xây']))
                infra_4 = st.checkbox("🗼 Cột anten (An toàn/Tốt)", value=(str(row_data.get('Cột anten')).strip() not in ['Hỏng', 'Yếu', 'nan']))

            with tab2:
                st.subheader("Hệ thống Nguồn điện")
                power_1 = st.checkbox("🔌 Thiết bị nguồn AC (Hoạt động)", value=(str(row_data.get('Thiết bị nguồn AC')).strip() in ['Hoạt động', 'Tốt']))
                power_2 = st.checkbox("🔋 Tủ nguồn 1 (Đạt tiêu chuẩn)", value=(str(row_data.get('Tủ nguồn 1')).strip() not in ['Hỏng', 'Lỗi', 'nan']))
                power_3 = st.checkbox("🏎️ Máy phát điện (Sẵn sàng chạy)", value=(str(row_data.get('Máy phát điện')).strip() in ['Có', 'Tốt', 'Hoạt động']))
                power_4 = st.checkbox("⚡ Cắt lọc sét (Hoạt động tốt)", value=(str(row_data.get('Cắt lọc sét')).strip() in ['Có', 'Tốt']))

            with tab3:
                st.subheader("Hệ thống Điều hòa & Vận hành")
                ac_1 = st.checkbox("❄️ Điều hoà 1 (Chạy tốt)", value=(str(row_data.get('Điều hoà 1')).strip() in ['Tốt', 'Hoạt động']))
                ac_2 = st.checkbox("❄️ Điều hoà 2 (Chạy tốt)", value=(str(row_data.get('Điều hoà 2')).strip() in ['Tốt', 'Hoạt động']))
                ac_3 = st.checkbox("🚨 Cảnh báo ngoài (Hoạt động)", value=(str(row_data.get('Cảnh báo ngoài')).strip() in ['Có', 'Tốt']))

            # ----------------------------------------------------
            # BƯỚC 3: GHI CHÚ VÀ XÁC NHẬN KIỂM KÊ
            # ----------------------------------------------------
            st.write("---")
            notes = st.text_area("📝 Ghi chú nhanh tại hiện trường (nếu có):", placeholder="Ví dụ: Điều hòa 2 hơi yếu, cần bảo dưỡng...")
            
            # Nút bấm kéo dài hết chiều rộng màn hình giúp dễ chạm trên điện thoại
            if st.button("💾 Ghi nhận kết quả kiểm kê", use_container_width=True, type="primary"):
                st.success(f"🎉 Đã xác nhận trạng thái kiểm kê của trạm {selected_station} thành công!")
                st.balloons() # Hiệu ứng bóng bay chúc mừng
                
except Exception as e:
    st.error(f"🚨 Lỗi kết nối hoặc cấu trúc file: {e}")
    st.write("Sếp vui lòng kiểm tra lại chế độ chia sẻ link Google Sheets nhé!")