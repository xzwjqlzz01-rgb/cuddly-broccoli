# agent_modules.py
import os
import json
from zhipuai import ZhipuAI

# 初始化智谱客户端（使用环境变量中的API Key）
client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))

def call_llm(prompt: str, max_tokens=2000) -> str:
    """调用智谱AI，并自动去除markdown代码块标记"""
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3
    )
    raw = response.choices[0].message.content
    # 去除可能的 ```json ... ``` 或 ``` ... ``` 包裹
    import re
    # 匹配以```json 或 ``` 开头，以```结尾的内容，提取中间部分
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    # 如果原始内容没有代码块，直接使用
    print("\n=== LLM原始响应 ===\n", raw, "\n==================\n")
    return raw

def module0_preprocess(text: str) -> dict:
    """模块0：预处理，输出JSON格式的目录、关键词、核心主张句"""
    prompt = f"""你是一个书籍分析预处理专家。请对以下文本执行：
1. 提取目录结构（如果有）。如果无明显目录，按自然段落分割，输出章节列表及对应起止位置（用行号或字符位置）。
2. 生成全文的关键词（不超过20个）。
3. 识别作者的核心主张句（直接摘录原文，不超过10句）。

输出格式必须为严格的JSON，例如：
{{
    "chapters": [{{"title": "第一章", "start_line": 10, "end_line": 50}}],
    "keywords": ["关键词1", "关键词2"],
    "core_claims": ["原句1", "原句2"]
}}

如果无法提取目录，chapters可输出空列表。只输出JSON，不要有其他解释。

文本内容：
{text[:12000]}
"""
    resp = call_llm(prompt, max_tokens=1500)
    # 尝试解析JSON，如果失败则返回空结构
    try:
        return json.loads(resp)
    except:
        return {"chapters": [], "keywords": [], "core_claims": []}

def module1_insight(text: str) -> dict:
    """模块1：洞察本质"""
    prompt = f"""你正在对一本书执行“洞察本质”分析。请基于以下文本，严格按三个问题输出JSON。

问题1（问题根源）：这本书试图解决的最根本、最基础的“元问题”是什么？这个问题触发了哪个人性或社会运作的最基本需求？请用一句话定义元问题，再用一句话解释其基础性。
问题2（概念还原）：从书中挑选1-3个核心概念。不使用任何书中的术语或比喻，只使用最基本的物理学、经济学或逻辑学原理来解释它们。输出格式：概念名 → 还原解释。
问题3（结论审视）：假设删掉书中所有案例、故事、修辞，作者真正想让你相信的核心结论最多有3个。逐一列出，每个结论用一句不超过30字的陈述句。

输出JSON格式：
{{
    "meta_question": {{"definition": "...", "foundation": "..."}},
    "concept_reduction": [{{"concept": "概念名", "explanation": "..."}}],
    "core_conclusions": ["结论1", "结论2"]
}}

文本内容：
{text[:10000]}
"""
    resp = call_llm(prompt, max_tokens=1500)
    try:
        return json.loads(resp)
    except:
        return {"meta_question": {}, "concept_reduction": [], "core_conclusions": []}

def module2_critique(text: str) -> dict:
    """模块2：极致批判"""
    prompt = f"""你正在对一本书执行“极致批判”分析。请基于以下文本，回答三个问题，输出JSON。

问题1（假设识别）：作者在论证中依赖了哪些“不证自明”的假设？列出最多3个。每个假设说明成立条件或可能失效的场景。
问题2（逻辑检验）：作者的推理链条中，是否存在“归纳法谬误”或“因果倒置”？如果有，明确指出；如果没有，说明作者最强的一个逻辑环节。
问题3（证据检视）：作者使用的主要证据是否存在“幸存者偏差”？提出至少一个被忽略的“失败案例”类型，并说明如果纳入该案例结论可能如何变化。

输出JSON格式：
{{
    "assumptions": [{{"assumption": "...", "valid_condition": "...", "failure_scenario": "..."}}],
    "logic_check": {{"has_fallacy": true/false, "description": "..."}},
    "evidence_review": {{"survivorship_bias": true/false, "missing_case": "...", "impact": "..."}}
}}

文本内容：
{text[:10000]}
"""
    resp = call_llm(prompt, max_tokens=1500)
    try:
        return json.loads(resp)
    except:
        return {"assumptions": [], "logic_check": {}, "evidence_review": {}}

def module3_practice(text: str, user_context: str = "一个资源有限的初创团队") -> dict:
    """模块3：极致实践，可传入用户情境"""
    prompt = f"""你正在对一本书执行“极致实践”分析。用户情境：{user_context}。请基于以下文本回答三个问题，输出JSON。

问题1（情境迁移）：假设用户所处领域的基础假设被推翻了，书中哪个核心策略仍然有效？哪个会彻底失效？
问题2（最小验证）：基于书中一个可操作的原则，设计一个“24小时内可完成的最小可行性实验”。输出：实验名称、步骤（3-5步）、成功指标。
问题3（极端压力测试）：假设用户预算为0、团队只有1人、对手是行业巨头。书中哪个单一策略仍然可以执行？给出具体的执行指令。

输出JSON格式：
{{
    "strategy_migration": {{"still_valid": "...", "invalid": "..."}},
    "minimal_experiment": {{"name": "...", "steps": ["step1", "step2"], "success_metric": "..."}},
    "extreme_instruction": "..."
}}

文本内容：
{text[:10000]}
"""
    resp = call_llm(prompt, max_tokens=1500)
    try:
        return json.loads(resp)
    except:
        return {"strategy_migration": {}, "minimal_experiment": {}, "extreme_instruction": ""}

def module4_internalize(text: str) -> dict:
    """模块4：极致内化"""
    prompt = f"""你正在对一本书执行“极致内化”分析。请回答三个问题，输出JSON。

问题1（对抗遗忘）：设计一个基于“间隔重复”的21天复习计划。每天只需5分钟。输出格式：第1天、第2天……第7天、第14天、第21天的复习动作（具体到做什么）。
问题2（构建网络）：将本书的核心模型与以下通用思维模型类比：①二八定律 ②奥卡姆剃刀 ③复利效应。对每个类比，说明异同点和一个交叉应用场景。
问题3（教授他人）：用费曼技巧，将本书最核心的一个洞见解释给一个10岁孩子听。不超过200字，不得使用专业术语，必须包含生活中的类比。

输出JSON格式：
{{
    "review_plan": {{"day1": "...", "day2": "...", "day7": "...", "day14": "...", "day21": "..."}},
    "model_analogies": [{{"model": "二八定律", "similarities": "...", "differences": "...", "cross_scenario": "..."}}],
    "feynman_explanation": "..."
}}

文本内容：
{text[:10000]}
"""
    resp = call_llm(prompt, max_tokens=1500)
    try:
        return json.loads(resp)
    except:
        return {"review_plan": {}, "model_analogies": [], "feynman_explanation": ""}

def generate_full_report(text: str, user_context: str = "资源有限的初创团队") -> dict:
    """依次调用五个模块，生成完整报告"""
    print("模块0：预处理...")
    pre = module0_preprocess(text)
    print("模块1：洞察本质...")
    ins = module1_insight(text)
    print("模块2：极致批判...")
    cri = module2_critique(text)
    print("模块3：极致实践...")
    pra = module3_practice(text, user_context)
    print("模块4：极致内化...")
    inter = module4_internalize(text)

    report = {
        "preprocess": pre,
        "insight": ins,
        "critique": cri,
        "practice": pra,
        "internalize": inter
    }
    return report