"""
Print orchestration functions that coordinate between learning managers and print formatting.

This module contains functions that need to import from both learning and prints modules.
By keeping these separate from print_manager.py, we avoid circular import issues.
"""

import json
import os
import random
from datetime import datetime
from logging import getLogger

from flask import current_app, request

from dashboard.src.ai.clients.ollama_client import OllamaClient
from dashboard.src.ai.clients.openai_client import OpenAIClient
from dashboard.src.calendars.calendar_manager import CalendarEventManager
from dashboard.src.learning.learning_manager import (
    CardManager,
    QuizManager,
    ReminderManager,
    RoutineTaskManager,
    SubjectManager,
)
from dashboard.src.prints.print_manager import PrintManager
from dashboard.src.prints.receipts.formatter import ReceiptFormatter
from dashboard.src.prints.receipts.section import MultiElementSection
from dashboard.src.weather.clients.base import get_weather_client
from dashboard.src.weather.clients.models.open_weather import OpenWeather

logger = getLogger(__name__)


def print_tasks():
    """
    Build and return the daily tasks receipt data.

    This orchestrates data from weather, calendar, routines, reminders,
    subjects, and cards to build a comprehensive daily printout.

    Returns:
        Dictionary with formatted receipt data ready for printing.
    """
    receipt_formatter = ReceiptFormatter()

    # weather
    weather_client = get_weather_client("open-weather")
    current_weather = weather_client.get_current_weather(current_app.config["LAT_LONG"])
    forecast_weather = weather_client.get_forecast_weather(
        current_app.config["LAT_LONG"]
    )
    weather = OpenWeather.from_current_and_forecast(current_weather, forecast_weather)

    weather_items = PrintManager.extract_weather(weather)
    receipt_formatter.add_section(
        MultiElementSection(
            title="Weather",
            items=weather_items,
            bullet="",
        )
    )

    # Sync and get calendar events from database
    today = datetime.now()
    today_date = today.date()

    calendar_manager = CalendarEventManager(request.db)
    calendars = [current_app.config["MAIN_CALENDAR"], "Chores"]

    # Sync events from CalDAV to database
    sync_result = calendar_manager.sync_events(
        calendars,
        today.replace(hour=0, minute=0, second=0, microsecond=0),
        today.replace(hour=23, minute=59, second=59, microsecond=0),
    )
    logger.info(f"Calendar sync result: {sync_result}")

    # Get events from database
    db_events = calendar_manager.get_events_for_date(today_date)
    logger.info(f"Events from database: {len(db_events)}")

    # Insert birthdays
    birthdays, non_birthday_events = PrintManager.extract_birthdays_from_db(db_events)
    if birthdays:
        receipt_formatter.add_section(MultiElementSection(" Birthdays ", birthdays))

    # Insert calendar events
    all_day_events, timed_events = PrintManager.extract_events_from_db(
        non_birthday_events, today_date
    )
    if all_day_events:
        receipt_formatter.add_section(
            MultiElementSection(
                " All Day Events ",
                all_day_events,
                bullet="-",
            )
        )

    if timed_events:
        receipt_formatter.add_section(
            MultiElementSection(
                " Calendar ",
                timed_events,
                bullet="*",
                formatter=lambda t: f"{t[0]} - {t[1]}",
            )
        )

    # Insert routine tasks
    routine_manager = RoutineTaskManager(request.db)
    routine_tasks = routine_manager.get_tasks_for_date(today_date)

    if routine_tasks:
        # Mark interval-based tasks as shown
        for task in routine_tasks:
            if task.interval_days:
                routine_manager.mark_task_shown(task.id, today_date)

        # Format tasks with checkboxes
        routine_items = [f"[ ] {task.title}" for task in routine_tasks]
        receipt_formatter.add_section(
            MultiElementSection(
                " Routines ",
                routine_items,
                bullet="",
            )
        )

    # Insert reminders
    reminder_manager = ReminderManager(request.db)
    active_reminders = reminder_manager.get_active_reminders()

    if active_reminders:
        # Mark reminders as shown
        for reminder in active_reminders:
            reminder_manager.mark_reminder_shown(reminder.id, today_date)

        reminder_items = [reminder.title for reminder in active_reminders]
        receipt_formatter.add_section(
            MultiElementSection(
                " Reminders ",
                reminder_items,
                bullet="o ",
            )
        )

    # Insert studies (spaced repetition)
    subject_manager = SubjectManager(request.db)
    study_subjects = subject_manager.get_subjects_for_study_today(
        today_date, max_subjects=1
    )

    if study_subjects:
        # Mark subjects as studied
        for subject in study_subjects:
            subject_manager.mark_subject_studied(subject.id, today_date)

        study_items = [f"Study: {subject.name}" for subject in study_subjects]
        receipt_formatter.add_section(
            MultiElementSection(
                " Today's Study ",
                study_items,
                bullet="*",
            )
        )

    # Insert questions
    card_manager = CardManager(request.db)
    non_grokked_cards = card_manager.get_non_grokked_cards()

    if non_grokked_cards:
        card_items = [card.title for card in non_grokked_cards]
        receipt_formatter.add_section(
            MultiElementSection(
                " Pop Quiz ",
                card_items,
                bullet="[] ",
            )
        )

    # Insert tasks
    final = receipt_formatter.build()
    return final


