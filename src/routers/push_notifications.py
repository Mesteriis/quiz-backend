from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models.user import User
from schemas.push_notification import (
    NotificationAnalytics,
    NotificationCategoriesUpdate,
    NotificationStats,
    PushNotificationCreate,
    PushNotificationResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    VapidKeyResponse,
)
from services.jwt_service import get_current_user
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
    db: AsyncSession = Depends(get_async_session),
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

        # Здесь будет сохранение в базу данных
        # Временная заглушка
        subscription_id = 1

        # Сохраняем подписку в localStorage frontend (через ответ)
        return {
            "status": "success",
            "message": "Подписка успешно создана",
            "subscription_id": str(subscription_id),
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
    db: AsyncSession = Depends(get_async_session),
):
    """
    Отписаться от push-уведомлений
    """
    try:
        # Здесь будет удаление подписки из базы данных
        # Временная заглушка

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
    db: AsyncSession = Depends(get_async_session),
):
    """
    Обновить категории уведомлений для пользователя
    """
    try:
        # Здесь будет обновление категорий в базе данных
        # Временная заглушка

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
    db: AsyncSession = Depends(get_async_session),
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

        # Отправляем уведомление пользователю
        result = await push_service.send_to_user(
            user_id=current_user.id, notification_data=notification_data, db=db
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
    db: AsyncSession = Depends(get_async_session),
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
            result = await push_service.send_to_user(
                user_id=target_user_id,
                notification_data=push_data,
                db=db,
                categories=[notification_data.category],
            )
        else:
            # Отправляем всем подписчикам категории
            result = await push_service.send_to_category(
                category=notification_data.category, notification_data=push_data, db=db
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
    analytics_data: NotificationAnalytics, db: AsyncSession = Depends(get_async_session)
):
    """
    Записать аналитику взаимодействия с уведомлениями
    """
    try:
        # Здесь будет сохранение аналитики в базу данных
        # Временная заглушка

        return {"status": "success", "message": "Аналитика записана"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка записи аналитики: {e!s}",
        )


@router.get("/subscriptions", response_model=list[PushSubscriptionResponse])
async def get_user_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Получить список подписок пользователя
    """
    try:
        # Здесь будет получение подписок из базы данных
        # Временная заглушка
        return []

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения подписок: {e!s}",
        )


@router.get("/history", response_model=list[PushNotificationResponse])
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    category: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Получить историю уведомлений пользователя
    """
    try:
        # Здесь будет получение истории из базы данных
        # Временная заглушка
        return []

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения истории: {e!s}",
        )


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
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
        # Здесь будет получение статистики из базы данных
        # Временная заглушка
        return NotificationStats(
            total_sent=0,
            total_delivered=0,
            total_clicked=0,
            total_dismissed=0,
            categories_stats={},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статистики: {e!s}",
        )


@router.delete("/cleanup", response_model=dict[str, Any])
async def cleanup_expired_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
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
        cleaned_count = await push_service.cleanup_expired_subscriptions(db)

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
