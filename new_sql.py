import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI
from constants import OpenAIConfig, LLMConfig

logger = logging.getLogger(__name__)

load_dotenv()  # Load variables from .env

api_key = os.getenv("OPENAI_API_KEY")
API_KEY_ENV_VAR = os.getenv("SARVAM_API_KEY")

# ────────────────────────────────────────────────────────────────
# BUSINESS SCHEMAS WE CARE ABOUT
# ────────────────────────────────────────────────────────────────
SCHEMAS = ["swiggy", "zomato", "magicpin"]


class DatabaseToolSpec(BaseToolSpec):
    """Natural-language → SQL tool spec (PostgreSQL + OpenAI)."""

    spec_functions = ["run_request"]

    # ────────────────────────────────────────────────────────────
    # INITIALISATION
    # ────────────────────────────────────────────────────────────
    def __init__(self, *, db_url: str) -> None:
        """
        Parameters
        ----------
        db_url : str
            Full SQLAlchemy-style Postgres URL.
        """
        try:
            self.engine = create_engine(db_url, echo=True)

            self.llm = OpenAI(
                api_key=api_key,
                api_base=OpenAIConfig.api_base,
                model="o3",
                timeout=OpenAIConfig.timeout,
                strict_validation=OpenAIConfig.strict_validation,
            )

            # self.llm = OpenAI(
            #     api_key=API_KEY_ENV_VAR,
            #     api_base=LLMConfig.API_BASE,
            #     model=LLMConfig.MODEL,
            #     timeout=LLMConfig.TIMEOUT,
            #     strict_validation=False,
            # )

        except Exception as e:
            logger.error("Error initialising DatabaseToolSpec: %s", e)
            raise

    # ────────────────────────────────────────────────────────────
    # LOW-LEVEL DB HELPERS
    # ────────────────────────────────────────────────────────────
    def execute_query(self, query: str):
        """
        Runs arbitrary SQL.

        Returns
        -------
        • {"ok": True,  "changed": <bool>, "rows": <int>, "data": [...] }  or the result on success
        • {"ok": False, "error": "<message>"}                              on failure
        """
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(query))

                # SELECT / RETURNING  → rows list + changed=False
                if result.returns_rows:
                    # row._mapping is a read-only dict-like view of column→value
                    # rows = [dict(r._mapping) for r in result.fetchall()]
                    return [dict(r._mapping) for r in result.fetchall()]
                else:
                    return result.rowcount

        except (SQLAlchemyError, OperationalError, ProgrammingError) as e:
            logger.error("Query execution error: %s", e)
            return {"ok": False, "error": str(e)}

    def get_schema(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Return { 'schema.table' : [(col_name, col_type), …], … } for every
        table in the swiggy / zomato / magicpin schemas.
        """
        insp = inspect(self.engine)
        schema_map: Dict[str, List[Tuple[str, str]]] = {}

        try:
            for schema in SCHEMAS:
                for tbl in insp.get_table_names(schema=schema):
                    cols = [
                        (col["name"], str(col["type"]))
                        for col in insp.get_columns(tbl, schema=schema)
                    ]
                    schema_map[f"{schema}.{tbl}"] = cols

            if not schema_map:
                logger.warning("No tables found in schemas %s", SCHEMAS)
            return schema_map
        except Exception as e:
            logger.error("Schema reflection error: %s", e)
            return {}

    # ────────────────────────────────────────────────────────────
    # PROMPT & LLM
    # ────────────────────────────────────────────────────────────
    @staticmethod
    def _sql_prompt(
        question: str, schema: Dict[str, List[Tuple[str, str]]]
    ) -> List[ChatMessage]:
        """Build messages for ChatCompletion."""
        schema_str = "\n".join(
            f"Table: {tbl}\nColumns: {{ {', '.join(c[0] for c in cols)} }}"
            for tbl, cols in schema.items()
        )

        user_prompt = (
            "You are an expert SQL generator. Convert the following question "
            "into a syntactically correct PostgreSQL query based on the given schema.\n\n"
            f"Schema:\n{schema_str}\n\n"
            f"Question: {question}\nSQL Query:"
        )

        sys_prompt = (
            "You generate SQL queries.\n"
            "Rules:\n"
            "1. Respond with ONLY the SQL statement.\n"
            "2. No markdown fences, explanations, or apologies."
            "3. If a flag column is SMALLINT or INTEGER, compare with 1/0   (NOT true/false).\n"
            "4. In promos table, status column is either live or scheduled, not 1/0."
            "5. Always compare columns of type VARCHAR in lowercase. "
            "6. Use table store_analytics for all analytics or insights related queries."
            "7. Refer to status column - active/inactive in stores table to find out whether restaurants are open or closed."
        )

        return [
            ChatMessage(role=MessageRole.SYSTEM, content=sys_prompt),
            ChatMessage(role=MessageRole.USER, content=user_prompt),
        ]

    def generate_sql(
        self, question: str, schema: Dict[str, List[Tuple[str, str]]]
    ) -> Optional[str]:
        """Ask the LLM for a query."""
        try:
            msgs = self._sql_prompt(question, schema)
            resp = self.llm.chat(msgs)
            return resp.message.content.strip()
        except Exception as e:
            logger.error("LLM SQL generation error: %s", e)
            return None

    # ────────────────────────────────────────────────────────────
    # PUBLIC ENTRY-POINT
    # ────────────────────────────────────────────────────────────
    def run_request(self, question: str):
        """End-to-end: NL → SQL → DB → result rows."""
        schema = self.get_schema()
        if not schema:
            logger.error("Could not retrieve schema; aborting.")
            return None

        sql_query = self.generate_sql(question, schema)
        if not sql_query:
            logger.error("Failed to generate SQL; aborting.")
            return None

        logger.debug("Generated SQL: %s", sql_query)
        return self.execute_query(sql_query)

    # ────────────────────────────────────────────────────────────
    # CLEAN-UP
    # ────────────────────────────────────────────────────────────
    def close_connection(self):
        try:
            self.engine.dispose()
        except Exception as e:
            logger.error("Error closing engine: %s", e)
