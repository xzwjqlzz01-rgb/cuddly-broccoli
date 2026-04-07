import os
import json
from llama_index.llms.zhipuai import ZhipuAI

# 初始化智谱 LLM
api_key = os.getenv("ZHIPUAI_API_KEY")
llm = ZhipuAI(model="glm-4-flash", api_key=api_key)

def module0_preprocess(text: str) -> dict:
    prompt = f"""你是一个书籍分析预处理专家。请对以下文本执行：
1. 提取目录结构（如果有）。如果没有明显目录，输出 null。
2. 按章节或自然段落分割，输出章节列表及对应起止位置（可用行号或字符位置）。
3. 生成全文的关键词（不超过20个）。
4. 识别作者的核心主张句（直接摘录原文，不超过10句）。
输出格式为JSON，例如：
{{
  "catalog": ["第1章 引言 (行1-50)", ...],
  "chapters": [{{"title": "第一章", "start": 0, "end": 1000}}, ...],
  "keywords": ["关键词1", ...],
  "core_sentences": ["句子1", ...]
}}

文本内容：
{text[:8000]}  # 限制长度避免超限
"""
    response = llm.complete(prompt)
    # 尝试解析 JSON，如果失败则返回原始文本
    try:
        return json.loads(response.text)
    except:
        return {"error": response.text}

def module1_insight(text: str) -> dict:
    prompt = f"""你正在对书籍执行“洞察本质”分析。请基于以下内容，严格按以下三个问题输出答案。每个答案控制在200字以内，禁止添加无关评论。输出JSON格式：{{"meta_question": "一句话定义元问题", "meta_question_explanation": "解释其基础性", "concept_reduction": [{{"concept": "概念名", "reduction": "还原解释"}}], "core_conclusions": ["结论1", "结论2", "结论3"]}}

文本内容：
{text[:8000]}
"""
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except:
        return {"error": response.text}

# 类似地，你可以继续实现 module2_critique, module3_practice, module4_internalize
# 为快速看到效果，我们先只实现模块0和1，后续再补充。

def module2_critique(text: str) -> dict:
    prompt = f"""你正在对书籍执行“极致批判”分析。请回答：1. 作者依赖的假设（最多3个）；2. 逻辑谬误或最强环节；3. 幸存者偏差及忽略的失败案例。输出JSON格式：{{"assumptions": [{{"assumption": "...", "condition": "..."}}], "logic_check": "...", "evidence_bias": "..."}}

文本：
{text[:8000]}
"""
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except:
        return {"error": response.text}

def module3_practice(text: str, user_context="普通职场或创业环境") -> dict:
    prompt = f"""你正在对书籍执行“极致实践”分析。用户情境：{user_context}。回答：1. 情境迁移（哪个策略仍有效，哪个失效）；2. 24小时最小实验（实验名称、步骤、成功指标）；3. 极端压力执行指令。输出JSON。

文本：
{text[:8000]}
"""
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except:
        return {"error": response.text}

def module4_internalize(text: str) -> dict:
    prompt = f"""你正在对书籍执行“极致内化”分析。回答：1. 21天复习计划（每天具体动作）；2. 与二八定律、奥卡姆剃刀、复利效应的类比；3. 费曼给孩子听（200字以内）。输出JSON。

文本：
{text[:8000]}
"""
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except:
        return {"error": response.text}