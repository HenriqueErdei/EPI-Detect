# core/capture.py — captura de vídeo
# Webcam e RTSP: thread separada elimina buffer acumulado (sempre o frame mais recente)
# Vídeo arquivo: leitura direta — threading não ajuda e adiciona overhead
import os
import re
import threading
import time
from pathlib import Path
from sys import platform
from urllib.parse import urlparse

import cv2

NETWORK_SCHEMES = ("rtsp://", "rtsps://", "http://", "https://")


def is_network_url(source) -> bool:
    return isinstance(source, str) and source.lower().startswith(NETWORK_SCHEMES)


def redact_source(source) -> str:
    if not isinstance(source, str):
        return str(source)
    return re.sub(r"(://[^:/?#]+:)[^@/#?]+@", r"\1***@", source)


def source_label(source) -> str:
    if isinstance(source, int):
        return "Webcam" if source == 0 else f"Câmera {source}"
    text = str(source)
    if is_network_url(text):
        parsed = urlparse(text)
        path = (parsed.path or "").strip("/")
        if path:
            return path.split("/")[-1]
        return parsed.hostname or "Stream"
    return Path(text).name


def parse_source(src: str):
    """Devolve (fonte, modo). Fonte é índice de câmera, caminho ou URL."""
    src = (src or "").strip()
    if src in ("webcam", "0"):
        return 0, "LIVE"
    if src.isdigit():
        return int(src), "LIVE"
    if is_network_url(src):
        return src, "LIVE"
    path = Path(src)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    return str(path.resolve()), "FILE"


def _prefer_rtsp_tcp():
    os.environ.setdefault(
        "OPENCV_FFMPEG_CAPTURE_OPTIONS",
        "rtsp_transport;tcp|fflags;nobuffer",
    )


class VideoCapture:
    def __init__(self, source, width=None, height=None, fps=None):
        self._is_webcam = isinstance(source, int)
        self._is_live = self._is_webcam or is_network_url(source)
        self._cap = self._open_capture(source)

        if not self._cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir: {redact_source(source)}")

        if self._is_webcam:
            if width:
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            if height:
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            if fps:
                self._cap.set(cv2.CAP_PROP_FPS, fps)

        if self._is_live:
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._frame = None
            self._ok = False
            self._lock = threading.Lock()
            self._stop = threading.Event()
            self._thread = threading.Thread(target=self._reader, daemon=True)
            self._thread.start()
            # Webcam local e RTSP podem demorar a entregar o primeiro frame.
            wait_s = 15.0 if is_network_url(source) else 5.0
            deadline = time.monotonic() + wait_s
            while self._frame is None and time.monotonic() < deadline:
                time.sleep(0.05)

    def _open_capture(self, source):
        if isinstance(source, int):
            backends = [cv2.CAP_ANY]
            if platform.startswith("win"):
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]

            for backend in backends:
                cap = cv2.VideoCapture(source, backend)
                if cap.isOpened():
                    return cap
                cap.release()

            return cv2.VideoCapture(source)

        if is_network_url(source):
            _prefer_rtsp_tcp()
            backends = [cv2.CAP_FFMPEG, cv2.CAP_ANY]
            for backend in backends:
                cap = cv2.VideoCapture(source, backend)
                if cap.isOpened():
                    return cap
                cap.release()

        return cv2.VideoCapture(source)

    def _reader(self):
        """Thread só usada em fontes ao vivo (webcam / RTSP)."""
        while not self._stop.is_set():
            ok, frame = self._cap.read()
            with self._lock:
                if ok and frame is not None:
                    self._frame = frame
                self._ok = ok
            if not ok:
                time.sleep(0.05)

    def read(self):
        if self._is_live:
            with self._lock:
                if self._frame is None:
                    return False, None
                return self._ok, self._frame.copy()
        return self._cap.read()

    @property
    def is_webcam(self):
        return self._is_webcam

    @property
    def fps(self):
        v = self._cap.get(cv2.CAP_PROP_FPS)
        return v if v > 0 else 30

    @property
    def width(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def release(self):
        if self._is_live:
            self._stop.set()
            self._thread.join(timeout=2)
        self._cap.release()
