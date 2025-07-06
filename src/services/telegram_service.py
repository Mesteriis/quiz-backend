"""
Telegram Bot Service for Quiz App using aiogram.

This module provides async Telegram bot functionality with polling support
for local development and webhook support for production.
"""

import logging
from typing import Optional
import uuid

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResult,
    InlineQueryResultArticle,
    InputTextMessageContent,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from config import get_settings
from database import get_async_session
from models.question import Question, QuestionType
from models.response import Response
from models.survey import Survey
from models.user import User, UserCreate
from services.jwt_service import jwt_service
from services.user_service import user_service

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

settings = get_settings()


class SurveyStates(StatesGroup):
    """FSM states for survey interactions."""

    # Survey selection
    browsing_surveys = State()

    # Survey taking states
    taking_survey = State()
    answering_question = State()
    confirming_answer = State()

    # Navigation states
    survey_navigation = State()
    question_navigation = State()

    # Results states
    viewing_results = State()
    exporting_results = State()


class AdminStates(StatesGroup):
    """FSM states for admin interactions."""

    admin_menu = State()
    creating_survey = State()
    editing_survey = State()
    managing_users = State()
    viewing_analytics = State()


class InlineStates(StatesGroup):
    """FSM states for inline mode interactions."""

    inline_search = State()
    inline_selection = State()