def print_pop_quiz(
    db,
    num_questions: int = None,
    include_answers: bool = True,
) -> dict:
    """
    Print a pop quiz with randomized questions.

    This is the main entry point for printing pop quizzes. It can be called
    from HTTP endpoints, voice assistants, or any other interface.

    Args:
        db: Database session
        num_questions: Number of questions to include. If None, includes all available.
        include_answers: Whether to print the answers after the quiz.

    Returns:
        Dictionary with:
            - status: "ok" or "error"
            - quiz_id: ID of the created quiz (or None if no questions)
            - question_count: Number of questions in the quiz
            - message: Human-readable status message
    """
    card_manager = CardManager(db)
    non_grokked_cards = card_manager.get_non_grokked_cards()

    if not non_grokked_cards:
        return {
            "status": "ok",
            "quiz_id": None,
            "question_count": 0,
            "message": "No questions available for quiz",
        }

    # Randomize the order
    randomized_cards = list(non_grokked_cards)
    random.shuffle(randomized_cards)

    # Limit to requested number of questions
    if num_questions is not None and num_questions > 0:
        randomized_cards = randomized_cards[:num_questions]

    # Create quiz record in database
    quiz_manager = QuizManager(db)
    quiz = quiz_manager.create_quiz(randomized_cards)

    # Build and send quiz to printer
    rabbit_client = current_app.config["message_broker_client"]

    quiz_data = PrintManager.build_pop_quiz(randomized_cards, quiz_id=quiz.id)
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(quiz_data)
    )

    # Print answers if requested
    if include_answers:
        answers_data = PrintManager.build_pop_quiz_answers(randomized_cards)
        rabbit_client.send_message(
            exchange="", routing_key="text_print", body=json.dumps(answers_data)
        )

    return {
        "status": "ok",
        "quiz_id": quiz.id,
        "question_count": len(randomized_cards),
        "message": f"Printed pop quiz with {len(randomized_cards)} questions",
    }


def reprint_quiz(
    db, quiz_id: int, include_answers: bool = True, randomize: bool = True
) -> dict:
    """
    Reprint a previously generated quiz.

    Args:
        db: Database session
        quiz_id: ID of the quiz to reprint
        include_answers: Whether to also print answers (default True)
        randomize: Whether to randomize question order (default True)

    Returns:
        Dictionary with:
            - status: "ok" or "error"
            - quiz_id: ID of the quiz
            - question_count: Number of questions in the quiz
            - message: Human-readable status message
    """
    quiz_manager = QuizManager(db)
    quiz = quiz_manager.get_quiz(quiz_id)

    if not quiz:
        return {
            "status": "error",
            "quiz_id": quiz_id,
            "question_count": 0,
            "message": f"Quiz #{quiz_id} not found",
        }

    # Get the cards in quiz order
    questions = quiz_manager.get_quiz_questions(quiz_id)
    cards = [q.card for q in questions]

    if not cards:
        return {
            "status": "ok",
            "quiz_id": quiz_id,
            "question_count": 0,
            "message": f"Quiz #{quiz_id} has no questions",
        }

    # Randomize order if requested
    if randomize:
        cards = list(cards)
        random.shuffle(cards)

    # Build and send quiz to printer
    rabbit_client = current_app.config["message_broker_client"]
    quiz_data = PrintManager.build_pop_quiz(cards, quiz_id=quiz_id)
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(quiz_data)
    )

    if include_answers:
        answers_data = PrintManager.build_pop_quiz_answers(cards)
        rabbit_client.send_message(
            exchange="", routing_key="text_print", body=json.dumps(answers_data)
        )

    return {
        "status": "ok",
        "quiz_id": quiz_id,
        "question_count": len(cards),
        "message": f"Reprinted quiz #{quiz_id} ({len(cards)} questions)",
    }


def print_quiz_answers(db, quiz_id: int) -> dict:
    """
    Print the answers for a specific quiz.

    Args:
        db: Database session
        quiz_id: ID of the quiz to print answers for

    Returns:
        Dictionary with:
            - status: "ok" or "error"
            - quiz_id: ID of the quiz
            - question_count: Number of questions in the quiz
            - message: Human-readable status message
    """
    quiz_manager = QuizManager(db)
    quiz = quiz_manager.get_quiz(quiz_id)

    if not quiz:
        return {
            "status": "error",
            "quiz_id": quiz_id,
            "question_count": 0,
            "message": f"Quiz #{quiz_id} not found",
        }

    # Get the cards in quiz order
    questions = quiz_manager.get_quiz_questions(quiz_id)
    cards = [q.card for q in questions]

    if not cards:
        return {
            "status": "ok",
            "quiz_id": quiz_id,
            "question_count": 0,
            "message": f"Quiz #{quiz_id} has no questions",
        }

    # Build and send answers to printer
    rabbit_client = current_app.config["message_broker_client"]
    answers_data = PrintManager.build_pop_quiz_answers(cards)
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(answers_data)
    )

    return {
        "status": "ok",
        "quiz_id": quiz_id,
        "question_count": len(cards),
        "message": f"Printed answers for quiz #{quiz_id} ({len(cards)} questions)",
    }


def print_voice_response(audio_path: str) -> dict:
    """
    Transcribe an audio file, send the transcription to the LLM, and print the response.

    Args:
        audio_path: Local path to the audio file to transcribe.

    Returns:
        Dictionary with transcription and llm_response.
    """
    openai_client = OpenAIClient()
    filename = os.path.basename(audio_path)
    with open(audio_path, "rb") as f:
        transcription = openai_client.transcribe(f, filename=filename)
    logger.info(f"Transcribed audio: {transcription!r}")

    ollama_client = OllamaClient()
    llm_response = ollama_client.generate_response(transcription)
    logger.info(f"LLM response: {llm_response!r}")

    receipt_data = PrintManager.print_text(llm_response.strip().splitlines())
    rabbit_client = current_app.config["message_broker_client"]
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(receipt_data)
    )

    return {"transcription": transcription, "llm_response": llm_response}
