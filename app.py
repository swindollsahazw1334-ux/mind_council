import streamlit as st
import time
import re
import random
from openai import OpenAI
import sys
# 强制设置标准输出为 UTF-8，解决云端中文报错问题
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 1. 后端配置 (云端安全版)
# ==========================================
# 尝试从 Streamlit 的云端密钥库读取，如果没有（本地运行），则使用空字符串或手动输入
try:
    API_KEY = st.secrets["VOLC_API_KEY"]
except:
    API_KEY = ""

MODEL_ENDPOINT_ID = "ep-m-20260204004144-cnhgb" 
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

client = None
if API_KEY and "YOUR_" not in API_KEY:
    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    except: pass

def call_llm(system_prompt, messages_history, temperature=0.7):
    if not client: 
        time.sleep(1)
        return "⚠️ (模拟回复) 请检查 API Key 连接。"
    try:
        full_messages = [{"role": "system", "content": system_prompt}] + messages_history
        # 摆渡人阶段温度调高，更有灵性
        if temperature > 0.8: 
             full_messages.append({"role": "system", "content": "请务必使用温暖、像人一样的语气。"})
             
        response = client.chat.completions.create(
            model=MODEL_ENDPOINT_ID,
            messages=full_messages,
            temperature=temperature, 
        )
        content = response.choices[0].message.content
        if "</think>" in content: content = content.split("</think>")[-1]
        return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    except Exception as e: return f"Error: {e}"

# --- 四大派系人设 ---
FACTIONS = {
    "rational": {
        "name": "🧠 理性派",
        "prompt": "你是博弈论专家。只看利益计算、沉没成本。字数60字内。"
    },
    "emotional": {
        "name": "❤️ 情绪派",
        "prompt": "你是心理咨询师。关注情绪感受、委屈。字数60字内。"
    },
    "conservative": {
        "name": "🛡️ 保守派",
        "prompt": "你是风控专家。关注安全、止损、维持现状。字数60字内。"
    },
    "adventure": {
        "name": "🔥 冒险派",
        "prompt": "你是尼采式哲学家。主张破坏、重建、冲突。字数60字内。"
    }
}

# ==========================================
# 2. 界面 CSS 配置
# ==========================================
st.set_page_config(page_title="Inner Council", page_icon="🧠", layout="centered")

