import json
import re
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="模拟面试陪练", layout="wide")

QUESTION_ROUNDS = 3  # 技术官提问次数

# 初始化 session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stage" not in st.session_state:
    st.session_state.stage = "init"
if "round" not in st.session_state:
    st.session_state.round = 0
if "position" not in st.session_state:
    st.session_state.position = ""
if "duties" not in st.session_state:
    st.session_state.duties = ""
if "project_exp" not in st.session_state:
    st.session_state.project_exp = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "report" not in st.session_state:
    st.session_state.report = ""
if "aspect_counts" not in st.session_state:
    st.session_state.aspect_counts = {}

PROJECT_EXP_MAX = 300  # 个人项目经历字数上限

def call_llm(system_prompt, user_prompt, max_tokens=500):
    client = OpenAI(api_key=st.session_state.api_key, base_url="https://api.deepseek.com")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        content = ""
        # 防截断：若输出因 max_tokens 用尽被截断（finish_reason=length），自动让模型续写，最多续写2次
        for _ in range(3):
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens
            )
            choice = response.choices[0]
            content += (choice.message.content or "")
            if choice.finish_reason != "length":
                break
            messages = messages + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": "上面的输出因长度限制被截断了。请从中断的位置直接继续输出剩余内容，不要重复任何已输出的内容。"}
            ]
        return content
    except Exception as e:
        return f"API调用错误：{e}"

def parse_question_json(raw):
    """从模型输出中解析 aspect 和 question，解析失败时把整段文本当作问题。"""
    text = raw.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            aspect = str(data.get("aspect", "")).strip()
            question = str(data.get("question", "")).strip()
            if question:
                return (aspect or "通用"), question
        except json.JSONDecodeError:
            pass
    return "通用", text

def history_text():
    return "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

# 侧边栏
with st.sidebar:
    st.title("设置")
    api_key = st.text_input("DeepSeek API Key", type="password")
    position = st.text_input("意向岗位")
    if st.button("生成岗位职责"):
        if not api_key:
            st.error("请填写 API Key")
        elif not position:
            st.error("请填写意向岗位")
        else:
            st.session_state.api_key = api_key
            st.session_state.position = position
            with st.spinner("正在生成岗位职责..."):
                duties = call_llm(
                    "你是一位资深的招聘负责人，熟悉各类岗位的职责与要求。",
                    f"请生成「{position}」岗位的核心岗位职责，5-8条，每条一行，只输出职责内容，不要其他解释。",
                    max_tokens=800,
                )
            st.session_state.duties = duties
            st.session_state.project_exp = ""
            st.session_state.stage = "confirm_duties"
            for k in ("duties_edit", "project_exp_input", "uploaded_name"):
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

st.title("🎤 模拟面试陪练")
st.caption("输入意向岗位 → 确认职责 → 填写项目经历 → 技术官针对性追问 → 生成诊断报告")

# 显示聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 阶段处理
if st.session_state.stage == "init":
    st.info("请在左侧填写 API Key 和意向岗位，点击「生成岗位职责」开始。")

elif st.session_state.stage == "confirm_duties":
    st.subheader(f"「{st.session_state.position}」岗位职责")
    st.caption("模型已根据岗位生成职责，请根据你的实际情况修改，或直接确认。")
    duties_edit = st.text_area("岗位职责（可修改）", value=st.session_state.duties, height=300, key="duties_edit")
    if st.button("确认"):
        st.session_state.duties = duties_edit
        st.session_state.stage = "input_project"
        st.rerun()

