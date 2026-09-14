# config.py

# 登入密碼設定（請保留您原本的密碼設定）
ADMIN_PASSWORD = "your_admin_password"
CREW_ACCESS_PASSWORD = "your_crew_password"

# 系統與模組所需參數
FEEDBACK_IMG_DIR = "feedback_images"
LEAVE_CODES = []
UNITS = []
FONT_PATH = "NotoSansTC.ttf"  # 專案中用於繪圖的字型檔

# 顏色常數
C_DO_TXT = "#881337"
C_PAY_TXT = "#9A3412"
C_HOLI_TXT = "#7C2D12"
C_OT_TXT = "#991818"
C_NOTE_TXT = "#4C1D95"
C_TOWN_TXT = "#000000"

# ==========================================
# 自訂 CSS 樣式
# ==========================================
CUSTOM_CSS = """
/* 徽章樣式 */
.hours-badge {
    background: rgba(56, 189, 248, 0.15) !important;
    color: #38BDF8 !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
    font-size: 10.5px !important;
}

/* 修復文字輸入框與文字域的樣式 */
.stTextInput input, .stTextArea textarea {
    background-color: rgba(15, 23, 42, 0.75) !important;
    color: #F8FAFC !important;
    border: none !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
    background: rgba(15, 23, 42, 0.75) !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 10px !important;
}
"""
