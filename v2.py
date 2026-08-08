import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面組態設定
st.set_page_config(page_title="香港大專生 GPA 綜合分析系統", page_icon="🎓", layout="wide")

st.title("🎓 香港大專生 GPA 綜合分析與未來目標預測器")
st.write("這是一個全功能的大專生 GPA 工具：輸入已完成科目即可實時計算加權 GPA、繪製學期趨勢圖，並利用演算法推算未來目標策略！")

# 2. 香港大專院校標準等級對照表 (4.3 滿分制)
GRADE_MAP = {
    "A+ (4.3)": 4.3, "A  (4.0)": 4.0, "A- (3.7)": 3.7,
    "B+ (3.3)": 3.3, "B  (3.0)": 3.0, "B- (2.7)": 2.7,
    "C+ (2.3)": 2.3, "C  (2.0)": 2.0, "C- (1.7)": 1.7,
    "D+ (1.3)": 1.3, "D  (1.0)": 1.0, "F  (0.0)": 0.0
}

POINT_TO_GRADE = {
    4.3: "A+", 4.0: "A", 3.7: "A-",
    3.3: "B+", 3.0: "B", 2.7: "B-",
    2.3: "C+", 2.0: "C", 1.7: "C-",
    1.3: "D+", 1.0: "D", 0.0: "F"
}

SEMESTER_OPTIONS = ["Y1S1", "Y1S2", "Y2S1", "Y2S2", "Y3S1", "Y3S2", "Y4S1", "Y4S2"]

# 3. 初始化 session_state
if "courses_db" not in st.session_state:
    st.session_state.courses_db = pd.DataFrame([
        {"學期": "Y1S1", "課程名稱": "COMP1117", "學分": 6, "成績": "A  (4.0)"},
        {"學期": "Y1S1", "課程名稱": "CCCH9001", "學分": 6, "成績": "B+ (3.3)"},
        {"學期": "Y1S2", "課程名稱": "ENGG1330", "學分": 6, "成績": "B  (3.0)"},
        {"學期": "Y1S2", "課程名稱": "MATH1013", "學分": 6, "成績": "A- (3.7)"},
        {"學期": "Y2S1", "課程名稱": "COMP2119", "學分": 6, "成績": "C+ (2.3)"},
    ])

# 4. 數據輸入介面
st.subheader("1️⃣ 輸入已修讀課程與成績")

