"""
Push notification repository for the Quiz App.

This module provides the push notification repository with specific methods
for push notification related database operations.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.push_notification import (
    PushSubscription,
    PushNotification,
    NotificationTemplate,
    NotificationAnalytics,
)
from schemas.push_notification import (
    PushSubscriptionCreate,
    PushSubscriptionUpdate,
    PushNotificationCreate,
    PushNotificationUpdate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationAnalyticsCreate,
)
from .base import BaseRepository


class PushSubscriptionRepository(
    BaseRepository[PushSubscription, PushSubscriptionCreate, PushSubscriptionUpdate]
):
    """
    Push subscription repository with specific subscription operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize PushSubscriptionRepository with database session."""
        super().__init__(PushSubscription, db)

    async def get_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> List[PushSubscription]:
        """
        Get all subscriptions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of user subscriptions
        """
        query = select(PushSubscription).where(PushSubscription.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> List[PushSubscription]:
        """
        Get active subscriptions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of active user subscriptions
        """
        query = select(PushSubscription).where(
            and_(
                PushSubscription.user_id == user_id, PushSubscription.is_active == True
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_endpoint(
        self, db: AsyncSession, endpoint: str
    ) -> Optional[PushSubscription]:
        """
        Get subscription by endpoint.

        Args:
            db: Database session
            endpoint: Push endpoint

        Returns:
            Subscription or None
        """
        return await self.get_by_field("endpoint", endpoint)

    async def get_by_category(
        self, db: AsyncSession, category: str, *, skip: int = 0, limit: int = 100
    ) -> List[PushSubscription]:
        """
        Get subscriptions that have a specific category enabled.

        Args:
            db: Database session
            category: Category to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of subscriptions with category enabled
        """
        query = (
            select(PushSubscription)
            .where(
                and_(
                    PushSubscription.is_active == True,
                    PushSubscription.enabled_categories.contains([category]),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def update_last_used(
        self, db: AsyncSession, subscription_id: int
    ) -> Optional[PushSubscription]:
        """
        Update last used timestamp for subscription.

        Args:
            db: Database session
            subscription_id: Subscription ID

        Returns:
            Updated subscription or None
        """
        subscription = await self.get(db, subscription_id)
        if subscription:
            subscription.last_used_at = datetime.utcnow()
            await db.commit()
            await db.refresh(subscription)
        return subscription

    async def cleanup_inactive(self, db: AsyncSession, days_inactive: int = 30) -> int:
        """
        Clean up subscriptions that haven't been used for specified days.

        Args:
            db: Database session
            days_inactive: Number of days to consider inactive

        Returns:
            Number of cleaned up subscriptions
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)

        query = select(PushSubscription).where(
            or_(
                PushSubscription.last_used_at < cutoff_date,
                and_(
                    PushSubscription.last_used_at.is_(None),
                    PushSubscription.created_at < cutoff_date,
                ),
            )
        )
        result = await db.execute(query)
        inactive_subscriptions = result.scalars().all()

        for subscription in inactive_subscriptions:
            await db.delete(subscription)

        await db.commit()
        return len(inactive_subscriptions)


