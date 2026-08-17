import os
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins =["*"],
    allow_methods =["*"],
    allow_headers =["*"]
)

ENDPOINT = os.getenv("AZURE_ENDPOINT")
KEY = os.getenv("AZURE_KEY")

cliente_azure = ImageAnalysisClient(endpoint=ENDPOINT,credential=AzureKeyCredential(KEY))

@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")

@app.post("/analisar")
async def analisar_imagem(arquivo: UploadFile = File(...)):
    bytes_imagem = await arquivo.read()

    try:
        resultado: cliente_azure.analyze(image_data = bytes_imagem, visual_features = [VisualFeatures.TAGS])

        tags_encontradas = []
        if resultado.tags is not None:
            for tag in resultado.tags.list:
                tags_encontradas.append({
                    "nome": tag.name.upper(),
                    "confianca": round(tag.confidence *100, 1),
                })
        return{"sucesso": True, "dados": tags_encontradas}
    except Exception as erro:
        return{"sucesso": False, "erro": str(erro)}
    
    if __name__ == "__main__":
        uvicorn.run(app, host="127.0.0.1", port=8000)