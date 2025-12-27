from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ---------- UTILIDADES ----------

def limpiar(url):
    return re.sub(r"/\?.*", "", url)

def analizar_pregunta(texto):
    texto = texto.lower()

    intent = "general"
    plataformas = []

    if "facebook" in texto or "fb" in texto:
        plataformas.append("facebook")

    if "instagram" in texto or "ig" in texto:
        plataformas.append("instagram")

    if any(p in texto for p in ["escuela", "secundaria", "prepa", "cbtis"]):
        intent = "institucion"

    if any(p in texto for p in ["persona", "se llama", "llamado", "nombre"]):
        intent = "persona"

    palabras_clave = re.sub(
        r"(facebook|instagram|persona|escuela|secundaria|prepa|cbtis|llamado|se llama)",
        "",
        texto
    ).strip()

    return {
        "intencion": intent,
        "plataformas": plataformas,
        "query": palabras_clave
    }

def buscar_publico(query, plataformas):
    if not plataformas:
        plataformas = ["facebook", "instagram"]

    sitio = " OR ".join([f"site:{p}.com" for p in plataformas])
    url = f"https://duckduckgo.com/html/?q={query} {sitio}"

    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    resultados = {p: set() for p in plataformas}

    for a in soup.find_all("a", href=True):
        link = a["href"]
        for p in plataformas:
            if f"{p}.com" in link:
                resultados[p].add(limpiar(link))

    return {k: list(v) for k, v in resultados.items()}

# ---------- ENDPOINTS ----------

@app.route("/")
def home():
    return {"status": "API inteligente funcionando"}

@app.route("/buscar")
def buscar():
    pregunta = request.args.get("q")
    if not pregunta:
        return jsonify({"error": "Falta parámetro q"}), 400

    analisis = analizar_pregunta(pregunta)
    resultados = buscar_publico(
        analisis["query"],
        analisis["plataformas"]
    )

    return jsonify({
        "pregunta": pregunta,
        "analisis": analisis,
        "resultados": resultados
    })