elif st.session_state.stage == "input_project":
    st.subheader("个人项目经历")
    st.caption(f"请填写或上传你的个人项目经历，{PROJECT_EXP_MAX} 字以内。技术官将结合岗位职责和你的项目经历进行针对性提问。")

    uploaded = st.file_uploader("上传项目经历文件（.txt / .md，可选）", type=["txt", "md"])
    if uploaded is not None and st.session_state.get("uploaded_name") != uploaded.name:
        st.session_state["uploaded_name"] = uploaded.name
        # 文件内容回填到文本框，超出上限则截断
        st.session_state["project_exp_input"] = uploaded.read().decode("utf-8", errors="ignore").strip()[:PROJECT_EXP_MAX]
        st.rerun()

    exp_edit = st.text_area(
        "项目经历（可直接填写，也可上传文件后修改）",
        height=200,
        key="project_exp_input",
        placeholder="例如：做过一个基于 RAG 的知识库问答系统，负责文档切分、向量检索与重排……",
    )
    used = len(exp_edit.strip())
    st.caption(f"已输入 {used}/{PROJECT_EXP_MAX} 字")
    if st.button("确认项目经历并继续"):
        if used == 0:
            st.warning("请填写或上传你的项目经历。")
        elif used > PROJECT_EXP_MAX:
            st.warning(f"项目经历不能超过 {PROJECT_EXP_MAX} 字，当前 {used} 字，请精简后再提交。")
        else:
            st.session_state.project_exp = exp_edit.strip()
            st.session_state.stage = "ready"
            st.rerun()

elif st.session_state.stage == "ready":
    st.subheader("信息确认")
    st.markdown(f"**岗位职责**")
    st.markdown(st.session_state.duties)
    st.markdown(f"**个人项目经历**")
    st.markdown(st.session_state.project_exp)
    if st.button("开始模拟"):
        st.session_state.messages = []
        st.session_state.round = 0
        st.session_state.aspect_counts = {}
        st.session_state.report = ""
        st.session_state.stage = "tech_q"
        st.rerun()

elif st.session_state.stage == "tech_q":
    if st.session_state.round >= QUESTION_ROUNDS:
        st.session_state.stage = "ref_answers"
        st.rerun()
    else:
        aspects_summary = "、".join(
            [f"{k}（{v}次）" for k, v in st.session_state.aspect_counts.items()]
        ) or "暂无"
        prompt = (
            f"岗位职责：\n{st.session_state.duties}\n\n"
            f"候选人的个人项目经历：\n{st.session_state.project_exp}\n\n"
            f"历史对话：\n{history_text() or '（无）'}\n\n"
            f"已提问的方面及次数：{aspects_summary}\n\n"
            "请结合岗位职责要求和候选人的项目经历，选择一个技术方面，向候选人提出下一个深入的技术问题。要求：\n"
            "1. 问题必须从候选人项目经历中的具体做法切入，并与岗位职责的要求挂钩，做到有针对性，不要问与候选人经历无关的泛泛问题；\n"
            "2. 问题要犀利、直击要害，善于发现项目经历或回答中的漏洞、含糊或夸大之处；\n"
            "3. 不要抠字眼、不纠结措辞，重点考察技术理解与逻辑；\n"
            "4. 若候选人的回答出现逻辑跑偏、无法回答或内容空洞，立即更换其他方面提问，新方面仍须与岗位职责和项目经历匹配；\n"
            "5. 同一个方面最多提问2次，已达2次的方面不要再问。\n"
            '只输出一个JSON对象，格式：{"aspect": "方面名称（简短）", "question": "问题内容"}'
        )
        with st.spinner("技术官正在思考..."):
            raw = call_llm("你是一位资深技术面试官，擅长犀利追问、发现漏洞，但不会抠字眼。", prompt)
        aspect, question = parse_question_json(raw)
        st.session_state.aspect_counts[aspect] = st.session_state.aspect_counts.get(aspect, 0) + 1
        st.session_state.messages.append(
            {"role": "assistant", "content": f"**【技术官 · 第{st.session_state.round + 1}问 · {aspect}】** {question}"}
        )
        st.session_state.stage = "wait_answer_tech"
        st.rerun()