st.markdown("""
<style>
    /* 1. 全局背景：深邃星空紫 */
    /* --- 动态星空背景 --- */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* --- 1. 深邃宇宙背景 --- */
    .stApp {
        /* 使用径向渐变模拟深空中心亮、四周暗的效果 */
        background: radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%);
        color: #E0C097;
        /* 极其重要：防止流星划出屏幕时出现滚动条 */
        overflow-x: hidden; 
        overflow-y: hidden;
    }
    header, footer {visibility: hidden;}

    /* 2. 聊天行容器 */
    .chat-row { 
        display: flex; 
        margin-bottom: 20px; 
        align-items: flex-start; 
        animation: fadeIn 0.5s ease-in;
    }
    
    /* 3. 头像框：改为金色边框 */
    .avatar { 
        width: 45px; height: 45px; 
        border-radius: 50%; 
        display: flex; align-items: center; justify-content: center; 
        font-size: 24px; margin-right: 15px; 
        border: 2px solid #5a3e7d;
        background: #0f0518;
        box-shadow: 0 0 10px rgba(90, 62, 125, 0.5);
    }

    /* 4. 气泡 -> 卡牌样式 */
    .bubble { 
        padding: 15px 20px; 
        border-radius: 4px; /* 卡牌直角 */
        max-width: 85%; 
        font-size: 15px; 
        line-height: 1.6; 
        position: relative;
        background: rgba(20, 10, 30, 0.8); /* 半透明黑紫 */
        border: 1px solid #5a3e7d;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        backdrop-filter: blur(5px);
    }
            
    /* --- 卡牌交互动效 --- */
    .chat-row {
        transition: all 0.3s ease;
    }
    
    /* 鼠标悬停时，整行微微上浮，卡牌变亮 */
    .chat-row:hover {
        transform: translateY(-3px); /* 上浮 3像素 */
    }
    
    .chat-row:hover .bubble {
        box-shadow: 0 8px 25px rgba(135, 206, 235, 0.2); /* 增加发光 */
        border-color: rgba(255, 255, 255, 0.4); /* 边框变亮 */
    }
            
    /* 角色名标题样式 */
    .role-title {
        font-family: 'Georgia', serif;
        font-weight: bold;
        font-size: 0.9em;
        margin-bottom: 8px;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 5px;
    }

    /* --- 角色配色 (霓虹光晕) --- */
    
    /* 用户：愚者 (The Fool) - 白色 */
    .user-bub { border-color: #E0E0E0; }
    .user-title { color: #E0E0E0; }

    /* 侦探：隐士 (The Hermit) - 灰色 */
    .detective-bub { border-left: 3px solid #9E9E9E; }
    .detective-title { color: #9E9E9E; }

    /* 理性派：宝剑国王 - 冰蓝 */
    .rational-bub { border-color: #87CEEB; box-shadow: 0 0 10px rgba(135, 206, 235, 0.1); }
    .rational-title { color: #87CEEB; text-shadow: 0 0 5px rgba(135, 206, 235, 0.5); }

    /* 情绪派：圣杯皇后 - 绯红 */
    .emotional-bub { border-color: #FF6B6B; box-shadow: 0 0 10px rgba(255, 107, 107, 0.1); }
    .emotional-title { color: #FF6B6B; text-shadow: 0 0 5px rgba(255, 107, 107, 0.5); }

    /* 保守派：钱币骑士 - 土黄 */
    .conservative-bub { border-color: #DAA520; box-shadow: 0 0 10px rgba(218, 165, 32, 0.1); }
    .conservative-title { color: #DAA520; text-shadow: 0 0 5px rgba(218, 165, 32, 0.5); }

    /* 冒险派：权杖骑士 - 青绿 */
    .adventure-bub { border-color: #00FA9A; box-shadow: 0 0 10px rgba(0, 250, 154, 0.1); }
    .adventure-title { color: #00FA9A; text-shadow: 0 0 5px rgba(0, 250, 154, 0.5); }

    /* 摆渡人：命运之轮 - 金色信笺 */
    .ferryman-card { 
        background: #0f0518; 
        border: 1px solid #FFD700; 
        padding: 30px; 
        margin-top: 30px; 
        position: relative;
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.15);
    }
    .ferryman-card::before {
        content: "✦"; position: absolute; top: -15px; left: 50%; transform: translateX(-50%); 
        background: #0f0518; padding: 0 10px; color: #FFD700; font-size: 20px;
    }
    .ferryman-text { 
        color: #E0C097; 
        font-family: 'Courier New', serif; 
        line-height: 1.8; 
    }
    
    /* 动画 */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    /* 1. 彻底隐藏 Streamlit 默认侧边栏和汉堡菜单 */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    
    /* 2. 顶部控制栏容器样式 */
    .top-bar {
        background: rgba(15, 5, 24, 0.6); /* 半透明黑紫 */
        border: 1px solid #5a3e7d;
        border-radius: 12px;
        padding: 15px 25px;
        margin-bottom: 30px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* 3. 调整标题样式，使其更紧凑 */
    h1 {
        padding-top: 0rem !important;
        margin-bottom: 0rem !important;
        font-size: 2.2rem !important;
        text-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
    }
    
    /* 4. 输入框和按钮的微调 */
    .stTextInput { margin-bottom: 0 !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }
            
    div[data-testid="stHorizontalBlock"] button {
        font-size: 12px !important;       /* 1. 调小字号 */
        padding: 0px 10px !important;     /* 2. 压扁按钮高度 */
        white-space: nowrap !important;   /* 3. 强制不换行 (核心) */
        min-height: 35px !important;      /* 4. 减小最小高度 */
        line-height: 1.2 !important;
    }
            
    /* --- 2. 精致流星动效定义 (修正版) --- */
    
    /* 流星容器：设定飞行轨迹的基准角度 */
    /* rotate(-45deg) 让它整体呈现“左上-右下”的倾斜，配合动画移动 */
    .meteor {
        position: fixed;
        z-index: 1; 
        pointer-events: none;
        opacity: 0;
        /* 初始状态：头朝左下，尾朝右上 */
        transform: rotate(-45deg); 
    }

    /* === 流星头部 (Head) === */
    .meteor::before {
        content: '';
        position: absolute;
        top: 50%; left: 0; /* 头部在左侧 (运动的前端) */
        transform: translateY(-50%);
        width: 4px; height: 4px;
        border-radius: 50%;
        background: #fff;
        box-shadow: 
            0 0 5px 2px rgba(255, 255, 255, 0.9),
            0 0 12px 4px rgba(135, 206, 235, 0.8),
            0 0 25px 8px rgba(0, 247, 255, 0.5);
        z-index: 2; /* 确保头部压在尾巴上面 */
    }

    /* === 流星拖尾 (Tail) === */
    .meteor::after {
        content: '';
        position: absolute;
        top: 50%; left: 2px; /* 尾巴接在头部右侧 (后面) */
        transform: translateY(-50%);
        height: 2px;
        
        /* 渐变修正：从左(接触头部)到右(末端) -> 从实色到透明 */
        background: linear-gradient(to right, 
            rgba(255, 255, 255, 1) 0%, 
            rgba(135, 206, 235, 0.6) 30%, 
            rgba(255,255,255,0) 100%
        );
        border-radius: 2px; 
        box-shadow: 0 0 15px rgba(135, 206, 235, 0.3);
    }

    /* 动画关键帧：从右上 飞向 左下 */
    @keyframes shower {
        0% {
            /* 初始：在屏幕右侧外 (300px)，且稍微压扁 */
            transform: rotate(-45deg) translateX(300px) scaleX(0.8);
            opacity: 0;
        }
        10% {
            opacity: 1; /* 出现 */
        }
        70% {
            opacity: 1; /* 保持 */
        }
        100% {
            /* 终点：飞到屏幕左侧外 (-800px)，拉长 */
            transform: rotate(-45deg) translateX(-800px) scaleX(1.5);
            opacity: 0;
        }
    }

    /* --- 3. 个性化配置 (4颗不同的流星) --- */
    /* 通过调整位置、尾巴长度、动画时长和延迟，制造随机感 */

    .meteor-1 { left: 85%; top: 10%; animation: shower 6s infinite ease-in-out 0s; }
    .meteor-1::after { width: 160px; } /* 这一颗尾巴比较长 */

    .meteor-2 { left: 65%; top: 30%; animation: shower 8s infinite ease-in-out 2.5s; }
    .meteor-2::after { width: 100px; height: 1.5px; } /* 这一颗比较细短 */

    .meteor-3 { left: 90%; top: 5%; animation: shower 7s infinite ease-in-out 1.2s; }
    .meteor-3::after { width: 220px; height: 3px; } /* 这一颗是巨大的火流星 */
    .meteor-3::before { width: 6px; height: 6px; } /* 头部也更大 */
    
    .meteor-4 { left: 50%; top: 20%; animation: shower 9s infinite ease-in-out 4.5s; }
    .meteor-4::after { width: 130px; }
                        
    /* 确保聊天内容始终压在流星上面 */
    .block-container {
        position: relative;
        z-index: 10;
    }
    /* --- 3. 呼吸感星星 (Twinkling Stars) --- */
    
    .star {
        position: fixed;
        background-color: white;
        border-radius: 50%;
        z-index: 0; /* 放在流星(1)下面，背景之上 */
        pointer-events: none;
        opacity: 0;
    }

    /* 星星闪烁动画：透明度变化 + 微微缩放 + 阴影呼吸 */
    @keyframes twinkle {
        0% { 
            opacity: 0.2; 
            transform: scale(0.8); 
            box-shadow: 0 0 0 transparent;
        }
        50% { 
            opacity: 0.9; 
            transform: scale(1.2); 
            box-shadow: 0 0 4px rgba(255, 255, 255, 0.8); /* 发光晕 */
        }
        100% { 
            opacity: 0.2; 
            transform: scale(0.8); 
            box-shadow: 0 0 0 transparent;
        }
    }
</style>
""", unsafe_allow_html=True)

