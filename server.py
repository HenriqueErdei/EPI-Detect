"""
server.py -- EPI Detect Web Dashboard
Acesse: http://localhost:5000

Pipeline assincrono:
  Thread 1 (capture) — mantem o frame mais recente da camera/video
  Thread 2 (detect)  — roda YOLO + HSV sem bloquear o stream
  Thread 3 (encode)  — renderiza e gera JPEG a STREAM_FPS
  Flask              — serve MJPEG + stats
"""

import argparse
import sys
import threading
import time
from pathlib import Path

import cv2
from flask import Flask, Response, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).parent))

import config as cfg
from core.capture import VideoCapture, parse_source, redact_source, source_label
from core.detector import EPIDetector
from core.display import Renderer

_RTSP_SCHEMES = ("rtsp://", "rtsps://")

app = Flask(__name__)
_lock = threading.Lock()

# estado compartilhado entre threads
_state = {
    "raw_frame": None,
    "detections": [],
    "jpeg": None,  # bytes        — escrito por encode, lido por Flask
    "with_vest": 0,
    "without_vest": 0,
    "total": 0,
    "det_fps": 0,  # FPS da detecção
    "stream_fps": 0,  # FPS do stream
    "mode": "LIVE",
    "alert": False,
    "camera_ready": False,
    "model_ready": False,
    "status": "starting",
    "error": None,
    "source": 0,
    "source_label": "Webcam",
    "generation": 0,
}
_running = True


def _refresh_status_locked():
    """Atualiza o estado publico; deve ser chamado com `_lock` adquirido."""
    if _state["error"]:
        _state["status"] = "error"
    elif not _state["camera_ready"]:
        _state["status"] = "waiting_camera"
    elif not _state["model_ready"]:
        _state["status"] = "loading_model"
    else:
        _state["status"] = "running"


def _box_iou(det, track) -> float:
    ax1, ay1, ax2, ay2 = det.x1, det.y1, det.x2, det.y2
    bx1, by1, bx2, by2 = track["box"]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


def _stabilize_detections(detections, tracks, frame_index):
    """Usa maioria temporal de 5 analises, associando pessoas por IoU."""
    used = set()
    for det in detections:
        candidates = [(i, _box_iou(det, track)) for i, track in enumerate(tracks) if i not in used]
        best_i, best_iou = max(candidates, key=lambda item: item[1], default=(-1, 0.0))
        if best_iou < 0.30:
            tracks.append(
                {"box": (det.x1, det.y1, det.x2, det.y2), "votes": [], "last": frame_index}
            )
            best_i = len(tracks) - 1

        track = tracks[best_i]
        used.add(best_i)
        track["box"] = (det.x1, det.y1, det.x2, det.y2)
        track["last"] = frame_index
        track["votes"].append(bool(det.has_vest))
        track["votes"] = track["votes"][-5:]
        if len(track["votes"]) >= 3:
            det.has_vest = sum(track["votes"]) > len(track["votes"]) / 2

    tracks[:] = [t for t in tracks if frame_index - t["last"] <= 10]
    return detections


# ── Thread 1: captura ─────────────────────────────────────────────────────────
def _apply_source(source, mode: str):
    with _lock:
        _state["source"] = source
        _state["mode"] = mode
        _state["source_label"] = source_label(source)
        _state["generation"] += 1
        _state["raw_frame"] = None
        _state["jpeg"] = None
        _state["detections"] = []
        _state["with_vest"] = 0
        _state["without_vest"] = 0
        _state["total"] = 0
        _state["alert"] = False
        _state["camera_ready"] = False
        _state["error"] = None
        _refresh_status_locked()


