import os
from flask import Flask, render_template, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.textanalytics import TextAnalyticsClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Aviso: python-dotenv não está instalado. As variáveis .env não foram carregadas.")

app = Flask(__name__)

AZURE_LANGUAGE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT")
AZURE_LANGUAGE_KEY = os.getenv("AZURE_LANGUAGE_KEY")

def criar_cliente_language():
    if not AZURE_LANGUAGE_ENDPOINT or not AZURE_LANGUAGE_KEY:
        raise ValueError(
            "Endpoint ou chave da Azure não configurados. "
            "Verifique se o arquivo .env existe e se contém "
            "AZURE_LANGUAGE_ENDPOINT e AZURE_LANGUAGE_KEY."
        )

    credential = AzureKeyCredential(AZURE_LANGUAGE_KEY)
    client = TextAnalyticsClient(
        endpoint=AZURE_LANGUAGE_ENDPOINT,
        credential=credential
    )
    return client

def verificar_resposta(resultado, etapa):
    if getattr(resultado, "is_error", False):
        if resultado.error:
            mensagem = resultado.error.message
        else:
            mensagem = "Erro desconhecido."
        raise ValueError(f"Erro na etapa {etapa}: {mensagem}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analisar", methods=["POST"])
def analisar_texto():
    try:
        client = criar_cliente_language()
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Nenhum JSON foi recebido."}), 400

        texto = dados.get("texto", "").strip()

        if not texto:
            return jsonify({"erro": "Digite um texto para análise."}), 400

        if len(texto) > 5000:
            return jsonify({
                "erro": "O texto está muito longo para este laboratório. Use até 5000 caracteres."
            }), 400

        resposta_idioma = client.detect_language(
            documents=[texto],
            country_hint="BR"
        )[0]
        verificar_resposta(resposta_idioma, "detecção de idioma")

        idioma_nome = resposta_idioma.primary_language.name
        idioma_codigo = resposta_idioma.primary_language.iso6391_name or "pt"
        idioma_confianca = round(resposta_idioma.primary_language.confidence_score, 2)

        documento = [
            {
                "id": "1",
                "language": idioma_codigo,
                "text": texto
            }
        ]

        resposta_sentimento = client.analyze_sentiment(documents=documento)[0]
        verificar_resposta(resposta_sentimento, "análise de sentimento")

        resposta_entidades = client.recognize_entities(documents=documento)[0]
        verificar_resposta(resposta_entidades, "reconhecimento de entidades")

        resposta_frases = client.extract_key_phrases(documents=documento)[0]
        verificar_resposta(resposta_frases, "extração de frases-chave")

        resposta_pii = client.recognize_pii_entities(documents=documento)[0]
        verificar_resposta(resposta_pii, "detecção de PII")

        entidades = []
        for entidade in resposta_entidades.entities:
            entidades.append({
                "texto": entidade.text,
                "categoria": entidade.category,
                "subcategoria": entidade.subcategory,
                "confianca": round(entidade.confidence_score, 2)
            })

        pii = []
        for entidade in resposta_pii.entities:
            pii.append({
                "texto": entidade.text,
                "categoria": entidade.category,
                "subcategoria": entidade.subcategory,
                "confianca": round(entidade.confidence_score, 2)
            })

        resultado_final = {
            "idioma": {
                "nome": idioma_nome,
                "codigo": idioma_codigo,
                "confianca": idioma_confianca
            },
            "sentimento": {
                "geral": resposta_sentimento.sentiment,
                "positivo": round(resposta_sentimento.confidence_scores.positive, 2),
                "neutro": round(resposta_sentimento.confidence_scores.neutral, 2),
                "negativo": round(resposta_sentimento.confidence_scores.negative, 2)
            },
            "entidades": entidades,
            "frases_chave": resposta_frases.key_phrases,
            "pii": pii,
            "texto_mascarado": resposta_pii.redacted_text
        }

        return jsonify(resultado_final)

    except HttpResponseError as erro_azure:
        return jsonify({
            "erro": f"Erro retornado pela Azure: {str(erro_azure)}"
        }), 502

    except Exception as erro: 
        return jsonify({
            "erro": str(erro)
        }), 500

if __name__ == "__main__":
    print("Servidor iniciado em http://127.0.0.1:5000")
    app.run(debug=True)