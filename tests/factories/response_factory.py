"""
Фабрики для создания тестовых ответов.
"""

import factory
from faker import Faker
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from models.response import Response

fake = Faker(["en_US", "ru_RU"])


class ResponseFactory(factory.Factory):
    class Meta:
        model = Response

    question_id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Sequence(lambda n: n + 1)
    user_session_id = factory.Sequence(lambda n: f"session-{n}")
    answer = {"text": "Test answer"}


class TextResponseFactory(ResponseFactory):
    answer = factory.LazyFunction(lambda: {"text": fake.text(max_nb_chars=200)})


class RatingResponseFactory(ResponseFactory):
    answer = factory.LazyFunction(lambda: {"rating": fake.random_int(min=1, max=10)})
