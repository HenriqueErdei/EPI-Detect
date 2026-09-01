#!/usr/bin/env python3
"""
detect.py — EPI Vest Detector
Uso:
  python detect.py                        # webcam padrão
  python detect.py --source video.mp4     # qualquer vídeo
  python detect.py --source 0             # webcam índice 0
  python detect.py --source 1             # webcam índice 1 (segunda câmera)
  python detect.py --source rtsp://user:pass@host:8554/cam
"""

import argparse
import sys
import time
from pathlib import Path

import cv2

# garante que o diretório do projeto esteja no path
sys.path.insert(0, str(Path(__file__).parent))

import config as cfg
from core.capture import VideoCapture, parse_source, redact_source
from core.detector import EPIDetector
from core.display import Renderer


def parse_args():
    p = argparse.ArgumentParser(description="EPI Vest Detector")
    p.add_argument(
        "--source",
        default="webcam",
        help="'webcam', índice de câmera, caminho de vídeo ou URL RTSP/HTTP",
    )
    p.add_argument(
        "--skip",
        type=int,
        default=cfg.FRAME_SKIP,
        help=f"processar 1 a cada N frames (padrão: {cfg.FRAME_SKIP})",
    )
    p.add_argument("--save", metavar="OUTPUT.mp4", default=None, help="salvar o vídeo processado")
    return p.parse_args()


def resolve_source(src: str):
    try:
        return parse_source(src)
    except FileNotFoundError as e:
        sys.exit(f"[erro] {e}")


def main():
    args = parse_args()
    source, mode = resolve_source(args.source)

    print(f"\n{'=' * 50}")
    print("  EPI Detect")
    print("  Henrique Erdei")
    print(f"  Fonte : {redact_source(source)}  |  Modo: {mode}")
    print(f"{'=' * 50}")
    print("  Carregando modelo YOLO...")

    detector = EPIDetector()
    renderer = Renderer(mode=mode)

    print("  Abrindo fonte de vídeo...")
    cap = VideoCapture(
        source,
        width=cfg.WEBCAM_WIDTH if isinstance(source, int) else None,
        height=cfg.WEBCAM_HEIGHT if isinstance(source, int) else None,
        fps=cfg.WEBCAM_FPS if isinstance(source, int) else None,
    )

    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.save, fourcc, cap.fps, (cap.width, cap.height))

    window = "EPI Detect | Q para sair"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 1280, 720)

    print("\n  Iniciando detecção. Pressione Q para sair.\n")

    frame_n = 0
    last_dets = []
    running = True
    frame_delay = 1.0 / (cap.fps if mode == "FILE" else cfg.STREAM_FPS)

    while running:
        started = time.perf_counter()
        ok, frame = cap.read()
        if not ok:
            if mode == "FILE":
                # reinicia o vídeo sem recriar o objeto
                cap.release()
                cap = VideoCapture(source)
                frame_n = 0
                # verifica tecla antes de continuar (permite fechar no loop)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                    break
                continue
            break

        frame_n += 1

        # --- Detecção (respeitando frame skip) ---
        if frame_n % max(args.skip, 1) == 0:
            last_dets = detector.detect(frame)

        # --- Render ---
        out = renderer.render(frame, last_dets)

        cv2.imshow(window, out)

        if writer:
            writer.write(out)

        remaining_ms = int((frame_delay - (time.perf_counter() - started)) * 1000)
        key = cv2.waitKey(max(1, remaining_ms)) & 0xFF
        if key in (ord("q"), ord("Q"), 27):  # Q ou ESC
            running = False
            break

    cap.release()
    if writer:
        writer.release()
        print(f"\n  Vídeo salvo em: {args.save}")
    cv2.destroyAllWindows()
    print("  Encerrado.\n")


if __name__ == "__main__":
    main()