def _capture_loop():
    global _running
    while _running:
        with _lock:
            source = _state["source"]
            mode = _state["mode"]
            gen = _state["generation"]
        try:
            cap = VideoCapture(
                source,
                width=cfg.WEBCAM_WIDTH if isinstance(source, int) else None,
                height=cfg.WEBCAM_HEIGHT if isinstance(source, int) else None,
                fps=cfg.WEBCAM_FPS if isinstance(source, int) else None,
            )
        except RuntimeError as e:
            message = redact_source(str(e))
            print(f"[capture] {message}", flush=True)
            with _lock:
                if _state["generation"] != gen:
                    continue
                _state["camera_ready"] = False
                _state["error"] = message
                _refresh_status_locked()
            time.sleep(2)
            continue

        frame_delay = 1.0 / (cap.fps if mode == "FILE" else cfg.STREAM_FPS)
        while _running:
            with _lock:
                if _state["generation"] != gen:
                    break
            started = time.perf_counter()
            try:
                ok, frame = cap.read()
            except Exception as e:
                print(f"[capture] cap.read erro: {e}", flush=True)
                break
            if not ok:
                break

            with _lock:
                _state["raw_frame"] = frame
                _state["camera_ready"] = True
                _state["error"] = None
                _refresh_status_locked()

            remaining = frame_delay - (time.perf_counter() - started)
            if remaining > 0:
                time.sleep(remaining)

        cap.release()
        with _lock:
            switched = _state["generation"] != gen
        if _running and mode == "LIVE" and not switched:
            time.sleep(0.5)


def _detect_loop():
    global _running
    try:
        det = EPIDetector()
    except Exception as e:
        import traceback

        print(f"[detect] ERRO ao iniciar: {e}", flush=True)
        traceback.print_exc()
        with _lock:
            _state["model_ready"] = False
            _state["error"] = f"Falha ao carregar o modelo: {e}"
            _refresh_status_locked()
        return
    print("[detect] modelo carregado", flush=True)
    with _lock:
        _state["model_ready"] = True
        _state["error"] = None
        _refresh_status_locked()

    det_times: list = []
    last_frame = None
    tracks = []
    frame_index = 0
    last_gen = -1
    while _running:
        cycle_start = time.perf_counter()
        with _lock:
            frame = _state["raw_frame"]
            gen = _state["generation"]

        if gen != last_gen:
            tracks = []
            last_frame = None
            last_gen = gen

        if frame is None or frame is last_frame:
            time.sleep(0.01)
            continue

        try:
            detections = det.detect(frame)
        except Exception as e:
            print(f"[detect] inferencia falhou: {e}", flush=True)
            with _lock:
                _state["error"] = f"Falha temporaria na inferencia: {e}"
                _refresh_status_locked()
            time.sleep(0.2)
            continue
        last_frame = frame
        frame_index += 1
        detections = _stabilize_detections(detections, tracks, frame_index)

        now = time.perf_counter()
        det_times.append(now)
        det_times = [t for t in det_times if now - t < 1.0]
        with_v = sum(1 for d in detections if d.has_vest)
        wout_v = len(detections) - with_v
        with _lock:
            _state["error"] = None
            _state["detections"] = detections
            _state["with_vest"] = with_v
            _state["without_vest"] = wout_v
            _state["total"] = len(detections)
            _state["det_fps"] = len(det_times)
            _state["alert"] = wout_v > 0
            _refresh_status_locked()

        remaining = cfg.DETECTION_INTERVAL - (time.perf_counter() - cycle_start)
        if remaining > 0:
            time.sleep(remaining)


