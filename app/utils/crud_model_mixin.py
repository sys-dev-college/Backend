from collections.abc import Iterable
from typing import Any, Dict

from sqlalchemy import (
    and_,
    delete,
    or_,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


class ModelCRUDMixin:
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    @classmethod
    async def get_instances_with_loaded_relations(
        cls,
        session: AsyncSession,
        filters: Dict[str, Any],
        relations: Iterable[str],
    ):
        relations_load = [joinedload(getattr(cls, name)) for name in relations]
        filter_statements = [getattr(cls, name) == value for name, value in filters.items()]
        cls_statement = select(cls).where(and_(*filter_statements)).options(*relations_load)
        results_with_relations = await session.execute(cls_statement)
        return results_with_relations.unique().scalars().all()

    @classmethod
    async def get_instance_attributes_by_parameter(
        cls,
        session: AsyncSession,
        parameter: str,
        parameter_values: Iterable[Any],
        attributes: Iterable[str],
    ):
        document_attributes = [getattr(cls, name) for name in attributes]
        query = select(*document_attributes).where(getattr(cls, parameter).in_(parameter_values))
        result = await session.execute(query)
        return result.fetchall()

    @classmethod
    async def get_attributes_by_AND_parameters(  # noqa: N802
        cls,
        filters: Dict[str, Any],
        attributes: Iterable[str],
        session: AsyncSession,
    ):
        filter_list = [getattr(cls, name) == value for name, value in filters.items()]
        columns = [getattr(cls, name) for name in attributes]
        filtered_statement = select(*columns).where(and_(*filter_list))
        result = await session.execute(filtered_statement)
        return result.fetchall()

    @classmethod
    async def get_attriblutes_by_OR_parameters(  # noqa: N802
        cls,
        filters: Dict[str, Any],
        attributes: Iterable[str],
        session: AsyncSession,
    ):
        filter_list = [getattr(cls, name) == value for name, value in filters.items()]
        columns = [getattr(cls, name) for name in attributes]
        filtered_statement = select(*columns).where(or_(*filter_list))
        result = await session.execute(filtered_statement)
        return result.fetchall()

    @classmethod
    async def get_attributes_unconditionally(
        cls,
        attributes: Iterable[str],
        session: AsyncSession,
    ):
        columns = [getattr(cls, name) for name in attributes]
        filtered_statement = select(*columns)
        result = await session.execute(filtered_statement)
        return result.fetchall()

    @classmethod
    async def get_all(
        cls,
        session: AsyncSession,
        attributes: Iterable[str],
    ):
        columns = [getattr(cls, name) for name in attributes]
        query = select(*columns)
        result = await session.execute(query)
        return result.fetchall()

    @classmethod
    async def update_attributes_by_conditions(
        cls,
        session: AsyncSession,
        filters: Dict[str, Any],
        attributes_vs_values: Dict[str, Any],
    ):
        filters_list = [getattr(cls, name) == value for name, value in filters.items()]
        update_stmt = update(cls).values(**attributes_vs_values).where(and_(*filters_list))
        await session.execute(update_stmt)

    @classmethod
    async def delete_by_conditions(
        cls,
        session: AsyncSession,
        filters: Dict[str, Any],
    ):
        filters_list = [getattr(cls, name) == value for name, value in filters.items()]
        delete_stmt = delete(cls).where(and_(*filters_list))
        await session.execute(delete_stmt)
