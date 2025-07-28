# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
#         Blueprint Arquitetural para um Avatar Falante com IA
#         ---------------------------------------------------
#
# Versão Final com Animação por Volume (Fallback Inteligente)
#
# -----------------------------------------------------------------------------

import pygame
import os
import threading
import tempfile
import speech_recognition as sr
import google.generativeai as genai
import json
import base64
import requests
import numpy as np  # <--- NOVO
from pydub import AudioSegment  # <--- NOVO
from pydub.utils import get_array_type # <--- NOVO

# --- CONFIGURAÇÃO INICIAL ---

elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

if not elevenlabs_api_key or not google_api_key:
    print("="*50)
    print("ERRO: Uma ou mais chaves de API não foram encontradas.")
    print("Por favor, configure ELEVENLABS_API_KEY e GOOGLE_API_KEY.")
    print("="*50)
    exit()

try:
    genai.configure(api_key=google_api_key)
except Exception as e:
    print(f"Erro ao inicializar clientes de API: {e}")
    exit()

pygame.init()
pygame.mixer.init()
recognizer = sr.Recognizer()

# --- CONSTANTES GLOBAIS ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Avatar Conversacional com IA (Gemini)")

# Cores e Fontes
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (200, 200, 200)
COLOR_BLUE = (100, 149, 237)
COLOR_GREEN_LIGHT = (144, 238, 144)
COLOR_ORANGE = (255, 165, 0)
COLOR_RED = (255, 69, 58)
COLOR_ROBOT_FACE = (224, 224, 224)
COLOR_ROBOT_STROKE = (51, 51, 51)
FONT_STATUS = pygame.font.Font(None, 32)
FONT_INSTRUCTIONS = pygame.font.Font(None, 28)
clock = pygame.time.Clock()

# --- ESTADO DA APLICAÇÃO ---
app_state = {
    "status": "idle",
    "status_message": "Pressione 'Espaço' para falar",
    "animation_timeline": [],
    "playback_start_time": 0,
    "current_mouth_shape": "closed",
    "audio_info_ready": None
}

# --- ASSETS DE ANIMAÇÃO (VISUALS DO ROBÔ) ---
face_margin = 50
face_width = SCREEN_WIDTH - (face_margin * 2)
face_height = SCREEN_HEIGHT * 0.7
ROBOT_FACE_RECT = pygame.Rect(face_margin, face_margin, face_width, face_height)

eye_y_pos = ROBOT_FACE_RECT.centery - (face_height * 0.15)
eye_x_offset = face_width * 0.2
EYE_RADIUS = face_width * 0.08
LEFT_EYE_POS = (ROBOT_FACE_RECT.centerx - eye_x_offset, eye_y_pos)
RIGHT_EYE_POS = (ROBOT_FACE_RECT.centerx + eye_x_offset, eye_y_pos)

mouth_y_pos = ROBOT_FACE_RECT.centery + (face_height * 0.25)
mouth_width = face_width * 0.5
MOUTH_RECT_BASE = pygame.Rect(0, 0, mouth_width, 20)
MOUTH_RECT_BASE.center = (ROBOT_FACE_RECT.centerx, mouth_y_pos)

mouth_shapes = {
    "closed": pygame.Surface(MOUTH_RECT_BASE.size, pygame.SRCALPHA),
    "open": pygame.Surface((mouth_width, face_height * 0.2), pygame.SRCALPHA),
    "mid": pygame.Surface((mouth_width, face_height * 0.1), pygame.SRCALPHA)
}
pygame.draw.rect(mouth_shapes["closed"], COLOR_ROBOT_STROKE, (0, 0, mouth_width, 15), border_radius=8)
pygame.draw.ellipse(mouth_shapes["open"], COLOR_ROBOT_STROKE, (0, 0, mouth_width, face_height * 0.2))
pygame.draw.ellipse(mouth_shapes["mid"], COLOR_ROBOT_STROKE, (0, 0, mouth_width, face_height * 0.1))

# --- LÓGICA DE ANIMAÇÃO E CONVERSA ---

def get_mouth_shape_for_char(char):
    char_lower = char.lower()
    if char_lower in 'aeiouáéíóúâêôãõ': return "open"
    if char_lower in 'bpm': return "closed"
    if char_lower in 'fv': return "mid"
    return "mid"

