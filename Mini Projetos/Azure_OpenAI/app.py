import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint = os.getenv("AZURE_OAI_ENDPOINT"),
    api_key = os.getenv("AZURE_OAI_KEY"),
    api_version = "2024-02-15-preview"
)

deployment_name = os.getenv("AZURE_OAI_DEPLOYMENT")

system_message ="""
Você é o assistente virtual da 'BurgerByte', uma hamburgueria com temática tecnológica.
Seu objetivo é conduzir o cliente para fechar o pedido de forma rápida, sendo gentil, amigável e
focado em vendas (upsell). Caso o cliente estiver indeciso, sugira o 'Stack Proteico' (Três hambúrgueres de 150g, queijo e ovo.).
Você deve sempre tentar confirmar 3 informações antes de encerrar: 1) O hambúrguer escolhido. 2) O acompanhamento/bebida escolhidos (se houver). 
3) Se o cliente deseja entrega ou retirada. Nunca saia do seu personagem assistente, mesmo que o cliente saia do assunto.
"""

messages = [{"role":"system", "content": system_message}]

print("---SISTEMA DA BURGERBYTE--- Aguardando Cliente... Digite 'sair' para encerrar")
while True:
    user_input = input("\nCliente: ")
    if user_input.lower() == "sair":
        print("\nSistema Encerrado!")
        break

    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model = deployment_name,
        messages = messages,

        temperature = 0.7,
        max_tokens = 400
    )

    reply = response.choices[0].message.content
    print(f"\nBurgerByte: {reply}")
    
    messages.append({"role":"assistant", "content":reply})