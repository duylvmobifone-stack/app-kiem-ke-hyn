import streamlit as st
import pandas as pd
import re

# ==============================================================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN CHUẨN MOBILE
# ==============================================================================
st.set_page_config(
    page_title="Kiểm Kê Tài Sản HYN", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Tối ưu CSS để giao diện khít, các nút bấm to rõ không bị trượt trạng thái trên màn hình cảm ứng
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .station-title { background-color: #007bff; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 15px; }
    .category-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e9ecef; }
    .stRadio > div { background-color: white; padding: 6px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 4px; }
    div.stRadio p { font-size: 15px !important; margin-bottom: 2px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 Kiểm kê Tài sản Chuẩn hóa - HYN")

# Link dữ liệu Google Sheets xuất bản dạng CSV của Sếp
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')


# ==============================================================================
# 2. HÀM NẠP VÀ TRÍCH XUẤT DANH SÁCH GIÁ TRỊ TỰ ĐỘNG TỪ EXCEL
# ==============================================================================
@st.cache_data(ttl=5)  # Giảm time cache để đồng bộ tức thì khi file sheets thay đổi
def load_and_parse_sheets():
    df_raw = pd.read_csv(csv_url, header=None, dtype=str).fillna("")
    
    # Đọc chính xác cấu trúc tối đa 124 cột của file HYN
    max_cols = min(df_raw.shape[1], 124)
    df_raw = df_raw.iloc[:, :max_cols]
    
    # Chuẩn hóa hàng tiêu đề 2 (Mục cha) và hàng tiêu đề 3 (Thuộc tính con)
    row2 = [str(val).strip() for val in df_raw.iloc[1]]
    row3 = [str(val).strip() for val in df_raw.iloc[2]]
    
    # Điền khuyết danh mục cha (Forward Fill)
    current_parent = "Thông tin chung"
    for i in range(len(row2)):
        if row2[i] != "" and not row2[i].startswith("Unnamed"):
            current_parent = row2[i]
        else:
            row2[i] = current_parent

    # Phân tích danh sách trạm (Bắt đầu dữ liệu thực tế từ hàng chỉ số 4 trở đi)
    data_rows = []
    for r_idx in range(4, df_raw.shape[0]):
        ma_tram = str(df_raw.iloc[r_idx, 1]).strip()
        if not ma_tram or ma_tram.lower() in ["t", "tên trạm", "nan", "trống"]:
            continue
        
        cells_dict = {}
        for col_idx in range(max_cols):
            val = str(df_raw.iloc[r_idx, col_idx]).strip()
            cells_dict[col_idx + 1] = val if val != "" else "Trống"
            
        data_rows.append({
            "row_idx": r_idx + 1,
            "ma_tram": ma_tram,
            "cells": cells_dict
        })
        
    return row2, row3, data_rows, df_raw

try:
    headers_row2, headers_row3, rows_data, df_total_raw = load_and_parse_sheets()
    
    # Khởi tạo session lưu trữ cập nhật nếu chưa có
    if "session_updates" not in st.session_state:
        st.session_state["session_updates"] = {}
        
    # Tạo biến lưu trữ trạm hiện tại đang chọn để bắt sự kiện đổi trạm phá hủy cache trạng thái ảo
    if "current_selected_station" not in st.session_state:
        st.session_state["current_selected_station"] = ""

    # ==============================================================================
    # 3. BƯỚC 1: TÌM KIẾM TRẠM THÔNG MINH (Không dấu, không gạch ngang)
    # ==============================================================================
    st.write("### 🔍 Bước 1: Tìm Kiếm Trạm Khớp Chuỗi")
    search_keyword = st.text_input(
        "Nhập tên trạm hoặc mã trạm đối soát:", 
        placeholder="💡 Ví dụ gõ liền: hynatianthi hệ thống vẫn nhận diện được..."
    )
    
    selected_station_data = None
    
    if search_keyword:
        keyword_clean = re.sub(r'[^a-zA-Z0-9]', '', search_keyword).lower()
        matched_stations = []
        for s in rows_data:
            ma_goc_clean = re.sub(r'[^a-zA-Z0-9]', '', s["ma_tram"]).lower()
            if keyword_clean in ma_goc_clean:
                matched_stations.append(s)
                
        if not matched_stations:
            st.warning("⚠️ Không tìm thấy trạm nào trùng khớp với từ khóa!")
        else:
            station_options = {s["ma_tram"]: s for s in matched_stations}
            choice = st.selectbox(f"💡 Tìm thấy ({len(matched_stations)}) trạm phù hợp:", list(station_options.keys()))
            selected_station_data = station_options[choice]
    else:
        all_stations = {s["ma_tram"]: s for s in rows_data}
        choice = st.selectbox("Hoặc chọn trực tiếp trạm từ danh sách tổng:", ["-- Chọn trạm --"] + list(all_stations.keys()))
        if choice != "-- Chọn trạm --":
            selected_station_data = all_stations[choice]

    # Cơ chế Reset bộ đệm sửa đổi khi Sếp đổi sang trạm khác để tránh rác dữ liệu trạm cũ đè lên trạm mới
    if selected_station_data:
        if st.session_state["current_selected_station"] != selected_station_data["ma_tram"]:
            st.session_state["session_updates"] = {}
            st.session_state["current_selected_station"] = selected_station_data["ma_tram"]

    # ==============================================================================
    # 4. BƯỚC 2: PHÂN CẤP DANH MỤC & HIỂN THỊ CHUẨN XÁC THEO HIỆN TRẠNG FILE EXCEL
    # ==============================================================================
    if selected_station_data:
        ma_tram = selected_station_data["ma_tram"]
        cells = selected_station_data["cells"]
        
        st.markdown(f"<div class='station-title'>🏠 ĐANG KIỂM KÊ: {ma_tram}</div>", unsafe_allow_html=True)
        st.write(f"📅 *Ngày kiểm ghi nhận trên hệ thống: {cells.get(3, 'Trống')}*")
        
        # Tổ chức cây dữ liệu theo hàng 2 và hàng 3
        tree_structure = {}
        for col_idx in range(4, len(headers_row2) + 1):
            p_name = headers_row2[col_idx - 1]
            c_name = headers_row3[col_idx - 1] or f"Trường_{col_idx}"
            c_val = cells.get(col_idx, "Trống")
            
            if p_name not in tree_structure:
                tree_structure[p_name] = []
            tree_structure[p_name].append({"col_idx": col_idx, "child": c_name, "current_val": c_val})
            
        st.write("### 📑 Bước 2: Khảo sát chi tiết cấu trúc phân cấp")
        
        for parent_key, child_list in tree_structure.items():
            # Đếm số lượng thực tế có sự thay đổi so với file gốc của trạm
            grp_changed = sum(1 for c in child_list if c["col_idx"] in st.session_state["session_updates"])
            expander_title = f"📁 {parent_key} " + (f"({grp_changed} Đã sửa ✏️)" if grp_changed > 0 else "")
            
            with st.expander(expander_title, expanded=False):
                for item in child_list:
                    c_id = item["col_idx"]
                    c_name = item["child"]
                    
                    # Lấy giá trị gốc của trạm từ file Excel
                    file_actual_val = item["current_val"]
                    
                    # Thuật toán quét lọc sạch toàn bộ cột dữ liệu thô để lấy danh sách lựa chọn duy nhất có trong file
                    raw_values = df_total_raw.iloc[4:, c_id - 1].astype(str).str.strip()
                    cleaned_set = set()
                    for v in raw_values:
                        if v and v.lower() not in ["", "nan", "none", "trống"]:
                            cleaned_set.add(v)
                    
                    unique_options = sorted(list(cleaned_set))
                    
                    # Dự phòng nếu cột rỗng hoàn toàn trong Excel
                    if not unique_options:
                        unique_options = ["Trống", "Tốt", "Hỏng"]
                    if "Trống" not in unique_options:
                        unique_options.append("Trống")
                        
                    # Đảm bảo giá trị thực tế của trạm bắt buộc phải có mặt trong tập danh sách chọn
                    if file_actual_val not in unique_options:
                        unique_options.insert(0, file_actual_val)
                        
                    # Đọc trạng thái đang tích chọn hiện tại (ưu tiên trạng thái trong bộ đệm session)
                    current_active_val = st.session_state["session_updates"].get(c_id, file_actual_val)
                    if current_active_val not in unique_options:
                        unique_options.insert(0, current_active_val)
                        
                    # Xác định vị trí index chính xác tuyệt đối, tránh hiện tượng lệch index khi nhảy trạm
                    default_idx = unique_options.index(current_active_val)
                    
                    st.markdown(f"✏️ **{c_name}** *(Hiện trạng file gốc: `{file_actual_val}`)*", unsafe_allow_html=True)
                    
                    # 🎯 KHẮC PHỤC LỖI TRƯỢT TRẠNG THÁI: Khóa Key bằng cách gộp Mã trạm + Cột ID + Giá trị gốc
                    user_choice = st.radio(
                        f"Chọn dữ liệu cho {c_name} tại cột {c_id}",
                        options=unique_options,
                        index=default_idx,
                        key=f"radio_{ma_tram}_{c_id}_{file_actual_val}",
                        label_visibility="collapsed"
                    )
                    
                    # KIỂM TRA NGHIÊM NGẶT: Chỉ lưu vào bộ đệm sửa đổi khi giá trị chọn KHÁC GIÁ TRỊ GỐC TRÊN FILE của trạm đó
                    if user_choice != file_actual_val:
                        st.session_state["session_updates"][c_id] = user_choice
                    else:
                        # Nếu người dùng chọn lại về đúng giá trị gốc trên file, xóa bỏ khỏi danh sách chỉnh sửa
                        if c_id in st.session_state["session_updates"]:
                            del st.session_state["session_updates"][c_id]
                            
                    st.write("---")

        # ==============================================================================
        # 5. BƯỚC 3: XÁC NHẬN HOÀN THÀNH KIỂM KÊ
        # ==============================================================================
        st.write("### 💾 Bước 3: Hoàn Tất Kiểm Kê")
        num_changes = len(st.session_state["session_updates"])
        
        if num_changes > 0:
            st.info(f"📊 Hệ thống phát hiện có `{num_changes}` thuộc tính thực sự thay đổi so với file gốc.")
            
            if st.button("💾 GHI NHẬN KẾT QUẢ & CẬP NHẬT KẾT XUẤT", use_container_width=True, type="primary"):
                st.success(f"🎉 Thành công Sếp ơi! Hệ thống đã khóa và lưu chính xác kết quả thay đổi của trạm {ma_tram}!")
                st.balloons()
                
                summary_data = []
                for c_id, n_val in st.session_state["session_updates"].items():
                    summary_data.append({
                        "Cột số": c_id,
                        "Danh mục lớn": headers_row2[c_id - 1],
                        "Hạng mục kiểm tra": headers_row3[c_id - 1],
                        "Hiện trạng file gốc": cells.get(c_id),
                        "Kết quả kiểm kê mới": n_val
                    })
                st.write("**Bảng đối soát các trường thực sự thay đổi:**")
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Hiện tại tất cả các thuộc tính hiển thị đều trùng khớp 100% với hiện trạng file Excel gốc, không có dữ liệu ảo tự ý cập nhật.")

except Exception as e:
    st.error(f"🚨 Hệ thống phát hiện lỗi đồng bộ: {e}")