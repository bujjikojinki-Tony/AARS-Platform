from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from storage import storage
from orchestrator import orchestrator


# =========================
# Menu builders
# =========================

def build_home_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Project", callback_data="nav:project")],
        [InlineKeyboardButton("Runtime", callback_data="nav:runtime")],
        [InlineKeyboardButton("Governance", callback_data="nav:governance")],
        [InlineKeyboardButton("Stable View", callback_data="nav:stable_view")],
        [InlineKeyboardButton("Closure", callback_data="nav:closure")],
        [InlineKeyboardButton("Refresh Home", callback_data="action:home_refresh")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_project_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("New Project", callback_data="action:new_project")],
        [InlineKeyboardButton("Project List", callback_data="action:project_list")],
        [InlineKeyboardButton("Status", callback_data="action:status")],
        [InlineKeyboardButton("Archive Current", callback_data="action:archive_current")],
        [InlineKeyboardButton("Pause", callback_data="action:pause")],
        [InlineKeyboardButton("Back Home", callback_data="nav:home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_runtime_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Spawn 1 Agent", callback_data="action:spawn1")],
        [InlineKeyboardButton("Spawn 3 Agents", callback_data="action:spawn3")],
        [InlineKeyboardButton("Run Intent Framing", callback_data="action:run_intent_framing")],
        [InlineKeyboardButton("Run Goal Definition", callback_data="action:run_goal_definition")],
        [InlineKeyboardButton("Run Task Execution", callback_data="action:run_task_execution")],
        [InlineKeyboardButton("Back Home", callback_data="nav:home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_governance_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Health", callback_data="action:health")],
        [InlineKeyboardButton("Risks", callback_data="action:risks")],
        [InlineKeyboardButton("Recovery", callback_data="action:recovery")],
        [InlineKeyboardButton("Gate Logs", callback_data="action:gate_logs")],
        [InlineKeyboardButton("Jump to Step 1", callback_data="action:jump_step_1")],
        [InlineKeyboardButton("Jump to Step 2", callback_data="action:jump_step_2")],
        [InlineKeyboardButton("Jump to Step 5", callback_data="action:jump_step_5")],
        [InlineKeyboardButton("Back Home", callback_data="nav:home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_stable_view_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Refresh Stable View", callback_data="action:stable_view_refresh")],
        [InlineKeyboardButton("Review", callback_data="action:review")],
        [InlineKeyboardButton("Back Home", callback_data="nav:home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_closure_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Closure", callback_data="action:closure")],
        [InlineKeyboardButton("Back Home", callback_data="nav:home")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_project_list_menu() -> InlineKeyboardMarkup:
    projects = storage.list_projects(include_archived=False)
    keyboard = []

    for p in projects[:10]:
        keyboard.append([
            InlineKeyboardButton(
                f"Use: {p['name'][:28]}",
                callback_data=f"action:use_project:{p['project_id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("Back Project Menu", callback_data="nav:project")])
    return InlineKeyboardMarkup(keyboard)


# =========================
# Session helpers
# =========================

def get_session():
    return storage.get_active_session()


def get_active_project_line() -> str:
    session = get_session()
    if session is None:
        return "Active Project: N/A"
    return f"Active Project: {session.name} ({session.project_id})"


def get_session_summary() -> str:
    session = get_session()
    if session is None:
        return (
            f"{get_active_project_line()}\n"
            "Step: N/A\n"
            "Health: N/A\n"
            "Status: N/A\n"
            "Agents: 0\n"
            "Tasks: 0\n"
            "Stable Step: N/A"
        )

    task_count = len(session.tasks)
    stable_step = session.latest_stable_view.stable_step if session.latest_stable_view else "N/A"

    return (
        f"{get_active_project_line()}\n"
        f"Step: {session.current_step}\n"
        f"Health: {session.health}\n"
        f"Status: {session.status}\n"
        f"Agents: {session.agents}\n"
        f"Tasks: {task_count}\n"
        f"Stable Step: {stable_step}"
    )


def read_health_snapshot_text() -> str:
    session = get_session()
    if session is None or session.health_snapshot is None:
        return "No active HealthSnapshot."

    hs = session.health_snapshot
    return (
        "Health Snapshot\n\n"
        f"Overall Health: {hs.overall_health}\n"
        f"Session Status: {hs.session_status}\n"
        f"Current Step: {hs.current_step}\n"
        f"Total Tasks: {hs.total_tasks}\n"
        f"Completed Tasks: {hs.completed_tasks}\n"
        f"Blocked Tasks: {hs.blocked_tasks}\n"
        f"Failed Tasks: {hs.failed_tasks}\n"
        f"Generated At: {hs.generated_at}"
    )


def read_risk_objects_text() -> str:
    session = get_session()
    if session is None:
        return "No active session."

    if not session.risk_objects:
        return "Risk Objects\n\nNo open risks recorded."

    parts = ["Risk Objects"]
    for r in session.risk_objects:
        parts.append(
            f"\n[{r.risk_id}] {r.title}\n"
            f"Severity: {r.severity}\n"
            f"Status: {r.status}\n"
            f"Description: {r.description}\n"
            f"Mitigation: {r.mitigation}"
        )
    return "\n".join(parts)


def read_recovery_path_text() -> str:
    session = get_session()
    if session is None or session.recovery_path is None:
        return "No active RecoveryPath."

    rp = session.recovery_path
    return (
        "Recovery Path\n\n"
        f"Current Step: {rp.current_step}\n"
        f"Latest Stable Step: {rp.latest_stable_step}\n"
        f"Reentry Point: {rp.reentry_point}\n"
        f"Suggested Action: {rp.suggested_action}\n"
        f"Recovery Mode: {rp.recovery_mode}\n"
        f"Generated At: {rp.generated_at}"
    )


def read_stable_view_text() -> str:
    session = get_session()
    if session is None:
        return "No active session.\nStable View unavailable."

    sv = session.latest_stable_view
    if sv is None:
        return (
            "Latest Stable View\n\n"
            "No stable checkpoint yet.\n"
            "Use 'Refresh Stable View' to generate one."
        )

    accepted_outputs = "\n".join(f"- {item}" for item in sv.accepted_outputs) or "- N/A"
    risks = "\n".join(f"- {item}" for item in sv.open_risks) or "- N/A"

    return (
        "Latest Stable View\n\n"
        f"Stable Step: {sv.stable_step}\n\n"
        f"Accepted Outputs:\n{accepted_outputs}\n\n"
        f"Open Risks:\n{risks}\n\n"
        f"Reentry Point: {sv.reentry_point}\n"
        f"Supervisor Note: {sv.supervisor_note}"
    )


def read_gate_logs_text(limit: int = 8) -> str:
    session = get_session()
    if session is None:
        return "No active session."

    if not session.gate_logs:
        return "Gate Logs\n\nNo gate decisions recorded yet."

    logs = session.gate_logs[-limit:]
    parts = ["Gate Logs (latest first)"]

    for log in reversed(logs):
        risk_text = ", ".join(log.blocking_risks) if log.blocking_risks else "None"
        parts.append(
            f"\n[{log.generated_at}]\n"
            f"Action: {log.action_name}\n"
            f"Gate: {log.gate_name}\n"
            f"Allowed: {log.allowed}\n"
            f"Reason: {log.reason}\n"
            f"Blocking Risks: {risk_text}"
        )

    return "\n".join(parts)


def read_project_list_text() -> str:
    projects = storage.list_projects(include_archived=False)
    active_id = storage.get_active_project_id()

    if not projects:
        return "Project List\n\nNo projects found."

    parts = ["Project List"]
    for p in projects:
        marker = " (ACTIVE)" if p["project_id"] == active_id else ""
        parts.append(
            f"\n- {p['name']}\n"
            f"  ID: {p['project_id']}{marker}\n"
            f"  Updated: {p['updated_at']}"
        )
    return "\n".join(parts)


def format_gate_decision(decision) -> str:
    lines = [
        f"Gate: {decision.gate_name}",
        f"Allowed: {decision.allowed}",
        f"Reason: {decision.reason}",
    ]
    if decision.blocking_risks:
        lines.append("Blocking Risks: " + ", ".join(decision.blocking_risks))
    return "\n".join(lines)


# =========================
# Screen renderers
# =========================

def render_home_text(extra: str = "") -> str:
    text = (
        "AARS Telegram Control Console v8\n"
        "Mode: Multi Project\n\n"
        "== Current Summary ==\n"
        f"{get_session_summary()}"
    )
    if extra:
        text += f"\n\n== Result ==\n{extra}"
    return text


def render_project_text(extra: str = "") -> str:
    text = (
        "AARS Console — Project Menu\n\n"
        "== Current Summary ==\n"
        f"{get_session_summary()}"
    )
    if extra:
        text += f"\n\n== Project Output ==\n{extra}"
    return text


def render_runtime_text(extra: str = "") -> str:
    text = (
        "AARS Console — Runtime Menu\n\n"
        "== Current Summary ==\n"
        f"{get_session_summary()}"
    )
    if extra:
        text += f"\n\n== Runtime Result ==\n{extra}"
    return text


def render_governance_text(extra: str = "") -> str:
    text = (
        "AARS Console — Governance Menu\n\n"
        "== Current Summary ==\n"
        f"{get_session_summary()}"
    )
    if extra:
        text += f"\n\n== Governance Output ==\n{extra}"
    return text


def render_stable_view_text(extra: str = "") -> str:
    text = (
        "AARS Console — Stable View Menu\n\n"
        "== Current Summary ==\n"
        f"{get_session_summary()}"
    )
    if extra:
        text += f"\n\n== Stable View ==\n{extra}"
    return text


def render_closure_text(extra: str = "") -> str:
    text = (
        "AARS Console — Closure Menu\n\n"
        "== Current Summary ==\n"
        f"{get_session_summary()}"
    )
    if extra:
        text += f"\n\n== Closure Output ==\n{extra}"
    return text


def render_project_list_text(extra: str = "") -> str:
    text = (
        "AARS Console — Project List\n\n"
        f"{read_project_list_text()}"
    )
    if extra:
        text += f"\n\n== Result ==\n{extra}"
    return text


# =========================
# Safe edit helper
# =========================

async def safe_edit(query, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    except Exception:
        await query.edit_message_text(text=text + "\n", reply_markup=reply_markup)


# =========================
# Command handlers
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(render_home_text(), reply_markup=build_home_menu())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Multi Project 已启用。\n"
        "新增能力：\n"
        "- Project List\n"
        "- Switch Active Project\n"
        "- Archive Current Project"
    )
    await update.message.reply_text(text, reply_markup=build_home_menu())


async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        render_project_list_text(),
        reply_markup=build_project_list_menu(),
    )


async def use_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("用法：/use_project project_id", reply_markup=build_project_menu())
        return

    project_id = context.args[0]
    session = storage.get_project(project_id)
    if session is None:
        await update.message.reply_text(f"Project not found: {project_id}", reply_markup=build_project_menu())
        return

    storage.set_active_project_id(project_id)
    await update.message.reply_text(
        render_project_text(f"Switched active project to: {session.name} ({session.project_id})"),
        reply_markup=build_project_menu(),
    )


async def new_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("用法：/new_project 项目名", reply_markup=build_project_menu())
        return

    project_name = " ".join(context.args)
    session = orchestrator.create_project(project_name)
    storage.save_active_session(session)

    result = (
        f"项目已创建并设为 active\n"
        f"Project ID: {session.project_id}\n"
        f"Name: {session.name}\n"
        f"Current Step: {session.current_step}\n"
        f"Health: {session.health}"
    )
    await update.message.reply_text(render_project_text(result), reply_markup=build_project_menu())


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(render_project_text("状态已刷新。"), reply_markup=build_project_menu())


async def spawn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project 或 /projects", reply_markup=build_runtime_menu())
        return

    try:
        count = int(context.args[0]) if context.args else 1
    except ValueError:
        await update.message.reply_text("用法：/spawn 数量", reply_markup=build_runtime_menu())
        return

    session = orchestrator.spawn_agents(session, count)
    storage.save_active_session(session)

    await update.message.reply_text(
        render_runtime_text(f"已启动 {count} 个 agent。"),
        reply_markup=build_runtime_menu(),
    )


async def run_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project 或 /projects", reply_markup=build_runtime_menu())
        return

    if not context.args:
        await update.message.reply_text("用法：/run 步骤名", reply_markup=build_runtime_menu())
        return

    step_name = " ".join(context.args)
    session, decision = orchestrator.run_step(session, step_name)
    storage.save_active_session(session)

    result = f"{decision.reason}\n\n{format_gate_decision(decision)}" if decision.allowed else f"Execution blocked.\n\n{format_gate_decision(decision)}"
    await update.message.reply_text(render_runtime_text(result), reply_markup=build_runtime_menu())


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project 或 /projects", reply_markup=build_stable_view_menu())
        return

    result = orchestrator.review(session)
    storage.save_active_session(session)
    await update.message.reply_text(render_stable_view_text(result), reply_markup=build_stable_view_menu())


async def stable_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project 或 /projects", reply_markup=build_stable_view_menu())
        return

    session = orchestrator.generate_stable_view(session)
    storage.save_active_session(session)

    await update.message.reply_text(
        render_stable_view_text(read_stable_view_text()),
        reply_markup=build_stable_view_menu(),
    )


async def closure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project 或 /projects", reply_markup=build_closure_menu())
        return

    session, decision, result = orchestrator.closure(session)
    storage.save_active_session(session)

    text = result + "\n\n" + format_gate_decision(decision) if decision.allowed else "Closure blocked.\n\n" + format_gate_decision(decision)
    await update.message.reply_text(render_closure_text(text), reply_markup=build_closure_menu())


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目。", reply_markup=build_project_menu())
        return

    session = orchestrator.pause_session(session)
    storage.save_active_session(session)
    await update.message.reply_text(
        render_project_text(f"项目已暂停：{session.name}"),
        reply_markup=build_project_menu(),
    )


# =========================
# Button router
# =========================

async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "nav:home":
        await safe_edit(query, render_home_text(), build_home_menu())
        return

    if data == "nav:project":
        await safe_edit(query, render_project_text(), build_project_menu())
        return

    if data == "nav:runtime":
        await safe_edit(query, render_runtime_text(), build_runtime_menu())
        return

    if data == "nav:governance":
        await safe_edit(query, render_governance_text(), build_governance_menu())
        return

    if data == "nav:stable_view":
        await safe_edit(query, render_stable_view_text(), build_stable_view_menu())
        return

    if data == "nav:closure":
        await safe_edit(query, render_closure_text(), build_closure_menu())
        return

    if data == "action:home_refresh":
        await safe_edit(query, render_home_text("Home summary refreshed."), build_home_menu())
        return

    if data == "action:new_project":
        session = orchestrator.create_project("AARS Governed Project Multi")
        storage.save_active_session(session)
        result = (
            f"项目已创建并设为 active\n"
            f"Project ID: {session.project_id}\n"
            f"Name: {session.name}\n"
            f"Current Step: {session.current_step}\n"
            f"Health: {session.health}"
        )
        await safe_edit(query, render_project_text(result), build_project_menu())
        return

    if data == "action:project_list":
        await safe_edit(query, render_project_list_text(), build_project_list_menu())
        return

    if data.startswith("action:use_project:"):
        project_id = data.split(":", 2)[2]
        session = storage.get_project(project_id)
        if session is None:
            await safe_edit(query, render_project_list_text(f"Project not found: {project_id}"), build_project_list_menu())
            return

        storage.set_active_project_id(project_id)
        await safe_edit(
            query,
            render_project_text(f"Switched active project to: {session.name} ({session.project_id})"),
            build_project_menu(),
        )
        return

    if data == "action:archive_current":
        session = get_session()
        if session is None:
            await safe_edit(query, render_project_text("当前没有活动项目。"), build_project_menu())
            return

        storage.archive_project(session.project_id)
        await safe_edit(
            query,
            render_project_text(f"Archived project: {session.name} ({session.project_id})"),
            build_project_menu(),
        )
        return

    if data == "action:status":
        await safe_edit(query, render_project_text("状态已刷新。"), build_project_menu())
        return

    if data == "action:pause":
        session = get_session()
        if session is None:
            await safe_edit(query, render_project_text("当前没有活动项目。"), build_project_menu())
            return
        session = orchestrator.pause_session(session)
        storage.save_active_session(session)
        await safe_edit(query, render_project_text(f"项目已暂停：{session.name}"), build_project_menu())
        return

    if data == "action:spawn1":
        session = get_session()
        if session is None:
            await safe_edit(query, render_runtime_text("当前没有活动项目，请先创建或切换项目。"), build_runtime_menu())
            return
        session = orchestrator.spawn_agents(session, 1)
        storage.save_active_session(session)
        await safe_edit(query, render_runtime_text("已启动 1 个 agent。"), build_runtime_menu())
        return

    if data == "action:spawn3":
        session = get_session()
        if session is None:
            await safe_edit(query, render_runtime_text("当前没有活动项目，请先创建或切换项目。"), build_runtime_menu())
            return
        session = orchestrator.spawn_agents(session, 3)
        storage.save_active_session(session)
        await safe_edit(query, render_runtime_text("已启动 3 个 agent。"), build_runtime_menu())
        return

    if data == "action:run_intent_framing":
        session = get_session()
        if session is None:
            await safe_edit(query, render_runtime_text("当前没有活动项目，请先创建或切换项目。"), build_runtime_menu())
            return
        session, decision = orchestrator.run_step(session, "Intent Framing")
        storage.save_active_session(session)
        result = f"{decision.reason}\n\n{format_gate_decision(decision)}" if decision.allowed else f"Execution blocked.\n\n{format_gate_decision(decision)}"
        await safe_edit(query, render_runtime_text(result), build_runtime_menu())
        return

    if data == "action:run_goal_definition":
        session = get_session()
        if session is None:
            await safe_edit(query, render_runtime_text("当前没有活动项目，请先创建或切换项目。"), build_runtime_menu())
            return
        session, decision = orchestrator.run_step(session, "Goal Definition")
        storage.save_active_session(session)
        result = f"{decision.reason}\n\n{format_gate_decision(decision)}" if decision.allowed else f"Execution blocked.\n\n{format_gate_decision(decision)}"
        await safe_edit(query, render_runtime_text(result), build_runtime_menu())
        return

    if data == "action:run_task_execution":
        session = get_session()
        if session is None:
            await safe_edit(query, render_runtime_text("当前没有活动项目，请先创建或切换项目。"), build_runtime_menu())
            return
        session, decision = orchestrator.run_step(session, "Task Execution")
        storage.save_active_session(session)
        result = f"{decision.reason}\n\n{format_gate_decision(decision)}" if decision.allowed else f"Execution blocked.\n\n{format_gate_decision(decision)}"
        await safe_edit(query, render_runtime_text(result), build_runtime_menu())
        return

    if data == "action:health":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目。"), build_governance_menu())
            return
        session = orchestrator.refresh_governance(session)
        storage.save_active_session(session)
        await safe_edit(query, render_governance_text(read_health_snapshot_text()), build_governance_menu())
        return

    if data == "action:risks":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目。"), build_governance_menu())
            return
        session = orchestrator.refresh_governance(session)
        storage.save_active_session(session)
        await safe_edit(query, render_governance_text(read_risk_objects_text()), build_governance_menu())
        return

    if data == "action:recovery":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目。"), build_governance_menu())
            return
        session = orchestrator.refresh_governance(session)
        storage.save_active_session(session)
        await safe_edit(query, render_governance_text(read_recovery_path_text()), build_governance_menu())
        return

    if data == "action:gate_logs":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目。"), build_governance_menu())
            return
        await safe_edit(query, render_governance_text(read_gate_logs_text()), build_governance_menu())
        return

    if data == "action:jump_step_1":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目，请先创建或切换项目。"), build_governance_menu())
            return
        session, decision = orchestrator.jump_to_step(session, "Intent Framing")
        storage.save_active_session(session)
        await safe_edit(query, render_governance_text(format_gate_decision(decision)), build_governance_menu())
        return

    if data == "action:jump_step_2":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目，请先创建或切换项目。"), build_governance_menu())
            return
        session, decision = orchestrator.jump_to_step(session, "Goal Definition")
        storage.save_active_session(session)
        await safe_edit(query, render_governance_text(format_gate_decision(decision)), build_governance_menu())
        return

    if data == "action:jump_step_5":
        session = get_session()
        if session is None:
            await safe_edit(query, render_governance_text("当前没有活动项目，请先创建或切换项目。"), build_governance_menu())
            return
        session, decision = orchestrator.jump_to_step(session, "Concept Layer Validation")
        storage.save_active_session(session)
        await safe_edit(query, render_governance_text(format_gate_decision(decision)), build_governance_menu())
        return

    if data == "action:review":
        session = get_session()
        if session is None:
            await safe_edit(query, render_stable_view_text("当前没有活动项目，请先创建或切换项目。"), build_stable_view_menu())
            return
        result = orchestrator.review(session)
        storage.save_active_session(session)
        await safe_edit(query, render_stable_view_text(result), build_stable_view_menu())
        return

    if data == "action:stable_view_refresh":
        session = get_session()
        if session is None:
            await safe_edit(query, render_stable_view_text("当前没有活动项目，请先创建或切换项目。"), build_stable_view_menu())
            return
        session = orchestrator.generate_stable_view(session)
        storage.save_active_session(session)
        await safe_edit(query, render_stable_view_text(read_stable_view_text()), build_stable_view_menu())
        return

    if data == "action:closure":
        session = get_session()
        if session is None:
            await safe_edit(query, render_closure_text("当前没有活动项目，请先创建或切换项目。"), build_closure_menu())
            return
        session, decision, result = orchestrator.closure(session)
        storage.save_active_session(session)
        text = result + "\n\n" + format_gate_decision(decision) if decision.allowed else "Closure blocked.\n\n" + format_gate_decision(decision)
        await safe_edit(query, render_closure_text(text), build_closure_menu())
        return
