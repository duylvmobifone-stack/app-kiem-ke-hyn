import streamlit as st
import pandas as pd
import re

# ==============================================================================
# 1. CẤU HÌNH TRANG & CÀI ĐẶT GIAO DIỆN MOBILE
# ==============================================================================
st.set_page_config(
    page_title="Kiểm Kê Tài Sản HYN", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Tối ưu giao diện hiển thị để các nút Radio Button khít nhau, dễ bấm trên màn hình nhỏ
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .station-title { background-color: #007bff; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 15px; }
    .category-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e9ecef; }
    .stRadio > div { background-color: white; padding: 6px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 4px; }
    div.stRadio p { font-size: 15px !important; margin-bottom: 2px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 Kiểm kê Chuẩn Hóa 100% - HYN")

# Link dữ liệu Google Sheets gốc của Sếp
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')


# ==============================================================================
# 2. HÀM NẠP VÀ PHÂN TÍCH DỮ LIỆU CHUẨN HÓA THEO FILE EXCEL
# ==============================================================================
@st.cache_data(ttl=10)
def load_and_parse_sheets():
    # Đọc dữ liệu thô từ file csv xuất từ Sheets
    df_raw = pd.read_csv(csv_url, header=None, dtype=str).fillna("")
    
    # Giới hạn số cột tối đa theo file của Sếp (124 cột)
    max_cols = min(df_raw.shape[1], 124)
    df_raw = df_raw.iloc[:, :max_cols]
    
    # Đọc Hàng 2 (Danh mục cha) và Hàng 3 (Thuộc tính con)
    row2 = [str(val).strip() for val in df_raw.iloc[1]]
    row3 = [str(val).strip() for val in df_raw.iloc[2]]
    
    # Thuật toán Forward Fill bổ sung tên Danh mục cha bị khuyết danh ở dòng 2
    current_parent = "Thông tin chung"
    for i in range(len(row2)):
        if row2[i] != "" and not row2[i].startswith("Unnamed"):
            current_parent = row2[i]
        else:
            row2[i] = current_parent

    # Trích xuất danh sách dữ liệu trạm thật (bắt đầu từ hàng dữ liệu số 5)
    data_rows = []
    for r_idx in range(4, df_raw.shape[0]):
        ma_tram = str(df_raw.iloc[r_idx, 1]).strip()
        if not ma_tram or ma_tram.lower() in ["t", "tên trạm", "nan", "trống"]:
            continue
        
        cells_dict = {}
        for col_idx in range(max_cols):
            cells_dict[col_idx + 1] = str(df_raw.iloc[r_idx, col_idx]).strip()
            
        data_rows.append({
            "row_idx": r_idx + 1,
            "ma_tram": ma_tram,
            "cells": cells_dict
        })
        
    return row2, row3, data_rows, df_raw

try:
    headers_row2, headers_row3, rows_data, df_total_raw = load_and_parse_sheets()
    
    if "session_updates" not in st.session_state:
        st.session_state["session_updates"] = {}

    # ==============================================================================
    # 3. BƯỚC 1: TÌM KIẾM TRẠM THÔNG MINH
    # ==============================================================================
    st.write("### 🔍 Bước 1: Tìm Kiếm Trạm Khớp Chuỗi")
    search_keyword = st.text_input(
        "Nhập tên trạm hoặc mã trạm đối soát:", 
        placeholder="💡 Gõ liền không dấu (vd: hynatianthi) vẫn tìm được..."
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
            st.warning("⚠️ Không tìm thấy trạm nào khớp với từ khóa!")
        else:
            station_options = {s["ma_tram"]: s for s in matched_stations}
            choice = st.selectbox(f"💡 Tìm thấy ({len(matched_stations)}) trạm phù hợp:", list(station_options.keys()))
            selected_station_data = station_options[choice]
    else:
        all_stations = {s["ma_tram"]: s for s in rows_data}
        choice = st.selectbox("Hoặc chọn trực tiếp trạm từ danh sách tổng:", ["-- Chọn trạm --"] + list(all_stations.keys()))
        if choice != "-- Chọn trạm --":
            selected_station_data = all_stations[choice]

    # ==============================================================================
    # 4. BƯỚC 2: PHÂN CẤP VÀ HIỂN THỊ LỰA CHỌN THUẦN TÚY THEO FILE EXCEL
    # ==============================================================================
    if selected_station_data:
        ma_tram = selected_station_data["ma_tram"]
        cells = selected_station_data["cells"]
        
        st.markdown(f"<div class='station-title'>🏠 ĐANG KIỂM KÊ: {ma_tram}</div>", unsafe_allow_html=True)
        st.write(f"📅 *Ngày kiểm gần nhất ghi nhận: {cells.get(3, 'Chưa có')}*")
        
        # Xây dựng cấu trúc cây phân cấp
        tree_structure = {}
        for col_idx in range(4, len(headers_row2) + 1):
            p_name = headers_row2[col_idx - 1]
            c_name = headers_row3[col_idx - 1] or f"Trường_{col_idx}"
            c_val = cells.get(col_idx, "Trống")
            
            if p_name not in tree_structure:
                tree_structure[p_name] = []
            tree_structure[p_name].append({"col_idx": col_idx, "child": c_name, "current_val": c_val})
            
        st.write("### 📑 Bước 2: Chọn Trạng Thái Thực Tế")
        
        # Hiển thị các Hạng mục cha dạng Expander
        for parent_key, child_list in tree_structure.items():
            grp_changed = sum(1 for c in child_list if c["col_idx"] in st.session_state["session_updates"])
            expander_title = f"📁 {parent_key} " + (f"({grp_changed} ✏️)" if grp_changed > 0 else "")
            
            with st.expander(expander_title, expanded=False):
                for item in child_list:
                    c_id = item["col_idx"]
                    c_name = item["child"]
                    current_active_val = st.session_state["session_updates"].get(c_id, item["current_val"])
                    
                    # 🎯 CHUẨN HÓA 100%: Quét file thô lấy dữ liệu thực tế tại đúng cột này (bỏ qua 4 dòng đầu tiêu đề)
                    raw_values = df_total_raw.iloc[4:, c_id - 1].astype(str).str.strip()
                    
                    # Loại bỏ các giá trị rác, trống hoặc lỗi định dạng hệ thống
                    cleaned_set = set()
                    for v in raw_values:
                        if v and v.lower() not in ["", "nan", "nan", "none", "trống"]:
                            cleaned_set.add(v)
                    
                    # Sắp xếp danh sách lựa chọn theo thứ tự A-Z để giao diện khoa học
                    unique_options = sorted(list(cleaned_set))
                    
                    # Trường hợp dự phòng nếu cột này trong Excel trống hoàn toàn chưa có mẫu dữ liệu
                    if not unique_options:
                        unique_options = ["Chưa có dữ liệu", "Tốt", "Hỏng"]
                    
                    # Đảm bảo giá trị hiện tại của trạm PHẢI NẰM trong danh sách lựa chọn
                    if current_active_val not in unique_options and current_active_val not in ["", "Trống"]:
                        unique_options.insert(0, current_active_val)
                    
                    # Tính toán vị trí hiển thị mặc định (Index) khớp với dữ liệu hiện tại của trạm
                    default_idx = 0
                    if current_active_val in unique_options:
                        default_idx = unique_options.index(current_active_val)
                    
                    # Hiển thị tiêu đề thuộc tính con
                    st.markdown(f"✏️ **{c_name}** *(Giá trị hiện tại: `{item['current_val']}`)*", unsafe_allow_html=True)
                    
                    # Tạo hộp chọn thông minh: Chỉ xuất hiện các giá trị thực tế của cột đó
                    user_choice = st.radio(
                        f"Chọn dữ liệu cho {c_name} tại cột {c_id}",
                        options=unique_options,
                        index=default_idx,
                        key=f"radio_{ma_tram}_{c_id}",
                        label_visibility="collapsed"
                    )
                    
                    # Đồng bộ cập nhật vào session_state của Streamlit
                    if user_choice != item["current_val"]:
                        st.session_state["session_updates"][c_id] = user_choice
                    else:
                        st.session_state["session_updates"].pop(c_id, None)
                    st.write("---")

        # ==============================================================================
        # 5. BƯỚC 3: XÁC NHẬN HOÀN THÀNH KIỂM KÊ
        # ==============================================================================
        st.write("### 💾 Bước 3: Hoàn Tất Kiểm Kê")
        num_changes = len(st.session_state["session_updates"])
        st.info(f"📊 Đang có `{num_changes}` thuộc tính được cập nhật trạng thái mới.")
        
        if st.button("💾 GHI NHẬN KẾT QUẢ & CẬP NHẬT KẾT XUẤT", use_container_width=True, type="primary"):
            if num_changes == 0:
                st.warning("⚠️ Sếp chưa tích chọn hoặc thay đổi thuộc tính kiểm kê nào!")
            else:
                st.success(f"🎉 Thành công Sếp ơi! Hệ thống đã khóa và lưu kết quả của trạm {ma_tram}!")
                st.balloons()
                
                # In bảng đối soát trực quan ngay dưới màn hình mobile
                summary_data = []
                for c_id, n_val in st.session_state["session_updates"].items():
                    summary_data.append({
                        "Cột số": c_id,
                        "Danh mục lớn": headers_row2[c_id - 1],
                        "Hạng mục kiểm tra": headers_row3[c_id - 1],
                        "Kết quả kiểm kê mới": n_val
                    })
                st.write("**Bảng đối soát dữ liệu hiện trường vừa ghi nhận:**")
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"🚨 Hệ thống phát hiện lỗi đồng bộ: {e}")