# <--- NOVA FUNÇÃO PARA ANÁLISE DE ÁUDIO ---
def analisar_audio_para_animacao(audio_path):
    """
    Cria uma timeline de animação baseada no volume do áudio.
    Retorna uma lista de frames para a animação da boca.
    """
    try:
        print("INFO: Analisando volume do áudio para criar animação...")
        # Carrega o áudio e garante que está no formato correto (mono)
        audio = AudioSegment.from_file(audio_path).set_channels(1)
        
        # Converte o áudio para um array numpy
        # A amplitude vai de -32768 a 32767 para áudio de 16-bit
        audio_samples = np.array(audio.get_array_of_samples())

        # Define o tamanho da janela de análise em milissegundos
        chunk_duration_ms = 50 
        chunk_size = int(audio.frame_rate * (chunk_duration_ms / 1000.0))
        
        volumes = []
        for i in range(0, len(audio_samples), chunk_size):
            chunk = audio_samples[i:i+chunk_size]
            # Calcula o RMS (Root Mean Square), uma boa medida de volume
            rms = np.sqrt(np.mean(chunk**2))
            volumes.append(rms)

        if not volumes: return []

        # Normaliza os volumes para um intervalo mais fácil de usar (0 a 1)
        max_rms = max(volumes) if volumes else 1
        normalized_volumes = [v / max_rms for v in volumes]

        timeline = []
        for i, volume in enumerate(normalized_volumes):
            time_ms = i * chunk_duration_ms
            shape = "closed"
            if volume > 0.3:
                shape = "open"
            elif volume > 0.1:
                shape = "mid"
            timeline.append({"time": time_ms, "shape": shape})
            
        print("INFO: Análise de volume concluída.")
        return timeline
    except Exception as e:
        print(f"ERRO ao analisar áudio: {e}. A animação pode falhar.")
        return []


def conversation_flow():
    app_state["status"] = "listening"
    app_state["status_message"] = "Ouvindo..."
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        user_text = recognizer.recognize_google(audio, language="pt-BR")
        print(f"Você disse: {user_text}")
    except (sr.UnknownValueError, sr.WaitTimeoutError):
        app_state["status_message"] = "Não entendi. Tente novamente."
        app_state["status"] = "error"
        return
    except Exception as e:
        print(f"Erro no reconhecimento de fala: {e}")
        app_state["status_message"] = "Erro no microfone."
        app_state["status"] = "error"
        return

    app_state["status"] = "thinking"
    app_state["status_message"] = "Pensando..."
    try:
        response = chat_session.send_message(user_text)
        ai_text = response.text
        print(f"IA (Gemini) respondeu: {ai_text}")
    except Exception as e:
        print(f"Erro na API do Gemini: {e}")
        app_state["status_message"] = "Erro ao conectar com a IA."
        app_state["status"] = "error"
        return

    generate_audio_file(ai_text)

def generate_audio_file(text_to_speak):
    try:
        app_state["status_message"] = "Processando..."
        voice_id = "JBFqnCBsd6RMkjVDRZzb"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "application/json",
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        data = { "text": text_to_speak, "model_id": "eleven_multilingual_v2" }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        full_audio = b''
        alignment_data = None

        if 'application/json' in content_type:
            print("INFO: Recebida resposta JSON com dados de alinhamento.")
            response_data = response.json()
            audio_base64 = response_data.get("audio_base64")
            alignment_data = response_data.get("alignment")
            if not audio_base64: raise Exception("JSON recebido, mas sem a chave 'audio_base64'.")
            full_audio = base64.b64decode(audio_base64)
        elif 'audio/mpeg' in content_type:
            print("AVISO: Recebido áudio MP3 puro, sem dados de alinhamento.")
            full_audio = response.content
        else:
            raise Exception(f"Tipo de conteúdo não esperado recebido: {content_type}")

        if not full_audio: raise Exception("Não foi possível extrair dados de áudio da resposta.")
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            audio_file_path = f.name
            f.write(full_audio)
        
        app_state["audio_info_ready"] = {"path": audio_file_path, "timeline": alignment_data}

    except requests.exceptions.HTTPError as http_err:
        print(f"Ocorreu um Erro HTTP: {http_err} - Resposta: {response.text}")
        app_state["status_message"] = "Erro de API."
        app_state["status"] = "error"
    except Exception as e:
        print(f"Ocorreu um erro na geração da fala: {e}")
        app_state["status_message"] = "Erro ao gerar a voz."
        app_state["status"] = "error"

