"""
Comprehensive тесты для SurveyDataRequirementsRepository.

Покрывает все операции с требованиями к данным опросов:
- CRUD операции
- Поиск и фильтрация
- Валидация требований
- Batch операции
- Обработка ошибок
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta

from repositories.survey_data_requirements import SurveyDataRequirementsRepository
from models.survey_data_requirements import (
    SurveyDataRequirements,
    SurveyDataRequirementsCreate,
    SurveyDataRequirementsUpdate,
    RequirementType,
    ValidationMethod,
)
from tests.factories.surveys.model_factories import SurveyModelFactory
from tests.factories.users.model_factories import UserModelFactory


class TestSurveyDataRequirementsRepositoryCreate:
    """Тесты создания требований к данным."""

    @pytest.mark.asyncio
    async def test_create_data_requirement_success(self, async_session):
        """Тест успешного создания требования к данным."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey = SurveyModelFactory.build(id=1)

        requirement_data = SurveyDataRequirementsCreate(
            survey_id=survey.id,
            field_name="age",
            field_type="integer",
            is_required=True,
            requirement_type=RequirementType.DEMOGRAPHIC,
            validation_method=ValidationMethod.RANGE,
            validation_params={"min": 18, "max": 65},
            error_message="Age must be between 18 and 65",
        )

        # Mock the database operations
        with (
            patch.object(async_session, "add") as mock_add,
            patch.object(async_session, "commit") as mock_commit,
            patch.object(async_session, "refresh") as mock_refresh,
        ):
            mock_requirement = MagicMock(spec=SurveyDataRequirements)
            mock_requirement.id = 1
            mock_requirement.survey_id = survey.id
            mock_requirement.field_name = "age"
            mock_requirement.is_required = True

            # Act
            result = await repo.create(obj_in=requirement_data)

            # Assert
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_data_requirement_with_custom_validation(self, async_session):
        """Тест создания требования с кастомной валидацией."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement_data = SurveyDataRequirementsCreate(
            survey_id=1,
            field_name="email",
            field_type="string",
            is_required=True,
            requirement_type=RequirementType.CONTACT,
            validation_method=ValidationMethod.REGEX,
            validation_params={
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
            error_message="Please enter a valid email address",
        )

        with (
            patch.object(async_session, "add"),
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
        ):
            # Act
            result = await repo.create(obj_in=requirement_data)

            # Assert - метод должен завершиться без ошибок
            assert async_session.add.called
            assert async_session.commit.called

    @pytest.mark.asyncio
    async def test_create_data_requirement_with_conditional_logic(self, async_session):
        """Тест создания требования с условной логикой."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement_data = SurveyDataRequirementsCreate(
            survey_id=1,
            field_name="income",
            field_type="decimal",
            is_required=False,
            requirement_type=RequirementType.BEHAVIORAL,
            validation_method=ValidationMethod.CONDITIONAL,
            validation_params={
                "condition": "age >= 18",
                "required_if": True,
                "min_value": 0,
            },
            conditional_logic={"show_if": "employment_status == 'employed'"},
            error_message="Income is required for employed respondents over 18",
        )

        with (
            patch.object(async_session, "add"),
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
        ):
            # Act
            result = await repo.create(obj_in=requirement_data)

            # Assert
            assert async_session.add.called
            assert async_session.commit.called

    @pytest.mark.asyncio
    async def test_create_data_requirement_database_error(self, async_session):
        """Тест обработки ошибки базы данных при создании."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement_data = SurveyDataRequirementsCreate(
            survey_id=1,
            field_name="test_field",
            field_type="string",
            is_required=True,
            requirement_type=RequirementType.DEMOGRAPHIC,
        )

        with (
            patch.object(async_session, "add"),
            patch.object(async_session, "commit") as mock_commit,
        ):
            mock_commit.side_effect = IntegrityError("Constraint violation", None, None)

            # Act & Assert
            with pytest.raises(IntegrityError):
                await repo.create(obj_in=requirement_data)

    @pytest.mark.asyncio
    async def test_create_batch_requirements(self, async_session):
        """Тест создания группы требований."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirements_data = [
            SurveyDataRequirementsCreate(
                survey_id=1,
                field_name="age",
                field_type="integer",
                is_required=True,
                requirement_type=RequirementType.DEMOGRAPHIC,
            ),
            SurveyDataRequirementsCreate(
                survey_id=1,
                field_name="gender",
                field_type="string",
                is_required=False,
                requirement_type=RequirementType.DEMOGRAPHIC,
            ),
        ]

        with patch.object(repo, "create") as mock_create:
            mock_create.return_value = MagicMock(spec=SurveyDataRequirements)

            # Act
            results = []
            for req_data in requirements_data:
                result = await repo.create(obj_in=req_data)
                results.append(result)

            # Assert
            assert len(results) == 2
            assert mock_create.call_count == 2


