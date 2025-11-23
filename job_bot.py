import os
import time
import requests
import feedparser
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN ---
load_dotenv() # Carga variables si estás probando en tu PC

# GitHub Actions inyectará estas variables automáticamente
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 2. CONFIGURACIÓN IA ---
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Usamos Flash 2.5 por ser el más balanceado
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error configurando IA: {e}")

# --- 3. TU PERFIL PROFESIONAL (DETALLADO) ---
# Aquí restauré tus puntos fuertes según tu Hoja de Vida real
MI_CV = """
PERFIL: Desarrollador Junior Python & Especialista en Automatización de Procesos (RPA).
ENFOQUE: Transición de Logística a Tecnología.

EXPERIENCIA RELEVANTE:
1. Process Automation Analyst (Productos Familia):
   - Desarrollo de scripts en Python (Pandas) y bots RPA.
   - LOGRO: Reducción del 45% en tiempos de respuesta de tickets y 10% de eficiencia operativa.
   - Integración de APIs y bases de datos SQL.
2. Experiencia en Dominio Logístico (5+ años):
   - Conocimiento profundo de aduanas, Zona Franca y cadena de suministro (ventaja para LogTech).

PROYECTOS TÉCNICOS:
- 'CV Automatic' (SaaS): Aplicación web full-stack para optimización de CVs usando IA Generativa.
- Tech Stack: Python, Streamlit, OpenAI API, Git.

EDUCACIÓN:
- Ingeniería en IA y Ciencia de Datos (4to semestre).
- Certificaciones: Azure Fundamentals, Prompt Engineering (IBM).

BUSCO:
- Roles: Junior Developer, Python Developer, RPA Analyst, Data Analyst.
- Modalidad: Remoto.
- NO BUSCO: Senior, Lead, Architect, ni roles que pidan +4 años de experiencia en código.
"""

# --- 4. FUENTES RSS ---
URLS_FEEDS = [
    "https://www.getonboard.com/jobs/programming/rss",
    "https://remotive.com/remote-jobs/software-dev/feed",
    "https://jobspresso.co/feed/",
    # Agrega aquí tu URL de Google Alerts si la tienes
]

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except:
        pass

def analizar_con_ia(titulo, descripcion):
    if not GEMINI_API_KEY: return False, "Sin API Key"
    try:
        prompt = f"""
        Actúa como un reclutador técnico senior.
        
        CANDIDATO:
        {MI_CV}
        
        VACANTE A EVALUAR:
        Título: {titulo}
        Descripción: {descripcion}
        
        INSTRUCCIONES DE FILTRADO:
        1. Tu objetivo es encontrar el PRIMER empleo de desarrollo para este perfil.
        2. DESCARTA INMEDIATAMENTE SI:
           - Piden "Senior", "Lead", "Staff", "Principal" o "Manager".
           - Piden más de 3 años de experiencia EXCLUSIVA en programación.
           - El stack es 100% Java, C#, Ruby o PHP (El candidato es fuerte en Python).
        3. APRUEBA SI:
           - Es rol Junior, Trainee, Entry-Level o Pasante.
           - Valoran experiencia de negocio (Logística/Procesos) + Python.
           - Es un rol de Automatización / RPA.
           
        FORMATO DE RESPUESTA:
        - Si es compatible: "SI: [Explica en 1 frase por qué encaja con su exp en logística o proyecto personal]"
        - Si no es compatible: "NO"
        """
        
        response = model.generate_content(prompt)
        txt = response.text.strip()
        
        if txt.upper().startswith("SI"):
            return True, txt.replace("SI:", "").replace("Si:", "").strip()
        return False, ""
    except Exception as e:
        print(f"Error en IA: {e}")
        return False, ""

def main():
    print(f"🚀 Ejecución GitHub Actions iniciada: {datetime.now().strftime('%H:%M')}...")
    
    ofertas_encontradas = 0
    ofertas_enviadas = 0

    for url in URLS_FEEDS:
        try:
            print(f"📡 Leyendo feed: {url[:40]}...")
            feed = feedparser.parse(url)
            
            # Solo revisamos las 7 más nuevas para ser eficientes
            nuevas_ofertas = feed.entries[:7]
            
            for entry in nuevas_ofertas:
                ofertas_encontradas += 1
                
                # 1. PRE-FILTRO RÁPIDO (Ahorra tiempo de IA)
                texto = (entry.title + " " + entry.get('summary', '')).lower()
                
                # Palabras que deben estar sí o sí
                keywords_obligatorias = ["python", "data", "automation", "rpa", "developer", "engineer", "analista", "programador", "ai", "ia"]
                
                if not any(k in texto for k in keywords_obligatorias):
                    continue
                
                # 2. ANÁLISIS PROFUNDO CON GEMINI
                print(f"   🤔 Analizando: {entry.title[:50]}...")
                match, razon = analizar_con_ia(entry.title, entry.get('summary', ''))
                
                if match:
                    print(f"   ✅ ¡MATCH!: {entry.title}")
                    msg = f"🤖 **Oportunidad Detectada**\n💼 **{entry.title}**\n🧠 {razon}\n🔗 [Ver]({entry.link})"
                    enviar_telegram(msg)
                    ofertas_enviadas += 1
                
                # Pequeña pausa para no saturar
                time.sleep(2)

        except Exception as e:
            print(f"🔥 Error en feed: {e}")

    print(f"🏁 Finalizado. Revisadas: {ofertas_encontradas}. Enviadas: {ofertas_enviadas}.")

if __name__ == "__main__":
    main()