class PushNotificationRepository(
    BaseRepository[PushNotification, PushNotificationCreate, PushNotificationUpdate]
):
    """
    Push notification repository with specific notification operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize PushNotificationRepository with PushNotification model."""
        super().__init__(PushNotification, db)

    async def get_by_subscription_id(
        self, db: AsyncSession, subscription_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[PushNotification]:
        """
        Get notifications for a subscription.

        Args:
            db: Database session
            subscription_id: Subscription ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of notifications for subscription
        """
        query = (
            select(PushNotification)
            .where(PushNotification.subscription_id == subscription_id)
            .order_by(PushNotification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_category(
        self, db: AsyncSession, category: str, *, skip: int = 0, limit: int = 100
    ) -> List[PushNotification]:
        """
        Get notifications by category.

        Args:
            db: Database session
            category: Category to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of notifications in category
        """
        query = (
            select(PushNotification)
            .where(PushNotification.category == category)
            .order_by(PushNotification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_status(
        self, db: AsyncSession, status: str, *, skip: int = 0, limit: int = 100
    ) -> List[PushNotification]:
        """
        Get notifications by status.

        Args:
            db: Database session
            status: Status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of notifications with status
        """
        query = (
            select(PushNotification)
            .where(PushNotification.status == status)
            .order_by(PushNotification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_pending_notifications(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[PushNotification]:
        """
        Get pending notifications.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of pending notifications
        """
        return await self.get_by_status(db, "pending", skip=skip, limit=limit)

    async def mark_as_sent(
        self, db: AsyncSession, notification_id: int
    ) -> Optional[PushNotification]:
        """
        Mark notification as sent.

        Args:
            db: Database session
            notification_id: Notification ID

        Returns:
            Updated notification or None
        """
        notification = await self.get(db, notification_id)
        if notification:
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notification)
        return notification

    async def mark_as_delivered(
        self, db: AsyncSession, notification_id: int
    ) -> Optional[PushNotification]:
        """
        Mark notification as delivered.

        Args:
            db: Database session
            notification_id: Notification ID

        Returns:
            Updated notification or None
        """
        notification = await self.get(db, notification_id)
        if notification:
            notification.status = "delivered"
            notification.delivered_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notification)
        return notification

    async def mark_as_clicked(
        self, db: AsyncSession, notification_id: int
    ) -> Optional[PushNotification]:
        """
        Mark notification as clicked.

        Args:
            db: Database session
            notification_id: Notification ID

        Returns:
            Updated notification or None
        """
        notification = await self.get(db, notification_id)
        if notification:
            notification.clicked = True
            notification.clicked_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notification)
        return notification

    async def mark_as_dismissed(
        self, db: AsyncSession, notification_id: int
    ) -> Optional[PushNotification]:
        """
        Mark notification as dismissed.

        Args:
            db: Database session
            notification_id: Notification ID

        Returns:
            Updated notification or None
        """
        notification = await self.get(db, notification_id)
        if notification:
            notification.dismissed = True
            notification.dismissed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notification)
        return notification

    async def get_notification_stats(
        self, db: AsyncSession, *, category: Optional[str] = None, days: int = 30
    ) -> dict:
        """
        Get notification statistics.

        Args:
            db: Database session
            category: Optional category filter
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        base_query = select(PushNotification).where(
            PushNotification.created_at >= cutoff_date
        )

        if category:
            base_query = base_query.where(PushNotification.category == category)

        # Total notifications
        total_result = await db.execute(
            select(func.count(PushNotification.id)).select_from(base_query.subquery())
        )
        total = total_result.scalar()

        # Sent notifications
        sent_result = await db.execute(
            select(func.count(PushNotification.id)).select_from(
                base_query.where(PushNotification.status == "sent").subquery()
            )
        )
        sent = sent_result.scalar()

        # Delivered notifications
        delivered_result = await db.execute(
            select(func.count(PushNotification.id)).select_from(
                base_query.where(PushNotification.status == "delivered").subquery()
            )
        )
        delivered = delivered_result.scalar()

        # Clicked notifications
        clicked_result = await db.execute(
            select(func.count(PushNotification.id)).select_from(
                base_query.where(PushNotification.clicked == True).subquery()
            )
        )
        clicked = clicked_result.scalar()

        # Failed notifications
        failed_result = await db.execute(
            select(func.count(PushNotification.id)).select_from(
                base_query.where(PushNotification.status == "failed").subquery()
            )
        )
        failed = failed_result.scalar()

        return {
            "total_notifications": total,
            "sent_notifications": sent,
            "delivered_notifications": delivered,
            "clicked_notifications": clicked,
            "dismissed_notifications": 0,  # Would need separate query
            "failed_notifications": failed,
            "click_rate": clicked / delivered if delivered > 0 else 0,
            "delivery_rate": delivered / sent if sent > 0 else 0,
        }


class NotificationTemplateRepository(
    BaseRepository[
        NotificationTemplate, NotificationTemplateCreate, NotificationTemplateUpdate
    ]
):
    """
    Notification template repository with specific template operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize NotificationTemplateRepository with NotificationTemplate model."""
        super().__init__(NotificationTemplate, db)

    async def get_by_name(
        self, db: AsyncSession, name: str
    ) -> Optional[NotificationTemplate]:
        """
        Get template by name.

        Args:
            db: Database session
            name: Template name

        Returns:
            Template or None
        """
        return await self.get_by_field(db, "name", name)

    async def get_by_category(
        self, db: AsyncSession, category: str
    ) -> List[NotificationTemplate]:
        """
        Get templates by category.

        Args:
            db: Database session
            category: Category to filter by

        Returns:
            List of templates in category
        """
        query = select(NotificationTemplate).where(
            NotificationTemplate.category == category
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_templates(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[NotificationTemplate]:
        """
        Get active templates.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active templates
        """
        query = (
            select(NotificationTemplate)
            .where(NotificationTemplate.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()


class NotificationAnalyticsRepository(
    BaseRepository[NotificationAnalytics, NotificationAnalyticsCreate, dict]
):
    """
    Notification analytics repository with specific analytics operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize NotificationAnalyticsRepository with NotificationAnalytics model."""
        super().__init__(NotificationAnalytics, db)

    async def get_by_event_type(
        self, db: AsyncSession, event_type: str, *, skip: int = 0, limit: int = 100
    ) -> List[NotificationAnalytics]:
        """
        Get analytics by event type.

        Args:
            db: Database session
            event_type: Event type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of analytics records
        """
        query = (
            select(NotificationAnalytics)
            .where(NotificationAnalytics.event_type == event_type)
            .order_by(NotificationAnalytics.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(
        self, db: AsyncSession, user_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[NotificationAnalytics]:
        """
        Get analytics by user ID.

        Args:
            db: Database session
            user_id: User ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of analytics records for user
        """
        query = (
            select(NotificationAnalytics)
            .where(NotificationAnalytics.user_id == user_id)
            .order_by(NotificationAnalytics.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()


# Repository instances are created through dependency injection
# See dependencies.py for repository creation
