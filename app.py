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
# --- 游戏互动区：彩票系统与输入框 ---
if st.session_state.stage == "AWAIT_CHOICE":
    
    # 🎰 彩票系统：成年后且没破产才能买
    if st.session_state.age >= 18 and st.session_state.attributes["金钱"] >= 20:
        if st.button("🎫 买彩票 (¥20) - 搏一搏，单车变摩托！", use_container_width=True):
            
            # 1. 扣除彩票钱
            st.session_state.attributes["金钱"] -= 20
            
            # 2. 独立抛掷彩票专用骰子
            lottery_dice = random.randint(1, 20)
            current_luck = st.session_state.attributes["运气"]
            
            # 3. 严格判定头奖 (运气满值 10 且 骰子满值 20)
            if current_luck == 10 and lottery_dice == 20:
                prize = 5000000 # 500万头奖
                st.session_state.attributes["金钱"] += prize
                st.session_state.attributes["健康"] = 100 # ✅ 暴富治百病，健康直接拉满
                st.session_state.assets.append("头奖彩票金牌")
                msg = f"""
                🎉 **【奇迹降临！】** 你花了 20 元买了一张彩票。
                **彩票骰子：{lottery_dice}** | **当前运气：{current_luck}**
                
                当开奖号码公布时，你揉了揉眼睛，不敢相信这是真的。
                你中了 **¥{prize}** 头奖！命运的齿轮疯狂转动，你一夜暴富，激动的你感觉身体前所未有的健康！
                """
            else:
                st.session_state.attributes["健康"] -= 1 # ✅ 没中奖，气得血压升高，健康 -1
                msg = f"""
                💸 **【谢谢参与】** 你花了 20 元买了一张彩票。
                **彩票骰子：{lottery_dice}** | **当前运气：{current_luck}**
                
                连个安慰奖都没有，20 块钱打了水漂。你感到一阵胸闷（健康-1）。你要继续买，还是面对现实去解决眼前的麻烦？
                """
            
            # 4. 把抽奖结果直接插入对话流中，并刷新页面
            st.session_state.history.append({"role": "detective", "content": msg.strip()})
            st.rerun()

    # 正常的命运选择输入框
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
            
            st.session_state.attributes = {
                "家境": random.randint(2, 9), 
                "天赋": random.randint(2, 9),
                "运气": random.randint(1, 10),
                "努力": random.randint(4, 8),
                "健康": 80,   # ✅ 改为健康，满分100，低健康会大幅增加暴毙概率
                "金钱": random.randint(1, 5) * 100 
            }
            st.session_state.assets = [] 
            st.session_state.age = 6
            
            # 生成投胎报告并写入聊天流
            assets_str = "无"
            
            # 生成投胎报告并写入聊天流
            report = f"""
            （系统档案建立完毕）
            **MBTI 人格**: {st.session_state.user_mbti}
            **初始年龄**: {st.session_state.age} 岁
            
            📊 **初始属性面板**：
            🏠 家境：{st.session_state.attributes['家境']} / 10 | ✨ 天赋：{st.session_state.attributes['天赋']} / 10
            🍀 运气：{st.session_state.attributes['运气']} / 10 | 💪 努力：{st.session_state.attributes['努力']} / 10
            ❤️ 健康：{st.session_state.attributes['健康']} / 100
            💰 金钱：¥{st.session_state.attributes['金钱']}
            🎒 资产：{assets_str}
            
            命运的帷幕已拉开，请准备迎接你的第一个人生事件。
            """
            
            st.session_state.history.append({"role": "detective", "content": report})
            
            # 状态扭转：跳过侧写师追问，直接进入“生成随机事件”的全新阶段
            st.session_state.stage = "GENERATE_EVENT"
            st.rerun()

