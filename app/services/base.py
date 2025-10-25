"""通用的仓储与服务基类，封装常见 CRUD 操作。"""

from __future__ import annotations

from typing import Any, Generic, Iterable, Optional, Sequence, Type, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.services.exceptions import NotFoundError

ModelT = TypeVar("ModelT", bound=Base)


class CRUDRepository(Generic[ModelT]):
    """提供基础 CRUD 能力，供领域服务组合使用。"""

    def __init__(self, model: Type[ModelT]) -> None:
        self.model = model

    def get(self, db: Session, *, id: Any) -> Optional[ModelT]:
        return db.get(self.model, id)

    def get_or_raise(self, db: Session, *, id: Any) -> ModelT:
        instance = self.get(db, id=id)
        if instance is None:
            raise NotFoundError(f"{self.model.__name__}<{id}> not found")
        return instance

    def list(self, db: Session, *, stmt: Optional[Select[tuple[ModelT]]] = None) -> Sequence[ModelT]:
        query = stmt or select(self.model)
        return db.execute(query).scalars().all()

    def first(self, db: Session, *, stmt: Optional[Select[tuple[ModelT]]] = None) -> Optional[ModelT]:
        query = stmt or select(self.model)
        return db.execute(query).scalars().first()

    def create(self, db: Session, *, obj_in: dict[str, Any] | Any) -> ModelT:
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        instance = self.model(**data)
        db.add(instance)
        db.flush()
        db.refresh(instance)
        return instance

    def bulk_create(self, db: Session, *, objs_in: Iterable[dict[str, Any] | Any]) -> list[ModelT]:
        instances: list[ModelT] = []
        for obj in objs_in:
            data = obj if isinstance(obj, dict) else obj.model_dump(exclude_unset=True)
            instance = self.model(**data)
            db.add(instance)
            instances.append(instance)
        db.flush()
        for instance in instances:
            db.refresh(instance)
        return instances

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelT,
        obj_in: dict[str, Any] | Any,
    ) -> ModelT:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, db_obj: ModelT) -> None:
        db.delete(db_obj)
        db.flush()
