import os
import random

from flask import Flask, render_template, request, redirect, url_for 
from azure.ai.vision.imageanalysis import ImageAnalysisClient  
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from PIL import Image, ImageDraw

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

AI_ENDPOINT = ''
AI_KEY = ''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'foto' not in request.files:
            return redirect(request.url)
        
        arquivo = request.files['foto']
        
        if arquivo.filename == '':
            return redirect(request.url)

        if arquivo:
            caminho_original = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_original.jpg')
            arquivo.save(caminho_original)

            with open(caminho_original, "rb") as f:
                image_data = f.read()

            cv_client = ImageAnalysisClient(
                endpoint=AI_ENDPOINT,
                credential=AzureKeyCredential(AI_KEY)
            )

            result = cv_client.analyze(
                image_data=image_data,
                visual_features=[
                    #VisualFeatures.CAPTION,
                    VisualFeatures.TAGS,
                    VisualFeatures.OBJECTS,
                    VisualFeatures.PEOPLE
                ],
            )

            img_pillow = Image.open(caminho_original)
            draw = ImageDraw.Draw(img_pillow)

            dados_analise = {
                'legenda': result.caption.text if result.caption else "Sem descrição disponível",
                'confianca': f"{result.caption.confidence * 100:.2f}%" if result.caption else "0%",
                'tags': [tag.name for tag in result.tags.list[:5]] if result.tags else [] 
            }

            if result.objects is not None:
                for obj in result.objects.list:
                    r = obj.bounding_box
                    draw.rectangle(((r.x, r.y), (r.x + r.width, r.y + r.height)), outline='cyan', width=4)

            if result.people is not None:
                for person in result.people.list:
                    r = person.bounding_box
                    draw.rectangle(((r.x, r.y), (r.x + r.width, r.y + r.height)), outline='magenta', width=4)

            nome_resultado = 'resultado.jpg'
            caminho_resultado = os.path.join(app.config['UPLOAD_FOLDER'], nome_resultado)
            img_pillow.save(caminho_resultado)

            versao = random.randint(1, 9999)

            return render_template('index.html', imagem_exibir=caminho_resultado, analise=dados_analise, v=versao)

    return render_template('index.html', imagem_exibir=None, analise=None, v=None)

if __name__ == '__main__':
    app.run(debug=True)