# ==========================================
# 游戏引擎循环
# ==========================================
# 2. 🎲 死亡判定与生成年龄事件
elif st.session_state.stage == "GENERATE_EVENT":
    
    # 💀 1. 每次事件前，先进行“死神概率检定”
    current_age = st.session_state.age
    current_health = st.session_state.attributes["健康"]
    
    # 算法：基础年龄死亡率(指数增长) + 疾病/低健康惩罚
    # 例如：20岁致死率约0.3%，60岁致死率约30%，80岁接近100%
    base_death_rate = (current_age / 80.0) ** 4 * 100 
    
    # 健康惩罚：健康低于 60 后，每低1点增加 1% 的暴毙概率
    health_penalty = max(0, (60 - current_health) * 1.0) 
    
    # 综合致死概率
    if current_health <= 0 or current_age >= 85:
        total_death_prob = 100.0  # 健康清零或极度高寿，必死
    else:
        total_death_prob = max(0.1, min(99.9, base_death_rate + health_penalty))
        
    # 🎲 掷一个 0~100 的百面骰子，判断是否暴毙
    death_roll = random.uniform(0, 100)
    
    if death_roll < total_death_prob:
        # 判定死亡！直接跳转到游戏结束
        st.session_state.stage = "GAME_OVER"
        if current_age >= 80:
            st.session_state.death_reason = f"历经岁月的洗礼，你在 {current_age} 岁这年安详地闭上了双眼，寿终正寝。"
        elif current_health <= 0:
            st.session_state.death_reason = f"由于长期积劳成疾，你的身体彻底崩溃，终年 {current_age} 岁。"
        else:
            st.session_state.death_reason = f"天有不测风云。虽然你只有 {current_age} 岁，但一场突如其来的意外（当年意外致死率: {total_death_prob:.2f}%）无情地夺走了你的生命..."
        st.rerun()

    # 👻 2. 如果成功生还，继续生成本年度的事件
    with st.spinner(f"正在生成 {st.session_state.age} 岁的命运... (当前意外致死率: {total_death_prob:.2f}%)"):
        
        assets_display = ', '.join(st.session_state.assets) if st.session_state.assets else '无'
        
        event_prompt = f"""
        你是一个深度的心理学人生模拟器。玩家当前 {st.session_state.age} 岁。
        当前属性：家境 {st.session_state.attributes['家境']}, 天赋 {st.session_state.attributes['天赋']}, 运气 {st.session_state.attributes['运气']}, 努力 {st.session_state.attributes['努力']}, 健康 {st.session_state.attributes['健康']}
        当前存款：¥{st.session_state.attributes['金钱']}
        拥有资产：{assets_display}
        
        【核心生成法则】：
        1. 聚焦心理与健康困境：事件围绕【人际关系、工作内卷、身体抱恙、原生家庭、生存压力】展开。
        2. 如果健康较低（<50），必须生成与生病、意外、体力不支相关的负面事件！
        
        请生成一个符合该年龄段的【深度冲突事件】。
        ⚠️ 严格控制在 80 字以内！直接描述发生了什么，以“你要怎么做？”结尾。绝对不要给选项。
        """
        event_text = call_llm(event_prompt, [])
        
        # 在前端显示今年的致死率，拉满压迫感
        st.session_state.history.append({"role": "detective", "content": f"**【{st.session_state.age}岁】** *(当年死亡风险: {total_death_prob:.2f}%*)\n{event_text}"})
        st.session_state.current_event = event_text
        st.session_state.stage = "AWAIT_CHOICE"
        st.rerun()

# 3. ⏳ 等待玩家输入 (由修改位置 1 的 st.chat_input 触发)
elif st.session_state.stage == "AWAIT_CHOICE":
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.user_choice = user_input
        st.session_state.stage = "ROLL_DICE"
        st.rerun()

# 3.5 🎲 命运骰子判定 (D20 TRPG 系统)
elif st.session_state.stage == "ROLL_DICE":
    with st.spinner("🎲 命运骰子滚动中..."):
        time.sleep(1.5)
        
        # 基础 D20 骰子 (1-20)
        base_roll = random.randint(1, 20)
        
        # 运气修正值：运气5点是平均值(不加不减)，运气10加5，运气1减4
        luck_stat = st.session_state.attributes["运气"]
        luck_mod = luck_stat - 5 
        final_score = base_roll + luck_mod
        
        # 判定结果
        if final_score >= 15:
            roll_status = "大成功 (Critical Success)"
            roll_desc = "命运眷顾了你，无论处境多艰难，奇迹都会发生。"
        elif final_score >= 10:
            roll_status = "成功 (Success)"
            roll_desc = "你的行动基本达到了预期效果，一切顺利。"
        elif final_score >= 5:
            roll_status = "失败 (Failure)"
            roll_desc = "事情并没有按计划进行，遇到了现实的阻碍。"
        else:
            roll_status = "大失败 (Critical Fumble)"
            roll_desc = "不仅行动失败，还引发了极其糟糕的连锁反应！"
            
        # 生成前端展示的骰子卡片
        dice_msg = f"""
        **🎲 命运判定**：掷出 D20
        **基础点数**：{base_roll}
        **运气修正**：{luck_mod:+} (当前运气: {luck_stat})
        **最终判定值**：{final_score} ➔ **【{roll_status}】**
        
        *{roll_desc}*
        """
        
        # 将骰子结果存入 session，准备喂给摆渡人
        st.session_state.dice_summary = f"最终判定值: {final_score} ({roll_status})。{roll_desc}"
        st.session_state.history.append({"role": "detective", "content": dice_msg.strip()})
        
        # 骰子掷完，进入摆渡人结算
        st.session_state.stage = "FERRYMAN_JUDGE"
        st.rerun()