# 注入流星的 HTML 实体元素
st.markdown("""
    <div class="meteor meteor-1"></div>
    <div class="meteor meteor-2"></div>
    <div class="meteor meteor-3"></div>
    <div class="meteor meteor-4"></div>
""", unsafe_allow_html=True)

# --- 注入动态背景元素 (流星 + 繁星) ---

# 定义一个生成随机星星的辅助函数
def generate_stars(n=50):
    stars_html = ""
    for _ in range(n):
        left = random.randint(0, 100)
        top = random.randint(0, 100)
        size = random.randint(1, 3)
        duration = random.uniform(2, 6)
        delay = random.uniform(0, 5)
        
        # ⚠️ 关键修改：去掉所有换行和缩进，写成一行！
        # 否则 Streamlit 会把它当成代码块显示在屏幕上
        stars_html += f'<div class="star" style="left: {left}%; top: {top}%; width: {size}px; height: {size}px; animation: twinkle {duration}s infinite ease-in-out {delay}s;"></div>'
        
    return stars_html

# 一次性注入所有背景元素
st.markdown(f"""
    <div class="meteor meteor-1"></div>
    <div class="meteor meteor-2"></div>
    <div class="meteor meteor-3"></div>
    <div class="meteor meteor-4"></div>
    
    {generate_stars(50)}
""", unsafe_allow_html=True)

