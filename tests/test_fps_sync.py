import config as cfg


def test_stream_and_vest_detection_target_30fps():
    assert cfg.STREAM_FPS == 30
    assert cfg.WEBCAM_FPS == 30
    assert cfg.FRAME_SKIP == 1
    assert cfg.DETECTION_INTERVAL == 1.0 / cfg.STREAM_FPS
