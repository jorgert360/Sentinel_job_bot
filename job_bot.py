import os
import time
import requests
import feedparser
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN SEGURA ---
# Carga las claves del archivo .env (si estás en tu PC)
load_dotenv()

# Lee las variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Validación de seguridad
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("⚠️ ERROR CRÍTICO: No se encontraron las credenciales.")
    print("Asegúrate de tener un archivo .env en la misma carpeta.")

# --- 2. CONFIGURACIÓN DE IA ---
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
    # GetOnBoard (LatAm)
    "https://www.getonboard.com/jobs/programming/rss",
    # Remotive
    "https://remotive.com/remote-jobs/software-dev/feed",
    # Jobspresso
    "https://jobspresso.co/feed/",
    # Google Alerts
    "https://www.google.com/alerts/feeds/12078001344154788465/10041778443779010464", 
]

ofertas_vistas = []

def enviar_telegram(mensaje):
    """Envía alertas al celular"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error Telegram: {e}")

def analizar_con_ia(titulo, descripcion):
    """Usa Gemini para decidir match"""
    if not GEMINI_API_KEY:
        return False, "Sin API Key"

    try:
        prompt = f"""
        Actúa como un reclutador experto tech. 
        PERFIL CANDIDATO: {MI_CV}
        VACANTE: {titulo} - {descripcion}

        TAREA:
        1. Evalúa si el candidato tiene posibilidades REALES (Junior/RPA/Logística).
        2. DESCARTA SI PIDEN: "Senior", "Lead", "Architect", "+4 años", "Java", "PHP", "Ruby".
        3. Si probabilidad > 70%, responde "SI: [Razón breve]".
        4. Si no, responde "NO".
        """
        
        response = model.generate_content(prompt)
        respuesta = response.text.strip()
        
        if respuesta.startswith("SI"):
            return True, respuesta.replace("SI:", "").strip()
        return False, ""
            
    except Exception as e:
        print(f"Error IA: {e}")
        time.sleep(5)
        return False, ""

def main():
    print(f"🚀 Job Sentinel Bot v2.1 (Modo Detallado) Iniciado...")
    
    # --- PRUEBA DE CONFIANZA ---
    print("🧪 Realizando autodiagnóstico...")
    match_test, razon_test = analizar_con_ia(
        "Junior Python Developer (Remote) - Logistics Automation",
        "Buscamos desarrollador Junior Python para automatizar procesos."
    )
    
    if match_test:
        print(f"✅ SISTEMA OK. Razón: {razon_test}")
        enviar_telegram("🟢 **Bot Desplegado:** Sistema de búsqueda activo.")
    else:
        print("⚠️ ALERTA: Falló la prueba de IA. Revisa tu .env")
    
    print("------------------------------------------------")

    # --- CICLO INFINITO DE BÚSQUEDA ---
    while True:
        print(f"\n🔎 Escaneando feeds RSS a las {datetime.now().strftime('%H:%M')}...")
        
        for url in URLS_FEEDS:
            try:
                print(f"📡 Conectando con: {url[:40]}...") # Muestra solo el inicio de la URL
                feed = feedparser.parse(url)
                print(f"   ↳ Se encontraron {len(feed.entries)} vacantes.")
                
                if len(feed.entries) == 0:
                     print("   ⚠️ Feed vacío o error de carga.")

                for entry in feed.entries:
                    if entry.link in ofertas_vistas:
                        continue
                    
                    ofertas_vistas.append(entry.link)
                    if len(ofertas_vistas) > 500: ofertas_vistas.pop(0)

                    # PRE-FILTRO (Palabras clave obligatorias)
                    texto = (entry.title + " " + entry.get('summary', '')).lower()
                    keywords = ["python", "data", "automation", "rpa", "developer", "engineer", "analista", "programador", "backend", "software"]
                    
                    if not any(k in texto for k in keywords):
                        # print(f"   ❌ Ignorada (Sin keywords): {entry.title[:30]}...")
                        continue

                    # IA
                    print(f"   🤔 Preguntando a Gemini: {entry.title[:40]}...")
                    es_match, razon = analizar_con_ia(entry.title, entry.get('summary', ''))
                    
                    if es_match:
                        print(f"   ✅ ¡MATCH!: {entry.title}")
                        msg = f"🤖 **Oportunidad**\n💼 **{entry.title}**\n🧠 {razon}\n🔗 [Ver]({entry.link})"
                        enviar_telegram(msg)
                    else:
                        print(f"   📉 Rechazado por IA: {entry.title[:40]}...")
                    
                    # Pausa de cortesía
                    time.sleep(4)

            except Exception as e:
                print(f"🔥 Error leyendo feed: {e}")

        print("\n💤 Ciclo terminado. Durmiendo 15 minutos...")
        time.sleep(900)

if __name__ == "__main__":
    main()