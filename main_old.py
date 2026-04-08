from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.zhipuai import ZhipuAI
from llama_index.embeddings.zhipuai import ZhipuAIEmbedding
import os
import shutil
import tempfile
from typing import List
from llama_index.core.schema import Document
from agent_modules import generate_full_report, call_llm

# OCR 相关导入
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# 配置 Tesseract 路径（如果安装时没加PATH，需要指定）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 配置 poppler 路径
poppler_path = r'D:\poppler\bin'

# 设置智谱AI
api_key = os.getenv("ZHIPUAI_API_KEY")
if not api_key:
    raise ValueError("请先设置环境变量 ZHIPUAI_API_KEY")

Settings.llm = ZhipuAI(model="glm-4-flash", api_key=api_key)
Settings.embed_model = ZhipuAIEmbedding(model="embedding-2", api_key=api_key)

index = None

def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF中提取文本，如果是扫描件则自动OCR"""
    try:
        # 先尝试直接提取文字
        from pypdf import PdfReader
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

    # 如果直接提取失败，则使用OCR
    print("检测到扫描件PDF，正在OCR识别...")
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    full_text = ""
    for i, image in enumerate(images):
        # 使用中英文混合识别
        page_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        full_text += page_text + "\n"
    return full_text

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global index
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    # 提取文本
    text = extract_text_from_pdf(tmp_path)
    if not text.strip():
        return {"error": "无法从PDF中提取任何文本，请确保文件不是空扫描件"}

    # 创建Document并索引
    doc = Document(text=text)
    index = VectorStoreIndex.from_documents([doc])
    return {"message": f"上传成功，提取了 {len(text)} 字符"}

@app.post("/ask")
async def ask(question: str):
    if index is None:
        return {"answer": "请先上传文件"}
    query_engine = index.as_query_engine()
    response = query_engine.query(question)
    return {"answer": str(response)}

@app.post("/summary")
async def summary():
    if index is None:
        return {"summary": "请先上传文件"}
    query_engine = index.as_query_engine()
    response = query_engine.query("请用中文总结这份文档的核心内容，分三点。")
    return {"summary": str(response)}

@app.post("/learning-path")
async def learning_path():
    if index is None:
        return {"learning_path": "请先上传文件"}
    query_engine = index.as_query_engine()
    response = query_engine.query(
        "请根据这份文档的内容，为一名初学者生成一个循序渐进的学习路径，"
        "分为3到5个步骤，每个步骤包含学习目标和核心知识点。"
    )
    return {"learning_path": str(response)}

# 新增导入
from agent_modules import generate_full_report
import json

# 存储最后一次生成的报告（用于问答）
last_report = None
last_text = None

@app.post("/analyze")
async def analyze_book(file: UploadFile = File(...)):
    global last_report, last_text
    # 1. 保存临时PDF并提取文本（复用已有函数）
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    text = extract_text_from_pdf(tmp_path)
    if not text.strip():
        return {"error": "无法提取文本"}
    # 2. 生成报告
    report = generate_full_report(text, user_context="你的行业（可自行修改）")
    last_report = report
    last_text = text
    return {"report": report}

@app.post("/ask_agent")
async def ask_agent(question: str):
    if last_report is None or last_text is None:
        return {"answer": "请先上传书籍并分析（调用 /analyze）"}
    # 构造一个综合提示，包含报告的关键内容和原文片段
    # 简单实现：让LLM基于报告+原文片段回答，并鼓励批判性
    prompt = f"""你是一个擅长苏格拉底式质疑的AI。用户对一本书提出了问题。以下是这本书的分析报告和原文片段。请结合这些信息回答用户。如果用户提出质疑，请引用报告中的“极致批判”模块内容进行反驳或深化。

用户问题：{question}

===== 分析报告摘要 =====
洞察本质：{json.dumps(last_report.get('insight', {}), ensure_ascii=False)}
极致批判：{json.dumps(last_report.get('critique', {}), ensure_ascii=False)}
极致实践：{json.dumps(last_report.get('practice', {}), ensure_ascii=False)}

===== 原文片段（前2000字符）=====
{last_text[:2000]}

请回答（要求：直接回应问题，可引用报告中的分析，语气可略带质疑但保持建设性）：
"""
    answer = call_llm(prompt, max_tokens=1000)  # 注意：call_llm定义在agent_modules中，需要导入
    return {"answer": answer}