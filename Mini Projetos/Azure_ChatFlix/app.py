import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speech_sdk

load_dotenv()
app = Flask(__name__)

ai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-02-15-preview"
)
deployment_name = os.getenv("AZURE_OAI_DEPLOYMENT")

speech_config = speech_sdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION")
)

MAPA_VOZES = {
    "pt": "pt-BR-FranciscaNeural",
    "en": "en-US-JennyNeural",
    "es": "es-ES-ElviraNeural",
    "ja": "ja-JP-NanamiNeural"
}

historico_chat = [
    {
        "role": "system",
        "content": """Você é o assistente do ChatFlix.
        Sua missão é recomendar filmes e séries.
        REGRA ABSOLUTA: Responda EXCLUSIVAMENTE em formato JSON com as chaves:
        - "fala": Sua resposta culta e imersiva.
        - "url_trailer": URL do YouTube se o trailer for pedido, ou null.
        - "tema": Analise o gênero do filme recomendado e retorne EXATAMENTE UMA destas palavras: "terror", "comedia", "acao", "romance", ou "padrao"."""
    }
]

def gerar_audio_ssml(texto, nome_arquivo, voice_name, tema):
    caminho_audio = os.path.join("static", "audio", nome_arquivo)
    audio_config = speech_sdk.audio.AudioOutputConfig(filename=caminho_audio)
    synthesizer = speech_sdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    lang_code = voice_name[:5]

    pitch = "+0%"
    rate = "+0%"
    style_open = ""
    style_close = ""

    if tema == "terror":
        pitch = "-15%"
        rate = "-15%"
    elif tema == "comedia":
        pitch = "+10%"
        rate = "+10%"
    elif tema == "acao":
        rate = "+15%"

    if voice_name == "pt-BR-FranciscaNeural" and tema in ["padrao", "comedia"]:
        style_open = '<mstts:express-as style="cheerful">'
        style_close = '</mstts:express-as>'

    ssml_texto = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{lang_code}">
        <voice name="{voice_name}">
            {style_open}
            <prosody pitch="{pitch}" rate="{rate}">
                {texto}
            </prosody>
            {style_close}
        </voice>
    </speak>
    """
    
    synthesizer.speak_ssml_async(ssml_texto).get()
    return f"/static/audio/{nome_arquivo}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    dados = request.json
    mensagem_usuario = dados.get("mensagem")
    idioma_solicitado = dados.get("idioma", "pt")

    voz_escolhida = MAPA_VOZES.get(idioma_solicitado, "pt-BR-FranciscaNeural")
    mensagem_turbinada = f"[INSTRUÇÃO: Responda no idioma '{idioma_solicitado.upper()}'] {mensagem_usuario}"
    
    historico_chat.append({"role": "user", "content": mensagem_turbinada})

    try:
        response = ai_client.chat.completions.create(
            model=deployment_name,
            messages=historico_chat,
            max_tokens=250,
            temperature=0.7,
            response_format={ "type": "json_object" }
        )

        resposta_crua = response.choices[0].message.content
        historico_chat.append({"role": "assistant", "content": resposta_crua})

        dados_ia = json.loads(resposta_crua)
        fala_ia = dados_ia.get("fala", "Error.")
        link_trailer = dados_ia.get("url_trailer")
        tema_ia = dados_ia.get("tema", "padrao").lower()

        url_audio = gerar_audio_ssml(fala_ia, "resposta_atual.wav", voz_escolhida, tema_ia)

        return jsonify({
            "resposta_texto": fala_ia,
            "url_audio": url_audio,
            "link_redirecionamento": link_trailer,
            "tema_visual": tema_ia
        })

    except Exception as e:
        print(f"\n[ERRO NA AZURE]: {e}\n")
        return jsonify({"erro": "Falha na comunicação."}), 500

if __name__ == '__main__':
    os.makedirs("static/audio", exist_ok=True)
    app.run(debug=True, use_reloader=False)