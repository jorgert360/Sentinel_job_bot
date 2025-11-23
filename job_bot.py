import os
import time
import requests
import feedparser
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN ---
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 2. CONFIGURACIÓN IA ---
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error IA: {e}")

MI_CV = """
PERFIL: Desarrollador Junior Python & Especialista en Automatización (RPA).
EXPERIENCIA: Process Automation Analyst (2 años), Logística (5+ años).
STACK: Python, SQL, Git, APIs. PROYECTO: 'CV Automatic' (SaaS con IA).
BUSCO: Junior, Remoto, Backend/Data/RPA. NO Senior/Lead.
"""

URLS_FEEDS = [
    "https://www.getonboard.com/jobs/programming/rss",
    "https://remotive.com/remote-jobs/software-dev/feed",
    "https://jobspresso.co/feed/",
   "https://www.google.com/alerts/feeds/12078001344154788465/10041778443779010464",
]

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except: pass

def analizar_con_ia(titulo, descripcion):
    if not GEMINI_API_KEY: return False, "Sin API Key"
    try:
        prompt = f"""
        Actúa como reclutador. PERFIL: {MI_CV}
        VACANTE: {titulo} - {descripcion}
        REGLAS:
        1. Evalúa fit para Junior/RPA/Logística.
        2. DESCARTA: Senior, Lead, +4 años, Java/Ruby/PHP.
        3. Si probabilidad > 70%, responde "SI: [Razón]".
        4. Si no, "NO".
        """
        response = model.generate_content(prompt)
        if response.text.strip().upper().startswith("SI"):
            return True, response.text.replace("SI:", "").strip()
        return False, ""
    except: return False, ""

def obtener_feed_seguro(url):
    """Descarga el feed haciéndose pasar por un navegador"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"   Error descarga manual: {e}")
        return None

def main():
    print(f"🚀 Bot 'Stealth' Iniciado: {datetime.now().strftime('%H:%M')}...")
    
    # Diagnóstico de llaves
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("⚠️ ALERTA: Faltan las claves secretas en GitHub Secrets.")
    
    ofertas_encontradas = 0
    
    for url in URLS_FEEDS:
        try:
            print(f"📡 Conectando a: {url[:30]}...")
            
            # USAMOS LA NUEVA FUNCIÓN SEGURA
            feed = obtener_feed_seguro(url)
            
            if not feed or len(feed.entries) == 0:
                print("   ⚠️ No se pudo leer contenido (Bloqueo o vacío).")
                continue

            print(f"   ↳ Encontradas: {len(feed.entries)} vacantes.")
            
            # Revisamos las 5 más recientes
            for entry in feed.entries[:5]:
                texto = (entry.title + " " + entry.get('summary', '')).lower()
                
                if not any(k in texto for k in ["python", "data", "automation", "rpa", "developer"]):
                    continue

                print(f"   🤔 IA Analizando: {entry.title[:40]}...")
                match, razon = analizar_con_ia(entry.title, entry.get('summary', ''))
                ofertas_encontradas += 1
                
                if match:
                    print(f"   ✅ MATCH: {entry.title}")
                    msg = f"🤖 **Oportunidad**\n💼 **{entry.title}**\n🧠 {razon}\n🔗 [Ver]({entry.link})"
                    enviar_telegram(msg)
                
                time.sleep(2)

        except Exception as e:
            print(f"🔥 Error general en feed: {e}")

    print(f"🏁 Fin del escaneo. Total analizadas por IA: {ofertas_encontradas}")

if __name__ == "__main__":
    main()