edited_df = st.data_editor(
    st.session_state.courses_db,
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

# 5. 數據預處理與加權運算核心
def process_course_data(df):
    if df.empty:
        return 0.0, 0, 0.0, pd.DataFrame()
    
    temp_df = df.copy()
    
    # 相容性自動修復：處理簡體/繁體欄位錯位
    if "課程名称" in temp_df.columns and "課程名稱" in temp_df.columns:
        temp_df["課程名稱"] = temp_df["課程名稱"].fillna(temp_df["課程名称"])
        
    temp_df["Point"] = temp_df["成績"].map(GRADE_MAP).fillna(0.0)
    temp_df["WeightedPoint"] = temp_df["Point"] * temp_df["學分"]
    
    total_credits = temp_df["學分"].sum()
    total_points = temp_df["WeightedPoint"].sum()
    current_gpa = total_points / total_credits if total_credits > 0 else 0.0
    
    # 分學期加權聚合
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
        
    return current_gpa, total_credits, total_points, pd.DataFrame(semester_summary)

current_gpa, past_credits, past_points, trend_df = process_course_data(edited_df)

# 6. 當前加權運算結果展報
col_metrics1, col_metrics2 = st.columns(2)
with col_metrics1:
    st.metric("📊 當前 Cumulative GPA", f"{current_gpa:.2f} / 4.3")
with col_metrics2:
    st.metric("📚 已修讀總學分", f"{past_credits} Credits")

st.divider()

# 7. 學期 GPA 走勢圖 (Plotly)
st.subheader("2️⃣ 各學期 GPA 走勢分析圖")

target_line = st.slider("🎯 設定趨勢圖中的目標 GPA 基準線:", min_value=2.0, max_value=4.3, value=3.0, step=0.1)

if not trend_df.empty:
    fig = go.Figure()

    # 單學期 GPA
    fig.add_trace(go.Scatter(
        x=trend_df["Semester"], y=trend_df["Semester GPA"],
        mode='lines+markers+text', name='單學期 GPA',
        text=trend_df["Semester GPA"], textposition="top center",
        line=dict(color='#1f77b4', width=3), marker=dict(size=8)
    ))

    # 累積 GPA
    fig.add_trace(go.Scatter(
        x=trend_df["Semester"], y=trend_df["Cumulative GPA"],
        mode='lines+markers+text', name='累積 GPA (Cumulative)',
        text=trend_df["Cumulative GPA"], textposition="bottom center",
        line=dict(color='#ff7f0e', width=3, dash='dot'), marker=dict(size=8)
    ))

    # 目標基準線
    fig.add_hline(
        y=target_line, line_dash="dash", line_color="red", 
        annotation_text=f"目標線 ({target_line})", annotation_position="bottom right"
    )

    fig.update_layout(
        title="<b>學期 GPA 走勢圖</b>",
        xaxis_title="學期 (Semester)", yaxis_title="GPA",
        yaxis=dict(range=[0, 4.3]), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("請在上方表格輸入至少一門課程資料以繪製趨勢圖。")

st.divider()

# 8. 未來成績預測優化演算法
st.subheader("3️⃣ 未來成績預測優化演算法")

col_pred1, col_pred2 = st.columns(2)
with col_pred1:
    target_gpa_input = st.number_input("🎯 畢業 / 目標 GPA:", min_value=1.0, max_value=4.3, value=3.0, step=0.1)
with col_pred2:
    future_credits_input = st.number_input("🔮 未來剩餘修讀總學分:", min_value=1, max_value=120, value=18, step=3)

# 貪婪預測演算法
def predict_future_grades_greedy(past_points, past_credits, future_credits, target_gpa):
    total_credits = past_credits + future_credits
    required_total_points = target_gpa * total_credits
    needed_future_points = required_total_points - past_points
    max_possible_points = 4.3 * future_credits
    
    # 狀況 1: 超出極限
    if needed_future_points > max_possible_points:
        max_possible_gpa = (past_points + max_possible_points) / total_credits
        return {
            "possible": False,
            "message": f"⚠️ 無法達成目標！即使未來 {future_credits} 個 Credits 全拿 A+，最高 Cumulative GPA 也只能達到 **{max_possible_gpa:.2f}**。"
        }
    
    # 狀況 2: 已經達標
    if needed_future_points <= 0:
        return {
            "possible": True,
            "easy": True,
            "message": "🎉 恭喜！你目前的 GPA 已經達到或超過目標 GPA，未來學期只需所有科目 Pass (D) 即可順利保住目標！",
            "required_future_avg_gpa": 1.0, "suggested_grade": "D", "projected_final_gpa": current_gpa
        }

    # 狀況 3: 計算需要平均表現
    required_future_avg_gpa = needed_future_points / future_credits
    
    sorted_points = sorted(POINT_TO_GRADE.keys())
    selected_point = 4.3
    for p in sorted_points:
        if p >= required_future_avg_gpa:
            selected_point = p
            break
            
    suggested_grade = POINT_TO_GRADE.get(selected_point, "A+")
    actual_projected_gpa = (past_points + (selected_point * future_credits)) / total_credits
    
    return {
        "possible": True, "easy": False,
        "required_future_avg_gpa": required_future_avg_gpa,
        "suggested_grade": suggested_grade,
        "grade_point": selected_point,
        "projected_final_gpa": actual_projected_gpa
    }

if st.button("🚀 執行目標預測演算法", type="primary"):
    res = predict_future_grades_greedy(past_points, past_credits, future_credits_input, target_gpa_input)
    
    st.markdown("#### 📋 演算法策略報告")
    
    if not res["possible"]:
        st.error(res["message"])
    elif res.get("easy", False):
        st.success(res["message"])
        st.balloons()
    else:
        st.info(f"為了達到目標 GPA **{target_gpa_input:.2f}**，你在未來的 **{future_credits_input}** 個學分中：")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric("📈 未來平均 GPA 需達", f"{res['required_future_avg_gpa']:.2f}")
        with col_res2:
            st.metric("🎯 每科建議最低等級", f"{res['suggested_grade']} ({res['grade_point']} 分)")
        with col_res3:
            st.metric("🏆 預計最終畢業 GPA", f"{res['projected_final_gpa']:.2f}")
            
        if res["suggested_grade"] in ["A+", "A"]:
            st.warning("🔥 提示：未來的目標設定較高，需要每門課都拿到 A 或以上，建議合理規劃難度較高的 Core Course 與 General Education！")
        elif res["suggested_grade"] in ["B+", "B"]:
            st.success("💪 提示：目標非常可行！保持穩定的 B / B+ 表現即可順利達標。")