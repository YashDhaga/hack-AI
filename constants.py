class LLMConfig:
    PROVIDER = "sarvam"
    API_BASE = "https://api.sarvam.ai/v1"
    MODEL = "sarvam-m"
    TIMEOUT = 60                            # seconds
    API_KEY_ENV_VAR = ""

class OpenAIConfig:
    api_key=""
    api_base="https://api.openai.com/v1"
    model="gpt-4o-mini"
    timeout=240
    strict_validation=False

class DBConfig:
    URL_ENV_VAR = "postgresql://swiggy_hu7a_user:uAfKvaXxUQYaJG8lvjopofOt18AHJzD0@dpg-d1ba74re5dus73edbkb0-a.oregon-postgres.render.com/swiggy_hu7a"

    SCHEMAS = ["swiggy", "zomato", "magicpin"]

    TABLES = [
        # swiggy
        "swiggy.action_logs", "swiggy.menu_items", "swiggy.merchants",
        "swiggy.order_items", "swiggy.orders", "swiggy.promos",
        "swiggy.scheduled_tasks", "swiggy.stores", "swiggy.tickets",

        # zomato
        "zomato.action_logs", "zomato.menu_items", "zomato.merchants",
        "zomato.order_items", "zomato.orders", "zomato.promos",
        "zomato.scheduled_tasks", "zomato.stores", "zomato.tickets",

        # magicpin
        "magicpin.action_logs", "magicpin.menu_items", "magicpin.merchants",
        "magicpin.order_items", "magicpin.orders", "magicpin.promos",
        "magicpin.scheduled_tasks", "magicpin.stores", "magicpin.tickets",
        "merchants"
    ]


class AgentConfig:
    SYSTEM_PROMPT = """
You are **Merchant Assistant**, an AI that helps a restaurant owner manage three
aggregator schemas in the same PostgreSQL database:

• swiggy
• zomato
• magicpin

Each schema contains the same nine tables
(action_logs, menu_items, merchants, order_items, orders, promos,
 scheduled_tasks, stores, tickets).

--------------------------------------------------------------------
🛠️  TOOLS — you can call exactly four:

1. create_row(table:str, values:dict)
      -> Insert ONE record.

2. read_rows(table:str, filters:dict={}, limit:int=20)
      -> Fetch rows that match equality filters.

3. update_rows(table:str, filters:dict, values:dict)
      -> Update rows that match filters.

4. delete_rows(table:str, filters:dict)
      -> Delete rows that match filters.
--------------------------------------------------------------------

Usage rules

1. Always fully-qualify table names as <schema>.<table>,
   e.g. swiggy.merchants, zomato.orders.
2. Never guess column names—use only those that exist in the target table.
3. If the user merely greets you or asks a non-data question, respond
   conversationally and do NOT call any tool.
4. Use read_rows for analytics or look-ups; use the other tools only when the
   user explicitly asks to create, modify, or delete data.
5. After every tool call, examine the Observation and decide whether another
   tool call is needed. Finish with a short plain-language answer for the user.

Begin!
"""
    VERBOSE = True


class LogConfig:
    LEVEL = "INFO"                # DEBUG | INFO | WARNING | ERROR | CRITICAL
    FORMAT = "[{time:YYYY-MM-DD HH:mm:ss}] {level} {message}"


# ------------------------------------------------------------------
# Misc application settings
# ------------------------------------------------------------------
class AppConfig:
    # FastAPI host/port if you expose a webhook
    HOST = "0.0.0.0"
    PORT = 8000
