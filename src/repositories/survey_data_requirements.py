"""
SurveyDataRequirements repository for the Quiz App.

This module provides the survey data requirements repository with specific methods
for managing survey data collection requirements and GDPR compliance settings.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.survey_data_requirements import SurveyDataRequirements
from schemas.survey_data_requirements import (
    SurveyDataRequirementsCreate,
    SurveyDataRequirementsUpdate,
)
from .base import BaseRepository


class SurveyDataRequirementsRepository(
    BaseRepository[
        SurveyDataRequirements,
        SurveyDataRequirementsCreate,
        SurveyDataRequirementsUpdate,
    ]
):
    """
    SurveyDataRequirements repository with specific data requirements operations.

    Inherits from BaseRepository and adds specific methods
    for managing survey data collection requirements and GDPR compliance.
    """

    def __init__(self, db: AsyncSession):
        """Initialize SurveyDataRequirementsRepository with database session."""
        super().__init__(SurveyDataRequirements, db)

    async def get_by_survey_id(
        self, survey_id: int
    ) -> Optional[SurveyDataRequirements]:
        """
        Get data requirements for a survey.

        Args:
            survey_id: Survey ID

        Returns:
            SurveyDataRequirements instance or None
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.survey_id == survey_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_with_survey_details(
        self, survey_id: int
    ) -> Optional[SurveyDataRequirements]:
        """
        Get data requirements with survey details.

        Args:
            survey_id: Survey ID

        Returns:
            SurveyDataRequirements with survey data or None
        """
        query = (
            select(SurveyDataRequirements)
            .options(selectinload(SurveyDataRequirements.survey))
            .where(SurveyDataRequirements.survey_id == survey_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_or_update_requirements(
        self, survey_id: int, requirements_data: Dict[str, Any]
    ) -> SurveyDataRequirements:
        """
        Create or update data requirements for a survey.

        Args:
            survey_id: Survey ID
            requirements_data: Requirements data

        Returns:
            SurveyDataRequirements instance
        """
        existing = await self.get_by_survey_id(survey_id)

        if existing:
            # Update existing requirements
            update_data = {**requirements_data}

            from schemas.survey_data_requirements import SurveyDataRequirementsUpdate

            requirements_update = SurveyDataRequirementsUpdate(**update_data)
            return await self.update(db_obj=existing, obj_in=requirements_update)
        else:
            # Create new requirements
            create_data = {
                "survey_id": survey_id,
                **requirements_data,
            }

            from schemas.survey_data_requirements import SurveyDataRequirementsCreate

            requirements_create = SurveyDataRequirementsCreate(**create_data)
            return await self.create(obj_in=requirements_create)

    async def get_surveys_requiring_location(self) -> List[SurveyDataRequirements]:
        """
        Get surveys that require location data.

        Returns:
            List of SurveyDataRequirements that require location
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.requires_location == True
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_surveys_requiring_personal_data(self) -> List[SurveyDataRequirements]:
        """
        Get surveys that require personal data.

        Returns:
            List of SurveyDataRequirements that require personal data
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.requires_personal_data == True
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_surveys_requiring_precise_location(
        self,
    ) -> List[SurveyDataRequirements]:
        """
        Get surveys that require precise location data.

        Returns:
            List of SurveyDataRequirements that require precise location
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.requires_precise_location == True
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_surveys_requiring_technical_data(
        self,
    ) -> List[SurveyDataRequirements]:
        """
        Get surveys that require technical data.

        Returns:
            List of SurveyDataRequirements that require technical data
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.requires_technical_data == True
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_surveys_with_gdpr_compliance(self) -> List[SurveyDataRequirements]:
        """
        Get surveys with GDPR compliance enabled.

        Returns:
            List of SurveyDataRequirements with GDPR compliance
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.gdpr_compliant == True
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_surveys_with_consent_requirements(
        self,
    ) -> List[SurveyDataRequirements]:
        """
        Get surveys with specific consent requirements.

        Returns:
            List of SurveyDataRequirements with consent requirements
        """
        query = select(SurveyDataRequirements).where(
            SurveyDataRequirements.consent_required.isnot(None)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_data_requirements_summary(self) -> Dict[str, Any]:
        """
        Get summary of data requirements across all surveys.

        Returns:
            Dictionary with data requirements statistics
        """
        # Total surveys with requirements
        total_query = select(func.count(SurveyDataRequirements.id))
        total_result = await self.db.execute(total_query)
        total_surveys = total_result.scalar() or 0

        # Surveys requiring location
        location_query = select(func.count(SurveyDataRequirements.id)).where(
            SurveyDataRequirements.requires_location == True
        )
        location_result = await self.db.execute(location_query)
        location_surveys = location_result.scalar() or 0

        # Surveys requiring precise location
        precise_location_query = select(func.count(SurveyDataRequirements.id)).where(
            SurveyDataRequirements.requires_precise_location == True
        )
        precise_location_result = await self.db.execute(precise_location_query)
        precise_location_surveys = precise_location_result.scalar() or 0

        # Surveys requiring personal data
        personal_data_query = select(func.count(SurveyDataRequirements.id)).where(
            SurveyDataRequirements.requires_personal_data == True
        )
        personal_data_result = await self.db.execute(personal_data_query)
        personal_data_surveys = personal_data_result.scalar() or 0

        # Surveys requiring technical data
        technical_data_query = select(func.count(SurveyDataRequirements.id)).where(
            SurveyDataRequirements.requires_technical_data == True
        )
        technical_data_result = await self.db.execute(technical_data_query)
        technical_data_surveys = technical_data_result.scalar() or 0

        # GDPR compliant surveys
        gdpr_query = select(func.count(SurveyDataRequirements.id)).where(
            SurveyDataRequirements.gdpr_compliant == True
        )
        gdpr_result = await self.db.execute(gdpr_query)
        gdpr_surveys = gdpr_result.scalar() or 0

        # Surveys with consent requirements
        consent_query = select(func.count(SurveyDataRequirements.id)).where(
            SurveyDataRequirements.consent_required.isnot(None)
        )
        consent_result = await self.db.execute(consent_query)
        consent_surveys = consent_result.scalar() or 0

        # Calculate percentages
        location_percentage = (
            (location_surveys / total_surveys * 100) if total_surveys > 0 else 0
        )
        precise_location_percentage = (
            (precise_location_surveys / total_surveys * 100) if total_surveys > 0 else 0
        )
        personal_data_percentage = (
            (personal_data_surveys / total_surveys * 100) if total_surveys > 0 else 0
        )
        technical_data_percentage = (
            (technical_data_surveys / total_surveys * 100) if total_surveys > 0 else 0
        )
        gdpr_percentage = (
            (gdpr_surveys / total_surveys * 100) if total_surveys > 0 else 0
        )
        consent_percentage = (
            (consent_surveys / total_surveys * 100) if total_surveys > 0 else 0
        )

        return {
            "total_surveys_with_requirements": total_surveys,
            "location_surveys": location_surveys,
            "location_percentage": location_percentage,
            "precise_location_surveys": precise_location_surveys,
            "precise_location_percentage": precise_location_percentage,
            "personal_data_surveys": personal_data_surveys,
            "personal_data_percentage": personal_data_percentage,
            "technical_data_surveys": technical_data_surveys,
            "technical_data_percentage": technical_data_percentage,
            "gdpr_surveys": gdpr_surveys,
            "gdpr_percentage": gdpr_percentage,
            "consent_surveys": consent_surveys,
            "consent_percentage": consent_percentage,
        }

    async def get_compliance_report(self) -> Dict[str, Any]:
        """
        Get compliance report for all surveys.

        Returns:
            Dictionary with compliance statistics
        """
        # Get all requirements
        all_requirements_query = select(SurveyDataRequirements)
        all_requirements_result = await self.db.execute(all_requirements_query)
        all_requirements = all_requirements_result.scalars().all()

        compliance_issues = []
        compliant_surveys = []

        for requirement in all_requirements:
            issues = []

            # Check if location is required but consent is not configured
            if requirement.requires_location and not requirement.consent_required:
                issues.append("Location required but no consent configured")

            # Check if personal data is required but not GDPR compliant
            if requirement.requires_personal_data and not requirement.gdpr_compliant:
                issues.append("Personal data required but not GDPR compliant")

            # Check if precise location is required but no specific consent
            if (
                requirement.requires_precise_location
                and not requirement.consent_required
            ):
                issues.append("Precise location required but no consent configured")

            # Check if technical data is required but no consent
            if requirement.requires_technical_data and not requirement.consent_required:
                issues.append("Technical data required but no consent configured")

            if issues:
                compliance_issues.append(
                    {
                        "survey_id": requirement.survey_id,
                        "issues": issues,
                    }
                )
            else:
                compliant_surveys.append(requirement.survey_id)

        total_surveys = len(all_requirements)
        compliant_count = len(compliant_surveys)
        non_compliant_count = len(compliance_issues)

        compliance_rate = (
            (compliant_count / total_surveys * 100) if total_surveys > 0 else 0
        )

        return {
            "total_surveys": total_surveys,
            "compliant_surveys": compliant_count,
            "non_compliant_surveys": non_compliant_count,
            "compliance_rate": compliance_rate,
            "compliance_issues": compliance_issues,
        }

    async def validate_survey_requirements(self, survey_id: int) -> Dict[str, Any]:
        """
        Validate data requirements for a specific survey.

        Args:
            survey_id: Survey ID

        Returns:
            Dictionary with validation results
        """
        requirements = await self.get_by_survey_id(survey_id)

        if not requirements:
            return {
                "is_valid": False,
                "errors": ["No data requirements configured for this survey"],
                "warnings": [],
            }

        errors = []
        warnings = []

        # Check location requirements
        if requirements.requires_location:
            if not requirements.consent_required:
                errors.append("Location data required but no consent configured")

            if (
                requirements.requires_precise_location
                and not requirements.gdpr_compliant
            ):
                warnings.append(
                    "Precise location required but GDPR compliance not enabled"
                )

        # Check personal data requirements
        if requirements.requires_personal_data:
            if not requirements.gdpr_compliant:
                errors.append("Personal data required but GDPR compliance not enabled")

            if not requirements.consent_required:
                errors.append("Personal data required but no consent configured")

        # Check technical data requirements
        if requirements.requires_technical_data:
            if not requirements.consent_required:
                warnings.append("Technical data required but no consent configured")

        # Check consent configuration
        if requirements.consent_required:
            # Validate consent requirements structure
            consent_req = requirements.consent_required
            if not isinstance(consent_req, dict):
                errors.append("Consent requirements must be a dictionary")
            else:
                required_consents = [
                    "location",
                    "device_info",
                    "personal_data",
                    "marketing",
                    "analytics",
                    "cookies",
                ]
                for consent_type in required_consents:
                    if consent_type not in consent_req:
                        warnings.append(f"Missing consent type: {consent_type}")

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
        }

    async def update_gdpr_compliance(
        self, survey_id: int, gdpr_compliant: bool
    ) -> Optional[SurveyDataRequirements]:
        """
        Update GDPR compliance status for a survey.

        Args:
            survey_id: Survey ID
            gdpr_compliant: GDPR compliance status

        Returns:
            Updated SurveyDataRequirements instance or None
        """
        requirements = await self.get_by_survey_id(survey_id)
        if not requirements:
            return None

        requirements.gdpr_compliant = gdpr_compliant
        await self.db.commit()
        await self.db.refresh(requirements)
        return requirements

    async def update_consent_requirements(
        self, survey_id: int, consent_required: Dict[str, Any]
    ) -> Optional[SurveyDataRequirements]:
        """
        Update consent requirements for a survey.

        Args:
            survey_id: Survey ID
            consent_required: Consent requirements

        Returns:
            Updated SurveyDataRequirements instance or None
        """
        requirements = await self.get_by_survey_id(survey_id)
        if not requirements:
            return None

        requirements.consent_required = consent_required
        await self.db.commit()
        await self.db.refresh(requirements)
        return requirements

    async def get_default_requirements(self) -> Dict[str, Any]:
        """
        Get default data requirements template.

        Returns:
            Dictionary with default requirements
        """
        return {
            "requires_location": False,
            "requires_precise_location": False,
            "requires_personal_data": False,
            "requires_technical_data": True,
            "gdpr_compliant": True,
            "consent_required": {
                "location": False,
                "device_info": True,
                "personal_data": False,
                "marketing": False,
                "analytics": True,
                "cookies": True,
            },
            "data_retention_days": 365,
            "notes": "Default requirements for new surveys",
        }

    async def clone_requirements(
        self, source_survey_id: int, target_survey_id: int
    ) -> Optional[SurveyDataRequirements]:
        """
        Clone data requirements from one survey to another.

        Args:
            source_survey_id: Source survey ID
            target_survey_id: Target survey ID

        Returns:
            Created SurveyDataRequirements instance or None
        """
        source_requirements = await self.get_by_survey_id(source_survey_id)
        if not source_requirements:
            return None

        # Check if target already has requirements
        existing_target = await self.get_by_survey_id(target_survey_id)
        if existing_target:
            return None  # Don't overwrite existing requirements

        # Create new requirements based on source
        create_data = {
            "survey_id": target_survey_id,
            "requires_location": source_requirements.requires_location,
            "requires_precise_location": source_requirements.requires_precise_location,
            "requires_personal_data": source_requirements.requires_personal_data,
            "requires_technical_data": source_requirements.requires_technical_data,
            "gdpr_compliant": source_requirements.gdpr_compliant,
            "consent_required": source_requirements.consent_required,
            "data_retention_days": source_requirements.data_retention_days,
            "notes": f"Cloned from survey {source_survey_id}",
        }

        from schemas.survey_data_requirements import SurveyDataRequirementsCreate

        requirements_create = SurveyDataRequirementsCreate(**create_data)
        return await self.create(obj_in=requirements_create)