# 4. ⚖️ 隐藏议会与命运结算
# 4. ⚖️ 极速命运结算
elif st.session_state.stage == "FERRYMAN_JUDGE":
    with st.spinner("命运结算中..."):
        
        judge_prompt = f"""
        你是洞察人心的命运摆渡人和心理分析师。
        【当前事件】：{st.session_state.current_event}
        【玩家的选择】："{st.session_state.user_choice}"
        【命运骰子判定】："{st.session_state.dice_summary}"
        
        【四大派系定义】：
        - 理性派：只看利益计算、课题分离、沉没成本。
        - 情绪派：关注情绪感受、内心委屈、共情与心理防御。
        - 保守派：关注安全、止损、维持现状、回避冲突。
        - 冒险派：主张破坏、重建、直面恐惧、打破舒适区。
        
        请直接判断玩家的选择最符合哪一派，并结合【命运骰子判定】给出心理学视角的结算。
        
        【数值变动严格法则】（注意：天赋和运气是先天的，绝对固定不变！）：
        1. 【健康】：核心指标！选择直面创伤、获得和解，或骰子成功，健康增加；过度劳累、遭遇意外、严重内耗、骰子失败，健康大幅下降。
        2. 【努力】：完全受玩家认知影响。选择迎难而上、积极沟通、克制本能，努力值增加。选择逃避、推卸责任、习得性无助，努力值下降。
        3. 【家境】：受现实条件和骰子运气影响。发生意外、破财、大失败会使家境下降，抓住机遇、获得横财则上升。
        4. 【金钱】：平时有收入覆盖。只有当事件明确涉及花大钱/赚钱，才进行金钱加减。其余填 0。
        
        ⚠️ 必须严格按照以下格式输出（绝不要输出天赋和运气变动！）：
        【判定倾向】：（填：理性派/情绪派/保守派/冒险派）
        【家境变动】：（填带正负号的数字）
        【努力变动】：（填带正负号的数字）
        【健康变动】：（填带正负号的数字）
        【金钱变动】：（填带正负号的数字）
        【新增资产】：（填资产名称，无则填“无”）
        【命运点评】：（严格控制在60字以内！用一句心理分析的话，精炼概括该选择带来的内在影响与现实后果。）
        """
        verdict = call_llm(judge_prompt, [])
        
        # C. 精准剥离（去掉了天赋和运气）
        try:
            faction_match = re.search(r'【判定倾向】：(.*)', verdict).group(1).strip()
            bg_delta = int(re.search(r'【家境变动】：([+-]?\d+)', verdict).group(1))
            effort_delta = int(re.search(r'【努力变动】：([+-]?\d+)', verdict).group(1))
            health_delta = int(re.search(r'【健康变动】：([+-]?\d+)', verdict).group(1))
            money_delta = int(re.search(r'【金钱变动】：([+-]?\d+)', verdict).group(1))
            new_asset = re.search(r'【新增资产】：(.*)', verdict).group(1).strip()
            comment = re.search(r'【命运点评】：(.*)', verdict, re.DOTALL).group(1).strip()
        except Exception as e:
            faction_match, bg_delta, effort_delta, health_delta, money_delta = "混沌派", 0, 0, -5, 0
            new_asset, comment = "无", f"命运的账本出现了模糊... (日志: {verdict})"

        # D. 更新玩家属性（天赋和运气不再更新）
        st.session_state.attributes["家境"] += bg_delta
        st.session_state.attributes["努力"] += effort_delta
        st.session_state.attributes["健康"] += health_delta
        st.session_state.attributes["金钱"] += money_delta
        
        if new_asset != "无" and new_asset != "无。":
            st.session_state.assets.append(new_asset)
        
        if st.session_state.attributes["健康"] > 100: st.session_state.attributes["健康"] = 100
        # ✅ 新增：锁死家境和努力的上下限 (0-10)
        st.session_state.attributes["家境"] = max(0, min(10, st.session_state.attributes["家境"]))
        st.session_state.attributes["努力"] = max(0, min(10, st.session_state.attributes["努力"]))
        
        # E. 展示给玩家看
        assets_display = ', '.join(st.session_state.assets) if st.session_state.assets else '无'
        result_display = f"""
        **⚖️ 命运判定**：你的行为充满了【{faction_match}】的色彩。
        
        **📊 核心属性变动**：
        🏠 家境 {bg_delta:+} (当前: {st.session_state.attributes['家境']}) | 💪 努力 {effort_delta:+} (当前: {st.session_state.attributes['努力']})
        *(先天锁定: ✨ 天赋 {st.session_state.attributes['天赋']} | 🍀 运气 {st.session_state.attributes['运气']})*
        
        **💳 资产与健康账单**：
        ❤️ 健康 {health_delta:+} (当前: {st.session_state.attributes['健康']}/100)
        💰 金钱 {money_delta:+} (当前余额: ¥{st.session_state.attributes['金钱']})
        🎒 你的资产：{assets_display}
        
        **📖 结局印记**：
        {comment}
        """
        st.session_state.history.append({"role": "ferryman", "content": result_display.strip()})
        
        # F. 年龄增长
        st.session_state.age += random.randint(3, 7)
        st.session_state.stage = "GENERATE_EVENT"
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
        ❤️ 健康：{st.session_state.attributes['健康']}
        
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
