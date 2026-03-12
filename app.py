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
    API_KEY = "344a2765-dbc5-4ee8-b194-ff0dc075129b"

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
if "age" not in st.session_state: st.session_state.age = 0
if "attributes" not in st.session_state: st.session_state.attributes = {}
if "game_over" not in st.session_state: st.session_state.game_over = False


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
# --- 只有在需要玩家做选择时，才显示输入框 ---
if st.session_state.stage == "AWAIT_CHOICE":
    user_input = st.chat_input(f"【{st.session_state.age}岁】命运的岔路口，你决定怎么做？...")
else:
    user_input = None

# --- 状态机 ---
# 1. 投胎大厅 (初始化属性)
if st.session_state.stage == "INIT":
    st.markdown("<h3 style='text-align: center; color: #FFD700; margin-top: 20px;'>🌌 灵魂转生枢纽</h3>", unsafe_allow_html=True)
    st.info("👋 欢迎来到潜意识模拟器。你的一生将由背景、天赋、运气和努力共同交织而成。")
    
    # 将输入框改为“投胎”按钮
    if st.button("🎲 抽取命格，开始新的人生", use_container_width=True):
        with st.spinner("命运齿轮开始转动..."):
            time.sleep(1)
            
            # 随机生成初始属性 (1-10分满分制)
            st.session_state.attributes = {
                "家境": random.randint(2, 9),  # 避免极端的 1 或 10
                "天赋": random.randint(2, 9),
                "运气": random.randint(1, 10),
                "努力": random.randint(4, 8),  # 初始努力值比较平均
                "SAN值": 100                   # 心理韧性，满血100，归零则游戏结束
            }
            st.session_state.age = 6 # 从6岁童年期开始
            
            # 生成投胎报告并写入聊天流
            report = f"""
            （系统档案建立完毕）
            **MBTI 人格**: {st.session_state.user_mbti}
            **初始年龄**: {st.session_state.age} 岁
            
            📊 **初始属性面板**：
            🏠 家境：{st.session_state.attributes['家境']} / 10
            ✨ 天赋：{st.session_state.attributes['天赋']} / 10
            🍀 运气：{st.session_state.attributes['运气']} / 10
            💪 努力：{st.session_state.attributes['努力']} / 10
            ❤️ SAN值：{st.session_state.attributes['SAN值']} / 100
            
            命运的帷幕已拉开，请准备迎接你的第一个人生事件。
            """
            
            st.session_state.history.append({"role": "detective", "content": report})
            
            # 状态扭转：跳过侧写师追问，直接进入“生成随机事件”的全新阶段
            st.session_state.stage = "GENERATE_EVENT"
            st.rerun()

# ==========================================
# 游戏引擎循环
# ==========================================
# 2. 🎲 生成年龄事件
elif st.session_state.stage == "GENERATE_EVENT":
    with st.spinner(f"正在生成 {st.session_state.age} 岁的命运轨迹..."):
        # 让 AI 结合当前属性，生成一个匹配年龄的随机事件
        event_prompt = f"""
        你是一个人生模拟器。玩家当前 {st.session_state.age} 岁。
        MBTI：{st.session_state.user_mbti}
        当前属性：家境{st.session_state.attributes['家境']}, 天赋{st.session_state.attributes['天赋']}, 运气{st.session_state.attributes['运气']}, 努力{st.session_state.attributes['努力']}, SAN值{st.session_state.attributes['SAN值']}
        
        请结合上述属性，生成一个符合该年龄段的【突发心理或现实冲突事件】。
        字数150字左右，以“你...”开头，结尾必须问一句：“你要怎么做？”。
        不要给出选项，让玩家自己发挥。
        """
        event_text = call_llm(event_prompt, [])
        
        # 将事件展示在屏幕上
        st.session_state.history.append({"role": "detective", "content": f"**【{st.session_state.age}岁】**\n{event_text}"})
        st.session_state.current_event = event_text
        st.session_state.stage = "AWAIT_CHOICE"
        st.rerun()

# 3. ⏳ 等待玩家输入 (由修改位置 1 的 st.chat_input 触发)
elif st.session_state.stage == "AWAIT_CHOICE":
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.user_choice = user_input
        st.session_state.stage = "FERRYMAN_JUDGE"
        st.rerun()