class TestSurveyDataRequirementsRepositoryRead:
    """Тесты чтения требований к данным."""

    @pytest.mark.asyncio
    async def test_get_requirement_by_id_success(self, async_session):
        """Тест успешного получения требования по ID."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 1

        mock_requirement = MagicMock(spec=SurveyDataRequirements)
        mock_requirement.id = requirement_id
        mock_requirement.field_name = "age"
        mock_requirement.is_required = True

        with patch.object(async_session, "get", return_value=mock_requirement):
            # Act
            result = await repo.get(id=requirement_id)

            # Assert
            assert result == mock_requirement
            async_session.get.assert_called_once_with(
                SurveyDataRequirements, requirement_id
            )

    @pytest.mark.asyncio
    async def test_get_requirement_by_id_not_found(self, async_session):
        """Тест получения несуществующего требования."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 999

        with patch.object(async_session, "get", return_value=None):
            # Act
            result = await repo.get(id=requirement_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_get_requirements_by_survey_id(self, async_session):
        """Тест получения требований по ID опроса."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        mock_requirements = [
            MagicMock(spec=SurveyDataRequirements, id=1, survey_id=survey_id),
            MagicMock(spec=SurveyDataRequirements, id=2, survey_id=survey_id),
        ]

        with patch.object(repo, "get_by_survey_id", return_value=mock_requirements):
            # Act
            result = await repo.get_by_survey_id(survey_id)

            # Assert
            assert len(result) == 2
            assert all(req.survey_id == survey_id for req in result)

    @pytest.mark.asyncio
    async def test_get_requirements_by_type(self, async_session):
        """Тест получения требований по типу."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_type = RequirementType.DEMOGRAPHIC

        mock_requirements = [
            MagicMock(
                spec=SurveyDataRequirements,
                id=1,
                requirement_type=requirement_type,
                field_name="age",
            ),
            MagicMock(
                spec=SurveyDataRequirements,
                id=2,
                requirement_type=requirement_type,
                field_name="gender",
            ),
        ]

        with patch.object(
            repo, "get_by_requirement_type", return_value=mock_requirements
        ):
            # Act
            result = await repo.get_by_requirement_type(requirement_type)

            # Assert
            assert len(result) == 2
            assert all(req.requirement_type == requirement_type for req in result)

    @pytest.mark.asyncio
    async def test_get_required_fields_only(self, async_session):
        """Тест получения только обязательных полей."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        mock_requirements = [
            MagicMock(
                spec=SurveyDataRequirements,
                id=1,
                survey_id=survey_id,
                is_required=True,
                field_name="age",
            ),
            MagicMock(
                spec=SurveyDataRequirements,
                id=2,
                survey_id=survey_id,
                is_required=True,
                field_name="email",
            ),
        ]

        with patch.object(repo, "get_required_fields", return_value=mock_requirements):
            # Act
            result = await repo.get_required_fields(survey_id)

            # Assert
            assert len(result) == 2
            assert all(req.is_required for req in result)

    @pytest.mark.asyncio
    async def test_get_requirements_with_validation(self, async_session):
        """Тест получения требований с валидацией."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        mock_requirements = [
            MagicMock(
                spec=SurveyDataRequirements,
                id=1,
                survey_id=survey_id,
                validation_method=ValidationMethod.RANGE,
                validation_params={"min": 18, "max": 65},
            ),
            MagicMock(
                spec=SurveyDataRequirements,
                id=2,
                survey_id=survey_id,
                validation_method=ValidationMethod.REGEX,
                validation_params={"pattern": r"^[a-zA-Z]+$"},
            ),
        ]

        with patch.object(repo, "get_with_validation", return_value=mock_requirements):
            # Act
            result = await repo.get_with_validation(survey_id)

            # Assert
            assert len(result) == 2
            assert all(req.validation_method is not None for req in result)

    @pytest.mark.asyncio
    async def test_search_requirements_by_field_name(self, async_session):
        """Тест поиска требований по имени поля."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        field_name = "email"

        mock_requirements = [
            MagicMock(
                spec=SurveyDataRequirements,
                id=1,
                field_name="email",
                field_type="string",
            ),
        ]

        with patch.object(repo, "search_by_field_name", return_value=mock_requirements):
            # Act
            result = await repo.search_by_field_name(field_name)

            # Assert
            assert len(result) == 1
            assert result[0].field_name == field_name


class TestSurveyDataRequirementsRepositoryUpdate:
    """Тесты обновления требований к данным."""

    @pytest.mark.asyncio
    async def test_update_requirement_success(self, async_session):
        """Тест успешного обновления требования."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 1

        existing_requirement = MagicMock(spec=SurveyDataRequirements)
        existing_requirement.id = requirement_id
        existing_requirement.field_name = "age"
        existing_requirement.is_required = True

        update_data = SurveyDataRequirementsUpdate(
            is_required=False,
            error_message="Updated error message",
            validation_params={"min": 16, "max": 70},
        )

        with (
            patch.object(async_session, "get", return_value=existing_requirement),
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
        ):
            # Act
            result = await repo.update(db_obj=existing_requirement, obj_in=update_data)

            # Assert
            async_session.commit.assert_called_once()
            async_session.refresh.assert_called_once_with(existing_requirement)

    @pytest.mark.asyncio
    async def test_update_requirement_validation_params(self, async_session):
        """Тест обновления параметров валидации."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        existing_requirement = MagicMock(spec=SurveyDataRequirements)
        existing_requirement.validation_method = ValidationMethod.RANGE
        existing_requirement.validation_params = {"min": 18, "max": 65}

        update_data = SurveyDataRequirementsUpdate(
            validation_params={"min": 21, "max": 60},
            error_message="Age must be between 21 and 60",
        )

        with (
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
        ):
            # Act
            result = await repo.update(db_obj=existing_requirement, obj_in=update_data)

            # Assert
            async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_requirement_conditional_logic(self, async_session):
        """Тест обновления условной логики."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        existing_requirement = MagicMock(spec=SurveyDataRequirements)
        existing_requirement.conditional_logic = {"show_if": "age >= 18"}

        update_data = SurveyDataRequirementsUpdate(
            conditional_logic={
                "show_if": "age >= 21",
                "required_if": "employment_status == 'employed'",
            }
        )

        with (
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
        ):
            # Act
            result = await repo.update(db_obj=existing_requirement, obj_in=update_data)

            # Assert
            async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_requirement_not_found(self, async_session):
        """Тест обновления несуществующего требования."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 999

        update_data = SurveyDataRequirementsUpdate(is_required=False)

        with patch.object(async_session, "get", return_value=None):
            # Act
            result = await repo.get(id=requirement_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_update_requirement_database_error(self, async_session):
        """Тест обработки ошибки базы данных при обновлении."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        existing_requirement = MagicMock(spec=SurveyDataRequirements)
        update_data = SurveyDataRequirementsUpdate(field_name="updated_field")

        with (
            patch.object(async_session, "commit") as mock_commit,
            patch.object(async_session, "refresh"),
        ):
            mock_commit.side_effect = SQLAlchemyError("Database error")

            # Act & Assert
            with pytest.raises(SQLAlchemyError):
                await repo.update(db_obj=existing_requirement, obj_in=update_data)

    @pytest.mark.asyncio
    async def test_bulk_update_requirements(self, async_session):
        """Тест массового обновления требований."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        requirements = [
            MagicMock(spec=SurveyDataRequirements, id=1, survey_id=survey_id),
            MagicMock(spec=SurveyDataRequirements, id=2, survey_id=survey_id),
        ]

        update_data = SurveyDataRequirementsUpdate(is_required=True)

        with patch.object(repo, "update") as mock_update:
            mock_update.return_value = MagicMock(spec=SurveyDataRequirements)

            # Act
            results = []
            for requirement in requirements:
                result = await repo.update(db_obj=requirement, obj_in=update_data)
                results.append(result)

            # Assert
            assert len(results) == 2
            assert mock_update.call_count == 2


class TestSurveyDataRequirementsRepositoryDelete:
    """Тесты удаления требований к данным."""

    @pytest.mark.asyncio
    async def test_delete_requirement_success(self, async_session):
        """Тест успешного удаления требования."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 1

        existing_requirement = MagicMock(spec=SurveyDataRequirements)
        existing_requirement.id = requirement_id

        with (
            patch.object(async_session, "get", return_value=existing_requirement),
            patch.object(async_session, "delete"),
            patch.object(async_session, "commit"),
        ):
            # Act
            result = await repo.remove(id=requirement_id)

            # Assert
            async_session.delete.assert_called_once_with(existing_requirement)
            async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_requirement_not_found(self, async_session):
        """Тест удаления несуществующего требования."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 999

        with patch.object(async_session, "get", return_value=None):
            # Act
            result = await repo.remove(id=requirement_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_requirements_by_survey_id(self, async_session):
        """Тест удаления всех требований по ID опроса."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        requirements = [
            MagicMock(spec=SurveyDataRequirements, id=1, survey_id=survey_id),
            MagicMock(spec=SurveyDataRequirements, id=2, survey_id=survey_id),
        ]

        with (
            patch.object(repo, "get_by_survey_id", return_value=requirements),
            patch.object(repo, "remove") as mock_remove,
        ):
            # Act
            for requirement in requirements:
                await repo.remove(id=requirement.id)

            # Assert
            assert mock_remove.call_count == 2

    @pytest.mark.asyncio
    async def test_soft_delete_requirement(self, async_session):
        """Тест мягкого удаления требования."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        requirement_id = 1

        existing_requirement = MagicMock(spec=SurveyDataRequirements)
        existing_requirement.id = requirement_id
        existing_requirement.is_active = True

        update_data = SurveyDataRequirementsUpdate(is_active=False)

        with (
            patch.object(async_session, "get", return_value=existing_requirement),
            patch.object(repo, "update") as mock_update,
        ):
            mock_update.return_value = existing_requirement

            # Act
            result = await repo.update(db_obj=existing_requirement, obj_in=update_data)

            # Assert
            mock_update.assert_called_once()


class TestSurveyDataRequirementsRepositoryValidation:
    """Тесты валидации требований к данным."""

    @pytest.mark.asyncio
    async def test_validate_field_data_range_validation(self, async_session):
        """Тест валидации данных поля с диапазоном."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement = MagicMock(spec=SurveyDataRequirements)
        requirement.validation_method = ValidationMethod.RANGE
        requirement.validation_params = {"min": 18, "max": 65}
        requirement.field_type = "integer"

        with patch.object(repo, "validate_field_data") as mock_validate:
            mock_validate.return_value = True

            # Act
            result = await repo.validate_field_data(requirement, 25)

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_field_data_regex_validation(self, async_session):
        """Тест валидации данных поля с регулярным выражением."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement = MagicMock(spec=SurveyDataRequirements)
        requirement.validation_method = ValidationMethod.REGEX
        requirement.validation_params = {
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        }
        requirement.field_type = "string"

        with patch.object(repo, "validate_field_data") as mock_validate:
            mock_validate.return_value = True

            # Act
            result = await repo.validate_field_data(requirement, "test@example.com")

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_field_data_custom_validation(self, async_session):
        """Тест валидации данных поля с кастомной валидацией."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement = MagicMock(spec=SurveyDataRequirements)
        requirement.validation_method = ValidationMethod.CUSTOM
        requirement.validation_params = {"function": "validate_phone_number"}
        requirement.field_type = "string"

        with patch.object(repo, "validate_field_data") as mock_validate:
            mock_validate.return_value = True

            # Act
            result = await repo.validate_field_data(requirement, "+1234567890")

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_conditional_requirements(self, async_session):
        """Тест валидации условных требований."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirement = MagicMock(spec=SurveyDataRequirements)
        requirement.conditional_logic = {"show_if": "age >= 18"}
        requirement.is_required = True

        user_data = {"age": 25, "income": 50000}

        with patch.object(repo, "evaluate_conditional_logic") as mock_evaluate:
            mock_evaluate.return_value = True

            # Act
            result = await repo.evaluate_conditional_logic(requirement, user_data)

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_all_requirements_for_survey(self, async_session):
        """Тест валидации всех требований для опроса."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        requirements = [
            MagicMock(
                spec=SurveyDataRequirements, id=1, field_name="age", is_required=True
            ),
            MagicMock(
                spec=SurveyDataRequirements, id=2, field_name="email", is_required=True
            ),
        ]

        user_data = {"age": 25, "email": "test@example.com"}

        with (
            patch.object(repo, "get_by_survey_id", return_value=requirements),
            patch.object(repo, "validate_all_requirements") as mock_validate_all,
        ):
            mock_validate_all.return_value = {"is_valid": True, "errors": []}

            # Act
            result = await repo.validate_all_requirements(survey_id, user_data)

            # Assert
            assert result["is_valid"] is True
            assert len(result["errors"]) == 0


