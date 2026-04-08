from telegram import Update
from telegram.ext import ContextTypes

from orchestrator import orchestrator
from storage import storage


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "AARS Telegram Control Bot 已启动。\n\n"
        "可用命令：\n"
        "/help\n"
        "/new_project 项目名\n"
        "/status\n"
        "/spawn 数量\n"
        "/run 步骤名\n"
        "/review\n"
        "/stable_view\n"
        "/closure\n"
        "/stop"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "命令帮助：\n"
        "/new_project 项目名 -> 创建项目\n"
        "/status -> 查看状态\n"
        "/spawn 数量 -> 启动 agent\n"
        "/run 步骤名 -> 执行步骤\n"
        "/review -> 审查当前进展\n"
        "/stable_view -> 查看最新稳定视图\n"
        "/closure -> 生成 closure summary\n"
        "/stop -> 停止当前项目"
    )


async def new_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("用法：/new_project 项目名")
        return

    project_name = " ".join(context.args)
    session = orchestrator.create_project(project_name)
    storage.save_active_session(session)

    await update.message.reply_text(
        f"项目已创建\n"
        f"Project ID: {session.project_id}\n"
        f"Name: {session.name}\n"
        f"Current Step: {session.current_step}\n"
        f"Health: {session.health}"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目。请先 /new_project")
        return

    task_count = len(session.tasks)
    stable_step = (
        session.latest_stable_view.stable_step if session.latest_stable_view else "N/A"
    )

    await update.message.reply_text(
        f"项目：{session.name}\n"
        f"Project ID: {session.project_id}\n"
        f"步骤：{session.current_step}\n"
        f"Health：{session.health}\n"
        f"Status：{session.status}\n"
        f"Agents：{session.agents}\n"
        f"Tasks：{task_count}\n"
        f"Latest Stable Step：{stable_step}"
    )


async def spawn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project")
        return

    try:
        count = int(context.args[0]) if context.args else 1
    except ValueError:
        await update.message.reply_text("用法：/spawn 数量")
        return

    session = orchestrator.spawn_agents(session, count)
    storage.save_active_session(session)

    await update.message.reply_text(
        f"已启动 {count} 个 agent。\n"
        f"当前总 agent 数：{session.agents}"
    )


async def run_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project")
        return

    if not context.args:
        await update.message.reply_text("用法：/run 步骤名")
        return

    step_name = " ".join(context.args)
    session = orchestrator.run_step(session, step_name)
    storage.save_active_session(session)

    await update.message.reply_text(
        f"步骤执行完成：{step_name}\n"
        f"当前步骤已更新为：{session.current_step}"
    )


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project")
        return

    result = orchestrator.review(session)
    storage.save_active_session(session)
    await update.message.reply_text(result)


async def stable_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project")
        return

    session = orchestrator.generate_stable_view(session)
    storage.save_active_session(session)

    sv = session.latest_stable_view
    accepted_outputs = "\n".join(f"- {item}" for item in sv.accepted_outputs)
    risks = "\n".join(f"- {item}" for item in sv.open_risks)

    await update.message.reply_text(
        f"Latest Stable View\n"
        f"Stable Step: {sv.stable_step}\n\n"
        f"Accepted Outputs:\n{accepted_outputs}\n\n"
        f"Open Risks:\n{risks}\n\n"
        f"Reentry Point: {sv.reentry_point}\n"
        f"Supervisor Note: {sv.supervisor_note}"
    )


async def closure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目，请先 /new_project")
        return

    result = orchestrator.closure(session)
    storage.save_active_session(session)
    await update.message.reply_text(result)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = storage.get_active_session()
    if session is None:
        await update.message.reply_text("当前没有活动项目。")
        return

    session.status = "paused"
    storage.save_active_session(session)
    await update.message.reply_text(
        f"项目已暂停：{session.name}\n"
        f"Current Step: {session.current_step}\n"
        f"Health: {session.health}"
    )