# 4. ⚖️ 隐藏议会与命运结算
elif st.session_state.stage == "FERRYMAN_JUDGE":
    with st.spinner("命运正在进行结算..."):
        
        # A. 暗中获取四大派系的看法（不显示给玩家看）
        factions_views = ""
        for key, faction in FACTIONS.items():
            p = f"事件：{st.session_state.current_event}。请给出简短建议。"
            res = call_llm(faction['prompt'], [{"role":"user", "content": p}])
            factions_views += f"[{faction['name']}]: {res}\n"
        
        # B. 摆渡人综合判定
        judge_prompt = f"""
        你是命运摆渡人。
        【当前事件】：{st.session_state.current_event}
        【四派暗中倾向】：
        {factions_views}
        
        【玩家的选择】："{st.session_state.user_choice}"
        
        请评判玩家的选择最偏向哪一派，并给出命运结算。
        ⚠️ 必须严格按照以下格式输出（变动范围是 -15 到 +15）：
        【判定倾向】：（填写：理性派/情绪派/保守派/冒险派）
        【家境变动】：（填写数字，带正负号，如 +2 或 -1 或 0）
        【天赋变动】：（填写数字）
        【运气变动】：（填写数字）
        【努力变动】：（填写数字）
        【SAN值变动】：（填写数字）
        【命运点评】：（100字左右叙述，描述这个选择带来的现实后果和心理影响）
        """
        
        verdict = call_llm(judge_prompt, [])
        
        # C. 使用正则表达式，精准剥离出属性变动数值
        try:
            faction_match = re.search(r'【判定倾向】：(.*)', verdict).group(1).strip()
            bg_delta = int(re.search(r'【家境变动】：([+-]?\d+)', verdict).group(1))
            talent_delta = int(re.search(r'【天赋变动】：([+-]?\d+)', verdict).group(1))
            luck_delta = int(re.search(r'【运气变动】：([+-]?\d+)', verdict).group(1))
            effort_delta = int(re.search(r'【努力变动】：([+-]?\d+)', verdict).group(1))
            san_delta = int(re.search(r'【SAN值变动】：([+-]?\d+)', verdict).group(1))
            comment = re.search(r'【命运点评】：(.*)', verdict, re.DOTALL).group(1).strip()
        except Exception as e:
            # 防呆机制：如果 AI 没按格式输出，给个兜底
            faction_match = "混沌派 (未按常理出牌)"
            bg_delta, talent_delta, luck_delta, effort_delta, san_delta = 0, 0, 0, 0, -5
            comment = f"命运的迷雾遮蔽了结算...这或许是一个代价高昂的失误。\n(系统日志: {verdict})"

        # D. 更新玩家属性
        st.session_state.attributes["家境"] += bg_delta
        st.session_state.attributes["天赋"] += talent_delta
        st.session_state.attributes["运气"] += luck_delta
        st.session_state.attributes["努力"] += effort_delta
        st.session_state.attributes["SAN值"] += san_delta
        
        # E. 展示给玩家看
        result_display = f"""
        **⚖️ 命运判定**：你的行为充满了【{faction_match}】的色彩。
        
        **📊 属性变动**：
        🏠 家境 {bg_delta:+} | ✨ 天赋 {talent_delta:+} | 🍀 运气 {luck_delta:+} | 💪 努力 {effort_delta:+} | ❤️ SAN值 {san_delta:+}
        *(当前SAN值：{st.session_state.attributes['SAN值']}/100)*
        
        **📖 结局印记**：
        {comment}
        """
        st.session_state.history.append({"role": "ferryman", "content": result_display.strip()})
        
        # F. 年龄增长 & 判断生死
        st.session_state.age += random.randint(3, 7) # 每次过完一个事件，随机长 3~7 岁
        
        if st.session_state.attributes["SAN值"] <= 0:
            st.session_state.stage = "GAME_OVER"
            st.session_state.death_reason = "SAN值归零，精神崩溃，灵魂坠入深渊..."
        elif st.session_state.age >= 80:
            st.session_state.stage = "GAME_OVER"
            st.session_state.death_reason = "寿终正寝，走完了漫长的一生。"
        else:
            st.session_state.stage = "GENERATE_EVENT" # 继续下一次循环
        
        st.rerun()

# 5. 🪦 游戏结束
elif st.session_state.stage == "GAME_OVER":
    if "over_reported" not in st.session_state:
        final_report = f"""
        <div style="text-align:center; font-size:1.5em; margin-bottom:15px; color:#FF6B6B;">
            🪦 THE END
        </div>
        
        **终年**：{st.session_state.age} 岁
        **结局原因**：{st.session_state.death_reason}
        
        **最终人生结算**：
        🏠 家境：{st.session_state.attributes['家境']}
        ✨ 天赋：{st.session_state.attributes['天赋']}
        🍀 运气：{st.session_state.attributes['运气']}
        💪 努力：{st.session_state.attributes['努力']}
        ❤️ SAN值：{st.session_state.attributes['SAN值']}
        
        *点击右上角「重启议会」，开启下一段轮回。*
        """
        st.session_state.history.append({"role": "detective", "content": final_report})
        st.session_state.over_reported = True
        st.rerun()
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.spinner("🌊 摆渡人正在思考..."):
            ctx = f"前文裁决：{st.session_state.history[-1]['content']}\n新追问：{user_input}"
            res = call_llm(f"摆渡人简短回答用户追问：{ctx}", [])
            st.session_state.history.append({"role": "ferryman", "content": res})
            st.rerun()
