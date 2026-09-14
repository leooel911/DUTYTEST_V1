import streamlit as st
from config import ADMIN_PASSWORD, CREW_ACCESS_PASSWORD, CUSTOM_CSS
from modules.admin_views import render_admin_panel
from modules.components import render_zoomable_image, show_feedback_modal
from modules.drawing import render_schedule_figure
from modules.services import (
    authenticate_user,
    is_user_allowed,
    load_system_config,
    process_file_data,
    verify_crew_membership,
)
from modules.user_views import render_user_home
from modules.utils import (
    format_display_name,
    get_employee_name,
    log_activity,
    send_admin_email,
)

# ---------------------------------------------------------
# 載入全域動態設定
# ---------------------------------------------------------
sys_cfg = load_system_config()
ADMIN_PASS_CODE = sys_cfg.get("admin_password") or ADMIN_PASSWORD
DEFAULT_EMP_ID = sys_cfg.get("default_emp_id", "A")

st.set_page_config(
    page_title="TRAIN CREW DUTY CALENDAR", page_icon=None, layout="centered"
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State 初始化
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False
if "user_input_field" not in st.session_state:
    st.session_state["user_input_field"] = DEFAULT_EMP_ID
if "show_admin_login" not in st.session_state:
    st.session_state["show_admin_login"] = False
if "show_feedback_dialog" not in st.session_state:
    st.session_state["show_feedback_dialog"] = False
if "inspect_emp_target" not in st.session_state:
    st.session_state["inspect_emp_target"] = None
if "nav_mode" not in st.session_state:
    st.session_state["nav_mode"] = "home"
if "page" not in st.session_state:
    st.session_state["page"] = "user"
if "current_user_id" not in st.session_state:
    st.session_state["current_user_id"] = DEFAULT_EMP_ID
if "login_user_id" not in st.session_state:
    st.session_state["login_user_id"] = DEFAULT_EMP_ID
if "current_unit" not in st.session_state:
    st.session_state["current_unit"] = "TTN"


# =========================================================
# 前置授權門戶檢核
# =========================================================
is_authed = st.session_state.get("authenticated", False)
is_admin_authed = st.session_state.get("admin_logged_in", False)

if not is_authed and not is_admin_authed:
    st.markdown(
        """
    <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1.2rem;">
        <div style="font-size: 24px; font-weight: 900; letter-spacing: 1.5px; color: #F8FAFC; font-family: monospace;">CREW DUTY ENGINE</div>
        <div style="color: #94A3B8; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 6px; font-family: monospace;">
            OPERATION MANAGEMENT SYSTEM | C.L.F EDITION
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2.4, 1])
    with col2:
        with st.expander("登入前系統說明與規範 (點擊展開)", expanded=False):
            st.markdown(
                """
            <div style="font-size: 12px; color: #CBD5E1; line-height: 1.7; font-family: monospace;">
                <div style="color: #38BDF8; font-weight: 800; margin-bottom: 6px;">[系統公告] 內部測試環境</div>
                本系統目前為正式營運前之特定人員內部測試階段。<br><br>
                <div style="color: #FBBF24; font-weight: 800; margin-bottom: 4px;">[注意事項] 資訊安全規範：</div>
                1. <b>排班依據</b>：本系統班表僅供個人排班與調班快篩參考，官方正式班表依公司公告為準。<br>
                2. <b>資安保護</b>：班表屬內部機密營運資料，請勿外流授權碼及相關截圖。<br>
                3. <b>問題反應</b>：系統異常或資料有誤請透過頁尾功能回報後台。
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        with st.form("login_main_form"):
            selected_unit = st.selectbox("選擇所屬基地單位", ["TTN", "TTC", "TTS"], key="login_unit_box")
            entered_emp = st.text_input(
                "使用者員編 (範例: A023300)",
                value=DEFAULT_EMP_ID,
                placeholder="請輸入員編...",
                max_chars=10,
                key="login_emp_box",
            )
            entered_key = st.text_input(
                "系統授權碼", type="password", placeholder="請輸入授權金鑰...", key="login_key_box"
            )

            btn_auth = st.form_submit_button("進入系統", type="primary", use_container_width=True)

        if btn_auth:
            success, message, user_session = authenticate_user(selected_unit, entered_emp, entered_key)
            
            if success:
                role = user_session.get("role", "USER")
                is_adm = (role == "ADMIN")
                
                st.session_state["authenticated"] = True
                st.session_state["admin_logged_in"] = is_adm
                st.session_state["show_admin_login"] = False
                st.session_state["nav_mode"] = "admin_panel" if is_adm else "home"
                st.session_state["page"] = "admin" if is_adm else "user"
                st.session_state["current_unit"] = user_session.get("unit", selected_unit)
                st.session_state["login_user_id"] = user_session.get("emp_id", "")
                
                emp_name = user_session.get("emp_name", "")
                emp_id = user_session.get("emp_id", "")
                
                if is_adm:
                    st.session_state["current_user_id"] = f"ADMIN ({emp_id})"
                else:
                    st.session_state["current_user_id"] = f"{emp_name} ({emp_id})" if emp_name else emp_id

                log_activity(
                    action="帳號登入",
                    detail=f"驗證通過: {emp_name} ({emp_id}) | 角色: {role}",
                    user=emp_id,
                    unit=selected_unit,
                )
                st.rerun()
            else:
                # 紅色示警語意
                st.markdown(f'<div class="alert-banner">[錯誤] 登入失敗：{message}</div>', unsafe_allow_html=True)

    st.stop()


# =========================================================
# 已登入狀態操作區塊
# =========================================================

if st.session_state.get("inspect_emp_target") is not None:
    target_emp = st.session_state["inspect_emp_target"]
    current_unit = st.session_state.get("current_unit", "TTN")

    st.markdown(
        f"""
    <div class="section-header-box">
        <div class="section-title">[{current_unit}] 組員完整班表檢視: {target_emp}</div>
        <div class="section-subtitle">Inspection Mode // Full Schedule View</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("上一頁 (返回快篩結果)"):
        st.session_state["inspect_emp_target"] = None
        st.rerun()

    try:
        start_dt, dates, emp_id, emp_name, cells = process_file_data(target_emp)
        with st.spinner(f"正在載入 [{emp_name}] 之完整月班表資料..."):
            buf = render_schedule_figure(
                start_dt,
                dates,
                emp_id,
                emp_name,
                cells,
                current_unit,
                badge_title="Inspector | C.L.F",
            )
            st.success(f"成功載入 [{emp_name}] ({emp_id}) 之完整月班表")
            render_zoomable_image(buf)

            col_dl1, col_dl2 = st.columns([1, 1])
            with col_dl1:
                st.download_button(
                    "下載月班表圖檔",
                    data=buf,
                    file_name=f"{current_unit}_班表_{emp_name}.png",
                    mime="image/png",
                    use_container_width=True,
                )
            with col_dl2:
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; height: 100%; font-size: 12px; color: #94A3B8; font-weight: 500; font-family: monospace; padding-left: 6px;">
                        [提示] 行動裝置可長按圖片儲存至相簿
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except Exception as e:
        st.markdown(f'<div class="alert-banner">[錯誤] 載入組員班表失敗：{e}</div>', unsafe_allow_html=True)

    st.stop()


current_unit_label = st.session_state.get("current_unit", "TTN")
current_operator_id = st.session_state.get("current_user_id", DEFAULT_EMP_ID)

st.markdown(
    f"""
<div class="header-container">
    <div class="main-title">CREW DUTY ENGINE</div>
    <div style="color: #94A3B8; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; font-family: monospace; margin-top: 3px;">
        OPERATION MANAGEMENT SYSTEM &bull; C.L.F EDITION
    </div>
    <div class="title-subtitle">
        <span class="status-dot"></span>WELCOME: {current_unit_label} | {current_operator_id}<span class="status-dot"></span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

enable_beta_banner = sys_cfg.get("enable_beta_notice", True)
announcement_msg = sys_cfg.get("announcement", "系統目前於維護模式運行中｜頁面末端可聯繫後台管理者")

if enable_beta_banner:
    # 黃色維修色調
    st.markdown(
        f"""
    <div class="maintenance-banner">
        <div class="maintenance-title">[系統維護公告] BETA TEST ENVIRONMENT</div>
        <div class="maintenance-sub">{announcement_msg}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

if st.session_state.get("show_admin_login", False) and not st.session_state.get(
    "admin_logged_in", False
):
    st.markdown(
        """
    <div class="section-header-box">
        <div class="section-title">管理員身分驗證</div>
        <div class="section-subtitle">Administrator Security Verification</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("admin_login_form"):
            adm_pwd_input = st.text_input(
                "管理員密碼",
                type="password",
                placeholder="請輸入密碼...",
                key="badge_admin_pwd_box",
            )
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_submit_adm = st.form_submit_button("登入後台")
            with col_btn2:
                btn_cancel_adm = st.form_submit_button("取消")

            if btn_submit_adm:
                if adm_pwd_input == ADMIN_PASS_CODE:
                    curr_op = st.session_state.get("user_input_field", DEFAULT_EMP_ID)
                    admin_uid = f"ADMIN_{curr_op}"
                    st.session_state["admin_logged_in"] = True
                    st.session_state["nav_mode"] = "admin_panel"
                    st.session_state["page"] = "admin"
                    st.session_state["show_admin_login"] = False
                    st.session_state["current_user_id"] = f"ADMIN ({curr_op})"
                    st.session_state["login_user_id"] = admin_uid
                    log_activity(
                        action="管理員操作",
                        detail=f"管理員登入後台 ({curr_op})",
                        user=admin_uid,
                        unit=st.session_state.get("current_unit", "全站"),
                    )
                    st.rerun()
                else:
                    st.markdown('<div class="alert-banner">[錯誤] 管理員密碼驗證失敗</div>', unsafe_allow_html=True)
            elif btn_cancel_adm:
                st.session_state["show_admin_login"] = False
                st.rerun()
    st.stop()

is_admin_active = (
    st.session_state.get("nav_mode") == "admin_panel"
    or st.session_state.get("page") == "admin"
) and st.session_state.get("page") != "user"

if is_admin_active and st.session_state.get("admin_logged_in", False):
    render_admin_panel()
else:
    render_user_home()

st.markdown(
    '<div style="margin-top: 2rem; padding-top: 0.8rem; border-top: 1px dashed rgba(255,255,255,0.08);"></div>',
    unsafe_allow_html=True,
)

col_f1, col_f2 = st.columns(2)

with col_f1:
    if st.button(
        "問題回報與建議",
        key="btn_feedback_left_footer",
        use_container_width=True,
    ):
        st.session_state["show_feedback_dialog"] = True
        st.rerun()

with col_f2:
    admin_btn_label = (
        "ADMIN PANEL [Leo]"
        if st.session_state.get("admin_logged_in", False)
        else "ADMIN PANEL [C.L.F]"
    )
    if st.button(
        admin_btn_label, key="btn_admin_right_footer", use_container_width=True
    ):
        if st.session_state.get("admin_logged_in", False):
            if is_admin_active:
                st.session_state["nav_mode"] = "home"
                st.session_state["page"] = "user"
            else:
                st.session_state["nav_mode"] = "admin_panel"
                st.session_state["page"] = "admin"
        else:
            st.session_state["show_admin_login"] = True
        st.rerun()

if st.session_state.get("show_feedback_dialog", False):
    show_feedback_modal()
