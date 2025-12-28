from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------
# Limpiar URLs
# -----------------------------
def limpiar(url):
    return re.sub(r"/\?.*", "", url)

# -----------------------------
# Analizar la pregunta
# -----------------------------
def analizar_pregunta(texto):
    texto_lower = texto.lower()
    resultado = {"intencion": None, "plataformas": [], "query": texto}

    # Detectar plataformas
    if "facebook" in texto_lower:
        resultado["plataformas"].append("facebook")
    if "instagram" in texto_lower:
        resultado["plataformas"].append("instagram")

    # Detectar intención
    if any(x in texto_lower for x in ["escuela", "cbtis", "secundaria", "instituto"]):
        resultado["intencion"] = "institucion"
    elif any(x in texto_lower for x in ["persona", "nombre", "juan", "maria"]):
        resultado["intencion"] = "persona"
    else:
        resultado["intencion"] = "general"

    # Si no se menciona plataforma, buscar en todas
    if not resultado["plataformas"]:
        resultado["plataformas"] = ["facebook", "instagram"]

    # Asegurar que query nunca quede vacía
    if not resultado["query"]:
        resultado["query"] = texto

    return resultado

# -----------------------------
# Buscar perfiles en DuckDuckGo
# -----------------------------
def buscar_perfiles(texto, plataformas):
    query = f"{texto} " + " OR ".join([f"site:{p}.com" for p in plataformas])
    url = f"https://duckduckgo.com/html/?q={query}"

    resultados = {"facebook": set(), "instagram": set()}

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            link = a["href"]
            if "facebook.com" in link:
                resultados["facebook"].add(limpiar(link))
            if "instagram.com" in link:
                resultados["instagram"].add(limpiar(link))
    except Exception as e:
        print("Error DuckDuckGo:", e)

    return {k: list(v) for k, v in resultados.items()}

# -----------------------------
# Buscar en Wikipedia
# -----------------------------
def buscar_wikipedia(query):
    resultados = []
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
        r = requests.get(wiki_url, headers=HEADERS, timeout=10).json()
        for item in r.get("query", {}).get("search", []):
            resultados.append({
                "titulo": item["title"],
                "snippet": item["snippet"],
                "link": f"https://en.wikipedia.org/wiki/{item['title'].replace(' ', '_')}"
            })
    except:
        pass
    return resultados

# -----------------------------
# Buscar en Google Custom Search
# -----------------------------
def buscar_google_cse(query):
    resultados = []
    # Reemplaza con tu API key y Search Engine ID
    API_KEY = "TU_GOOGLE_API_KEY"
    CX = "TU_CSE_ID"

    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CX}&q={query}"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        for item in r.get("items", []):
            resultados.append({
                "titulo": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link")
            })
    except:
        pass
    return resultados

# -----------------------------
# Rutas API
# -----------------------------
@app.route("/")
def home():
    return {"status": "API inteligente funcionando"}

@app.route("/buscar")
def buscar():
    texto = request.args.get("q")
    if not texto:
        return jsonify({"error": "Falta parámetro q"}), 400

    analisis = analizar_pregunta(texto)
    perfiles = buscar_perfiles(analisis["query"], analisis["plataformas"])
    wiki = buscar_wikipedia(analisis["query"])
    google = buscar_google_cse(analisis["query"])

    return jsonify({
        "pregunta": texto,
        "analisis": analisis,
        "resultados": perfiles,
        "wikipedia": wiki,
        "google_cse": google
    })

if __name__ == "__main__":
    app.run(debug=True)
