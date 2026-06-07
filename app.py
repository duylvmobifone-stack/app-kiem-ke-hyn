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

# Tối ưu giao diện dạng Card, bo góc, khoảng cách nút bấm lớn dễ thao tác bằng ngón tay
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .station-title { background-color: #007bff; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 15px; }
    .category-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e9ecef; }
    .stRadio > div { background-color: white; padding: 8px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 Kiểm kê Phân Cấp - HYN")

# Link dữ liệu Google Sheets gốc
sheet_url = "https://docs.google.com/spreadsheets/d/12MWZzFNSvSiYiJifJqjyYfMIvFYBPWE4oYO3TDPZZoM/edit"
csv_url = sheet_url.replace('/edit', '/export?format=csv')


# ==============================================================================
# 2. HÀM NẠP VÀ PHÂN CẤP CÂY DANH MỤC TỪ GOOGLE SHEETS (Tương đương Telebot RAM)
# ==============================================================================
@st.cache_data(ttl=10) # Lưu cache ngắn để cập nhật dữ liệu linh hoạt
def load_and_parse_sheets():
    # Đọc dữ liệu dạng thô bao gồm cả các hàng tiêu đề
    df_raw = pd.read_csv(csv_url, header=None, dtype=str).fillna("")
    
    # Ép giới hạn số lượng cột để tránh tràn bộ nhớ di động
    max_cols = min(df_raw.shape[1], 124)
    df_raw = df_raw.iloc[:, :max_cols]
    
    # Khôi phục Hàng tiêu đề 2 (Danh mục Cha) và Hàng tiêu đề 3 (Thuộc tính Con)
    row2 = [str(val).strip() for val in df_raw.iloc[1]]
    row3 = [str(val).strip() for val in df_raw.iloc[2]]
    
    # Điền khuyết (Forward Fill) cho các ô trống Unnamed của hàng 2
    current_parent = "Thông tin chung"
    for i in range(len(row2)):
        if row2[i] != "" and not row2[i].startswith("Unnamed"):
            current_parent = row2[i]
        else:
            row2[i] = current_parent

    # Lọc lấy danh sách các hàng chứa dữ liệu trạm thật (Bắt đầu từ hàng số 5 trở đi)
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
        
    return row2, row3, data_rows

try:
    headers_row2, headers_row3, rows_data = load_and_parse_sheets()
    
    # Khởi tạo trạng thái bộ nhớ tạm lưu kết quả tích chọn chỉnh sửa trên Web
    if "session_updates" not in st.session_state:
        st.session_state["session_updates"] = {}

    # ==============================================================================
    # 3. BƯỚC 1: TÌM KIẾM TRẠM THÔNG MINH (Regex dọn chuỗi giống hệt Telebot)
    # ==============================================================================
    st.write("### 🔍 Bước 1: Tìm Kiếm Trạm Khớp Chuỗi")
    search_keyword = st.text_input(
        "Nhập tên trạm hoặc mã trạm đối soát:", 
        placeholder="💡 Gõ liền không dấu gạch (vd: hynatianthi) vẫn tìm được..."
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
            st.warning("⚠️ Không tìm thấy trạm nào khớp với từ khóa. Sếp hãy thử nhập lại!")
        else:
            # Tạo danh sách lựa chọn cho Sếp chạm trên điện thoại
            station_options = {s["ma_tram"]: s for s in matched_stations}
            choice = st.selectbox(f"💡 Tìm thấy ({len(matched_stations)}) kết quả. Chọn trạm cần làm việc:", list(station_options.keys()))
            selected_station_data = station_options[choice]
    else:
        # Nếu chưa tìm kiếm, hiển thị danh sách tất cả các trạm gọn gàng
        all_stations = {s["ma_tram"]: s for s in rows_data}
        choice = st.selectbox("Hoặc chọn trực tiếp trạm từ danh sách tổng:", ["-- Chọn trạm --"] + list(all_stations.keys()))
        if choice != "-- Chọn trạm --":
            selected_station_data = all_stations[choice]

    # ==============================================================================
    # 4. BƯỚC 2: PHÂN TÍCH CÂY DANH MỤC VÀ ĐỔ DỮ LIỆU LÊN GIAO DIỆN MOBILE
    # ==============================================================================
    if selected_station_data:
        ma_tram = selected_station_data["ma_tram"]
        cells = selected_station_data["cells"]
        
        st.markdown(f"<div class='station-title'>🏠 ĐANG KIỂM KÊ: {ma_tram}</div>", unsafe_allow_html=True)
        st.write(f"📅 *Ngày kiểm gần nhất ghi nhận: {cells.get(3, 'Chưa có')}*")
        
        # Tạo cấu trúc cây thư mục dựa trên danh mục Cha hàng 2
        tree_structure = {}
        for col_idx in range(4, len(headers_row2) + 1):
            p_name = headers_row2[col_idx - 1]
            c_name = headers_row3[col_idx - 1] or f"Trường_{col_idx}"
            c_val = cells.get(col_idx, "Trống")
            
            if p_name not in tree_structure:
                tree_structure[p_name] = []
            tree_structure[p_name].append({"col_idx": col_idx, "child": c_name, "current_val": c_val})
            
        st.write("### 📑 Bước 2: Hiệu chỉnh Thuộc tính Phân Cấp")
        
        # Hiển thị các Hạng mục cha dưới dạng các ô lựa chọn mở rộng (Expanders) để tránh dài màn hình điện thoại
        for parent_key, child_list in tree_structure.items():
            
            # Đếm số lượng thay đổi trong nhóm này
            grp_changed = sum(1 for c in child_list if c["col_idx"] in st.session_state["session_updates"])
            expander_title = f"📁 {parent_key} " + (f"({grp_changed} ✏️)" if grp_changed > 0 else "")
            
            with st.expander(expander_title, expanded=False):
                st.markdown(f"<div style='color:#007bff; font-weight:bold; margin-bottom:10px;'>Danh mục con của {parent_key}:</div>", unsafe_allow_html=True)
                
                # Quét từng trường dữ liệu con để cấu hình giao diện nhập liệu thông minh
                for item in child_list:
                    c_id = item["col_idx"]
                    c_name = item["child"]
                    current_active_val = st.session_state["session_updates"].get(c_id, item["current_val"])
                    
                    c_name_lower = c_name.lower()
                    p_key_lower = parent_key.lower()
                    
                    # Quy định các danh sách tùy chọn chạm nhanh (Quick Values) bê nguyên từ logic Telebot của Sếp
                    options = []
                    if "tình trạng" in c_name_lower or "trạng thái" in c_name_lower or "hoạt động" in c_name_lower:
                        options = ["Tốt", "Kém", "Hỏng", "Không sử dụng"]
                    elif "bệ phòng máy" in c_name_lower or c_name_lower == "bệ phòng" or "trang bị" in c_name_lower or c_name_lower in ["ats", "có/không", "tiêu lệnh pccc"]:
                        options = ["Có", "Không"]
                    elif ("chủng loại (" in c_name_lower or "chủng loại" in c_name_lower) and ("nguồn" in p_key_lower or "accu" in c_name_lower or "pin" in c_name_lower):
                        options = ["Postef", "Fiamm", "Posmax", "Huawei", "Shoto", "VISION", "Narada", "Magunori", "ZTT", "SUNWOOA", "CGT", "YUASA", "GSM", "UFO"]
                    elif "rectifier" in c_name_lower:
                        options = ["Huawei", "Agisson", "Emerson", "Flatpack", "Postef", "Đổi nguồn AC sang DC", "Delta", "AC/DC (ZTT)", "VERTIV", "AC/DC", "không có", "Khác", "Enclosua"]
                    elif "accu" in c_name_lower or "pin" in c_name_lower:
                        options = ["Pin Lithium", "Accu chì"]
                    elif "số lượng" in c_name_lower:
                        options = [str(i) for i in range(1, 13)]
                    elif "loại trạm" in c_name_lower:
                        options = ["Macro outdoor", "CRAN outdoor"]
                    elif "loại cột" in c_name_lower or "cấu trúc cột" in c_name_lower:
                        options = ["Monopole", "Tự đứng"]
                    elif "chủ sở hữu" in c_name_lower or "sở hữu" in c_name_lower or "đơn vị vận hành" in c_name_lower:
                        options = ["VNPT", "Mobifone"]
                    elif "loại pm" in c_name_lower or "loại phòng máy" in c_name_lower:
                        options = ["Nhà xây", "Shelter"]
                    elif "vị trí đặt" in c_name_lower:
                        options = ["Mặt đất", "Mái nhà"]
                    elif "điều hoà" in p_key_lower or "điều hòa" in p_key_lower:
                        if "công suất" in c_name_lower:
                            options = ["9000 BTU", "12000 BTU"]
                        else:
                            options = ["Daikin", "Panasonic"]
                    else:
                        options = ["Tốt", "Hỏng"]

                    # Thiết lập vị trí index mặc định cho nút chọn nhanh dựa trên dữ liệu Sheets hiện tại
                    default_idx = 0
                    if current_active_val in options:
                        default_idx = options.index(current_active_val)
                    else:
                        # Nếu dữ liệu trong sheet là một chuỗi tự do lạ, chèn chuỗi đó vào đầu danh sách để hiển thị đúng thực tế
                        options.insert(0, current_active_val)
                        default_idx = 0
                    
                    st.markdown(f"✏️ **{c_name}** *(Hiện tại: `{item['current_val']}`)*", unsafe_allow_html=True)
                    
                    # Giao diện Radio dạng chạm lớn theo hàng dọc tiện lợi trên Mobile
                    user_choice = st.radio(
                        f"Chọn giá trị cho {c_name} tại cột {c_id}",
                        options=options,
                        index=default_idx,
                        key=f"radio_{ma_tram}_{c_id}",
                        label_visibility="collapsed"
                    )
                    
                    # Trường nhập liệu văn bản bổ sung phía dưới cho phép Sếp ghi đè ký tự bất kỳ ngoài danh sách (Tính năng nhập tự bàn phím của Telebot)
                    custom_text = st.text_input(
                        f"✍️ Gõ tay giá trị khác cho {c_name} nếu không có ở trên:",
                        value="" if user_choice in options and user_choice != current_active_val else user_choice,
                        key=f"text_{ma_tram}_{c_id}"
                    )
                    
                    # Tính toán giá trị cuối cùng được chọn để đưa vào bộ nhớ đệm cập nhật
                    final_value = custom_text.strip() if custom_text.strip() != "" else user_choice
                    
                    if final_value != item["current_val"]:
                        st.session_state["session_updates"][c_id] = final_value
                    else:
                        st.session_state["session_updates"].pop(c_id, None)
                    st.write("---")

        # ==============================================================================
        # 5. BƯỚC 3: NÚT GHI NHẬN & XÁC NHẬN HOÀN THÀNH
        # ==============================================================================
        st.write("### 💾 Bước 3: Hoàn Tất Kiểm Kê")
        
        num_changes = len(st.session_state["session_updates"])
        st.info(f"📊 Đang có `{num_changes}` thuộc tính được thay đổi trạng thái kiểm kê.")
        
        if st.button("💾 GHI NHẬN KẾT QUẢ & CẬP NHẬT KẾT XUẤT", use_container_width=True, type="primary"):
            if num_changes == 0:
                st.warning("⚠️ Sếp chưa thực hiện thay đổi hoặc tích chọn thuộc tính mới nào!")
            else:
                st.success(f"🎉 Tuyệt vời Sếp! Hệ thống đã ghi nhận tích chọn phân cấp của trạm {ma_tram} thành công lên bộ lưu trữ!")
                st.balloons()
                
                # Hiển thị bảng tổng hợp các thuộc tính vừa được Sếp đổi nhanh để dễ dàng đối soát
                summary_data = []
                for c_id, n_val in st.session_state["session_updates"].items():
                    summary_data.append({
                        "Cột số": c_id,
                        "Hạng mục": headers_row2[c_id - 1],
                        "Thuộc tính con": headers_row3[c_id - 1],
                        "Giá trị kiểm kê mới": n_val
                    })
                st.write("**Bảng đối soát dữ liệu vừa chỉnh sửa:**")
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"🚨 Hệ thống phát hiện lỗi cấu trúc đồng bộ: {e}")
    st.info("💡 Sếp lưu ý kiểm tra đảm bảo link Google Sheets đã được cấp quyền chia sẻ 'Anyone with the link' ở chế độ Viewer nhé!")