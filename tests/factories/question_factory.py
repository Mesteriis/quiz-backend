"""
Фабрики для создания тестовых вопросов.
"""

from pathlib import Path
import sys

import factory
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.question import Question, QuestionType

fake = Faker(["en_US", "ru_RU"])


class QuestionFactory(factory.Factory):
    class Meta:
        model = Question

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=200)
    question_type = QuestionType.TEXT
    is_required = True
    order = factory.Sequence(lambda n: n + 1)
    options = None
    survey_id = factory.Sequence(lambda n: n + 1)


class TextQuestionFactory(QuestionFactory):
    question_type = QuestionType.TEXT


class RatingQuestionFactory(QuestionFactory):
    question_type = QuestionType.RATING_1_10
    options = {"min": 1, "max": 10, "step": 1}
