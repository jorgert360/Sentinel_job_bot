import os
import time
import requests
import feedparser
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN SEGURA ---
# Carga variables locales solo si existe el archivo .env (Pruebas en PC)
load_dotenv()

# Lee las variables del entorno (Ya sea PC o GitHub Actions)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 2. CONFIGURACIÓN IA ---
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error configurando IA: {e}")

# --- 3. TU PERFIL PROFESIONAL ---
MI_CV = """
PERFIL: Desarrollador Junior Python & Especialista en Automatización (RPA).
EXPERIENCIA:
- Process Automation Analyst (2 años): Uso de Python (Pandas) y RPA para reducir 45% tiempos operativos en logística.
- Experiencia previa en Logística y Aduanas (5+ años).
HABILIDADES TÉCNICAS:
- Lenguajes: Python, SQL, HTML/CSS.
- Herramientas: RPA, APIs, Git, Azure (Basics).
- Proyectos: Desarrollo de 'CV Automatic' (SaaS con IA) y bots de Telegram.
EDUCACIÓN: Ingeniero en formación (IA y Ciencia de Datos - 4to semestre).
BUSCO: Roles Junior, Remotos, enfocados en Backend, Automatización o Data. NO busco Senior, Lead o Architect.
"""

# --- 4. FUENTES RSS ---
URLS_FEEDS = [
    "https://www.getonboard.com/jobs/programming/rss",
    "https://remotive.com/remote-jobs/software-dev/feed",
    "https://jobspresso.co/feed/",
    "https://www.google.com/alerts/feeds/12078001344154788465/10041778443779010464"
]

ofertas_vistas = []

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Faltan credenciales de Telegram")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error Telegram: {e}")

def analizar_con_ia(titulo, descripcion):
    if not GEMINI_API_KEY: return False, "Sin API Key"
    try:
        prompt = f"""
        Actúa como reclutador tech. PERFIL: {MI_CV}
        VACANTE: {titulo} - {descripcion}
        
        TAREA:
        1. Evalúa fit para Junior/RPA/Logística.
        2. DESCARTA SI PIDEN: "Senior", "Lead", "Architect", "+4 años", "Java", "PHP", "Ruby".
        3. Si probabilidad > 70%, responde "SI: [Razón breve]".
        4. Si no, "NO".
        """
        response = model.generate_content(prompt)
        txt = response.text.strip()
        if txt.upper().startswith("SI"):
            return True, txt.replace("SI:", "").replace("Si:", "").strip()
        return False, ""
    except Exception as e:
        print(f"Error IA: {e}")
        return False, ""

def main():
    print(f"🚀 Ejecución GitHub Actions iniciada: {datetime.now().strftime('%H:%M')}...")
    
    # --- PRUEBA DE DIAGNÓSTICO (Solo corre si las claves están bien) ---
    if TELEGRAM_TOKEN and GEMINI_API_KEY:
        print("🧪 Verificando sistemas...")
        match, razon = analizar_con_ia("Junior Python Dev", "Python automation junior role")
        if match: print("✅ IA Operativa.")
    else:
        print("⚠️ ALERTA: No se detectaron las claves secretas. Revisa los Secrets de GitHub.")

    # --- BÚSQUEDA ---
    for url in URLS_FEEDS:
        try:
            print(f"📡 Leyendo: {url[:30]}...")
            feed = feedparser.parse(url)
            
            # Solo las 5 más nuevas para ser rápido
            nuevas_ofertas = feed.entries[:5]
            
            for entry in nuevas_ofertas:
                # Pre-filtro básico
                texto = (entry.title + " " + entry.get('summary', '')).lower()
                if not any(k in texto for k in ["python", "data", "automation", "rpa", "developer"]):
                    continue

                # Análisis IA
                print(f"   🤔 Analizando: {entry.title[:40]}...")
                match, razon = analizar_con_ia(entry.title, entry.get('summary', ''))
                
                if match:
                    print(f"   ✅ ¡MATCH!: {entry.title}")
                    msg = f"🤖 **Oportunidad**\n💼 **{entry.title}**\n🧠 {razon}\n🔗 [Ver]({entry.link})"
                    enviar_telegram(msg)
                
                time.sleep(2) # Pausa técnica

        except Exception as e:
            print(f"🔥 Error en feed: {e}")

    print("🏁 Escaneo finalizado.")

if __name__ == "__main__":
    main()