"""
Base repository class for the Quiz App.

This module provides the base repository class with common CRUD operations
that can be inherited by specific model repositories.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import Base

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Base repository class with common CRUD operations.

    This class provides standard database operations that can be used
    by all model-specific repositories.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record in the database.

        Args:
            obj_in: Pydantic schema with create data

        Returns:
            Created model instance
        """
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get(
        self, id: int, *, load_relationships: bool = False
    ) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            id: Record ID
            load_relationships: Whether to load relationships

        Returns:
            Model instance or None
        """
        query = select(self.model).where(self.model.id == id)

        if load_relationships:
            # Load all relationships - можно переопределить в наследниках
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_field(
        self,
        field_name: str,
        field_value: Any,
        *,
        load_relationships: bool = False,
    ) -> Optional[ModelType]:
        """
        Get a record by any field.

        Args:
            field_name: Field name to search by
            field_value: Field value to search for
            load_relationships: Whether to load relationships

        Returns:
            Model instance or None
        """
        query = select(self.model).where(getattr(self.model, field_name) == field_value)

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        load_relationships: bool = False,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            load_relationships: Whether to load relationships

        Returns:
            List of model instances
        """
        query = select(self.model).offset(skip).limit(limit)

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            db_obj: Existing model instance
            obj_in: Update data (Pydantic schema or dict)

        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            Deleted model instance or None
        """
        db_obj = await self.get(id=id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
        return db_obj

    async def remove(self, id: int) -> Optional[ModelType]:
        """
        Remove a record by ID (alias for delete).

        Args:
            id: Record ID

        Returns:
            Deleted model instance or None
        """
        return await self.delete(id=id)

    async def count(self) -> int:
        """
        Count total records.

        Returns:
            Total count of records
        """
        query = select(func.count(self.model.id))
        result = await self.db.execute(query)
        return result.scalar()

    async def exists(self, *, id: int) -> bool:
        """
        Check if a record exists by ID.

        Args:
            id: Record ID

        Returns:
            True if record exists, False otherwise
        """
        db_obj = await self.get(id=id)
        return db_obj is not None

    async def bulk_create(self, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            objs_in: List of Pydantic schemas with create data

        Returns:
            List of created model instances
        """
        db_objs = []
        for obj_in in objs_in:
            obj_data = obj_in.model_dump()
            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)

        self.db.add_all(db_objs)
        await self.db.commit()

        for db_obj in db_objs:
            await self.db.refresh(db_obj)

        return db_objs

    async def bulk_update(self, *, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in bulk.

        Args:
            updates: List of update dictionaries with 'id' and update fields

        Returns:
            Number of updated records
        """
        updated_count = 0
        for update_data in updates:
            record_id = update_data.pop("id")
            if update_data:  # Only update if there are fields to update
                query = (
                    update(self.model)
                    .where(self.model.id == record_id)
                    .values(**update_data)
                )
                result = await self.db.execute(query)
                updated_count += result.rowcount

        await self.db.commit()
        return updated_count

    async def bulk_delete(self, *, ids: List[int]) -> int:
        """
        Delete multiple records in bulk.

        Args:
            ids: List of record IDs to delete

        Returns:
            Number of deleted records
        """
        query = delete(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def get_by_field_list(
        self,
        field_name: str,
        field_values: List[Any],
        *,
        load_relationships: bool = False,
    ) -> List[ModelType]:
        """
        Get records by field values (IN clause).

        Args:
            field_name: Field name to search by
            field_values: List of field values to search for
            load_relationships: Whether to load relationships

        Returns:
            List of model instances
        """
        query = select(self.model).where(
            getattr(self.model, field_name).in_(field_values)
        )

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().all()