elif st.session_state.stage == "wait_answer_tech":
    st.info(f"第 {st.session_state.round + 1}/{QUESTION_ROUNDS} 问，请回答")
    # key 按轮次区分，进入下一问时是全新控件，不会残留上一轮的答案
    answer = st.text_area("你的回答", key=f"tech_answer_{st.session_state.round}", height=150)
    if st.button("提交回答", key="submit_tech"):
        if answer.strip():
            st.session_state.messages.append({"role": "user", "content": answer})
            st.session_state.round += 1
            st.session_state.stage = "tech_q"
            st.rerun()
        else:
            st.warning("请输入你的回答后再提交。")

elif st.session_state.stage == "ref_answers":
    q_list = [m["content"] for m in st.session_state.messages
              if m["role"] == "assistant" and "【技术官" in m["content"]]
    questions_block = "\n\n".join([f"问题{i+1}：{q}" for i, q in enumerate(q_list)])
    prompt = (
        f"岗位职责：\n{st.session_state.duties}\n\n"
        f"候选人的个人项目经历：\n{st.session_state.project_exp}\n\n"
        f"本次面试技术官提出的{len(q_list)}个问题：\n{questions_block}\n\n"
        "请针对每个问题分别给出参考答案。要求：\n"
        "1. 每题先列出核心要点（3-5条），再结合候选人项目经历中的实际场景，用2-3句话给出回答思路示范；\n"
        "2. 答案深度须匹配岗位职责，体现面试官期待的水平；\n"
        "3. 用 Markdown 格式，按「### 第1问」「### 第2问」…分节，只输出参考答案内容，不要输出其他解释。"
    )
    with st.spinner("正在生成三道题的参考答案..."):
        result = call_llm(
            "你是一位资深技术面试官，给出的参考答案专业、全面、要点清晰。",
            prompt,
            max_tokens=3072,
        )
    if result.startswith("API调用错误"):
        st.error(f"{result}，请点击下方按钮重试。")
        if st.button("重新生成参考答案"):
            st.rerun()
    else:
        st.session_state.messages.append({"role": "assistant", "content": f"**【参考答案】**\n\n{result}"})
        st.session_state.stage = "report"
        st.rerun()

elif st.session_state.stage == "report":
    if not st.session_state.report:
        prompt = (
            f"意向岗位：{st.session_state.position}\n"
            f"面试轮次：{QUESTION_ROUNDS} 轮\n\n"
            f"岗位职责：\n{st.session_state.duties}\n\n"
            f"候选人的个人项目经历：\n{st.session_state.project_exp}\n\n"
            f"完整对话：\n{history_text()}\n\n"
            "注意：对话中标注【参考答案】的内容是面试官的参考材料，不是候选人的回答，评分时请忽略它。\n"
            "请基于对话中候选人的实际回答生成面试诊断报告正文，严格使用 Markdown，且只包含以下四个部分：\n"
            "## 一、总体表现\n（2-4句话概述候选人的整体表现）\n"
            "## 二、各维度得分汇总\n（对「技术深度」「逻辑清晰度」「边界意识」三个维度各打 1-5 分，"
            "用表格列出维度、得分、评分依据）\n"
            "## 三、最需要改进的点\n（指出一个或几个最需要改进的点，每个点结合对话中的具体表现说明，不要泛泛而谈）\n"
            "## 四、下一步学习建议\n（给出具体、可执行的学习建议，可分阶段列出）\n"
            "不要输出报告标题，不要输出这四部分以外的内容。"
        )
        with st.spinner("正在生成诊断报告..."):
            result = call_llm(
                "你是一位资深的面试教练兼评估官，评分客观、建议具体可执行。",
                prompt,
                max_tokens=8192,
            )
        if result.startswith("API调用错误"):
            st.error(f"{result}，请点击下方按钮重试。")
            if st.button("重新生成报告"):
                st.rerun()
        else:
            st.session_state.report = result
            st.rerun()
    else:
        st.divider()
        st.title("面试诊断报告")
        st.caption(f"意向岗位：{st.session_state.position}　|　面试轮次：{QUESTION_ROUNDS} 轮")
        st.markdown(st.session_state.report)
        st.success("面试结束！诊断报告已生成。")
        if st.button("重新开始"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
