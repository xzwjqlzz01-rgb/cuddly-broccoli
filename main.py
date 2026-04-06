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