# ==========================================
# 3. 状态与逻辑
# ==========================================
if "stage" not in st.session_state: st.session_state.stage = "INIT"
if "history" not in st.session_state: st.session_state.history = []
if "investigate_round" not in st.session_state: st.session_state.investigate_round = 0
if "investigate_history" not in st.session_state: st.session_state.investigate_history = []
if "case_summary" not in st.session_state: st.session_state.case_summary = ""
if "faction_opinions" not in st.session_state: st.session_state.faction_opinions = {}
if "user_mbti" not in st.session_state: st.session_state.user_mbti = "INFP"

def render_chat():
    for msg in st.session_state.history:
        role = msg["role"]
        text = msg["content"]
        
        # 角色配置映射：(CSS类后缀, 图标, 塔罗称号)
        role_map = {
            "user": ("user", "👤", "THE FOOL (提问者)"),
            "detective": ("detective", "🕯️", "THE HERMIT (隐士·侧写师)"),
            "rational": ("rational", "⚔️", "KING of SWORDS (宝剑国王·理性)"),
            "emotional": ("emotional", "🍷", "QUEEN of CUPS (圣杯皇后·情绪)"),
            "conservative": ("conservative", "🪙", "KNIGHT of PENTACLES (钱币骑士·保守)"),
            "adventure": ("adventure", "🔥", "KNIGHT of WANDS (权杖骑士·冒险)"),
        }
        
        # 处理换行
        safe_text = text.replace("\n", "<br>")

        if role == "ferryman":
            # 摆渡人特殊卡片
            st.markdown(f"""
            <div class="ferryman-card">
                <div style="text-align:center; color:#FFD700; margin-bottom:20px; letter-spacing:2px; font-size:0.8em;">
                    WHEEL OF FORTUNE (命运之轮·摆渡人)
                </div>
                <div class="ferryman-text">{safe_text}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 普通角色卡片
            css_suffix, icon, title = role_map.get(role, ("user", "👤", "USER"))
            
            st.markdown(f"""
            <div class="chat-row">
                <div class="avatar">{icon}</div>
                <div class="bubble {css_suffix}-bub">
                    <div class="role-title {css_suffix}-title">{title}</div>
                    <div>{safe_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
# ==========================================
# 4. 主程序 (顶部导航栏版)
# ==========================================

# --- 顶部 HUD (Heads-Up Display) ---
with st.container():
    c1, c2, c3 = st.columns([3, 1.5, 1], gap="medium", vertical_alignment="bottom")
    
    with c1:
        st.title("🧠 Inner Council")
        
    with c2:
        # ✅ 修改点：直接绑定 key="user_mbti"，Streamlit 会自动同步 session_state
        st.text_input("MBTI", key="user_mbti", label_visibility="collapsed")
    
    with c3:
        if st.button("🔄 重启议会", use_container_width=True):
            st.session_state.clear()
            st.rerun()

st.markdown("---") # 加一条分割线，区分控制区和聊天区
render_chat()
user_input = st.chat_input("输入信息...")

# --- 状态机 ---

# 1. 初始化
if st.session_state.stage == "INIT":
    if not st.session_state.history: st.info("👋 请输入你的烦恼，召唤四方议会。")
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.investigate_history = [{"role": "system", "content": f"用户烦恼：{user_input}。性格：{st.session_state.user_mbti}"}]
        with st.spinner("🕵️ 侧写师正在分析..."):
            q1 = call_llm("这是第一轮。请提出一个最关键的追问。", st.session_state.investigate_history)
            st.session_state.history.append({"role": "detective", "content": q1})
            st.session_state.investigate_history.append({"role": "assistant", "content": q1})
            st.session_state.investigate_round = 1
            st.session_state.stage = "INVESTIGATE"
            st.rerun()

# 2. 侦探追问
elif st.session_state.stage == "INVESTIGATE":
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.investigate_history.append({"role": "user", "content": user_input})
        
        MIN_ROUNDS = 3
        curr = st.session_state.investigate_round
        
        with st.spinner("🕵️ 侧写师正在思考..."):
            if curr < MIN_ROUNDS:
                prompt = f"第{curr}/3轮。禁止结束。请检查缺失维度，继续追问。"
            else:
                prompt = "信息够了吗？够了输出【ENOUGH】，不够输出追问。"
            
            resp = call_llm(prompt, st.session_state.investigate_history)
            
            if "ENOUGH" in resp and curr >= MIN_ROUNDS:
                st.session_state.history.append({"role": "detective", "content": "（信息收集完毕，正在移交议会...）"})
                summary = call_llm("用第三人称总结完整案情。", st.session_state.investigate_history)
                st.session_state.case_summary = summary
                st.session_state.stage = "ROUND_TABLE"
                st.rerun()
            else:
                q = resp.replace("【ENOUGH】", "").strip()
                st.session_state.history.append({"role": "detective", "content": q})
                st.session_state.investigate_history.append({"role": "assistant", "content": q})
                st.session_state.investigate_round += 1
                st.rerun()

# 3. 圆桌发表 (四方观点)
elif st.session_state.stage == "ROUND_TABLE":
    order = ["rational", "emotional", "conservative", "adventure"]
    next_speaker = None
    for faction in order:
        if faction not in st.session_state.faction_opinions:
            next_speaker = faction
            break
            
    if next_speaker:
        faction_data = FACTIONS[next_speaker]
        with st.spinner(f"{faction_data['name']} 正在发言..."):
            time.sleep(0.3) # 稍微快一点
            prompt = f"案情：{st.session_state.case_summary}。性格：{st.session_state.user_mbti}。请给出你的核心主张。"
            res = call_llm(faction_data['prompt'], [{"role":"user", "content": prompt}])
            
            st.session_state.history.append({"role": next_speaker, "content": res})
            st.session_state.faction_opinions[next_speaker] = res
            st.rerun()
    else:
        # ❌ 这里跳过了 CROSSFIRE，直接去裁决
        st.session_state.stage = "VERDICT"
        st.rerun()

# 4. 摆渡人裁决 (核心升级点)
elif st.session_state.stage == "VERDICT":
    with st.spinner("🌊 摆渡人正在进行最终裁决..."):
        time.sleep(1.5)
        
        # 构造一个极强的 Prompt，强制 AI 进行内部辩证
        full_debate = "\n".join([f"{k}: {v}" for k,v in st.session_state.faction_opinions.items()])
        
        prompt = f"""
        你是摆渡人。用户：{st.session_state.user_mbti}。
        
        【案情】：{st.session_state.case_summary}
        
        【四方观点】：
        {full_debate}
        
        💡 **你的核心任务**：
        请不要只是罗列他们的观点。你需要在内心完成一次**“辩证仲裁”**：
        1. "冒险派"太激进了，但他的**勇气**可取。
        2. "保守派"太怂了，但他的**风控**有理。
        3. "理性派"太冷血，"情绪派"太冲动。
        
        请为用户找到一个**完美的平衡点**（Golden Mean）。
        
        **输出格式**：
        ⚠️ **格式红线（绝对禁止，违反会死机）**：
        1. ❌ **禁止**使用任何列表符号（如 1. 2. 3. 或 - ）。
        2. ❌ **禁止**使用方括号标题（如【行动指南】、【话术】）。
        3. ❌ **禁止**像写说明书一样分点作答。
    
        ✅ **必须这样做（自然流露）**：
        1. **叙述性语言**：像给老朋友谈心一样，把“问题的本质”、“具体的行动”自然地融合在段落里。不要有明显的分割感。
        2. **MBTI定制**：你面对的是{st.session_state.user_mbti}，语气要照顾她的特质（比如对ENFP要保护她的热情，但提醒她不要泛滥）。
        3. **话术融入**：在文章的最后，自然地写出：“今晚，你可以试着给他发这么一条信息：‘......’”
    
        语气：温暖、从容、坚定。不要说教，要共情。
        请开始你的独白：
        """
        
        verdict = call_llm(prompt, [], temperature=0.9) # 温度调高，增加灵性
        st.session_state.history.append({"role": "ferryman", "content": verdict})
        st.session_state.stage = "CONSULT"
        st.rerun()

# 5. 会后追问
elif st.session_state.stage == "CONSULT":
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.spinner("🌊 摆渡人正在思考..."):
            ctx = f"前文裁决：{st.session_state.history[-1]['content']}\n新追问：{user_input}"
            res = call_llm(f"摆渡人简短回答用户追问：{ctx}", [])
            st.session_state.history.append({"role": "ferryman", "content": res})

            st.rerun()


