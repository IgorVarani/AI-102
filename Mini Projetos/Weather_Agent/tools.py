import requests

def get_weather(cidade: str):
    try:
        geo = requests.get(
            'https://geocoding-api.open-meteo.com/v1/search',
            params={
                "nome": cidade,
                "count": 1,
                "language": "pt"
            },
            timeout=10
        ).json()
        if "results" not in geo:
            return{
                "erro": "cidade não encontrada",
                "entrada": cidade
            }
        
        loc = geo["results"][0]
        lat = loc["latitude"]
        lon = loc["longitude"]
        nome_real = loc["name"]

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True
            },
            timeout=10
        ).json()

        w = weather["current_weather"]

        return{
            "cidade": nome_real,
            "temperatura_c": w["temperatura"],
            "vento_kmh": w["windspeed"],
            "condicao": w["weathercode"]
        }
    except Exception as e:
        return {
            "erro": "falha ao consultar o clima",
            "detalhe": str(e),
            "entrada": cidade
        }