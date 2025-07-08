from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from models.user import User
from repositories.dependencies import (
    get_push_subscription_repository,
    get_push_notification_repository,
    get_notification_analytics_repository,
)
from repositories.push_notification import (
    PushSubscriptionRepository,
    PushNotificationRepository,
    NotificationAnalyticsRepository,
)
from routers.auth import get_current_user
from schemas.push_notification import (
    NotificationAnalyticsCreate,
    NotificationCategoriesUpdate,
    PushNotificationCreate,
    PushNotificationRead,
    PushNotificationStatsResponse,
    PushSubscriptionCreate,
    PushSubscriptionRead,
    VapidKeyResponse,
)
from services.push_notification_service import push_service

router = APIRouter(prefix="/notifications", tags=["Push Notifications"])


@router.get("/vapid-key", response_model=VapidKeyResponse)
async def get_vapid_public_key():
    """
    Получить публичный VAPID ключ для подписки на push-уведомления
    """
    try:
        public_key = push_service.get_vapid_public_key()
        return VapidKeyResponse(public_key=public_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения VAPID ключа: {e!s}",
        )


@router.post("/subscribe", response_model=dict[str, str])
async def subscribe_to_push_notifications(
    subscription_data: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Подписаться на push-уведомления
    """
    try:
        # Извлекаем данные подписки
        subscription = subscription_data.subscription
        endpoint = subscription.get("endpoint")
        keys = subscription.get("keys", {})
        p256dh_key = keys.get("p256dh")
        auth_key = keys.get("auth")

        if not all([endpoint, p256dh_key, auth_key]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неполные данные подписки",
            )

        # Создаем подписку через репозиторий
        new_subscription = await subscription_repo.create_subscription(
            user_id=current_user.id,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
        )

        return {
            "status": "success",
            "message": "Подписка успешно создана",
            "subscription_id": str(new_subscription.id),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания подписки: {e!s}",
        )


@router.post("/unsubscribe", response_model=dict[str, str])
async def unsubscribe_from_push_notifications(
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Отписаться от push-уведомлений
    """
    try:
        # Удаляем подписку пользователя через репозиторий
        await subscription_repo.delete_user_subscriptions(current_user.id)

        return {"status": "success", "message": "Подписка успешно удалена"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления подписки: {e!s}",
        )


@router.put("/categories", response_model=dict[str, str])
async def update_notification_categories(
    categories_data: NotificationCategoriesUpdate,
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Обновить категории уведомлений для пользователя
    """
    try:
        # Обновляем категории через репозиторий
        await subscription_repo.update_user_categories(
            current_user.id, categories_data.categories
        )

        return {
            "status": "success",
            "message": "Категории уведомлений обновлены",
            "categories": categories_data.categories,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления категорий: {e!s}",
        )


@router.post("/test", response_model=dict[str, str])
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Отправить тестовое push-уведомление
    """
    try:
        # Создаем тестовое уведомление
        notification_data = push_service.create_notification_data(
            title="🎉 Тестовое уведомление",
            body=f"Привет, {current_user.username}! Push-уведомления работают корректно.",
            category="test",
            icon="/pwa-192x192.png",
            url="/profile",
            priority="normal",
        )

        # Отправляем уведомление пользователю через репозиторий
        result = await push_service.send_to_user_via_repo(
            user_id=current_user.id,
            notification_data=notification_data,
            subscription_repo=subscription_repo,
        )

        if result["sent"] > 0:
            return {
                "status": "success",
                "message": "Тестовое уведомление отправлено",
                "sent": str(result["sent"]),
            }
        else:
            return {
                "status": "warning",
                "message": "Нет активных подписок для отправки уведомления",
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отправки тестового уведомления: {e!s}",
        )


@router.post("/send", response_model=dict[str, Any])
async def send_notification(
    notification_data: PushNotificationCreate,
    target_user_id: int = None,
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Отправить push-уведомление (только для администраторов)
    """
    # Проверка прав доступа
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для отправки уведомлений",
        )

    try:
        # Создаем данные уведомления
        push_data = push_service.create_notification_data(
            title=notification_data.title,
            body=notification_data.body,
            category=notification_data.category,
            icon=notification_data.icon,
            image=notification_data.image,
            url=notification_data.url,
            priority=notification_data.priority,
            require_interaction=notification_data.require_interaction,
            silent=notification_data.silent,
        )

        if target_user_id:
            # Отправляем конкретному пользователю
            result = await push_service.send_to_user_via_repo(
                user_id=target_user_id,
                notification_data=push_data,
                subscription_repo=subscription_repo,
                categories=[notification_data.category],
            )
        else:
            # Отправляем всем подписчикам категории
            result = await push_service.send_to_category_via_repo(
                category=notification_data.category,
                notification_data=push_data,
                subscription_repo=subscription_repo,
            )

        return {
            "status": "success",
            "message": "Уведомления отправлены",
            "result": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отправки уведомления: {e!s}",
        )


@router.post("/analytics", response_model=dict[str, str])
async def record_notification_analytics(
    analytics_data: NotificationAnalyticsCreate,
    analytics_repo: NotificationAnalyticsRepository = Depends(
        get_notification_analytics_repository
    ),
):
    """
    Записать аналитику взаимодействия с уведомлениями
    """
    try:
        # Сохраняем аналитику через репозиторий
        await analytics_repo.record_analytics(
            notification_id=analytics_data.notification_id,
            user_id=analytics_data.user_id,
            action=analytics_data.action,
            timestamp=analytics_data.timestamp,
        )

        return {"status": "success", "message": "Аналитика записана"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка записи аналитики: {e!s}",
        )


@router.get("/subscriptions", response_model=list[PushSubscriptionRead])
async def get_user_subscriptions(
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Получить список подписок пользователя
    """
    try:
        # Получаем подписки пользователя через репозиторий
        subscriptions = await subscription_repo.get_user_subscriptions(current_user.id)

        return [
            PushSubscriptionRead.model_validate(subscription)
            for subscription in subscriptions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения подписок: {e!s}",
        )


@router.get("/history", response_model=list[PushNotificationRead])
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    category: str = None,
    current_user: User = Depends(get_current_user),
    notification_repo: PushNotificationRepository = Depends(
        get_push_notification_repository
    ),
):
    """
    Получить историю уведомлений пользователя
    """
    try:
        # Получаем историю уведомлений через репозиторий
        notifications = await notification_repo.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            category=category,
        )

        return [
            PushNotificationRead.model_validate(notification)
            for notification in notifications
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения истории: {e!s}",
        )


@router.get("/stats", response_model=PushNotificationStatsResponse)
async def get_notification_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    analytics_repo: NotificationAnalyticsRepository = Depends(
        get_notification_analytics_repository
    ),
):
    """
    Получить статистику уведомлений (только для администраторов)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра статистики",
        )

    try:
        # Получаем статистику через репозиторий
        stats = await analytics_repo.get_notification_stats(days)

        return PushNotificationStatsResponse.model_validate(stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статистики: {e!s}",
        )


@router.delete("/cleanup", response_model=dict[str, Any])
async def cleanup_expired_subscriptions(
    current_user: User = Depends(get_current_user),
    subscription_repo: PushSubscriptionRepository = Depends(
        get_push_subscription_repository
    ),
):
    """
    Очистить устаревшие подписки (только для администраторов)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для очистки подписок",
        )

    try:
        # Очищаем устаревшие подписки через репозиторий
        cleaned_count = await subscription_repo.cleanup_expired_subscriptions()

        return {
            "status": "success",
            "message": f"Очищено {cleaned_count} устаревших подписок",
            "cleaned_count": cleaned_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка очистки подписок: {e!s}",
        )
