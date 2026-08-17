import os
from dotenv import load_dotenv
from openai import AzureOpenAI

import azure.cognitiveservices.speech as speech_sdk

speech_config = None

def configurar_fala():

    global speech_config
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    speech_config = speech_sdk.SpeechConfig(subscription=speech_key, region=speech_region)

    speech_config.speech_synthesis_voice_name="pt-BR-FranciscaNeural"

def falar_texto(texto_para_falar):
    global speech_config
    if not speech_config:
        print("ERRO")
        return
    
    audio_config = speech_sdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesizer.speak_text_async(texto_para_falar).get()
    
    def main():
        try:
            load_dotenv()
            configurar_fala()

            client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OAI_KEY"),
                api_version="2024-02-15-preview"
            )
            deployment_name = os.getenv("AZURE_OAI_DEPLOYMENT")
            system_message = """Você é um assistente prestativo e amigável, 
            responda sempre de forma MUITO curta e em tom de conversa. Pois sua resposta
            será lida em voz alta por um sintetizador de fala."""

            messages_array = [{"role":"system", "content": system_message}]
            print("---IA com Voz Iniciada (digite 'quit' para sair)---")
            while True:
                input_text = input("\nVoce:")
                if input_text.lower() == "quit":
                    print("Encerrando o sistema...")
                    break

                messages_array.append({"role":"system", "content":input_text})
                print("A IA está em processamento...")

                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=messages_array,
                    max_tokens=150
                )

                generate_text = response.choices[0].messages.content
                messages_array.append({"role": "assistant", "content": generate_text})
                print(f"IA: {generate_text}")
                falar_texto(generate_text)
        except Exception as ex:
            print(f"Ocorreu um erro durante a execução {ex}")

if __name__ == "__main__":
    main()