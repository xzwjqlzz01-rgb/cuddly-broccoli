from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
from agent_modules import generate_full_report
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# 配置 Tesseract 和 poppler（根据你的实际路径）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
poppler_path = r'D:\poppler\bin'

def extract_text_from_pdf(pdf_path: str) -> str:
    """提取PDF文本，必要时OCR"""
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

# 存储最后一次分析的文本和报告（用于问答）
last_text = ""
last_report = None

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
async def ask_agent(question: str):
    if not last_text or not last_report:
        return {"answer": "请先上传书籍并分析（调用 /analyze）"}
    # 使用智谱AI直接回答问题，结合报告内容
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
    # 构造 prompt，包含报告摘要和原文片段
    prompt = f"""你是一个擅长苏格拉底式质疑的AI。用户对一本书提出了问题。以下是这本书的分析报告摘要和原文片段。请结合这些信息回答用户。如果用户提出质疑，请引用报告中的“极致批判”模块内容进行反驳或深化。

用户问题：{question}

===== 分析报告摘要 =====
{last_report.get('insight', '')[:2000]}
{last_report.get('critique', '')[:2000]}

===== 原文片段（前2000字符）=====
{last_text[:2000]}

请回答（要求：直接回应问题，可引用报告中的分析，语气可略带质疑但保持建设性）：
"""
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.5
    )
    return {"answer": response.choices[0].message.content}