class TelegramService:
    """Service for managing Telegram bot operations using aiogram."""

    def __init__(self):
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.webapp_url = "http://localhost:3000"  # TODO: Configure in settings
        self.active_surveys: dict[int, dict] = {}  # Cache for active surveys

    async def initialize(self) -> None:
        """Initialize the Telegram bot."""
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token not configured")
            return

        # Initialize bot with default properties
        self.bot = Bot(
            token=settings.telegram_bot_token,
            parse_mode=ParseMode.HTML,
        )

        # Initialize dispatcher with memory storage
        storage = MemoryStorage()
        self.dp = Dispatcher(storage=storage)

        # Register handlers
        await self._register_handlers()

        logger.info("Telegram bot initialized successfully with aiogram")

    async def _register_handlers(self) -> None:
        """Register all bot handlers."""
        if not self.dp:
            return

        # Command handlers
        self.dp.message.register(self.start_command, Command("start"))
        self.dp.message.register(self.help_command, Command("help"))
        self.dp.message.register(self.surveys_command, Command("surveys"))
        self.dp.message.register(self.admin_command, Command("admin"))
        self.dp.message.register(self.cancel_command, Command("cancel"))

        # Inline query handlers
        self.dp.inline_query.register(self.handle_inline_query)

        # FSM handlers for survey taking
        self.dp.callback_query.register(
            self.handle_start_survey, F.data.startswith("start_survey_")
        )
        self.dp.callback_query.register(
            self.handle_answer_question,
            F.data.startswith("answer_"),
            StateFilter(SurveyStates.answering_question),
        )
        self.dp.callback_query.register(
            self.handle_navigation,
            F.data.startswith("nav_"),
            StateFilter(
                SurveyStates.survey_navigation, SurveyStates.question_navigation
            ),
        )
        self.dp.callback_query.register(
            self.handle_confirm_answer,
            F.data.startswith("confirm_"),
            StateFilter(SurveyStates.confirming_answer),
        )

        # Text message handlers for different states
        self.dp.message.register(
            self.handle_text_answer,
            F.text,
            StateFilter(SurveyStates.answering_question),
        )
        self.dp.message.register(
            self.handle_email_answer,
            F.text,
            StateFilter(SurveyStates.answering_question),
        )
        self.dp.message.register(
            self.handle_phone_answer,
            F.text,
            StateFilter(SurveyStates.answering_question),
        )

        # Basic callback query handlers
        self.dp.callback_query.register(
            self.handle_list_surveys, F.data == "list_surveys"
        )
        self.dp.callback_query.register(self.handle_help, F.data == "help")
        self.dp.callback_query.register(
            self.handle_admin_panel, F.data == "admin_panel"
        )
        self.dp.callback_query.register(
            self.handle_admin_stats, F.data == "admin_stats"
        )
        self.dp.callback_query.register(
            self.handle_admin_surveys, F.data == "admin_surveys"
        )
        self.dp.callback_query.register(
            self.handle_admin_users, F.data == "admin_users"
        )
        self.dp.callback_query.register(
            self.handle_admin_reports, F.data == "admin_reports"
        )
        self.dp.callback_query.register(
            self.handle_survey_details, F.data.startswith("survey_")
        )

        # Message handlers
        self.dp.message.register(self.handle_text_message, F.text)

        logger.info("All handlers registered successfully")

    async def start_polling(self) -> None:
        """Start polling for updates (for local development)."""
        if not self.dp or not self.bot:
            await self.initialize()

        if not self.dp or not self.bot:
            logger.error("Failed to initialize Telegram bot")
            return

        logger.info("🤖 Starting Telegram bot polling...")
        try:
            await self.dp.start_polling(self.bot, drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error in polling: {e}")

    async def stop_polling(self) -> None:
        """Stop polling."""
        if self.dp:
            await self.dp.stop_polling()
            logger.info("Telegram bot polling stopped")

    # ======================
    # INLINE QUERY HANDLERS
    # ======================

    async def handle_inline_query(self, query: InlineQuery) -> None:
        """Handle inline queries for survey search."""
        try:
            search_text = query.query.strip().lower()

            # Search surveys
            async with get_async_session() as session:
                stmt = (
                    select(Survey)
                    .where(
                        and_(
                            Survey.is_active == True,
                            Survey.is_public == True,
                            Survey.title.ilike(f"%{search_text}%")
                            if search_text
                            else True,
                        )
                    )
                    .limit(10)
                )

                result = await session.execute(stmt)
                surveys = result.scalars().all()

            # Create inline results
            results: list[InlineQueryResult] = []

            for survey in surveys:
                # Count questions
                async with get_async_session() as session:
                    q_count = await session.execute(
                        select(func.count(Question.id)).where(
                            Question.survey_id == survey.id
                        )
                    )
                    questions_count = q_count.scalar() or 0

                result = InlineQueryResultArticle(
                    id=str(survey.id),
                    title=f"📋 {survey.title}",
                    description=f"{survey.description or 'Нет описания'} ({questions_count} вопросов)",
                    input_message_content=InputTextMessageContent(
                        message_text=f"📋 <b>{survey.title}</b>\n\n"
                        f"{survey.description or 'Без описания'}\n\n"
                        f"📊 Вопросов: {questions_count}\n"
                        f"🔗 Нажмите кнопку ниже, чтобы пройти опрос"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🚀 Начать опрос",
                                    callback_data=f"start_survey_{survey.id}",
                                )
                            ]
                        ]
                    ),
                )
                results.append(result)

            # Add help result if no surveys found
            if not results:
                help_result = InlineQueryResultArticle(
                    id="help",
                    title="📚 Помощь",
                    description="Введите название опроса для поиска",
                    input_message_content=InputTextMessageContent(
                        message_text="🔍 <b>Поиск опросов</b>\n\n"
                        "Введите название опроса после @bot_name для поиска.\n"
                        "Например: <code>@quiz_bot математика</code>"
                    ),
                )
                results.append(help_result)

            await query.answer(results, cache_time=30)

        except Exception as e:
            logger.error(f"Error handling inline query: {e}")
            await query.answer([], cache_time=0)

    # ======================
    # FSM SURVEY HANDLERS
    # ======================

    async def handle_start_survey(
        self, callback: types.CallbackQuery, state: FSMContext
    ) -> None:
        """Start taking a survey."""
        try:
            await callback.answer()
            survey_id = int(callback.data.split("_")[2])

            # Get survey with questions
            async with get_async_session() as session:
                stmt = (
                    select(Survey)
                    .options(selectinload(Survey.questions))
                    .where(Survey.id == survey_id)
                )
                result = await session.execute(stmt)
                survey = result.scalar_one_or_none()

                if not survey or not survey.is_active:
                    await callback.message.edit_text("❌ Опрос не найден или неактивен.")
                    return

                questions = sorted(survey.questions, key=lambda q: q.order)

                if not questions:
                    await callback.message.edit_text("❌ В опросе нет вопросов.")
                    return

            # Create user session
            session_id = str(uuid.uuid4())
            user_data = {
                "survey_id": survey_id,
                "survey_title": survey.title,
                "questions": [q.id for q in questions],
                "current_question": 0,
                "answers": {},
                "session_id": session_id,
            }

            await state.set_data(user_data)
            await state.set_state(SurveyStates.taking_survey)

            # Show first question
            await self.show_question(
                callback.message, questions[0], 0, len(questions), state
            )

        except Exception as e:
            logger.error(f"Error starting survey: {e}")
            await callback.message.edit_text("❌ Ошибка при запуске опроса.")

    async def show_question(
        self,
        message: types.Message,
        question: Question,
        current: int,
        total: int,
        state: FSMContext,
    ) -> None:
        """Display a question to the user."""
        try:
            progress = f"[{current + 1}/{total}]"

            text = f"📋 <b>{progress} {question.title}</b>\n\n"
            if question.description:
                text += f"{question.description}\n\n"

            # Create keyboard based on question type
            builder = InlineKeyboardBuilder()

            if question.question_type == QuestionType.YES_NO:
                builder.row(
                    InlineKeyboardButton(
                        text="✅ Да", callback_data=f"answer_yes_{question.id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Нет", callback_data=f"answer_no_{question.id}"
                    ),
                )
            elif question.question_type == QuestionType.RATING_1_10:
                # Create rating buttons
                for i in range(1, 11):
                    emoji = "⭐" if i <= 5 else "🌟"
                    builder.add(
                        InlineKeyboardButton(
                            text=f"{emoji} {i}",
                            callback_data=f"answer_rating_{question.id}_{i}",
                        )
                    )
                builder.adjust(5)  # 5 buttons per row
            elif question.question_type in [
                QuestionType.TEXT,
                QuestionType.EMAIL,
                QuestionType.PHONE,
            ]:
                text += "✍️ <i>Введите ваш ответ текстом:</i>"
                builder.row(
                    InlineKeyboardButton(
                        text="⏭️ Пропустить", callback_data=f"answer_skip_{question.id}"
                    )
                ) if not question.is_required else None
            else:
                # For other question types, show input prompt
                text += "✍️ <i>Введите ваш ответ:</i>"
                builder.row(
                    InlineKeyboardButton(
                        text="⏭️ Пропустить", callback_data=f"answer_skip_{question.id}"
                    )
                ) if not question.is_required else None

            # Add navigation buttons
            if current > 0:
                builder.row(
                    InlineKeyboardButton(
                        text="⬅️ Предыдущий", callback_data=f"nav_prev_{question.id}"
                    )
                )

            builder.row(
                InlineKeyboardButton(text="🚫 Отменить", callback_data="nav_cancel")
            )

            await state.set_state(SurveyStates.answering_question)

            if message.photo:
                await message.edit_caption(
                    caption=text, reply_markup=builder.as_markup()
                )
            else:
                await message.edit_text(text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error showing question: {e}")
            await message.edit_text("❌ Ошибка при отображении вопроса.")

    async def handle_answer_question(
        self, callback: types.CallbackQuery, state: FSMContext
    ) -> None:
        """Handle answer to a question."""
        try:
            await callback.answer()

            # Parse callback data
            parts = callback.data.split("_")
            answer_type = parts[1]
            question_id = int(parts[2])

            # Get state data
            data = await state.get_data()
            current_question_index = data.get("current_question", 0)

            # Process answer based on type
            answer_value = None
            if answer_type == "yes":
                answer_value = True
            elif answer_type == "no":
                answer_value = False
            elif answer_type == "rating":
                answer_value = int(parts[3])
            elif answer_type == "skip":
                answer_value = None

            # Save answer
            data["answers"][question_id] = answer_value
            await state.set_data(data)

            # Move to next question or finish
            await self.next_question(callback.message, state)

        except Exception as e:
            logger.error(f"Error handling answer: {e}")
            await callback.message.edit_text("❌ Ошибка при обработке ответа.")

    async def handle_text_answer(
        self, message: types.Message, state: FSMContext
    ) -> None:
        """Handle text answer to a question."""
        try:
            data = await state.get_data()
            current_question_index = data.get("current_question", 0)
            questions = data.get("questions", [])

            if current_question_index >= len(questions):
                return

            question_id = questions[current_question_index]

            # Get current question to validate answer
            async with get_async_session() as session:
                stmt = select(Question).where(Question.id == question_id)
                result = await session.execute(stmt)
                question = result.scalar_one_or_none()

                if not question:
                    await message.answer("❌ Вопрос не найден.")
                    return

                # Validate answer based on question type
                if question.question_type == QuestionType.EMAIL:
                    if "@" not in message.text or "." not in message.text:
                        await message.answer(
                            "❌ Пожалуйста, введите корректный email адрес."
                        )
                        return

                elif question.question_type == QuestionType.PHONE:
                    # Simple phone validation
                    cleaned_phone = "".join(filter(str.isdigit, message.text))
                    if len(cleaned_phone) < 10:
                        await message.answer(
                            "❌ Пожалуйста, введите корректный номер телефона."
                        )
                        return
                    message.text = cleaned_phone

            # Save text answer
            data["answers"][question_id] = message.text
            await state.set_data(data)

            # Confirm answer
            await self.confirm_answer(message, question_id, message.text, state)

        except Exception as e:
            logger.error(f"Error handling text answer: {e}")
            await message.answer("❌ Ошибка при обработке текстового ответа.")

    async def confirm_answer(
        self, message: types.Message, question_id: int, answer: str, state: FSMContext
    ) -> None:
        """Confirm user answer."""
        try:
            text = f"✅ <b>Ваш ответ:</b>\n\n{answer}\n\n<i>Подтвердите или измените ответ:</i>"

            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(
                    text="✅ Подтвердить", callback_data=f"confirm_yes_{question_id}"
                ),
                InlineKeyboardButton(
                    text="✏️ Изменить", callback_data=f"confirm_edit_{question_id}"
                ),
            )

            await state.set_state(SurveyStates.confirming_answer)
            await message.answer(text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error confirming answer: {e}")
            await message.answer("❌ Ошибка при подтверждении ответа.")

    async def handle_confirm_answer(
        self, callback: types.CallbackQuery, state: FSMContext
    ) -> None:
        """Handle answer confirmation."""
        try:
            await callback.answer()

            parts = callback.data.split("_")
            action = parts[1]
            question_id = int(parts[2])

            if action == "yes":
                # Confirmed, move to next question
                await callback.message.delete()
                await self.next_question(callback.message, state)
            elif action == "edit":
                # Edit answer, go back to answering state
                await callback.message.delete()
                await state.set_state(SurveyStates.answering_question)
                await callback.message.answer("✏️ Введите новый ответ:")

        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")
            await callback.message.edit_text("❌ Ошибка при обработке подтверждения.")

    async def next_question(self, message: types.Message, state: FSMContext) -> None:
        """Move to the next question or finish survey."""
        try:
            data = await state.get_data()
            current_question_index = data.get("current_question", 0)
            questions = data.get("questions", [])

            # Move to next question
            current_question_index += 1
            data["current_question"] = current_question_index
            await state.set_data(data)

            if current_question_index >= len(questions):
                # Survey completed
                await self.finish_survey(message, state)
            else:
                # Show next question
                question_id = questions[current_question_index]
                async with get_async_session() as session:
                    stmt = select(Question).where(Question.id == question_id)
                    result = await session.execute(stmt)
                    question = result.scalar_one_or_none()

                    if question:
                        await self.show_question(
                            message,
                            question,
                            current_question_index,
                            len(questions),
                            state,
                        )
                    else:
                        await message.answer("❌ Вопрос не найден.")

        except Exception as e:
            logger.error(f"Error moving to next question: {e}")
            await message.answer("❌ Ошибка при переходе к следующему вопросу.")

    async def finish_survey(self, message: types.Message, state: FSMContext) -> None:
        """Finish survey and save responses."""
        try:
            data = await state.get_data()
            survey_id = data.get("survey_id")
            survey_title = data.get("survey_title")
            answers = data.get("answers", {})
            session_id = data.get("session_id")

            # Save responses to database
            async with get_async_session() as session:
                # Get user if authenticated
                user_id = None
                if hasattr(message.from_user, "id"):
                    user = await user_service.get_user_by_telegram_id(
                        session, message.from_user.id
                    )
                    user_id = user.id if user else None

                # Save each answer
                for question_id, answer_value in answers.items():
                    if answer_value is not None:
                        response = Response(
                            question_id=int(question_id),
                            user_id=user_id,
                            user_session_id=session_id,
                            answer={"value": answer_value},
                        )
                        session.add(response)

                await session.commit()

            # Show completion message
            text = "🎉 <b>Опрос завершен!</b>\n\n"
            text += f"📋 <b>{survey_title}</b>\n"
            text += f"✅ Ответов дано: {len([a for a in answers.values() if a is not None])}\n\n"
            text += "Спасибо за участие! 💚"

            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(
                    text="📋 Другие опросы", callback_data="list_surveys"
                ),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
            )

            await state.clear()
            await message.answer(text, reply_markup=builder.as_markup())

            # Send notification to admin if enabled
            await self.send_admin_notification(
                f"🎉 Новый ответ на опрос!\n\n"
                f"📋 {survey_title}\n"
                f"👤 Пользователь: {message.from_user.first_name or 'Неизвестно'}\n"
                f"📊 Ответов: {len([a for a in answers.values() if a is not None])}"
            )

        except Exception as e:
            logger.error(f"Error finishing survey: {e}")
            await message.answer("❌ Ошибка при завершении опроса.")

    async def handle_navigation(
        self, callback: types.CallbackQuery, state: FSMContext
    ) -> None:
        """Handle navigation buttons."""
        try:
            await callback.answer()

            parts = callback.data.split("_")
            action = parts[1]

            if action == "cancel":
                await state.clear()
                await callback.message.edit_text("🚫 Опрос отменен.")
            elif action == "prev":
                data = await state.get_data()
                current_question_index = data.get("current_question", 0)

                if current_question_index > 0:
                    current_question_index -= 1
                    data["current_question"] = current_question_index
                    await state.set_data(data)

                    # Show previous question
                    questions = data.get("questions", [])
                    question_id = questions[current_question_index]

                    async with get_async_session() as session:
                        stmt = select(Question).where(Question.id == question_id)
                        result = await session.execute(stmt)
                        question = result.scalar_one_or_none()

                        if question:
                            await self.show_question(
                                callback.message,
                                question,
                                current_question_index,
                                len(questions),
                                state,
                            )

        except Exception as e:
            logger.error(f"Error handling navigation: {e}")
            await callback.message.edit_text("❌ Ошибка навигации.")

    async def cancel_command(self, message: types.Message, state: FSMContext) -> None:
        """Handle /cancel command."""
        current_state = await state.get_state()
        if current_state is None:
            await message.answer("🤔 Нечего отменять.")
            return

        await state.clear()
        await message.answer(
            "🚫 Действие отменено.", reply_markup=types.ReplyKeyboardRemove()
        )

    # ======================
    # BASIC COMMAND HANDLERS
    # ======================

    async def start_command(self, message: types.Message) -> None:
        """Handle /start command."""
        user_data = message.from_user

        # Create or get user
        async with get_async_session() as session:
            user = await self.create_or_get_telegram_user(session, user_data)

            if not user:
                await message.answer("❌ Ошибка регистрации. Попробуйте позже.")
                return

            # Generate access token
            access_token = jwt_service.create_access_token(
                user_id=user.id,
                telegram_id=user_data.id,
                username=user_data.username,
                is_admin=user.is_admin,
            )

        # Welcome message
        welcome_text = f"""🎯 <b>Добро пожаловать в Quiz App, {user.get_display_name()}!</b>

Это интерактивная платформа для создания и прохождения опросов.

🚀 <b>Что вы можете делать:</b>
• Проходить опросы прямо в Telegram
• Искать опросы через @bot_name запрос
• Получать результаты в PDF
• Создавать собственные опросы (для админов)

📱 Используйте кнопки ниже для навигации:"""

        # Create keyboard
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📋 Доступные опросы", callback_data="list_surveys"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🌐 Открыть веб-приложение",
                web_app=WebAppInfo(url=f"{self.webapp_url}?token={access_token}"),
            )
        )
        builder.row(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))

        # Add admin button for admins
        if user.is_admin:
            builder.row(
                InlineKeyboardButton(
                    text="⚙️ Панель администратора", callback_data="admin_panel"
                )
            )

        await message.answer(welcome_text, reply_markup=builder.as_markup())

    async def help_command(self, message: types.Message) -> None:
        """Handle /help command."""
        help_text = """🆘 <b>Помощь по Quiz App</b>

📋 <b>Доступные команды:</b>
• /start - Начать работу с ботом
• /help - Показать это сообщение
• /surveys - Список доступных опросов
• /admin - Панель администратора (только для админов)
• /cancel - Отменить текущее действие

🎯 <b>Как пройти опрос:</b>
1. Используйте команду /surveys или кнопку "📋 Доступные опросы"
2. Выберите интересующий вас опрос
3. Нажмите кнопку "🚀 Начать опрос"
4. Отвечайте на вопросы прямо в Telegram
5. Получите результаты в PDF формате

🔍 <b>Поиск опросов:</b>
Используйте @bot_name название_опроса для поиска опросов в любом чате

🔗 <b>Веб-приложение:</b>
Вы можете использовать полную веб-версию приложения через кнопку "🌐 Открыть веб-приложение"

❓ Если у вас есть вопросы, обратитесь к администратору."""

        await message.answer(help_text)

    async def surveys_command(self, message: types.Message) -> None:
        """Handle /surveys command."""
        await self.show_surveys_list(message)

    async def admin_command(self, message: types.Message) -> None:
        """Handle /admin command."""
        user_data = message.from_user

        # Check if user is admin
        async with get_async_session() as session:
            user = await user_service.get_user_by_telegram_id(session, user_data.id)

            if not user or not user.is_admin:
                await message.answer("❌ У вас нет прав администратора.")
                return

        await self.show_admin_panel(message)

    async def handle_list_surveys(self, callback: types.CallbackQuery) -> None:
        """Handle 'list_surveys' callback."""
        await callback.answer()
        await self.show_surveys_list(callback.message)

    async def handle_help(self, callback: types.CallbackQuery) -> None:
        """Handle 'help' callback."""
        await callback.answer()
        await self.help_command(callback.message)

    async def handle_admin_panel(self, callback: types.CallbackQuery) -> None:
        """Handle 'admin_panel' callback."""
        await callback.answer()

        # Check admin permissions
        user_data = callback.from_user
        async with get_async_session() as session:
            user = await user_service.get_user_by_telegram_id(session, user_data.id)

            if not user or not user.is_admin:
                await callback.message.answer("❌ У вас нет прав администратора.")
                return

        await self.show_admin_panel(callback.message)

    async def handle_admin_stats(self, callback: types.CallbackQuery) -> None:
        """Handle admin stats callback."""
        await callback.answer()
        await self.show_admin_stats(callback.message)

    async def handle_admin_surveys(self, callback: types.CallbackQuery) -> None:
        """Handle admin surveys callback."""
        await callback.answer()
        await self.show_admin_surveys(callback.message)

    async def handle_admin_users(self, callback: types.CallbackQuery) -> None:
        """Handle admin users callback."""
        await callback.answer()
        await self.show_admin_users(callback.message)

    async def handle_admin_reports(self, callback: types.CallbackQuery) -> None:
        """Handle admin reports callback."""
        await callback.answer()
        await self.show_admin_reports(callback.message)

    async def handle_survey_details(self, callback: types.CallbackQuery) -> None:
        """Handle survey details callback."""
        await callback.answer()
        survey_id = int(callback.data.split("_")[1])
        await self.show_survey_details(callback.message, survey_id)

    async def handle_text_message(self, message: types.Message) -> None:
        """Handle regular text messages."""
        text = message.text.lower()

        if "привет" in text or "hello" in text:
            await message.answer("👋 Привет! Используйте /start для начала работы.")
        elif "помощь" in text or "help" in text:
            await self.help_command(message)
        elif "опрос" in text or "survey" in text:
            await self.show_surveys_list(message)
        else:
            await message.answer(
                "🤔 Я не понимаю эту команду. Используйте /help для списка доступных команд."
            )

    async def create_or_get_telegram_user(
        self, session, user_data: types.User
    ) -> Optional[User]:
        """Create or get Telegram user from database."""
        try:
            # Try to get user by telegram_id
            user = await user_service.get_user_by_telegram_id(session, user_data.id)

            if user:
                return user

            # Create new user
            user_create = UserCreate(
                username=user_data.username or f"telegram_{user_data.id}",
                email=f"telegram_{user_data.id}@telegram.local",
                first_name=user_data.first_name or "",
                last_name=user_data.last_name or "",
                telegram_id=user_data.id,
                is_telegram_user=True,
            )

            user = await user_service.create_user(session, user_create)
            await session.commit()

            return user

        except Exception as e:
            logger.error(f"Error creating/getting Telegram user: {e}")
            return None

    async def show_surveys_list(self, message: types.Message) -> None:
        """Show list of available surveys."""
        async with get_async_session() as session:
            # Get active public surveys
            result = await session.execute(
                select(Survey).where(Survey.is_active == True, Survey.is_public == True)
            )
            surveys = result.scalars().all()

            if not surveys:
                await message.answer("📋 На данный момент нет доступных опросов.")
                return

            text = "📋 <b>Доступные опросы:</b>\n\n"

            builder = InlineKeyboardBuilder()

            for survey in surveys[:10]:  # Limit to 10 surveys
                text += f"• <b>{survey.title}</b>\n"
                if survey.description:
                    text += f"  {survey.description[:100]}{'...' if len(survey.description) > 100 else ''}\n"

            await message.answer(text, reply_markup=builder.as_markup())

    async def show_admin_panel(self, message: types.Message) -> None:
        """Show admin panel."""
        text = "⚙️ <b>Панель администратора</b>\n\n"
        text += "Выберите действие:"

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        )
        builder.row(
            InlineKeyboardButton(text="📋 Опросы", callback_data="admin_surveys")
        )
        builder.row(
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        )
        builder.row(
            InlineKeyboardButton(text="📈 Отчеты", callback_data="admin_reports")
        )

        await message.answer(text, reply_markup=builder.as_markup())

    async def show_admin_stats(self, message: types.Message) -> None:
        """Show admin statistics."""
        text = "📊 <b>Статистика</b>\n\n"
        text += "• Общее количество пользователей: N/A\n"
        text += "• Активных опросов: N/A\n"
        text += "• Завершенных опросов: N/A\n"
        text += "• Ответов получено: N/A\n"

        await message.answer(text)

    async def show_admin_surveys(self, message: types.Message) -> None:
        """Show admin surveys management."""
        text = "📋 <b>Управление опросами</b>\n\n"
        text += "Здесь будет список опросов для управления."

        await message.answer(text)

    async def show_admin_users(self, message: types.Message) -> None:
        """Show admin users management."""
        text = "👥 <b>Управление пользователями</b>\n\n"
        text += "Здесь будет список пользователей для управления."

        await message.answer(text)

    async def show_admin_reports(self, message: types.Message) -> None:
        """Show admin reports."""
        text = "📈 <b>Отчеты</b>\n\n"
        text += "Здесь будут доступны отчеты и аналитика."

        await message.answer(text)

    async def show_survey_details(self, message: types.Message, survey_id: int) -> None:
        """Show survey details."""
        text = f"📋 <b>Детали опроса #{survey_id}</b>\n\n"
        text += "Здесь будут подробности опроса."

        await message.answer(text)


# ======================
# TELEGRAM SERVICE SINGLETON
# ======================

# Global instance of TelegramService
_telegram_service: Optional[TelegramService] = None


async def get_telegram_service() -> TelegramService:
    """Get the global TelegramService instance."""
    global _telegram_service

    if _telegram_service is None:
        _telegram_service = TelegramService()
        await _telegram_service.initialize()

    return _telegram_service


def get_telegram_service_sync() -> TelegramService:
    """Get the global TelegramService instance synchronously."""
    global _telegram_service

    if _telegram_service is None:
        _telegram_service = TelegramService()
        # Note: Initialize must be called separately in async context

    return _telegram_service