# ── Thread 2: encoder JPEG (roda a STREAM_FPS) ───────────────────────────────
def _encode_loop():
    global _running
    target = 1.0 / cfg.STREAM_FPS
    enc_times: list = []
    last_arr = None
    last_dets = None
    renderer = Renderer(mode=_state["mode"])

    while _running:
        t0 = time.perf_counter()

        with _lock:
            arr = _state["raw_frame"]
            dets_ref = _state["detections"]
            detections = list(dets_ref)
            renderer.mode = _state["mode"]

        if arr is None:
            time.sleep(0.02)
            continue

        if arr is not last_arr or dets_ref is not last_dets:
            rendered = renderer.render(arr, detections)
            ok, buf = cv2.imencode(".jpg", rendered, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ok:
                now = time.perf_counter()
                enc_times.append(now)
                enc_times = [t for t in enc_times if now - t < 1.0]
                with _lock:
                    _state["jpeg"] = buf.tobytes()
                    _state["stream_fps"] = len(enc_times)
                last_arr = arr
                last_dets = dets_ref

        elapsed = time.perf_counter() - t0
        sleep = target - elapsed
        if sleep > 0:
            time.sleep(sleep)


# ── MJPEG generator ──────────────────────────────────────────────────────────
def _gen():
    last = None
    while True:
        with _lock:
            frame = _state["jpeg"]
        if frame is None or frame is last:
            time.sleep(0.002)
            continue
        last = frame
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


# ── rotas Flask ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template(
        "index.html",
        mode=_state["mode"],
        source_label=_state["source_label"],
    )


@app.route("/video_feed")
def video_feed():
    return Response(_gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/stats")
def stats():
    with _lock:
        return jsonify(
            {
                "with_vest": _state["with_vest"],
                "without_vest": _state["without_vest"],
                "total": _state["total"],
                "fps": _state["stream_fps"],
                "det_fps": _state["det_fps"],
                "alert": _state["alert"],
                "status": _state["status"],
                "error": _state["error"],
                "mode": _state["mode"],
                "source_label": _state["source_label"],
            }
        )


@app.route("/health")
def health():
    with _lock:
        payload = {
            "ok": _state["status"] != "error",
            "status": _state["status"],
            "camera_ready": _state["camera_ready"],
            "model_ready": _state["model_ready"],
        }
        return jsonify(payload), (200 if payload["ok"] else 503)


def _parse_public_source(raw: str):
    """Painel público: só RTSP. Arquivo e webcam ficam no CLI (--source)."""
    url = (raw or "").strip()
    if not url.lower().startswith(_RTSP_SCHEMES):
        raise ValueError("Informe um link RTSP (rtsp:// ou rtsps://).")
    return parse_source(url)


@app.route("/source", methods=["POST"])
def set_source():
    if "file" in request.files and request.files["file"].filename:
        return jsonify(
            {"ok": False, "error": "Upload de vídeo está desativado. Use um link RTSP."}
        ), 400
    payload = request.get_json(silent=True) or request.form
    raw = (payload.get("url") or payload.get("source") or "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "Informe um link RTSP (rtsp:// ou rtsps://)."}), 400
    try:
        source, mode = _parse_public_source(raw)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    _apply_source(source, mode)
    print(f"[source] {mode} {redact_source(source)}", flush=True)
    return jsonify({"ok": True, "mode": mode, "source_label": source_label(source)})


# ── main ─────────────────────────────────────────────────────────────────────
def resolve_source(src: str):
    try:
        return parse_source(src)
    except FileNotFoundError as e:
        sys.exit(f"[erro] {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source",
        default="webcam",
        help="webcam, índice, arquivo MP4 ou URL RTSP (o painel só aceita RTSP)",
    )
    p.add_argument("--port", default=5000, type=int)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    source, mode = resolve_source(args.source)
    _apply_source(source, mode)

    print("\n  EPI Detect")
    print("  Henrique Erdei")
    print(f"  Fonte  : {redact_source(source)}")
    print(f"  Modo   : {mode}")
    print(f"  URL    : http://localhost:{args.port}")
    print(f"  Stream : {cfg.STREAM_FPS} fps alvo")
    print(f"  Detect : {1.0 / cfg.DETECTION_INTERVAL:.0f} fps alvo\n")

    threading.Thread(target=_capture_loop, daemon=True).start()
    threading.Thread(target=_detect_loop, daemon=True).start()
    threading.Thread(target=_encode_loop, daemon=True).start()

    if not args.no_browser:
        import webbrowser

        time.sleep(2.0)
        webbrowser.open(f"http://localhost:{args.port}")

    app.run(host=args.host, port=args.port, debug=False, threaded=True)
