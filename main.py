from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
from agent_modules import generate_full_report
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader
from ddgs import DDGS  # 使用新的 ddgs 库

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# 配置 Tesseract 和 poppler（根据你的实际路径）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
poppler_path = r'D:\poppler\bin'

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text += page_text + "\n"
        if text.strip():
            return text
    except:
        pass
    print("检测到扫描件PDF，正在OCR识别...")
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    full_text = ""
    for image in images:
        page_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        full_text += page_text + "\n"
    return full_text

# 存储最后一次分析的文本和报告
last_text = ""
last_report = None

# 联网搜索工具函数（供 Agent 使用）
def search_web(query: str, max_results: int = 3) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "未找到相关结果。"
            output = ""
            for r in results:
                output += f"- {r['title']}: {r['body']}\n"
            return output
    except Exception as e:
        return f"搜索失败：{str(e)}"

@app.post("/analyze")
async def analyze_book(file: UploadFile = File(...)):
    global last_text, last_report
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    text = extract_text_from_pdf(tmp_path)
    if not text.strip():
        return {"error": "无法提取文本"}
    last_text = text
    report = generate_full_report(text, user_context="资源有限的初创团队")
    last_report = report
    return {"report": report}

@app.post("/ask_agent")
async def ask_agent(question: str, mode: str = "normal"):
    if not last_text or not last_report:
        return {"answer": "请先上传书籍并分析（调用 /analyze）"}
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
    
    # 根据模式选择不同的系统提示
    if mode == "debate":
        system_prompt = """你是一个擅长苏格拉底式质疑的辩论对手。你的任务是：
1. 对用户提出的观点或书中的结论，进行尖锐反驳。
2. 指出逻辑漏洞、隐藏假设、反例。
3. 用反问引导用户深入思考。
4. 不要轻易同意用户，要持续追问。
语气可以犀利，但保持建设性。"""
        # 辩论模式下温度稍高，更有创造性
        temperature = 0.7
    else:
        system_prompt = """你是一个温和的读书助手，基于分析报告和原文回答问题。如果用户需要实时信息（如天气、新闻、作者最新动态等），请使用联网搜索工具。"""
        temperature = 0.5
    
    # 构造消息（普通模式下加入搜索工具定义）
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""用户问题：{question}

===== 分析报告摘要 =====
{last_report.get('insight', '')[:1500]}
{last_report.get('critique', '')[:1500]}

===== 原文片段（前1500字符）=====
{last_text[:1500]}

请回答："""}
    ]
    
    # 普通模式下，增加工具调用能力（联网搜索）
    if mode != "debate":
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "当用户需要实时信息、新闻、天气、百科等外部知识时，调用此工具搜索网络。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        # 第一轮：让模型决定是否调用工具
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1000,
            temperature=temperature
        )
        # 检查是否有工具调用请求
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            tool_name = tool_call.function.name
            import json
            tool_args = json.loads(tool_call.function.arguments)
            if tool_name == "search_web":
                search_result = search_web(tool_args.get("query"))
                # 将工具结果添加到对话中
                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": search_result
                })
                final_response = client.chat.completions.create(
                    model="glm-4-flash",
                    messages=messages,
                    max_tokens=1000,
                    temperature=temperature
                )
                answer = final_response.choices[0].message.content
            else:
                answer = "未知工具调用"
        else:
            answer = response.choices[0].message.content
    else:
        # 辩论模式：不调用工具，直接生成反驳
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            max_tokens=1000,
            temperature=temperature
        )
        answer = response.choices[0].message.content
    
    return {"answer": answer}