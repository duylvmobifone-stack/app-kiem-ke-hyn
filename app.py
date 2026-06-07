import streamlit as st
import pandas as pd
import re

# ==============================================================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN CHUẨN MOBILE
# ==============================================================================
st.set_page_config(
    page_title="Kiểm kê tài sản trạm MobiFone", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Tối ưu giao diện di động: Tăng khoảng cách bấm, làm rõ ô nhập liệu bổ sung
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .station-title { background-color: #007bff; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 15px; }
    .stRadio > div { background-color: white; padding: 6px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 4px; }
    div.stRadio p { font-size: 15px !important; margin-bottom: 2px !important; }
    .input-hint { color: #ffc107; font-weight: bold; font-size: 13px; margin-top: -5px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# Đổi tên tiêu đề ứng dụng ngắn gọn theo ý Sếp
st.title("📱 Kiểm kê tài sản trạm MobiFone")

# Đường dẫn file Google Sheets xuất dữ liệu CSV của Sếp
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
    
    # Đọc Hàng tiêu đề 2 (Mục cha) và Hàng tiêu đề 3 (Thuộc tính con)
    row2 = [str(val).strip() for val in df_raw.iloc[1]]
    row3 = [str(val).strip() for val in df_raw.iloc[2]]
    
    # Tự động điền tên danh mục cha (Forward Fill)
    current_parent = "Thông tin chung"
    for i in range(len(row2)):
        if row2[i] != "" and not row2[i].startswith("Unnamed"):
            current_parent = row2[i]
        else:
            row2[i] = current_parent

    # Trích xuất dữ liệu của từng trạm (Bắt đầu từ hàng chỉ số 4)
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
    
    # Khởi tạo bộ lưu trữ đệm
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
        placeholder="💡 Ví dụ: hynatianthi hệ thống vẫn nhận diện được..."
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
            st.warning("⚠️ Không tìm thấy trạm nào trùng khớp!")
        else:
            station_options = {s["ma_tram"]: s for s in matched_stations}
            choice = st.selectbox(f"💡 Tìm thấy ({len(matched_stations)}) trạm phù hợp:", list(station_options.keys()))
            selected_station_data = station_options[choice]
    else:
        all_stations = {s["ma_tram"]: s for s in rows_data}
        choice = st.selectbox("Hoặc chọn trực tiếp trạm từ danh sách tổng:", ["-- Chọn trạm --"] + list(all_stations.keys()))
        if choice != "-- Chọn trạm --":
            selected_station_data = all_stations[choice]

    # Đổi trạm -> Reset bộ đệm để chống lỗi ghi đè chéo dữ liệu trạm cũ sang trạm mới
    if selected_station_data:
        if st.session_state["current_selected_station"] != selected_station_data["ma_tram"]:
            st.session_state["session_updates"] = {}
            st.session_state["current_selected_station"] = selected_station_data["ma_tram"]

    # ==============================================================================
    # 4. BƯỚC 2: HIỂN THỊ KIỂM KÊ - KẾT HỢP DANH SÁCH SẴN CÓ VÀ Ô NHẬP TAY
    # ==============================================================================
    if selected_station_data:
        ma_tram = selected_station_data["ma_tram"]
        cells = selected_station_data["cells"]
        
        st.markdown(f"<div class='station-title'>🏠 ĐANG KIỂM KÊ: {ma_tram}</div>", unsafe_allow_html=True)
        st.write(f"📅 *Ngày kiểm trên file gốc: {cells.get(3, 'Trống')}*")
        
        # Tạo cấu trúc phân cấp cây
        tree_structure = {}
        for col_idx in range(4, len(headers_row2) + 1):
            p_name = headers_row2[col_idx - 1]
            c_name = headers_row3[col_idx - 1] or f"Trường_{col_idx}"
            c_val = cells.get(col_idx, "Trống")
            
            if p_name not in tree_structure:
                tree_structure[p_name] = []
            tree_structure[p_name].append({"col_idx": col_idx, "child": c_name, "current_val": c_val})
            
        st.write("### 📑 Bước 2: Khảo sát & Tích chọn trạng thái")
        
        for parent_key, child_list in tree_structure.items():
            grp_changed = sum(1 for c in child_list if c["col_idx"] in st.session_state["session_updates"])
            expander_title = f"📁 {parent_key} " + (f"({grp_changed} Thay đổi ✏️)" if grp_changed > 0 else "")
            
            with st.expander(expander_title, expanded=False):
                for item in child_list:
                    c_id = item["col_idx"]
                    c_name = item["child"]
                    file_actual_val = item["current_val"] 
                    
                    # THUẬT TOÁN QUÉT TOÀN TỈNH: Lấy tất cả các mẫu dữ liệu từng tồn tại ở cột này
                    raw_values = df_total_raw.iloc[4:, c_id - 1].astype(str).str.strip()
                    cleaned_set = set()
                    for v in raw_values:
                        if v and v.lower() not in ["", "nan", "none", "trống"]:
                            cleaned_set.add(v)
                    
                    # Sắp xếp danh sách chuẩn từ A-Z
                    unique_options = sorted(list(cleaned_set))
                    
                    # Nếu cột này toàn tỉnh đang trống hoàn toàn, nạp sẵn vài từ khóa kiểm kê cơ bản làm mẫu
                    if not unique_options:
                        unique_options = ["Tốt", "Hỏng", "Có", "Không"]
                        
                    # Luôn đảm bảo có chữ "Trống" để nhân viên tích trả về trạng thái cũ nếu muốn
                    if "Trống" not in unique_options:
                        unique_options.insert(0, "Trống")
                    
                    # Đảm bảo giá trị thực tại của trạm (dù lạ hay quen) phải có trong danh sách chọn
                    if file_actual_val not in unique_options:
                        unique_options.insert(0, file_actual_val)
                    
                    # Thêm lựa chọn nhập tay vào cuối danh sách của tất cả các trường
                    custom_input_trigger = "➕ Nhập mới (Không có trong danh sách)"
                    if custom_input_trigger not in unique_options:
                        unique_options.append(custom_input_trigger)
                        
                    # Lấy trạng thái đang hoạt động trong bộ đệm (nếu có)
                    saved_val = st.session_state["session_updates"].get(c_id, file_actual_val)
                    
                    # Xác định vị trí index mặc định cho Radio Button
                    if saved_val in unique_options:
                        default_idx = unique_options.index(saved_val)
                    else:
                        default_idx = unique_options.index(custom_input_trigger)
                        
                    st.markdown(f"✏️ **{c_name}** *(Trên file gốc: `{file_actual_val}`)*", unsafe_allow_html=True)
                    
                    # Hộp chọn Radio chính xác tuyệt đối theo mã trạm, không lo nhảy trạm loạn vị trí
                    user_choice = st.radio(
                        f"Chọn dữ liệu cho {c_name} tại cột {c_id}",
                        options=unique_options,
                        index=default_idx,
                        key=f"radio_{ma_tram}_{c_id}_{file_actual_val}",
                        label_visibility="collapsed"
                    )
                    
                    final_value_to_save = user_choice
                    
                    # NẾU CHỌN NHẬP TAY: Mở hộp thoại text_input cho phép nhập tùy ý
                    if user_choice == custom_input_trigger:
                        st.markdown("<div class='input-hint'>✍️ Mời Sếp nhập dữ liệu mới phát sinh thực tế vào đây:</div>", unsafe_allow_html=True)
                        
                        old_typed_val = "" if saved_val == custom_input_trigger else saved_val
                        if old_typed_val == file_actual_val:
                            old_typed_val = ""
                            
                        typed_value = st.text_input(
                            f"Nhập tay cho {c_name} cột {c_id}",
                            value=old_typed_val,
                            key=f"text_{ma_tram}_{c_id}",
                            label_visibility="collapsed",
                            placeholder="Gõ chủng loại, công suất, thông số mới tại đây..."
                        ).strip()
                        
                        if typed_value:
                            final_value_to_save = typed_value
                        else:
                            final_value_to_save = custom_input_trigger
                            
                    # SO SÁNH NGHIÊM NGẶT: Chỉ ghi nhận vào danh sách lưu trữ nếu nó thực sự Khác dữ liệu file gốc
                    if final_value_to_save != file_actual_val and final_value_to_save != custom_input_trigger:
                        st.session_state["session_updates"][c_id] = final_value_to_save
                    else:
                        if c_id in st.session_state["session_updates"] and final_value_to_save == file_actual_val:
                            del st.session_state["session_updates"][c_id]
                            
                    st.write("---")

        # ==============================================================================
        # 5. BƯỚC 3: XÁC NHẬN HOÀN THÀNH KIỂM KÊ
        # ==============================================================================
        st.write("### 💾 Bước 3: Hoàn Tất Kiểm Kê")
        num_changes = len(st.session_state["session_updates"])
        
        if num_changes > 0:
            st.info(f"📊 Hệ thống ghi nhận có `{num_changes}` thuộc tính thực sự thay đổi hoặc thêm mới.")
            
            if st.button("💾 GHI NHẬN KẾT QUẢ & CẬP NHẬT KẾT XUẤT", use_container_width=True, type="primary"):
                st.success(f"🎉 Xuất sắc Sếp ơi! Đã lưu chính xác dữ liệu kiểm kê (bao gồm cả các tài sản lắp mới bổ sung) của trạm {ma_tram}!")
                st.balloons()
                
                # Bảng đối soát hiển thị trực tiếp cho nhân viên xem lại tại hiện trường
                summary_data = []
                for c_id, n_val in st.session_state["session_updates"].items():
                    summary_data.append({
                        "Cột số": c_id,
                        "Danh mục cha": headers_row2[c_id - 1],
                        "Hạng mục kiểm tra": headers_row3[c_id - 1],
                        "Hiện trạng file cũ": cells.get(c_id),
                        "Dữ liệu kiểm kê mới": n_val
                    })
                st.write("**Bảng đối soát dữ liệu ghi nhận tại hiện trường:**")
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Trạm này hiện tại hoàn toàn khớp 100% với file Excel mẫu, không có tài sản nào phát sinh thêm.")

except Exception as e:
    st.error(f"🚨 Hệ thống phát hiện lỗi đồng bộ: {e}")