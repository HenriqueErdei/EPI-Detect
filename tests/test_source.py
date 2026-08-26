from pathlib import Path

import pytest

from core.capture import is_network_url, parse_source, redact_source, source_label


def test_rtsp_is_live_and_keeps_url():
    url = "rtsp://user:pass@host:8554/cam-01"
    source, mode = parse_source(url)
    assert source == url
    assert mode == "LIVE"


def test_http_stream_is_live():
    source, mode = parse_source("http://camera.local/stream")
    assert source == "http://camera.local/stream"
    assert mode == "LIVE"


def test_webcam_and_index():
    assert parse_source("webcam") == (0, "LIVE")
    assert parse_source("1") == (1, "LIVE")


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_source("nao-existe.mp4")


def test_demo_is_not_a_source():
    with pytest.raises(FileNotFoundError):
        parse_source("demo")


def test_local_video_is_file(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake")
    source, mode = parse_source(str(video))
    assert Path(source) == video.resolve()
    assert mode == "FILE"


def test_redact_password_in_rtsp():
    assert (
        redact_source("rtsp://sondo:secret@host:8554/orion-09-cam-01")
        == "rtsp://sondo:***@host:8554/orion-09-cam-01"
    )


def test_source_label_hides_credentials():
    assert source_label("rtsp://user:pass@host:8554/orion-05-cam-01") == "orion-05-cam-01"
    assert source_label(0) == "Webcam"
    assert source_label("videos-teste/testesabesp.mp4") == "testesabesp.mp4"


def test_is_network_url():
    assert is_network_url("rtsp://host/cam")
    assert is_network_url("rtsps://host/cam")
    assert not is_network_url("videos-teste/clip.mp4")
    assert not is_network_url(0)