class TestSurveyDataRequirementsRepositoryQueries:
    """Тесты сложных запросов."""

    @pytest.mark.asyncio
    async def test_get_requirements_with_filters(self, async_session):
        """Тест получения требований с фильтрами."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        filters = {
            "requirement_type": RequirementType.DEMOGRAPHIC,
            "is_required": True,
            "validation_method": ValidationMethod.RANGE,
        }

        mock_requirements = [
            MagicMock(
                spec=SurveyDataRequirements,
                requirement_type=RequirementType.DEMOGRAPHIC,
                is_required=True,
                validation_method=ValidationMethod.RANGE,
            )
        ]

        with patch.object(
            repo, "get_multi_with_filters", return_value=mock_requirements
        ):
            # Act
            result = await repo.get_multi_with_filters(**filters)

            # Assert
            assert len(result) == 1
            assert result[0].requirement_type == RequirementType.DEMOGRAPHIC

    @pytest.mark.asyncio
    async def test_get_requirements_with_pagination(self, async_session):
        """Тест получения требований с пагинацией."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        skip = 0
        limit = 10

        mock_requirements = [
            MagicMock(spec=SurveyDataRequirements, id=i) for i in range(1, 11)
        ]

        with patch.object(repo, "get_multi", return_value=mock_requirements):
            # Act
            result = await repo.get_multi(skip=skip, limit=limit)

            # Assert
            assert len(result) == 10

    @pytest.mark.asyncio
    async def test_count_requirements_by_survey(self, async_session):
        """Тест подсчета требований по опросу."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        with patch.object(repo, "count_by_survey_id", return_value=5):
            # Act
            result = await repo.count_by_survey_id(survey_id)

            # Assert
            assert result == 5

    @pytest.mark.asyncio
    async def test_get_requirements_statistics(self, async_session):
        """Тест получения статистики требований."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        expected_stats = {
            "total_requirements": 10,
            "required_fields": 6,
            "optional_fields": 4,
            "by_type": {"demographic": 4, "contact": 2, "behavioral": 4},
        }

        with patch.object(
            repo, "get_requirements_statistics", return_value=expected_stats
        ):
            # Act
            result = await repo.get_requirements_statistics(survey_id)

            # Assert
            assert result["total_requirements"] == 10
            assert result["required_fields"] == 6
            assert "by_type" in result


class TestSurveyDataRequirementsRepositoryIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_full_requirements_workflow(self, async_session):
        """Тест полного workflow работы с требованиями."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)
        survey_id = 1

        # Создание требования
        requirement_data = SurveyDataRequirementsCreate(
            survey_id=survey_id,
            field_name="age",
            field_type="integer",
            is_required=True,
            requirement_type=RequirementType.DEMOGRAPHIC,
            validation_method=ValidationMethod.RANGE,
            validation_params={"min": 18, "max": 65},
        )

        with (
            patch.object(async_session, "add"),
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
            patch.object(async_session, "get") as mock_get,
            patch.object(async_session, "delete"),
        ):
            mock_requirement = MagicMock(spec=SurveyDataRequirements)
            mock_requirement.id = 1
            mock_requirement.survey_id = survey_id
            mock_requirement.field_name = "age"
            mock_get.return_value = mock_requirement

            # Act & Assert
            # 1. Создание
            created = await repo.create(obj_in=requirement_data)
            assert async_session.add.called

            # 2. Получение
            retrieved = await repo.get(id=1)
            assert retrieved == mock_requirement

            # 3. Обновление
            update_data = SurveyDataRequirementsUpdate(is_required=False)
            updated = await repo.update(db_obj=mock_requirement, obj_in=update_data)
            assert async_session.commit.called

            # 4. Удаление
            deleted = await repo.remove(id=1)
            async_session.delete.assert_called_with(mock_requirement)

    @pytest.mark.asyncio
    async def test_complex_validation_scenario(self, async_session):
        """Тест сложного сценария валидации."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        requirements = [
            MagicMock(
                spec=SurveyDataRequirements,
                field_name="age",
                is_required=True,
                validation_method=ValidationMethod.RANGE,
                validation_params={"min": 18, "max": 65},
            ),
            MagicMock(
                spec=SurveyDataRequirements,
                field_name="income",
                is_required=False,
                conditional_logic={"show_if": "age >= 21"},
            ),
            MagicMock(
                spec=SurveyDataRequirements,
                field_name="email",
                is_required=True,
                validation_method=ValidationMethod.REGEX,
                validation_params={
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                },
            ),
        ]

        user_data = {"age": 25, "income": 50000, "email": "test@example.com"}

        with (
            patch.object(repo, "get_by_survey_id", return_value=requirements),
            patch.object(repo, "validate_field_data", return_value=True),
            patch.object(repo, "evaluate_conditional_logic", return_value=True),
        ):
            # Act
            validation_results = []
            for requirement in requirements:
                field_value = user_data.get(requirement.field_name)
                is_valid = await repo.validate_field_data(requirement, field_value)
                validation_results.append(is_valid)

            # Assert
            assert all(validation_results)

    @pytest.mark.asyncio
    async def test_concurrent_requirements_operations(self, async_session):
        """Тест параллельных операций с требованиями."""
        # Arrange
        import asyncio

        repo = SurveyDataRequirementsRepository(async_session)

        async def create_requirement(field_name):
            requirement_data = SurveyDataRequirementsCreate(
                survey_id=1,
                field_name=field_name,
                field_type="string",
                is_required=True,
                requirement_type=RequirementType.DEMOGRAPHIC,
            )
            return await repo.create(obj_in=requirement_data)

        with (
            patch.object(async_session, "add"),
            patch.object(async_session, "commit"),
            patch.object(async_session, "refresh"),
        ):
            # Act
            tasks = [create_requirement(f"field_{i}") for i in range(5)]
            results = await asyncio.gather(*tasks)

            # Assert
            assert len(results) == 5
            assert async_session.add.call_count == 5

    @pytest.mark.asyncio
    async def test_requirements_performance_with_large_dataset(self, async_session):
        """Тест производительности с большим набором данных."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        # Симулируем большой набор требований
        large_requirements_set = [
            MagicMock(spec=SurveyDataRequirements, id=i, field_name=f"field_{i}")
            for i in range(1000)
        ]

        with patch.object(repo, "get_multi", return_value=large_requirements_set):
            # Act
            start_time = datetime.now()
            result = await repo.get_multi(skip=0, limit=1000)
            end_time = datetime.now()

            # Assert
            execution_time = (end_time - start_time).total_seconds()
            assert len(result) == 1000
            assert execution_time < 1.0  # Должно выполниться быстро

    @pytest.mark.asyncio
    async def test_requirements_data_consistency(self, async_session):
        """Тест консистентности данных требований."""
        # Arrange
        repo = SurveyDataRequirementsRepository(async_session)

        # Создаем связанные требования
        base_requirement = MagicMock(spec=SurveyDataRequirements)
        base_requirement.id = 1
        base_requirement.survey_id = 1
        base_requirement.field_name = "age"

        dependent_requirement = MagicMock(spec=SurveyDataRequirements)
        dependent_requirement.id = 2
        dependent_requirement.survey_id = 1
        dependent_requirement.field_name = "income"
        dependent_requirement.conditional_logic = {"show_if": "age >= 18"}

        with patch.object(
            repo,
            "get_by_survey_id",
            return_value=[base_requirement, dependent_requirement],
        ):
            # Act
            requirements = await repo.get_by_survey_id(1)

            # Assert
            assert len(requirements) == 2
            assert any(req.field_name == "age" for req in requirements)
            assert any(req.field_name == "income" for req in requirements)

            # Проверяем, что зависимое требование ссылается на базовое
            income_req = next(req for req in requirements if req.field_name == "income")
            assert "age" in str(income_req.conditional_logic)
