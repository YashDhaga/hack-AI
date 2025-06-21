from sqlalchemy import create_engine, inspect

class DBConfig:
    URL = "postgresql://swiggy_hu7a_user:uAfKvaXxUQYaJG8lvjopofOt18AHJzD0@dpg-d1ba74re5dus73edbkb0-a.oregon-postgres.render.com/swiggy_hu7a"
    SCHEMAS = ["swiggy", "zomato", "magicpin"]

def get_full_schema():
    engine = create_engine(DBConfig.URL)
    inspector = inspect(engine)

    full_schema = ""
    for schema in DBConfig.SCHEMAS:
        full_schema += f"\nSchema: {schema}\n"
        tables = inspector.get_table_names(schema=schema)
        for table in tables:
            full_schema += f"\n  Table: {table}\n"
            columns = inspector.get_columns(table, schema=schema)
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                full_schema += f"    - {col_name}: {col_type}\n"
    return full_schema

def build_prompt_template(schema_str: str) -> str:
    return f"""
You are a smart assistant that understands the entire database schema and can answer user queries by interpreting the schema accurately.

Below is the schema of all the tables across the schemas `swiggy`, `zomato`, and `magicpin`.

Use this schema to:
- Understand what the user means semantically (e.g., "dish" may refer to `item` or `menu_items.name`)
- Compare values in lowercase when matching (e.g., `lower(column_name) = lower('value')`)
- Avoid literal matching of user words to table/column names; infer based on schema meaning.

SCHEMA:
{schema_str}

Respond to user questions accordingly.
"""

if __name__ == "__main__":
    schema_str = get_full_schema()
    prompt = build_prompt_template(schema_str)
    with open("db_schema_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    print("Saved prompt to db_schema_prompt.txt")
