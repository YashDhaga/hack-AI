from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
# from openai import OpenAI
from constants import LLMConfig, AgentConfig, OpenAIConfig
import os
from llama_index.core.prompts import PromptTemplate
from llama_index.core.memory import ChatMemoryBuffer
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

api_key = os.getenv("OPENAI_API_KEY")
API_KEY_ENV_VAR = os.getenv("SARVAM_API_KEY")

def create_agent():
    with open("db_schema_prompt.txt", "r", encoding="utf-8") as f:
        prompt_text = f.read()

    memory = ChatMemoryBuffer.from_defaults(token_limit=1000)   
    system_prompt = PromptTemplate(prompt_text)

    llm = OpenAI(
        api_key=API_KEY_ENV_VAR,
        api_base=LLMConfig.API_BASE,
        model=LLMConfig.MODEL,
        timeout=LLMConfig.TIMEOUT,
        strict_validation=False,
    )

    # from llama_index.llms.openai import OpenAI
    # llm = OpenAI(
    #     api_key=api_key,
    #     api_base="https://api.openai.com/v1",  
    #     model="gpt-4o-mini",
    #     timeout=240,
    #     strict_validation=False,
    # )

    # tools = build_crud_tools()
    from sql_tester import tool
    tools = tool.to_tool_list()
    return ReActAgent.from_tools(
        tools,
        llm=llm,
        verbose=AgentConfig.VERBOSE,
        system_prompt=system_prompt,
        memory=memory,
        max_iterations = 25
    )
