from typing import Dict, Any, List
import os

from sqlalchemy import (
    create_engine, MetaData, Table,
    insert, select, update, delete, and_
)
from sqlalchemy.engine import Engine
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from constants import DBConfig


# ────────── helpers ──────────
def _table_for(engine: Engine, fq_name: str) -> Table:
    if fq_name not in DBConfig.TABLES:
        raise ValueError(f"{fq_name} not whitelisted")

    schema, name = fq_name.split(".", 1)
    meta = MetaData(schema=schema)
    meta.reflect(bind=engine, only=[name])
    return meta.tables[f"{schema}.{name}"]     # key includes schema


def _clause(table: Table, filters: Dict[str, Any]):
    return and_(*(table.c[k] == v for k, v in filters.items())) if filters else True


class CRUDToolSpec(BaseToolSpec):
    """CRUD helpers for the aggregator schemas."""

    # Order matters: put read_rows first so it's chosen by default.
    spec_functions = [
        "read_rows",
        "create_row",
        "update_rows",
        "delete_rows",
    ]

    def __init__(self, engine: Engine):
        self._engine = engine

    # ---------------- CREATE ----------------
    def create_row(self, table: str, values: Dict[str, Any]):
        """
        Insert exactly ONE record into <schema>.<table>.
        Example:
            create_row(
                table="swiggy.merchants",
                values={"merchant_id": 1, "display_name": "Foo"}
            )
        """
        tbl = _table_for(self._engine, table)
        stmt = insert(tbl).values(**dict(values))
        with self._engine.begin() as conn:
            res = conn.execute(stmt)
            return {"rows_affected": res.rowcount}

    # ---------------- READ ------------------
    def read_rows(
        self,
        table: str,
        filters: Dict[str, Any] | None = None,
        limit: int | None = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch up to <limit> rows that match equality filters.
        Example:
            read_rows(
                table="zomato.orders",
                filters={"store_id": 42},
                limit=3
            )
        """
        tbl = _table_for(self._engine, table)
        stmt = select(tbl).where(_clause(tbl, filters)).limit(limit)
        with self._engine.begin() as conn:
            res = conn.execute(stmt)
            return [dict(r._mapping) for r in res]

    # ---------------- UPDATE ----------------
    def update_rows(
        self,
        table: str,
        filters: Dict[str, Any],
        values: Dict[str, Any],
    ):
        """
        Update rows that match equality filters.
        Example:
            update_rows(
                table="magicpin.promos",
                filters={"promo_id": 55},
                values={"status": "expired"}
            )
        """
        tbl = _table_for(self._engine, table)
        stmt = update(tbl).where(_clause(tbl, filters)).values(**values)
        with self._engine.begin() as conn:
            res = conn.execute(stmt)
            return {"rows_affected": res.rowcount}

    # ---------------- DELETE ----------------
    def delete_rows(self, table: str, filters: Dict[str, Any]):
        """
        Delete rows that match equality filters.
        Example:
            delete_rows(
                table="swiggy.scheduled_tasks",
                filters={"task_id": 77}
            )
        """
        tbl = _table_for(self._engine, table)
        stmt = delete(tbl).where(_clause(tbl, filters))
        with self._engine.begin() as conn:
            res = conn.execute(stmt)
            return {"rows_affected": res.rowcount}


# ────────── factory ──────────
def build_crud_tools():
    db_url = DBConfig.URL_ENV_VAR
    if not db_url:
        raise RuntimeError(
            f"Environment variable {DBConfig.URL_ENV_VAR} is missing."
        )

    engine = create_engine(db_url, future=True)
    spec = CRUDToolSpec(engine)
    return spec.to_tool_list()                       # → list[Tool] for ReActAgent