# --- FUNÇÕES DE RENDERIZAÇÃO ---
def draw_robot():
    eye_color = COLOR_ROBOT_STROKE
    if app_state["status"] == "thinking": eye_color = COLOR_ORANGE
    elif app_state["status"] == "speaking": eye_color = COLOR_BLUE
    elif app_state["status"] == "error": eye_color = COLOR_RED

    pygame.draw.rect(screen, COLOR_ROBOT_FACE, ROBOT_FACE_RECT, border_radius=int(face_width * 0.1))
    pygame.draw.rect(screen, COLOR_ROBOT_STROKE, ROBOT_FACE_RECT, width=6, border_radius=int(face_width * 0.1))
    pygame.draw.circle(screen, eye_color, LEFT_EYE_POS, EYE_RADIUS)
    pygame.draw.circle(screen, eye_color, RIGHT_EYE_POS, EYE_RADIUS)
    
    mouth_surface = mouth_shapes[app_state["current_mouth_shape"]]
    mouth_rect = mouth_surface.get_rect(center=MOUTH_RECT_BASE.center)
    screen.blit(mouth_surface, mouth_rect)

def draw_ui():
    status_colors = {"idle": COLOR_BLUE, "listening": COLOR_GREEN_LIGHT, "thinking": COLOR_ORANGE, "speaking": COLOR_BLUE, "error": COLOR_RED}
    status_color = status_colors.get(app_state["status"], COLOR_BLACK)
    status_surface = FONT_STATUS.render(app_state["status_message"], True, COLOR_BLACK)
    status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
    pygame.draw.rect(screen, COLOR_WHITE, status_rect.inflate(20, 20), border_radius=10)
    pygame.draw.rect(screen, status_color, status_rect.inflate(20, 20), width=3, border_radius=10)
    screen.blit(status_surface, status_rect)
    if app_state["status"] in ["idle", "error"]:
        inst_surface = FONT_INSTRUCTIONS.render("Pressione 'Espaço' para falar ou 'Q' para sair", True, COLOR_BLACK)
        inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(inst_surface, inst_rect)

# --- LOOP PRINCIPAL DA APLICAÇÃO ---
running = True
generation_config_gemini = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
}
model_gemini = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config_gemini,
    system_instruction="Você é um robô assistente amigável. Seja conciso em suas respostas.",
)
chat_session = model_gemini.start_chat(history=[])

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and app_state["status"] in ["idle", "error"]:
            threading.Thread(target=conversation_flow).start()

    # --- Lógica de Estado e Animação ---
    if info := app_state.get("audio_info_ready"):
        app_state["audio_info_ready"] = None
        try:
            alignment_data = info["timeline"]
            timeline = []

            if alignment_data:
                # Se temos dados da API, usamos para a sincronia perfeita
                print("INFO: Usando timeline da API para animação.")
                chars = alignment_data.get("characters", [])
                start_times_sec = alignment_data.get("character_start_times_seconds", [])
                
                for char, start_time in zip(chars, start_times_sec):
                    if not char.isspace():
                        start_ms = start_time * 1000
                        shape = get_mouth_shape_for_char(char)
                        timeline.append({"time": start_ms, "shape": shape})
            else:
                # <--- MUDANÇA: Se não temos dados, analisamos o áudio ---
                # Esta é a nossa animação de fallback baseada em volume
                timeline = analisar_audio_para_animacao(info["path"])
            
            app_state["animation_timeline"] = timeline
            pygame.mixer.music.load(info["path"])
            pygame.mixer.music.play()
            app_state["status"] = "speaking"
            app_state["status_message"] = "Falando..."
            app_state["playback_start_time"] = pygame.time.get_ticks()
        except pygame.error as e:
            print(f"Erro ao carregar ou tocar o som: {e}")
            app_state["status"] = "error"
            app_state["status_message"] = "Erro no áudio."

    if app_state["status"] == "speaking":
        if not pygame.mixer.music.get_busy():
            app_state["status"] = "idle"
            app_state["status_message"] = "Pressione 'Espaço' para falar"
            app_state["current_mouth_shape"] = "closed"
        else:
            elapsed_time = pygame.time.get_ticks() - app_state["playback_start_time"]
            current_shape = "closed" # Começa fechada
            
            # Esta lógica agora funciona para AMBAS as timelines (real ou simulada)
            for frame in reversed(app_state["animation_timeline"]):
                if elapsed_time >= frame["time"]:
                    current_shape = frame["shape"]
                    break
            
            app_state["current_mouth_shape"] = current_shape
    
    # --- Renderização ---
    screen.fill(COLOR_GRAY)
    draw_robot()
    draw_ui()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
