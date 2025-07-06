"""
Validation API router for the Quiz App.

This module contains FastAPI endpoints for validating emails,
phone numbers, and other user input data.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from services.email_validation import email_validator
from schemas.validation import (
    EmailValidationRequest, EmailValidationResponse,
    PhoneValidationRequest, PhoneValidationResponse
)


router = APIRouter()


@router.post("/email", response_model=EmailValidationResponse)
async def validate_email_endpoint(
    request: EmailValidationRequest,
    session: AsyncSession = Depends(get_async_session)
):
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
            check_smtp=request.check_smtp
        )
        
        # Convert service result to response schema
        response = EmailValidationResponse(
            email=result["email"],
            is_valid=result["is_valid"],
            mx_valid=result["mx_valid"],
            smtp_valid=result.get("smtp_valid"),
            error_message=result.get("error_message")
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email validation failed: {str(e)}"
        )


@router.post("/email/batch")
async def validate_emails_batch(
    emails: List[str],
    check_mx: bool = True,
    check_smtp: bool = False,
    session: AsyncSession = Depends(get_async_session)
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
                status_code=400,
                detail="Maximum 100 emails per batch request"
            )
        
        # Perform batch validation
        results = await email_validator.validate_email_batch(
            emails=emails,
            check_mx=check_mx,
            check_smtp=check_smtp
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
                "suggestions": result.get("suggestions", [])
            }
            responses.append(response)
        
        return {
            "total_count": len(emails),
            "valid_count": sum(1 for r in responses if r["is_valid"]),
            "invalid_count": sum(1 for r in responses if not r["is_valid"]),
            "results": responses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch email validation failed: {str(e)}"
        )


@router.post("/phone", response_model=PhoneValidationResponse)
async def validate_phone_endpoint(
    request: PhoneValidationRequest,
    session: AsyncSession = Depends(get_async_session)
):
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
        phone_digits = re.sub(r'[\s\-\(\)\+]', '', phone)
        
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
            if not phone_digits.startswith('+'):
                if len(phone_digits) == 10 and not country_code:
                    # Assume US format for 10 digits
                    normalized_phone = f"+1{phone_digits}"
                    detected_country = "US"
                elif len(phone_digits) == 11 and phone_digits.startswith('1'):
                    # US format with country code
                    normalized_phone = f"+{phone_digits}"
                    detected_country = "US"
                elif len(phone_digits) == 11 and phone_digits.startswith('7'):
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
            error_message=error_message
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Phone validation failed: {str(e)}"
        )


@router.get("/email/domain/{domain}")
async def check_domain_mx_records(
    domain: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Check MX records for a specific domain.
    
    Returns MX record information for email domain validation.
    Useful for checking if a domain can receive emails.
    """
    try:
        # Use the email validation service's MX checking
        mx_result = await email_validator._validate_mx_records(domain)
        
        return {
            "domain": domain,
            "mx_valid": mx_result["mx_valid"],
            "mx_records": mx_result["mx_records"],
            "error_message": mx_result.get("error_message")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MX record check failed: {str(e)}"
        )


@router.post("/email/suggestions")
async def get_email_suggestions(
    email: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get email correction suggestions for typos.
    
    Analyzes email for common typos and returns suggested corrections.
    Useful for improving user experience with email input.
    """
    try:
        # Generate suggestions using the email validation service
        suggestions = email_validator._generate_email_suggestions(email)
        
        return {
            "original_email": email,
            "suggestions": suggestions,
            "has_suggestions": len(suggestions) > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email suggestion generation failed: {str(e)}"
        )


@router.get("/email/test-smtp/{email}")
async def test_email_smtp(
    email: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Test SMTP connectivity for email deliverability.
    
    Performs actual SMTP connection test to verify email can receive messages.
    Note: This operation may be slow and should be used sparingly.
    """
    try:
        # First get MX records
        if "@" not in email:
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        domain = email.split("@")[1]
        mx_result = await email_validator._validate_mx_records(domain)
        
        if not mx_result["mx_valid"]:
            return {
                "email": email,
                "smtp_valid": False,
                "error_message": "No MX records found for domain"
            }
        
        # Test SMTP connectivity
        smtp_result = await email_validator._validate_smtp_connectivity(
            email, mx_result["mx_records"]
        )
        
        return {
            "email": email,
            "smtp_valid": smtp_result["smtp_valid"],
            "smtp_server": smtp_result.get("smtp_server"),
            "smtp_response": smtp_result.get("smtp_response"),
            "error_message": smtp_result.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SMTP test failed: {str(e)}"
        )


@router.get("/health")
async def validation_health_check():
    """
    Health check for validation services.
    
    Returns status of email validation dependencies and services.
    """
    try:
        # Check DNS availability
        dns_available = email_validator.DNS_AVAILABLE if hasattr(email_validator, 'DNS_AVAILABLE') else False
        
        # Test basic email format validation
        test_email = "test@example.com"
        try:
            format_result = await email_validator._validate_format(test_email)
            format_working = format_result["format_valid"]
        except Exception:
            format_working = False
        
        return {
            "status": "healthy",
            "dns_available": dns_available,
            "format_validation_working": format_working,
            "mx_check_enabled": email_validator.mx_check_enabled,
            "smtp_timeout": email_validator.timeout,
            "services": {
                "email_validation": "available",
                "phone_validation": "basic",
                "mx_checking": "available" if dns_available else "unavailable",
                "smtp_testing": "available"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        ) 