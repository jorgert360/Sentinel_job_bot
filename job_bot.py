import os
import time
import requests
import feedparser
import google.generativeai as genai
import urllib3  # <--- NUEVO
from datetime import datetime
from dotenv import load_dotenv

# --- 0. DESACTIVAR ALERTAS SSL ---
# Esto evita que la consola se llene de advertencias por saltarnos la seguridad
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURACIÓN ---
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 2. IA ---
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except: pass

MI_CV = """
PERFIL: Desarrollador Junior Python & Automatización (RPA).
EXP: Logística (5 años), Python/RPA (2 años, -45% tiempos).
STACK: Python, SQL, APIs.
BUSCO: Junior, Remoto, Backend/Data/RPA. NO Senior.
"""

URLS_FEEDS = [
    "https://www.getonboard.com/jobs/programming/rss",
    "https://remotive.com/remote-jobs/software-dev/feed",
    "https://jobspresso.co/feed/",
    "https://www.google.com/alerts/feeds/12078001344154788465/10041778443779010464",
]

def enviar_telegram(msg):
    if not TELEGRAM_TOKEN: return
    try:
        # verify=False también aquí por si acaso
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                      verify=False)
    except: pass

def analizar_con_ia(titulo, desc):
    if not GEMINI_API_KEY: return False, ""
    try:
        prompt = f"Rol: Reclutador. CV: {MI_CV}. Vacante: {titulo} - {desc}. ¿Fit Junior/RPA? SI/NO. Razón."
        res = model.generate_content(prompt)
        return (True, res.text.replace("SI:", "").strip()) if res.text.strip().upper().startswith("SI") else (False, "")
    except: return False, ""

def obtener_feed_seguro(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        # AQUÍ ESTÁ LA MAGIA: verify=False
        r = requests.get(url, headers=headers, timeout=20, verify=False)
        return feedparser.parse(r.content)
    except Exception as e: 
        print(f"   Error conexión: {e}")
        return None

def main():
    print(f"🚀 Bot 'Stealth + NoSSL' Iniciado: {datetime.now().strftime('%H:%M')}...")
    
    if TELEGRAM_TOKEN and GEMINI_API_KEY:
        print("✅ Credenciales detectadas.")
    else:
        print("⚠️ Faltan credenciales.")

    ofertas_encontradas = 0
    
    for url in URLS_FEEDS:
        print(f"📡 Conectando a: {url[:40]}...")
        feed = obtener_feed_seguro(url)
        
        if not feed or len(feed.entries) == 0:
            print("   ⚠️ Bloqueado o vacío.")
            continue

        print(f"   ↳ Encontradas: {len(feed.entries)} vacantes.")
        
        for entry in feed.entries[:5]:
            texto = (entry.title + " " + entry.get('summary', '')).lower()
            if not any(k in texto for k in ["python", "data", "automation", "rpa", "developer"]):
                continue

            print(f"   🤔 IA Analizando: {entry.title[:30]}...")
            match, razon = analizar_con_ia(entry.title, entry.get('summary', ''))
            
            if match:
                print(f"   ✅ MATCH: {entry.title}")
                enviar_telegram(f"🤖 **Oportunidad**\n💼 {entry.title}\n🧠 {razon}\n🔗 [Ver]({entry.link})")
                ofertas_encontradas += 1
            
            time.sleep(2)

    print(f"🏁 Fin. Matchs encontrados: {ofertas_encontradas}")

if __name__ == "__main__":
    main()