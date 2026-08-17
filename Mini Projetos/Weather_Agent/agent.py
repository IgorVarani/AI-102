from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json

from tools import get_weather

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

client = AzureOpenAI(
    api_key = api_key,
    api_version = "2024-02-15-preview",
    azure_endpoint = endpoint
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Consultar o clima de qualquer cidade do mundo",
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {
                        "type": "string",
                        "description": "O nome da cidade para buscar o clima"
                    }
                },
                "required": ["cidade"]
            }
        }
    }
]

def main():
    print("\n Agente de Clima \n")

    messages = []
    while True:
        user_input = input("Pergunta: ")
        if user_input.lower() == "sair":
            print("Encerrando o sistema!")
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        
        print("\n[DEBUG tool_calls]:", message.tool_calls)
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            name = tool_call.function.name

            args = json.loads(tool_call.function.arguments)

            resultado = get_weather(**args)
            print("\n[TOOL RESULTADO]: ", resultado)
            messages.append(message)
            messages