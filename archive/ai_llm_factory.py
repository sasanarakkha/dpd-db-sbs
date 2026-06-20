
import re
import json
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap

class ChatDeepSeekWrapper():
    def __init__(self, framework: str, api_key: str, model: str = "deepseek-chat", temperature: float = 0.7):
        self.framework = framework
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
    
    def langchain_deekseek(self):
        # Create an instance of ChatDeepSeek from langchain_deepseek
        return ChatDeepSeek(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if self.framework == "langchain":
             # Create an instance of ChatDeepSeek from langchain_deepseek
            deekseek_llm = self.langchain_deekseek()
            # Define the system and human prompts
            messages = [
                (
                    "system",
                    system_prompt,
                ),
                ("human", user_prompt),
            ]
            ai_msg = deekseek_llm.invoke(messages)
            response_content = ai_msg.content
            return response_content

        # Fallback return statement if the provider is not "langchain"
        return "Invalid provider type."
    
    def batch_processing(self, system_prompt: str, user_prompt: str, batch_input: list[dict]) -> list[dict]:
        if self.framework == "langchain":
            # Step 1: Setup DeepSeek LLM
            deekseek_llm = self.langchain_deekseek()

            # Step 2: Create LangChain-compatible prompt
            prompt = ChatPromptTemplate([
                ("system", system_prompt.strip()),
                ("human", user_prompt.strip()),
            ])

            # To check the valid input variables
            # print(prompt.input_variables)

            # Step 3: Create chain using `prompt | llm`
            chain = prompt | deekseek_llm

            # Step 4: Use RunnableMap to batch it
            batch_chain = RunnableMap({"response": chain})
            result = batch_chain.batch(batch_input)

            # Step 5: Clean + parse results
            parsed_result = []

            for i, r in enumerate(result):
                raw = r["response"].content
                cleaned = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.DOTALL)
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    try:
                        parsed = json.loads(json.loads(cleaned)) # fallback for escaped JSON
                    except:
                        parsed = {"error": "Failed to parse", "raw": raw}
                parsed_result.append(parsed)

            return parsed_result

        # Return empty list if framework doesn't match
        return []


class ChatOpenAIWrapper():
    def __init__(self, framework: str, api_key: str, model: str = "gpt-4.1", temperature: float = 0.7):
        self.framework = framework
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def langchain_openai(self):
        # Create an instance of ChatOpenAI from langchain_openai
        return ChatOpenAI(
            model_name=self.model,
            openai_api_key=self.api_key,
            temperature=self.temperature
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if self.framework == "langchain":
            openai_llm = self.langchain_openai()
            messages = [
                (
                    "system",
                    system_prompt,
                ),
                ("human", user_prompt),
            ]
            ai_msg = openai_llm.invoke(messages)
            response_content = ai_msg.content
            return response_content
        return "Invalid provider type."

    def batch_processing(self, system_prompt: str, user_prompt: str, batch_input: list[dict]) -> list[dict]:
        if self.framework == "langchain":
            openai_llm = self.langchain_openai()
            prompt = ChatPromptTemplate([("system", system_prompt.strip()), ("human", user_prompt.strip())])
            chain = prompt | openai_llm
            batch_chain = RunnableMap({"response": chain})
            result = batch_chain.batch(batch_input)
            parsed_result = []
            for r in result:
                raw = r["response"].content
                cleaned = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.DOTALL)
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    try:
                        parsed = json.loads(json.loads(cleaned)) # fallback for escaped JSON
                    except:
                        parsed = {"error": "Failed to parse", "raw": raw}
                parsed_result.append(parsed)
            return parsed_result
        return []


class LLMFactory:
    def __init__(self, provider: str, framework: str, model: str, api_key: str,  temperature: float = 0.7):
        self.provider = provider
        self.framework = framework
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
    
    def get_llm(self):
        if self.provider == "deepseek":
            return ChatDeepSeekWrapper(
                framework=self.framework,
                model=self.model,
                api_key=self.api_key,
                temperature=self.temperature
            )
        elif self.provider == "openai":
            return ChatOpenAIWrapper(
                framework=self.framework,
                model=self.model,
                api_key=self.api_key,
                temperature=self.temperature
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")