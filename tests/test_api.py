import server


def test_stats_contract():
    client = server.app.test_client()
    response = client.get("/stats")
    assert response.status_code == 200
    payload = response.get_json()
    assert {
        "with_vest",
        "without_vest",
        "total",
        "fps",
        "det_fps",
        "alert",
        "status",
        "error",
        "mode",
        "source_label",
    } <= payload.keys()


def test_health_contract():
    client = server.app.test_client()
    response = client.get("/health")
    assert response.status_code in {200, 503}
    payload = response.get_json()
    assert {"ok", "status", "camera_ready", "model_ready"} <= payload.keys()


def test_source_rejects_empty():
    response = server.app.test_client().post("/source", json={})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_source_rejects_webcam():
    response = server.app.test_client().post("/source", json={"source": "webcam"})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_source_rejects_http_and_file():
    from io import BytesIO

    client = server.app.test_client()
    http = client.post("/source", json={"url": "http://camera.local/stream"})
    assert http.status_code == 400
    demo = client.post("/source", json={"url": "demo"})
    assert demo.status_code == 400
    upload = client.post("/source", data={"file": (BytesIO(b"fake"), "clip.mp4")})
    assert upload.status_code == 400
    assert "RTSP" in upload.get_json()["error"]


def test_source_accepts_rtsp():
    response = server.app.test_client().post(
        "/source", json={"url": "rtsp://user:pass@host:8554/cam-01"}
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["mode"] == "LIVE"
    assert payload["source_label"] == "cam-01"


def test_source_rejects_demo():
    response = server.app.test_client().post("/source", json={"url": "demo"})
    assert response.status_code == 400
