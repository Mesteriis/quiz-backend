import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import logging
from typing import Any, Optional

from pywebpush import WebPushException, webpush
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Сервис для отправки push-уведомлений"""

    def __init__(self):
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_claims = {"sub": f"mailto:{settings.VAPID_EMAIL}"}
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def send_notification(
        self,
        subscription_info: dict[str, Any],
        notification_data: dict[str, Any],
        vapid_private_key: Optional[str] = None,
        vapid_claims: Optional[dict[str, str]] = None,
    ) -> bool:
        """
        Отправляет push-уведомление

        Args:
            subscription_info: Данные подписки браузера
            notification_data: Данные уведомления
            vapid_private_key: Приватный VAPID ключ
            vapid_claims: VAPID claims

        Returns:
            bool: True если отправлено успешно
        """
        try:
            # Подготавливаем данные для отправки
            payload = json.dumps(notification_data)

            # Используем переданные параметры или значения по умолчанию
            private_key = vapid_private_key or self.vapid_private_key
            claims = vapid_claims or self.vapid_claims

            # Отправляем в отдельном потоке, чтобы не блокировать async
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._send_webpush,
                subscription_info,
                payload,
                private_key,
                claims,
            )

            logger.info(
                f"Push notification sent successfully to {subscription_info.get('endpoint', 'unknown')}"
            )
            return True

        except WebPushException as e:
            logger.error(f"WebPush error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    def _send_webpush(
        self,
        subscription_info: dict[str, Any],
        payload: str,
        vapid_private_key: str,
        vapid_claims: dict[str, str],
    ):
        """
        Синхронная отправка через pywebpush
        """
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims,
        )

    async def send_to_user(
        self,
        user_id: int,
        notification_data: dict[str, Any],
        db: AsyncSession,
        categories: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Отправляет уведомление всем активным подпискам пользователя

        Args:
            user_id: ID пользователя
            notification_data: Данные уведомления
            db: Сессия базы данных
            categories: Список категорий для фильтрации

        Returns:
            Dict: Результат отправки
        """
        try:
            # Получаем активные подписки пользователя
            subscriptions = await self._get_user_subscriptions(user_id, db, categories)

            if not subscriptions:
                logger.warning(f"No active subscriptions found for user {user_id}")
                return {"sent": 0, "failed": 0, "subscriptions": []}

            # Отправляем уведомления
            sent_count = 0
            failed_count = 0
            results = []

            for subscription in subscriptions:
                try:
                    subscription_info = {
                        "endpoint": subscription["endpoint"],
                        "keys": {
                            "p256dh": subscription["p256dh_key"],
                            "auth": subscription["auth_key"],
                        },
                    }

                    success = await self.send_notification(
                        subscription_info, notification_data
                    )

                    if success:
                        sent_count += 1
                        await self._update_subscription_status(
                            subscription["id"], "sent", db
                        )
                    else:
                        failed_count += 1
                        await self._update_subscription_status(
                            subscription["id"], "failed", db
                        )

                    results.append(
                        {"subscription_id": subscription["id"], "success": success}
                    )

                except Exception as e:
                    logger.error(
                        f"Error sending to subscription {subscription['id']}: {e}"
                    )
                    failed_count += 1
                    await self._update_subscription_status(
                        subscription["id"], "failed", db
                    )

                    results.append(
                        {
                            "subscription_id": subscription["id"],
                            "success": False,
                            "error": str(e),
                        }
                    )

            return {
                "sent": sent_count,
                "failed": failed_count,
                "subscriptions": results,
            }

        except Exception as e:
            logger.error(f"Error sending notifications to user {user_id}: {e}")
            return {"sent": 0, "failed": 1, "error": str(e)}

    async def send_to_category(
        self,
        category: str,
        notification_data: dict[str, Any],
        db: AsyncSession,
        user_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        """
        Отправляет уведомление всем подпискам определенной категории

        Args:
            category: Категория уведомления
            notification_data: Данные уведомления
            db: Сессия базы данных
            user_ids: Список ID пользователей для ограничения

        Returns:
            Dict: Результат отправки
        """
        try:
            # Получаем подписки по категории
            subscriptions = await self._get_category_subscriptions(
                category, db, user_ids
            )

            if not subscriptions:
                logger.warning(f"No subscriptions found for category {category}")
                return {"sent": 0, "failed": 0, "subscriptions": []}

            # Отправляем уведомления пакетами
            batch_size = 50
            total_sent = 0
            total_failed = 0
            all_results = []

            for i in range(0, len(subscriptions), batch_size):
                batch = subscriptions[i : i + batch_size]
                batch_results = await self._send_batch(batch, notification_data, db)

                total_sent += batch_results["sent"]
                total_failed += batch_results["failed"]
                all_results.extend(batch_results["subscriptions"])

                # Небольшая задержка между пакетами
                await asyncio.sleep(0.1)

            return {
                "sent": total_sent,
                "failed": total_failed,
                "subscriptions": all_results,
            }

        except Exception as e:
            logger.error(f"Error sending notifications to category {category}: {e}")
            return {"sent": 0, "failed": 1, "error": str(e)}

    async def _send_batch(
        self,
        subscriptions: list[dict[str, Any]],
        notification_data: dict[str, Any],
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Отправляет пакет уведомлений"""

        tasks = []
        for subscription in subscriptions:
            task = self._send_single_notification(subscription, notification_data, db)
            tasks.append(task)

        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sent_count = sum(1 for r in results if r is True)
        failed_count = len(results) - sent_count

        return {
            "sent": sent_count,
            "failed": failed_count,
            "subscriptions": [
                {
                    "subscription_id": sub["id"],
                    "success": result is True,
                    "error": str(result) if result is not True else None,
                }
                for sub, result in zip(subscriptions, results)
            ],
        }

    async def _send_single_notification(
        self,
        subscription: dict[str, Any],
        notification_data: dict[str, Any],
        db: AsyncSession,
    ) -> bool:
        """Отправляет одно уведомление"""
        try:
            subscription_info = {
                "endpoint": subscription["endpoint"],
                "keys": {
                    "p256dh": subscription["p256dh_key"],
                    "auth": subscription["auth_key"],
                },
            }

            success = await self.send_notification(subscription_info, notification_data)

            status = "sent" if success else "failed"
            await self._update_subscription_status(subscription["id"], status, db)

            return success

        except Exception as e:
            logger.error(
                f"Error sending notification to subscription {subscription['id']}: {e}"
            )
            await self._update_subscription_status(subscription["id"], "failed", db)
            return False

    async def _get_user_subscriptions(
        self, user_id: int, db: AsyncSession, categories: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Получает активные подписки пользователя"""
        # Временная реализация без ORM
        # В реальном приложении здесь будет запрос к базе данных
        return []

    async def _get_category_subscriptions(
        self, category: str, db: AsyncSession, user_ids: Optional[list[int]] = None
    ) -> list[dict[str, Any]]:
        """Получает подписки по категории"""
        # Временная реализация без ORM
        # В реальном приложении здесь будет запрос к базе данных
        return []

    async def _update_subscription_status(
        self, subscription_id: int, status: str, db: AsyncSession
    ):
        """Обновляет статус подписки"""
        # Временная реализация без ORM
        # В реальном приложении здесь будет обновление в базе данных
        pass

    def create_notification_data(
        self,
        title: str,
        body: str,
        category: str,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        url: Optional[str] = None,
        priority: str = "normal",
        require_interaction: bool = False,
        silent: bool = False,
        vibrate: Optional[list[int]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Создает данные уведомления в правильном формате

        Args:
            title: Заголовок
            body: Текст
            category: Категория
            icon: URL иконки
            image: URL изображения
            url: URL для перехода
            priority: Приоритет
            require_interaction: Требовать взаимодействие
            silent: Тихое уведомление
            vibrate: Паттерн вибрации
            **kwargs: Дополнительные параметры

        Returns:
            Dict: Данные уведомления
        """
        notification_data = {
            "title": title,
            "body": body,
            "category": category,
            "icon": icon or "/pwa-192x192.png",
            "badge": "/pwa-192x192.png",
            "url": url or "/",
            "priority": priority,
            "requireInteraction": require_interaction,
            "silent": silent,
            "vibrate": vibrate or [100, 50, 100],
            "timestamp": int(datetime.now().timestamp() * 1000),
            "id": kwargs.get("id", str(int(datetime.now().timestamp() * 1000))),
        }

        if image:
            notification_data["image"] = image

        # Добавляем дополнительные параметры
        for key, value in kwargs.items():
            if key not in notification_data:
                notification_data[key] = value

        return notification_data

    def get_vapid_public_key(self) -> str:
        """Возвращает публичный VAPID ключ"""
        return self.vapid_public_key

    async def cleanup_expired_subscriptions(self, db: AsyncSession) -> int:
        """Очищает устаревшие подписки"""
        # Временная реализация
        # В реальном приложении здесь будет очистка базы данных
        return 0


# Создаем глобальный экземпляр сервиса
push_service = PushNotificationService()


async def send_push_notification(
    subscription_info: dict[str, Any],
    notification_data: dict[str, Any],
    vapid_private_key: Optional[str] = None,
    vapid_claims: Optional[dict[str, str]] = None,
) -> bool:
    """
    Convenience function to send push notification.

    Args:
        subscription_info: Browser subscription data
        notification_data: Notification data
        vapid_private_key: VAPID private key
        vapid_claims: VAPID claims

    Returns:
        bool: True if sent successfully
    """
    return await push_service.send_notification(
        subscription_info, notification_data, vapid_private_key, vapid_claims
    )
