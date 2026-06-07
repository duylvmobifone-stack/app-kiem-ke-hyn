import streamlit as st
import pandas as pd
import re

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN CHUẨN SMARTPHONE (MOBILE-FIRST UI)
# ==============================================================================
st.set_page_config(
    page_title="Kiểm kê tài sản trạm MobiFone", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Khóa chết màu nhấn hiển thị (Accent/Primary) từ Đỏ sang Xanh MobiFone
st.markdown("""
    <style>
    /* Nới rộng không gian hiển thị trên mobile */
    .block-container { padding-top: 0.5rem; padding-bottom: 1rem; padding-left: 0.8rem; padding-right: 0.8rem; }
    
    /* Khắc phục lỗi lấp dấu chữ: Hạ cỡ chữ tiêu đề App nhỏ gọn */
    .app-main-title {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #212529;
        margin-top: 5px;
        margin-bottom: 15px;
        text-align: left;
        line-height: 1.2;
    }
    
    /* Thiết kế Banner trạm hiện đại */
    .station-banner {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%);
        color: white; padding: 14px; border-radius: 12px;
        text-align: center; font-weight: bold; font-size: 18px;
        margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Làm đẹp các Khung Expander danh mục cha */
    .stExpander { border: 1px solid #dee2e6 !important; border-radius: 10px !important; margin-bottom: 10px !important; background-color: #f8f9fa; }
    
    /* Thiết kế tiêu đề thuộc tính con tinh gọn, rõ ràng */
    .prop-title { font-size: 15px; font-weight: 600; color: #212529; margin-bottom: 2px; margin-top: 5px; }
    .prop-old-val { font-size: 12px; color: #6c757d; margin-bottom: 6px; }
    
    /* ÉP CÁC NÚT RADIO HIỂN THỊ HÀNG NGANG DẠNG THẺ CHẠM (FLEXBOX INLINE) */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* Biến các item lựa chọn thành nút bấm bo góc xinh xắn giống App di động */
    div[data-testid="stRadio"] label {
        background-color: #ffffff !important;
        border: 1px solid #ced4da !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        cursor: pointer !important;
        min-width: 60px;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    /* ĐỔI MÀU ĐỎ SANG XANH: Khi nút được TÍCH CHỌN, đổi nền xanh nhạt viền xanh đậm */
    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"]:checked + div {
        background-color: #e6f0fa !important;
        border: 1.5px solid #007bff !important;
        border-radius: 20px !important;
    }
    
    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"]:checked + div p {
        color: #007bff !important;
        font-weight: bold !important;
    }
    
    /* Ẩn dấu chấm tròn Radio mặc định của trình duyệt */
    div[data-testid="stRadio"] input[type="radio"] { display: none !important; }
    div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p { font-size: 14px !important; margin: 0 !important; }
    
    /* Đường phân cách siêu mảnh gọn gàng */
    .divider { border-top: 1px dashed #e0e0e0; margin-top: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='app-main-title'>📱 Kiểm kê tài sản trạm MobiFone</div>", unsafe_allow_html=True)

# Đường dẫn file Google Sheets gốc của Sếp
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')

# ==============================================================================
# 2. HÀM NẠP VÀ TRÍCH XUẤT CHUẨN DANH MỤC TOÀN TỈNH
# ==============================================================================
@st.cache_data(ttl=5)
def load_and_parse_sheets():
    df_raw = pd.read_csv(csv_url, header=None, dtype=str).fillna("")
    max_cols = min(df_raw.shape[1], 124)
    df_raw = df_raw.iloc[:, :max_cols]
    
    row2 = [str(val).strip() for val in df_raw.iloc[1]]
    row3 = [str(val).strip() for val in df_raw.iloc[2]]
    
    current_parent = "Thông tin chung"
    for i in range(len(row2)):
        if row2[i] != "" and not row2[i].startswith("Unnamed"):
            current_parent = row2[i]
        else:
            row2[i] = current_parent

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
    
    if "session_updates" not in st.session_state:
        st.session_state["session_updates"] = {}
    if "current_selected_station" not in st.session_state:
        st.session_state["current_selected_station"] = ""

    # ==============================================================================
    # 3. BƯỚC 1: TÌM KIẾM TRẠM
    # ==============================================================================
    st.write("### 🔍 Bước 1: Tìm Kiếm Trạm Khớp Chuỗi")
    search_keyword = st.text_input(
        "Nhập tên trạm hoặc mã trạm đối soát:", 
        placeholder="💡 Gõ liền không dấu vẫn tìm ra trạm...",
        label_visibility="collapsed"
    )
    
    selected_station_data = None
    
    if search_keyword:
        keyword_clean = re.sub(r'[^a-zA-Z0-9]', '', search_keyword).lower()
        matched_stations = []
        for s in rows_data:
            ma_goc_clean = re.sub(r'[^a-zA-Z0-9]', '', s["ma_tram"]).lower()
            if keyword_clean in ma_goc_clean:
                matched_stations.append(s)
                
        if matched_stations:
            station_options = {s["ma_tram"]: s for s in matched_stations}
            choice = st.selectbox(f"💡 Tìm thấy ({len(matched_stations)}) trạm:", list(station_options.keys()))
            selected_station_data = station_options[choice]
        else:
            st.warning("⚠️ Không tìm thấy trạm nào trùng khớp!")
    else:
        all_stations = {s["ma_tram"]: s for s in rows_data}
        choice = st.selectbox("Hoặc chọn trực tiếp từ danh sách tổng:", ["-- Chọn trạm kiểm kê --"] + list(all_stations.keys()))
        if choice != "-- Chọn trạm kiểm kê --":
            selected_station_data = all_stations[choice]

    if selected_station_data:
        if st.session_state["current_selected_station"] != selected_station_data["ma_tram"]:
            st.session_state["session_updates"] = {}
            st.session_state["current_selected_station"] = selected_station_data["ma_tram"]

    # ==============================================================================
    # 4. BƯỚC 2: GIAO DIỆN HIỂN THỊ KIỂM KÊ HIỆN ĐẠI DẠNG CHẠM VUỐT
    # ==============================================================================
    if selected_station_data:
        ma_tram = selected_station_data["ma_tram"]
        cells = selected_station_data["cells"]
        
        st.markdown(f"<div class='station-banner'>🏠 TRẠM: {ma_tram}</div>", unsafe_allow_html=True)
        
        tree_structure = {}
        for col_idx in range(4, len(headers_row2) + 1):
            p_name = headers_row2[col_idx - 1]
            c_name = headers_row3[col_idx - 1] or f"Trường_{col_idx}"
            c_val = cells.get(col_idx, "Trống")
            
            if any(err_tag in c_name.upper() for err_tag in ["DWDM", "THIẾT BỊ PE", "ROUTER PE"]):
                continue
                
            if p_name not in tree_structure:
                tree_structure[p_name] = []
            tree_structure[p_name].append({"col_idx": col_idx, "child": c_name, "current_val": c_val})
            
        st.write("### 📑 Bước 2: Tích chọn nhanh trạng thái")
        
        for parent_key, child_list in tree_structure.items():
            if not child_list:
                continue
                
            grp_changed = sum(1 for c in child_list if c["col_idx"] in st.session_state["session_updates"])
            expander_title = f"📁 {parent_key} " + (f"({grp_changed} Thay đổi ✏️)" if grp_changed > 0 else "")
            
            with st.expander(expander_title, expanded=False):
                for item in child_list:
                    c_id = item["col_idx"]
                    c_name = item["child"]
                    file_actual_val = item["current_val"] 
                    
                    # Quét toàn tỉnh gom danh sách chọn sạch sẽ
                    raw_values = df_total_raw.iloc[4:, c_id - 1].astype(str).str.strip()
                    cleaned_set = set()
                    for v in raw_values:
                        if v and v.lower() not in ["", "nan", "none", "trống"]:
                            cleaned_set.add(v)
                    
                    # 🎯 THUẬT TOÁN SẮP XẾP SỐ THÔNG MINH
                    numbers_list = []
                    strings_list = []
                    
                    for v in cleaned_set:
                        # Kiểm tra xem chuỗi có phải là số nguyên hoặc số thập phân không
                        if re.match(r'^\d+(\.\d+)?$', v):
                            numbers_list.append(float(v) if '.' in v else int(v))
                        else:
                            strings_list.append(v)
                    
                    # Sắp xếp danh sách số theo toán học, danh sách chữ theo bảng chữ cái A-Z
                    numbers_list = sorted(numbers_list)
                    strings_list = sorted(strings_list)
                    
                    # Chuyển đổi ngược danh sách số về chuỗi và gộp lại
                    unique_options = [str(x) for x in numbers_list] + strings_list
                    
                    if not unique_options:
                        unique_options = ["Tốt", "Hỏng", "Có", "Không"]
                        
                    # Đảm bảo chữ "Trống" luôn nằm ở đầu danh sách để dễ chọn
                    if "Trống" in unique_options:
                        unique_options.remove("Trống")
                    unique_options.insert(0, "Trống")
                    
                    # Đảm bảo giá trị thực tế của trạm (nếu có sẵn) phải nằm trong danh mục chọn
                    if file_actual_val not in unique_options:
                        unique_options.insert(0, file_actual_val)
                    
                    # Luôn đặt lựa chọn "Nhập mới" ở vị trí cuối cùng dưới đáy
                    custom_input_trigger = "➕ Nhập mới"
                    if custom_input_trigger in unique_options:
                        unique_options.remove(custom_input_trigger)
                    unique_options.append(custom_input_trigger)
                        
                    saved_val = st.session_state["session_updates"].get(c_id, file_actual_val)
                    default_idx = unique_options.index(saved_val) if saved_val in unique_options else unique_options.index(custom_input_trigger)
                    
                    st.markdown(f"<div class='prop-title'>{c_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='prop-old-val'>Hiện trạng: {file_actual_val}</div>", unsafe_allow_html=True)
                    
                    user_choice = st.radio(
                        f"col_{ma_tram}_{c_id}",
                        options=unique_options,
                        index=default_idx,
                        key=f"radio_{ma_tram}_{c_id}_{file_actual_val}",
                        label_visibility="collapsed"
                    )
                    
                    final_value_to_save = user_choice
                    
                    if user_choice == custom_input_trigger:
                        old_typed_val = "" if saved_val == custom_input_trigger else saved_val
                        if old_typed_val == file_actual_val:
                            old_typed_val = ""
                            
                        typed_value = st.text_input(
                            f"text_{ma_tram}_{c_id}",
                            value=old_typed_val,
                            key=f"text_{ma_tram}_{c_id}",
                            label_visibility="collapsed",
                            placeholder="Gõ thông số mới tại đây..."
                        ).strip()
                        
                        if typed_value:
                            final_value_to_save = typed_value
                            
                    if final_value_to_save != file_actual_val and final_value_to_save != custom_input_trigger:
                        st.session_state["session_updates"][c_id] = final_value_to_save
                    else:
                        if c_id in st.session_state["session_updates"] and final_value_to_save == file_actual_val:
                            del st.session_state["session_updates"][c_id]
                            
                    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # ==============================================================================
        # 5. BƯỚC 3: HOÀN TẤT KIỂM KÊ
        # ==============================================================================
        st.write("### 💾 Bước 3: Hoàn Tất Kiểm Kê")
        num_changes = len(st.session_state["session_updates"])
        
        if num_changes > 0:
            st.info(f"📊 Có `{num_changes}` thuộc tính thay đổi.")
            if st.button("💾 GHI NHẬN KẾT QUẢ & CẬP NHẬT KẾT XUẤT", use_container_width=True, type="primary"):
                st.success(f"🎉 Đã lưu kết quả của trạm {ma_tram}!")
                st.balloons()
        else:
            st.success("✅ Trạm trùng khớp 100% với file gốc.")

except Exception as e:
    st.error(f"🚨 Lỗi đồng bộ: {e}")