# config.py — EPI Vest Detector
# Ajuste aqui sem tocar no código principal

# --- Modelo ---
MODEL_NAME = "yolov8n-pose.pt"  # pose: detecta APENAS humanos + keypoints (filtra cones etc.)
INPUT_SIZE = 416  # menor custo em CPU; suficiente para webcam/CCTV proxima
CONF_THRESH = 0.20  # baixo para pegar pessoas no fundo
PERSON_CLASS = 0  # mantido para compatibilidade, ignorado pelo pose model

# Filtros anti-falso-positivo
KP_CONF_THRESH = 0.30  # confiança mínima de keypoint para usar coordenada
MIN_PERSON_HEIGHT = 35  # px mínimos — aceita pessoas distantes/menores
MIN_PERSON_RATIO = 0.35  # altura/largura mínima (cones têm ratio < isso)

# --- Análise de colete (HSV) ---
# Laranja high-vis  (EN ISO 20471 — H 5-22, alta saturação)
ORANGE_LOW = (5, 90, 60)
ORANGE_HIGH = (22, 255, 255)
# Amarelo-limão / verde fluorescente (coletes padrão CCTV — H 25-92)
# S e V baixos porque câmera de segurança tem compressão e variação de luz
YELLOW_LOW = (25, 50, 50)
YELLOW_HIGH = (92, 255, 255)

# Torso: pescoço (22%) até quadril (78%) — região exata do colete
TORSO_TOP = 0.22
TORSO_BOTTOM = 0.78
# Colete cobre uma area grande do peito. Faixas de uniforme cinza ficam ~5-15%.
VEST_THRESH = 0.20
# Exige cor fluorescente nos dois lados do torso para rejeitar uma faixa solta
# colocada somente sobre um braco ou ombro.
VEST_SIDE_THRESH = 0.04
# Fracao minima de linhas do torso com pixels fluorescentes.
# Rejeita 1-2 faixas horizontais (cintura/biceps) que nao formam um colete.
VEST_SPAN_THRESH = 0.40

# --- Performance ---
FRAME_SKIP = 8  # detecta 1 a cada N frames; reaproveita o resultado entre inferencias
STREAM_FPS = 20  # FPS alvo do stream web (encoder thread)
DETECTION_INTERVAL = 0.20  # ate 5 analises/s; captura e stream nao aguardam a IA
TORCH_THREADS = 2  # reserva CPU para captura, JPEG e servidor web (maquina com 4 threads)
WEBCAM_WIDTH = 960
WEBCAM_HEIGHT = 540
WEBCAM_FPS = 30

# --- UI ---
# OpenCV usa BGR.
COLOR_OK = (255, 140, 79)  # azul  RGB #4f8cff
COLOR_WARN = (42, 140, 240)  # laranja  RGB #f08c2a
COLOR_INFO = (255, 168, 90)  # azul claro  RGB #5aa8ff
COLOR_BG = (36, 20, 10)  # azul-marinho  RGB #0a1424
ALPHA_OVERLAY = 0.65  # opacidade dos painéis

# Fontes (Pillow) — caminho relativo ao projeto
FONT_PATH = None  # None = usa fonte embutida do Pillow
FONT_SIZE_LG = 22
FONT_SIZE_MD = 16
FONT_SIZE_SM = 13
