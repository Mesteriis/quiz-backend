"""
Admin schemas for the Quiz App.

This module contains Pydantic schemas for admin panel operations,
including survey management, analytics, and reporting.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from models.survey import SurveyRead, SurveyReadWithQuestions  
from models.question import QuestionRead
from models.response import ResponseRead
from models.user_data import UserDataRead


class SuccessResponse(BaseModel):
    """Generic success response schema."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Dict[str, Any] | None = Field(default=None, description="Optional response data")


class AdminSurveyCreate(BaseModel):
    """Schema for creating a survey through admin panel."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Survey title")
    description: str | None = Field(default=None, max_length=1000, description="Survey description")
    is_active: bool = Field(default=True, description="Whether survey is active")
    is_public: bool = Field(default=True, description="Whether survey is public")
    telegram_notifications: bool = Field(default=True, description="Enable Telegram notifications")
    questions: List["AdminQuestionCreate"] = Field(default_factory=list, description="Survey questions")


class AdminQuestionCreate(BaseModel):
    """Schema for creating a question through admin panel."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Question title")
    description: str | None = Field(default=None, max_length=2000, description="Question description")
    image_url: str | None = Field(default=None, max_length=500, description="Attached image URL")
    question_type: str = Field(..., description="Type of question")
    is_required: bool = Field(default=True, description="Whether answer is required")
    order: int = Field(default=0, description="Question order in survey")
    options: Dict[str, Any] | None = Field(default=None, description="Question options")


class AdminSurveyList(BaseModel):
    """Schema for listing surveys in admin panel."""
    
    surveys: List[SurveyRead] = Field(..., description="List of surveys")
    total: int = Field(..., description="Total number of surveys")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class AdminSurveyDetail(BaseModel):
    """Schema for detailed survey view in admin panel."""
    
    survey: SurveyReadWithQuestions = Field(..., description="Survey with questions")
    stats: "SurveyStats" = Field(..., description="Survey statistics")
    recent_responses: List[ResponseRead] = Field(..., description="Recent responses")


class SurveyStats(BaseModel):
    """Schema for survey statistics."""
    
    total_responses: int = Field(..., description="Total number of responses")
    unique_users: int = Field(..., description="Number of unique users")
    completion_rate: float = Field(..., description="Completion rate percentage")
    average_time: Optional[float] = Field(default=None, description="Average completion time in seconds")
    last_response: Optional[datetime] = Field(default=None, description="Last response timestamp")
    daily_responses: List[Dict[str, Any]] = Field(default_factory=list, description="Daily response counts")
    question_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Per-question statistics")


class AdminUserData(BaseModel):
    """Schema for user data in admin panel."""
    
    user_data: UserDataRead = Field(..., description="User data")
    response_count: int = Field(..., description="Number of responses")
    surveys_participated: List[str] = Field(..., description="Survey titles participated in")
    first_seen: datetime = Field(..., description="First activity timestamp")
    last_seen: datetime = Field(..., description="Last activity timestamp")


class AdminUsersList(BaseModel):
    """Schema for listing users in admin panel."""
    
    users: List[AdminUserData] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class AdminAnalytics(BaseModel):
    """Schema for admin analytics dashboard."""
    
    total_surveys: int = Field(..., description="Total number of surveys")
    active_surveys: int = Field(..., description="Number of active surveys")
    total_responses: int = Field(..., description="Total number of responses")
    unique_users: int = Field(..., description="Number of unique users")
    responses_today: int = Field(..., description="Responses today")
    responses_this_week: int = Field(..., description="Responses this week")
    responses_this_month: int = Field(..., description="Responses this month")
    top_surveys: List[Dict[str, Any]] = Field(..., description="Top surveys by response count")
    user_countries: Dict[str, int] = Field(..., description="User distribution by country")
    user_devices: Dict[str, int] = Field(..., description="User distribution by device")
    user_browsers: Dict[str, int] = Field(..., description="User distribution by browser")
    telegram_users: int = Field(..., description="Number of Telegram users")
    response_trends: List[Dict[str, Any]] = Field(..., description="Response trends over time")


class AdminReportRequest(BaseModel):
    """Schema for generating admin reports."""
    
    survey_id: int = Field(..., description="Survey ID")
    format: str = Field(default="pdf", description="Report format (pdf, csv, json)")
    include_user_data: bool = Field(default=True, description="Include user data in report")
    include_raw_responses: bool = Field(default=True, description="Include raw responses")
    include_analytics: bool = Field(default=True, description="Include analytics")
    date_from: Optional[datetime] = Field(default=None, description="Start date filter")
    date_to: Optional[datetime] = Field(default=None, description="End date filter")
    send_to_telegram: bool = Field(default=False, description="Send report to Telegram")


class AdminReportResponse(BaseModel):
    """Schema for admin report response."""
    
    report_id: str = Field(..., description="Report identifier")
    report_url: str = Field(..., description="Report download URL")
    format: str = Field(..., description="Report format")
    file_size: int = Field(..., description="File size in bytes")
    generated_at: datetime = Field(..., description="Generation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    sent_to_telegram: bool = Field(..., description="Whether sent to Telegram")


class AdminSurveyBulkOperation(BaseModel):
    """Schema for bulk survey operations."""
    
    survey_ids: List[int] = Field(..., description="Survey IDs to operate on")
    operation: str = Field(..., description="Operation type (activate, deactivate, delete)")
    confirm: bool = Field(..., description="Confirmation flag")


class AdminSurveyBulkResponse(BaseModel):
    """Schema for bulk survey operation response."""
    
    operation: str = Field(..., description="Operation performed")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Error details")


class AdminSettings(BaseModel):
    """Schema for admin settings."""
    
    telegram_notifications: bool = Field(..., description="Enable Telegram notifications")
    auto_reports: bool = Field(..., description="Enable automatic reports")
    report_frequency: str = Field(..., description="Report frequency (daily, weekly, monthly)")
    max_file_size: int = Field(..., description="Maximum file size in bytes")
    rate_limit_enabled: bool = Field(..., description="Enable rate limiting")
    rate_limit_per_minute: int = Field(..., description="Rate limit per minute")
    maintenance_mode: bool = Field(..., description="Maintenance mode enabled")


class AdminSettingsUpdate(BaseModel):
    """Schema for updating admin settings."""
    
    telegram_notifications: Optional[bool] = Field(default=None)
    auto_reports: Optional[bool] = Field(default=None)
    report_frequency: Optional[str] = Field(default=None)
    max_file_size: Optional[int] = Field(default=None)
    rate_limit_enabled: Optional[bool] = Field(default=None)
    rate_limit_per_minute: Optional[int] = Field(default=None)
    maintenance_mode: Optional[bool] = Field(default=None)


class AdminActivityLog(BaseModel):
    """Schema for admin activity logging."""
    
    id: int = Field(..., description="Log entry ID")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type (survey, user, etc.)")
    resource_id: Optional[int] = Field(default=None, description="Resource ID")
    details: Dict[str, Any] = Field(..., description="Action details")
    ip_address: str = Field(..., description="Admin IP address")
    timestamp: datetime = Field(..., description="Action timestamp")


class AdminActivityLogList(BaseModel):
    """Schema for listing admin activity logs."""
    
    logs: List[AdminActivityLog] = Field(..., description="List of activity logs")
    total: int = Field(..., description="Total number of logs")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


# Forward references for complex schemas
AdminSurveyCreate.model_rebuild()
AdminQuestionCreate.model_rebuild() 