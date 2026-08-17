import sys
import os
from flask import Flask, render_template, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.formrecognizer import DocumentAnalysisClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Faz o L, a env ta configurada mal em")

app = Flask(__name__)

ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
CHAVE = os.getenv("DOC_INTEL_KEY")

cliente_documento = DocumentAnalysisClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(CHAVE)
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analisar', methods=['POST'])
def analisarRecibo():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado de forma correta."}), 400
        
    arquivo = request.files['file']
    
    if arquivo.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    try: 
        documento_bytes = arquivo.read()
                
        print("A enviar documento para análise de docs via Web")
        operacao = cliente_documento.begin_analyze_document(
            model_id="prebuilt-receipt",
            document=documento_bytes
        )
        recibos_extraidos = operacao.result()

        dados_finais = {
            "fornecedor": "Não identificado",
            "data": "Não identificada",
            "total": "Não identificado"
        }

        for recibo in recibos_extraidos.documents:
            nomeLoja = recibo.fields.get("MerchantName")
            totalGasto = recibo.fields.get("Total")
            dataCompra = recibo.fields.get("TransactionDate")
            
            if nomeLoja and nomeLoja.value:
                dados_finais["fornecedor"] = str(nomeLoja.value)
                
            if dataCompra and dataCompra.value:
                dados_finais["data"] = str(dataCompra.value)
                
            if totalGasto and totalGasto.value:
                dados_finais["total"] = f"R$ {totalGasto.value:.2f}" if isinstance(totalGasto.value, (int, float)) else str(totalGasto.value)

            print("Resultado da Extração: \n")
            print(f"Fornecedor: {dados_finais['fornecedor']}")
            print(f"Data da Compra: {dados_finais['data']}")
            print(f"O total a reembolsar: {dados_finais['total']}\n")

        return jsonify(dados_finais)

    except Exception as error:
        print(f"[ERRO NA LEITURA] {error}")
        return jsonify({"error": f"Erro na Azure: {str(error)}"}), 500

if __name__ == '__main__':
    print("\n --------------------- \n Sistema de Auditoria de Recibo Iniciado \n ---------------------")
    app.run(debug=True)