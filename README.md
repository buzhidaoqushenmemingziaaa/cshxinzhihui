# 模拟面试陪练

一个基于 Streamlit + DeepSeek 的模拟面试练习工具。  
输入意向岗位后，它会生成岗位职责，结合你的项目经历进行 3 轮技术追问，最后给出参考答案和面试诊断报告。

## 功能特性

- 根据意向岗位自动生成岗位职责
- 支持手动修改并确认岗位职责
- 支持填写或上传个人项目经历（最多 300 字）
- 技术官结合岗位职责和项目经历进行针对性追问
- 默认进行 3 轮技术提问
- 面试结束后生成参考答案
- 自动生成面试诊断报告，包括总体表现、维度得分、改进点和学习建议
- 支持重新开始面试

## 技术栈

- Python
- Streamlit：网页界面
- OpenAI Python SDK：调用大模型接口
- DeepSeek API：生成岗位职责、面试问题、参考答案和诊断报告
- 模型：`deepseek-chat`

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- 可访问 DeepSeek API 的网络
- 一个 DeepSeek API Key

### 2. 安装依赖

```bash
pip install streamlit openai
```

也可以创建 `requirements.txt`：

```txt
streamlit
openai
```

然后运行：

```bash
pip install -r requirements.txt
```

### 3. 获取 DeepSeek API Key

前往 DeepSeek 开放平台注册并创建 API Key：

```text
https://platform.deepseek.com/
```

### 4. 启动应用

```bash
streamlit run app.py
```

启动后，浏览器会自动打开本地页面。

### 5. 使用流程

1. 在左侧边栏填写 DeepSeek API Key；
2. 填写意向岗位，例如“Python 后端开发”；
3. 点击“生成岗位职责”；
4. 根据实际情况修改岗位职责，然后点击“确认”；
5. 填写或上传个人项目经历，最多 300 字；
6. 点击“确认项目经历并继续”；
7. 检查信息后点击“开始模拟”；
8. 回答技术官提出的 3 个问题；
9. 查看参考答案；
10. 查看面试诊断报告；
11. 如需重新练习，点击“重新开始”。

## 项目结构

```text
.
├── app.py              # 主程序
├── requirements.txt    # 依赖列表，可选
└── README.md           # 项目说明
```

## 配置说明

主要配置都在 `app.py` 顶部或调用逻辑中：

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `QUESTION_ROUNDS` | 技术官提问次数 | `3` |
| `PROJECT_EXP_MAX` | 个人项目经历字数上限 | `300` |
| `base_url` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `model` | 使用的模型 | `deepseek-chat` |

API Key 不需要写在代码里，直接在应用左侧边栏填写即可。

## 注意事项

- 请不要把真实 API Key 写进代码或提交到 GitHub；
- 本项目依赖大模型输出，模型回答可能存在波动；
- 参考答案和诊断报告仅供练习参考，不代表真实面试结果；
- 如果提示“API调用错误”，请检查 API Key、网络和账户余额；
- 项目经历最多 300 字，超出后需要精简。

## 常见问题

### 1. 启动时报错 `streamlit: command not found`

请先安装 Streamlit：

```bash
pip install streamlit
```

### 2. 提示 API 调用错误怎么办？

检查：

- API Key 是否填写正确；
- 网络是否能访问 DeepSeek；
- DeepSeek 账户是否有余额；
- 是否安装了 `openai` 库。

### 3. 为什么每次刷新后数据没了？

Streamlit 默认不持久化数据。当前项目使用 `st.session_state` 保存会话状态，关闭页面或重新开始后数据会清空。

## License

MIT