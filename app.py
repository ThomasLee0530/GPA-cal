import streamlit as st
import pandas as pd

# 1. 設定網頁頁面
st.set_page_config(page_title="大專生 GPA 計算器", page_icon="🎓", layout="wide")

st.title("🎓 香港大專生 GPA 實時計算器")
st.write("在下方表格中自由新增/修改課程，系統會自動計算你的 GPA 與總學分！")

# 2. 定義香港各大專院校常用的 Grade Point 對照表
GRADE_POINT_MAP = {
    "A+ (4.3 / 4.0)": 4.3,
    "A  (4.0)": 4.0,
    "A- (3.7)": 3.7,
    "B+ (3.3)": 3.3,
    "B  (3.0)": 3.0,
    "B- (2.7)": 2.7,
    "C+ (2.3)": 2.3,
    "C  (2.0)": 2.0,
    "C- (1.7)": 1.7,
    "D+ (1.3)": 1.3,
    "D  (1.0)": 1.0,
    "F  (0.0)": 0.0
}

# 3. 初始化預設資料（若 session_state 未建立，則給予預設範例）
if "course_data" not in st.session_state:
    st.session_state.course_data = pd.DataFrame(
        [
            {"課程名稱 / Code": "COMP1117", "學分 (Credits)": 6, "成績 (Grade)": "A  (4.0)"},
            {"課程名稱 / Code": "CCCH9001", "學分 (Credits)": 6, "成績 (Grade)": "B+ (3.3)"},
            {"課程名稱 / Code": "MATH1013", "學分 (Credits)": 3, "成績 (Grade)": "A- (3.7)"},
        ]
    )

st.divider()

# 4. 使用 st.data_editor 建立動態可編輯表格
edited_df = st.data_editor(
    st.session_state.course_data,
    num_rows="dynamic",  # 允許使用者動態新增/刪除資料列
    column_config={
        "課程名稱 / Code": st.column_config.TextColumn(
            "課程名稱 / Code",
            help="輸入課程編號，例如 CCGL9001",
            default="New Course",
            required=True
        ),
        "學分 (Credits)": st.column_config.NumberColumn(
            "學分 (Credits)",
            help="課程學分數（通常為 3 或 6）",
            min_value=1,
            max_value=18,
            step=1,
            default=6,
            required=True
        ),
        "成績 (Grade)": st.column_config.SelectboxColumn(
            "成績 (Grade)",
            help="選擇該科得到的 Letter Grade",
            options=list(GRADE_POINT_MAP.keys()),
            default="B  (3.0)",
            required=True
        )
    },
    use_container_width=True,
    hide_index=True # 隱藏最左側的索引數字欄
)

# 5. 核心 GPA 演算法邏輯
def calculate_gpa(df):
    if df.empty:
        return 0.0, 0
    
    total_credits = 0
    total_points = 0.0
    
    for _, row in df.iterrows():
        credits = row["學分 (Credits)"]
        grade_str = row["成績 (Grade)"]
        
        # 從 Grade Point 對照表取出對應的分數
        point = GRADE_POINT_MAP.get(grade_str, 0.0)
        
        if credits > 0:
            total_credits += credits
            total_points += point * credits
            
    if total_credits == 0:
        return 0.0, 0
        
    gpa = total_points / total_credits
    return gpa, total_credits

# 計算結果
gpa, total_credits = calculate_gpa(edited_df)

# 6. 結果面板展示
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🎯 你的 GPA", f"{gpa:.2f} / 4.3")

with col2:
    st.metric("📚 總修讀學分", f"{total_credits} Credits")

with col3:
    if gpa >= 3.6:
        st.metric("🏆 成績等級", "First Class / Dean's List")
    elif gpa >= 3.0:
        st.metric("👍 成績等級", "Second Upper (2:1)")
    elif gpa >= 2.5:
        st.metric("👌 成績等級", "Second Lower (2:2)")
    else:
        st.metric("⚠️ 成績等級", "Pass / Need Improvement")

# 7. 互動小功能：播放慶祝動畫
if gpa >= 3.6 and total_credits > 0:
    st.balloons()