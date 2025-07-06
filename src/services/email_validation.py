"""
Email validation service for the Quiz App.

This module provides comprehensive email validation including:
- Format validation
- MX record checking
- SMTP server connectivity testing
- Domain validation
"""

import asyncio
import logging
import smtplib
import socket

from email_validator import EmailNotValidError, validate_email

try:
    import dns.exception
    import dns.resolver

    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from config import settings

logger = logging.getLogger(__name__)


class EmailValidationService:
    """Service for comprehensive email validation."""

    def __init__(self):
        self.timeout = settings.smtp_timeout
        self.mx_check_enabled = settings.mx_check_enabled

    async def validate_email_comprehensive(
        self, email: str, check_mx: bool = True, check_smtp: bool = False
    ) -> dict[str, any]:
        """
        Perform comprehensive email validation.

        Args:
            email: Email address to validate
            check_mx: Whether to check MX records
            check_smtp: Whether to test SMTP connectivity

        Returns:
            dict: Validation results with detailed information
        """
        result = {
            "email": email,
            "is_valid": False,
            "format_valid": False,
            "mx_valid": False,
            "smtp_valid": None,
            "domain": None,
            "mx_records": [],
            "error_message": None,
            "suggestions": [],
        }

        try:
            # Step 1: Format validation using email-validator
            format_result = await self._validate_format(email)
            result.update(format_result)

            if not result["format_valid"]:
                return result

            # Step 2: MX record validation
            if check_mx and self.mx_check_enabled:
                mx_result = await self._validate_mx_records(result["domain"])
                result.update(mx_result)

                # Step 3: SMTP validation (only if MX records exist)
                if check_smtp and result["mx_valid"] and result["mx_records"]:
                    smtp_result = await self._validate_smtp_connectivity(
                        email, result["mx_records"]
                    )
                    result.update(smtp_result)

            # Final validation status
            result["is_valid"] = (
                result["format_valid"]
                and (result["mx_valid"] if check_mx else True)
                and (result["smtp_valid"] if check_smtp else True)
            )

        except Exception as e:
            logger.error(f"Email validation error for {email}: {e!s}")
            result["error_message"] = f"Validation error: {e!s}"

        return result

    async def _validate_format(self, email: str) -> dict[str, any]:
        """
        Validate email format using email-validator library.

        Args:
            email: Email address to validate

        Returns:
            dict: Format validation results
        """
        result = {
            "format_valid": False,
            "domain": None,
            "normalized_email": None,
            "suggestions": [],
        }

        try:
            # Use email-validator for comprehensive format checking
            validation = validate_email(
                email, check_deliverability=False  # We'll do this separately
            )

            result["format_valid"] = True
            result["normalized_email"] = validation.email
            result["domain"] = validation.domain

        except EmailNotValidError as e:
            logger.debug(f"Email format invalid for {email}: {e!s}")
            result["error_message"] = str(e)

            # Generate suggestions for common typos
            result["suggestions"] = self._generate_email_suggestions(email)

        except Exception as e:
            logger.error(f"Unexpected error in format validation: {e!s}")
            result["error_message"] = f"Format validation error: {e!s}"

        return result

    async def _validate_mx_records(self, domain: str) -> dict[str, any]:
        """
        Validate MX records for the email domain.

        Args:
            domain: Domain to check MX records for

        Returns:
            dict: MX validation results
        """
        result = {"mx_valid": False, "mx_records": [], "error_message": None}

        if not DNS_AVAILABLE:
            logger.warning("DNS library not available, skipping MX validation")
            result["error_message"] = "DNS validation not available"
            return result

        try:
            # Query MX records
            mx_records = dns.resolver.resolve(domain, "MX")

            mx_list = []
            for mx in mx_records:
                mx_list.append(
                    {
                        "priority": mx.preference,
                        "exchange": str(mx.exchange).rstrip("."),
                    }
                )

            # Sort by priority (lower is higher priority)
            mx_list.sort(key=lambda x: x["priority"])

            result["mx_records"] = mx_list
            result["mx_valid"] = len(mx_list) > 0

            if not result["mx_valid"]:
                result["error_message"] = "No MX records found for domain"

        except dns.resolver.NXDOMAIN:
            result["error_message"] = "Domain does not exist"
        except dns.resolver.NoAnswer:
            result["error_message"] = "No MX records found for domain"
        except dns.exception.Timeout:
            result["error_message"] = "DNS query timeout"
        except Exception as e:
            logger.error(f"MX validation error for {domain}: {e!s}")
            result["error_message"] = f"MX validation error: {e!s}"

        return result

    async def _validate_smtp_connectivity(
        self, email: str, mx_records: list[dict[str, any]]
    ) -> dict[str, any]:
        """
        Test SMTP connectivity to verify email deliverability.

        Args:
            email: Email address to test
            mx_records: List of MX records to test

        Returns:
            dict: SMTP validation results
        """
        result = {
            "smtp_valid": False,
            "smtp_server": None,
            "smtp_response": None,
            "error_message": None,
        }

        # Try each MX server in priority order
        for mx in mx_records:
            server = mx["exchange"]

            try:
                # Test SMTP connection
                smtp_result = await self._test_smtp_server(email, server)

                if smtp_result["success"]:
                    result["smtp_valid"] = True
                    result["smtp_server"] = server
                    result["smtp_response"] = smtp_result["response"]
                    break
                else:
                    logger.debug(
                        f"SMTP test failed for {server}: {smtp_result['error']}"
                    )

            except Exception as e:
                logger.debug(f"SMTP connection error to {server}: {e!s}")
                continue

        if not result["smtp_valid"]:
            result["error_message"] = "Unable to connect to any SMTP server"

        return result

    async def _test_smtp_server(self, email: str, server: str) -> dict[str, any]:
        """
        Test SMTP server connectivity for email validation.

        Args:
            email: Email address to test
            server: SMTP server to test

        Returns:
            dict: SMTP test results
        """

        def test_smtp():
            try:
                # Connect to SMTP server
                smtp = smtplib.SMTP(timeout=self.timeout)
                smtp.connect(server, 25)

                # HELO command
                code, response = smtp.helo("quiz-app.local")
                if code != 250:
                    return {"success": False, "error": f"HELO failed: {response}"}

                # MAIL FROM command (use a generic sender)
                code, response = smtp.mail("test@quiz-app.local")
                if code != 250:
                    return {"success": False, "error": f"MAIL FROM failed: {response}"}

                # RCPT TO command (test the actual email)
                code, response = smtp.rcpt(email)
                smtp.quit()

                if code in [250, 251]:  # 250 = OK, 251 = User not local
                    return {
                        "success": True,
                        "response": response.decode()
                        if isinstance(response, bytes)
                        else response,
                    }
                else:
                    return {"success": False, "error": f"RCPT TO failed: {response}"}

            except smtplib.SMTPServerDisconnected:
                return {"success": False, "error": "Server disconnected"}
            except smtplib.SMTPConnectError as e:
                return {"success": False, "error": f"Connection error: {e!s}"}
            except socket.timeout:
                return {"success": False, "error": "Connection timeout"}
            except Exception as e:
                return {"success": False, "error": f"SMTP error: {e!s}"}

        # Run SMTP test in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, test_smtp)

    def _generate_email_suggestions(self, email: str) -> list[str]:
        """
        Generate suggestions for common email typos.

        Args:
            email: Original email with potential typos

        Returns:
            list: List of suggested email corrections
        """
        suggestions = []

        # Common domain typos
        domain_corrections = {
            "gmail.co": "gmail.com",
            "gmail.cm": "gmail.com",
            "gmai.com": "gmail.com",
            "gmial.com": "gmail.com",
            "yahoo.co": "yahoo.com",
            "yahoo.cm": "yahoo.com",
            "yaho.com": "yahoo.com",
            "hotmail.co": "hotmail.com",
            "hotmail.cm": "hotmail.com",
            "outlook.co": "outlook.com",
            "outlook.cm": "outlook.com",
            "mail.ru.com": "mail.ru",
            "yandex.co": "yandex.ru",
            "yandex.cm": "yandex.ru",
        }

        if "@" in email:
            local, domain = email.rsplit("@", 1)

            # Check for domain corrections
            if domain.lower() in domain_corrections:
                suggestions.append(f"{local}@{domain_corrections[domain.lower()]}")

            # Check for missing TLD
            if "." not in domain:
                for common_tld in [".com", ".ru", ".org", ".net"]:
                    suggestions.append(f"{local}@{domain}{common_tld}")

        return suggestions

    async def validate_email_batch(
        self, emails: list[str], check_mx: bool = True, check_smtp: bool = False
    ) -> list[dict[str, any]]:
        """
        Validate multiple emails in batch.

        Args:
            emails: List of email addresses to validate
            check_mx: Whether to check MX records
            check_smtp: Whether to test SMTP connectivity

        Returns:
            list: List of validation results for each email
        """
        tasks = [
            self.validate_email_comprehensive(email, check_mx, check_smtp)
            for email in emails
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "email": emails[i],
                        "is_valid": False,
                        "error_message": f"Validation exception: {result!s}",
                    }
                )
            else:
                processed_results.append(result)

        return processed_results


# Global email validation service instance
email_validator = EmailValidationService()


async def validate_email(
    email: str, check_mx: bool = True, check_smtp: bool = False
) -> dict[str, any]:
    """
    Convenience function for email validation.

    Args:
        email: Email address to validate
        check_mx: Whether to check MX records
        check_smtp: Whether to test SMTP connectivity

    Returns:
        dict: Validation results
    """
    return await email_validator.validate_email_comprehensive(
        email, check_mx, check_smtp
    )
