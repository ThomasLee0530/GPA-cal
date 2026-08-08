import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="GPA 計算器 & 趨勢圖", page_icon="📈", layout="wide")

st.title("📈 大專生 GPA 實時計算與學期趨勢分析")

# 2. 香港大專對照表
GRADE_MAP = {
    "A+ (4.3)": 4.3, "A  (4.0)": 4.0, "A- (3.7)": 3.7,
    "B+ (3.3)": 3.3, "B  (3.0)": 3.0, "B- (2.7)": 2.7,
    "C+ (2.3)": 2.3, "C  (2.0)": 2.0, "C- (1.7)": 1.7,
    "D+ (1.3)": 1.3, "D  (1.0)": 1.0, "F  (0.0)": 0.0
}

SEMESTER_OPTIONS = ["Y1S1", "Y1S2", "Y2S1", "Y2S2", "Y3S1", "Y3S2", "Y4S1", "Y4S2"]

# 3. 初始化乾淨的數據（統一使用繁體「課程名稱」）
if "past_courses_fixed" not in st.session_state:
    st.session_state.past_courses_fixed = pd.DataFrame([
        {"學期": "Y1S1", "課程名稱": "COMP1117", "學分": 6, "成績": "A  (4.0)"},
        {"學期": "Y1S1", "課程名稱": "CCCH9001", "學分": 6, "成績": "B+ (3.3)"},
        {"學期": "Y1S2", "課程名稱": "ENGG1330", "學分": 6, "成績": "B  (3.0)"},
        {"學期": "Y1S2", "課程名稱": "MATH1013", "學分": 6, "成績": "A- (3.7)"},
        {"學期": "Y2S1", "課程名稱": "COMP2119", "學分": 6, "成績": "C+ (2.3)"},
    ])

st.subheader("1️⃣ 輸入學期與課程成績")

# 4. 可編輯表格（指定明確欄位與寬度）
edited_df = st.data_editor(
    st.session_state.past_courses_fixed,
    num_rows="dynamic",
    column_config={
        "學期": st.column_config.SelectboxColumn("學期", options=SEMESTER_OPTIONS, default="Y1S1", required=True, width="small"),
        "課程名稱": st.column_config.TextColumn("課程名稱 / Code", default="COMPxxxx", required=True, width="medium"),
        "學分": st.column_config.NumberColumn("學分", min_value=1, max_value=12, step=1, default=6, required=True, width="small"),
        "成績": st.column_config.SelectboxColumn("成績", options=list(GRADE_MAP.keys()), default="B  (3.0)", required=True, width="medium")
    },
    use_container_width=True,
    hide_index=True
)

st.divider()

# 5. 計算各學期 GPA 的邏輯（包含相容性自動修復）
def calculate_trends(df):
    if df.empty:
        return pd.DataFrame()
    
    temp_df = df.copy()
    
    # 🛠️ 自動容錯修復：如果同時存在簡體「課程名称」與繁體「課程名稱」，進行合併
    if "課程名称" in temp_df.columns and "課程名稱" in temp_df.columns:
        temp_df["課程名稱"] = temp_df["課程名稱"].fillna(temp_df["課程名称"])
    
    # 將成績標籤轉換為數字點數
    temp_df["Point"] = temp_df["成績"].map(GRADE_MAP).fillna(0.0)
    temp_df["WeightedPoint"] = temp_df["Point"] * temp_df["學分"]
    
    semester_summary = []
    present_semesters = [sem for sem in SEMESTER_OPTIONS if sem in temp_df["學期"].unique()]
    
    cum_credits = 0
    cum_weighted_points = 0.0
    
    for sem in present_semesters:
        sem_data = temp_df[temp_df["學期"] == sem]
        
        sem_credits = sem_data["學分"].sum()
        sem_points = sem_data["WeightedPoint"].sum()
        sem_gpa = sem_points / sem_credits if sem_credits > 0 else 0.0
        
        cum_credits += sem_credits
        cum_weighted_points += sem_points
        cum_gpa = cum_weighted_points / cum_credits if cum_credits > 0 else 0.0
        
        semester_summary.append({
            "Semester": sem,
            "Semester GPA": round(sem_gpa, 2),
            "Cumulative GPA": round(cum_gpa, 2),
            "Semester Credits": sem_credits
        })
        
    return pd.DataFrame(semester_summary)

trend_df = calculate_trends(edited_df)

# 6. 繪製 Plotly 圖表
st.subheader("2️⃣ GPA 學期變化趨勢圖")

target_line = st.slider("🎯 設定目標 GPA 基準線:", min_value=2.0, max_value=4.3, value=3.0, step=0.1)

if not trend_df.empty:
    fig = go.Figure()

    # 線條 1：單學期 GPA
    fig.add_trace(go.Scatter(
        x=trend_df["Semester"],
        y=trend_df["Semester GPA"],
        mode='lines+markers+text',
        name='單學期 GPA (Semester GPA)',
        text=trend_df["Semester GPA"],
        textposition="top center",
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))

    # 線條 2：累積 GPA
    fig.add_trace(go.Scatter(
        x=trend_df["Semester"],
        y=trend_df["Cumulative GPA"],
        mode='lines+markers+text',
        name='累積 GPA (Cumulative GPA)',
        text=trend_df["Cumulative GPA"],
        textposition="bottom center",
        line=dict(color='#ff7f0e', width=3, dash='dot'),
        marker=dict(size=8)
    ))

    # 線條 3：目標基準線
    fig.add_hline(
        y=target_line, 
        line_dash="dash", 
        line_color="red", 
        annotation_text=f"目標 GPA ({target_line})", 
        annotation_position="bottom right"
    )

    fig.update_layout(
        title="<b>各學期 GPA 走勢比較圖</b>",
        xaxis_title="學期 (Semester)",
        yaxis_title="GPA",
        yaxis=dict(range=[0, 4.3]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("請在上方表格輸入至少一門課程資料以繪製趨勢圖。")