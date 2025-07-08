"""
Validation API router for the Quiz App.

This module contains FastAPI endpoints for validating emails,
phone numbers, and other user input data.
"""

from fastapi import APIRouter, HTTPException

from schemas.validation import (
    EmailValidationRequest,
    EmailValidationResponse,
    PhoneValidationRequest,
    PhoneValidationResponse,
)
from services.email_validation import email_validator

router = APIRouter()


@router.post("/email", response_model=EmailValidationResponse)
async def validate_email_endpoint(request: EmailValidationRequest):
    """
    Validate email address with comprehensive checks.

    Performs format validation, MX record checking, and optional SMTP testing.
    Returns detailed validation results with suggestions for common typos.
    """
    try:
        # Perform email validation
        result = await email_validator.validate_email_comprehensive(
            email=request.email,
            check_mx=request.check_mx,
            check_smtp=request.check_smtp,
        )

        # Convert service result to response schema
        response = EmailValidationResponse(
            email=result["email"],
            is_valid=result["is_valid"],
            mx_valid=result["mx_valid"],
            smtp_valid=result.get("smtp_valid"),
            error_message=result.get("error_message"),
            suggestions=result.get("suggestions", []),
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email validation failed: {e!s}")


@router.post("/email/batch")
async def validate_emails_batch(
    emails: list[str],
    check_mx: bool = True,
    check_smtp: bool = False,
):
    """
    Validate multiple email addresses in batch.

    Efficiently validates up to 100 email addresses at once
    with optional MX and SMTP checking.
    """
    try:
        # Limit batch size for performance
        if len(emails) > 100:
            raise HTTPException(
                status_code=400, detail="Maximum 100 emails per batch request"
            )

        # Perform batch validation
        results = await email_validator.validate_email_batch(
            emails=emails, check_mx=check_mx, check_smtp=check_smtp
        )

        # Convert results to response format
        responses = []
        for result in results:
            response = {
                "email": result["email"],
                "is_valid": result["is_valid"],
                "mx_valid": result.get("mx_valid", False),
                "smtp_valid": result.get("smtp_valid"),
                "error_message": result.get("error_message"),
                "suggestions": result.get("suggestions", []),
            }
            responses.append(response)

        return {
            "total_count": len(emails),
            "valid_count": sum(1 for r in responses if r["is_valid"]),
            "invalid_count": sum(1 for r in responses if not r["is_valid"]),
            "results": responses,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch email validation failed: {e!s}"
        )


@router.post("/phone", response_model=PhoneValidationResponse)
async def validate_phone_endpoint(request: PhoneValidationRequest):
    """
    Validate phone number format and normalize.

    Performs format validation and number normalization.
    Supports international phone number formats.
    """
    try:
        # Basic phone validation and normalization
        phone = request.phone.strip()
        country_code = request.country_code

        # Remove common formatting characters
        import re

        phone_digits = re.sub(r"[\s\-\(\)\+]", "", phone)

        # Basic validation
        is_valid = False
        normalized_phone = phone_digits
        detected_country = None
        error_message = None

        # Check phone length (international standard: 10-15 digits)
        if len(phone_digits) < 10:
            error_message = "Phone number too short"
        elif len(phone_digits) > 15:
            error_message = "Phone number too long"
        else:
            is_valid = True

            # Normalize international format
            if not phone_digits.startswith("+"):
                if len(phone_digits) == 10 and not country_code:
                    # Assume US format for 10 digits
                    normalized_phone = f"+1{phone_digits}"
                    detected_country = "US"
                elif len(phone_digits) == 11 and phone_digits.startswith("1"):
                    # US format with country code
                    normalized_phone = f"+{phone_digits}"
                    detected_country = "US"
                elif len(phone_digits) == 11 and phone_digits.startswith("7"):
                    # Russian format
                    normalized_phone = f"+{phone_digits}"
                    detected_country = "RU"
                else:
                    normalized_phone = f"+{phone_digits}"
            else:
                normalized_phone = phone_digits

        response = PhoneValidationResponse(
            phone=request.phone,
            normalized_phone=normalized_phone,
            is_valid=is_valid,
            country_code=detected_country or country_code,
            carrier=None,  # Would require external service
            error_message=error_message,
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phone validation failed: {e!s}")


@router.get("/email/domain/{domain}")
async def check_domain_mx_records(domain: str):
    """
    Check MX records for a specific domain.

    Returns MX record information for email domain validation.
    Useful for checking if a domain can receive emails.
    """
    try:
        # Create email validation service instance and use MX checking
        from services.email_validation import EmailValidationService

        service = EmailValidationService()
        mx_result = await service._validate_mx_records(domain)

        return {
            "domain": domain,
            "mx_valid": mx_result["mx_valid"],
            "mx_records": mx_result["mx_records"],
            "error_message": mx_result.get("error_message"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MX record check failed: {e!s}")


@router.post("/email/suggestions")
async def get_email_suggestions(email: str):
    """
    Get email suggestions for common typos.

    Analyzes the email and suggests corrections for common domain typos.
    """
    try:
        # Create email validation service instance for suggestions
        from services.email_validation import EmailValidationService

        service = EmailValidationService()
        suggestions = service._generate_email_suggestions(email)

        return {
            "email": email,
            "suggestions": suggestions,
            "has_suggestions": len(suggestions) > 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email suggestions failed: {e!s}")


@router.get("/email/test-smtp/{email}")
async def test_email_smtp(email: str):
    """
    Test SMTP connection for email validation.

    Attempts to connect to email server to verify if email exists.
    Note: This is resource-intensive and should be used sparingly.
    """
    try:
        # Extract domain from email
        if "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid email format")

        domain = email.split("@")[1]

        # Create email validation service and get MX records first
        from services.email_validation import EmailValidationService

        service = EmailValidationService()

        # Get MX records for domain
        mx_result = await service._validate_mx_records(domain)

        if not mx_result["mx_valid"]:
            smtp_result = {
                "smtp_valid": False,
                "error_message": "No MX records found for domain",
            }
        else:
            # Test SMTP connection using MX records
            smtp_result = await service._validate_smtp_connectivity(
                email, mx_result["mx_records"]
            )

        return {
            "email": email,
            "domain": domain,
            "smtp_valid": smtp_result["smtp_valid"],
            "response_message": smtp_result.get("response_message"),
            "error_message": smtp_result.get("error_message"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP test failed: {e!s}")


@router.get("/health")
async def validation_health_check():
    """
    Check validation service health.

    Returns status of validation services and dependencies.
    """
    try:
        # Test email validation service
        test_result = await email_validator.validate_email_comprehensive(
            email="test@example.com", check_mx=False, check_smtp=False
        )

        return {
            "status": "healthy",
            "services": {
                "email_validator": "operational",
                "phone_validator": "operational",
            },
            "test_validation": {
                "email": test_result["email"],
                "is_valid": test_result["is_valid"],
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z",
        }
