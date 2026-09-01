import cv2
import numpy as np

import config as cfg
from core.detector import EPIDetector, is_vest_evidence


def _fluorescent_bgr():
    return cv2.cvtColor(np.uint8([[[35, 230, 230]]]), cv2.COLOR_HSV2BGR)[0, 0]


def _hsv_metrics(torso):
    detector = EPIDetector.__new__(EPIDetector)
    return detector._hsv_coverage(torso)


def test_bilateral_evidence_is_required():
    assert not is_vest_evidence(0.50, 0.50, 0.0, 0.70)
    assert not is_vest_evidence(0.50, 0.0, 0.50, 0.70)
    assert is_vest_evidence(0.50, 0.50, 0.50, 0.70)


def test_thresholds_are_inclusive():
    assert is_vest_evidence(
        cfg.VEST_THRESH,
        cfg.VEST_SIDE_THRESH,
        cfg.VEST_SIDE_THRESH,
        cfg.VEST_SPAN_THRESH,
    )


def test_low_coverage_is_not_a_vest():
    # ~5% e o tamanho tipico de uma faixa na cintura, nao de um colete.
    assert not is_vest_evidence(0.05, 0.05, 0.05, 1.0)


def test_thin_horizontal_span_is_not_a_vest():
    # Area grande o bastante para o limiar, mas so uma faixa baixa no tronco.
    assert not is_vest_evidence(0.25, 0.25, 0.25, 0.12)


def test_hsv_metrics_distinguish_one_and_two_sides():
    torso = np.zeros((100, 100, 3), dtype=np.uint8)
    yellow = _fluorescent_bgr()

    torso[:, :40] = yellow
    total, left, right, span = _hsv_metrics(torso)
    assert total > cfg.VEST_THRESH
    assert left > cfg.VEST_SIDE_THRESH
    assert right == 0.0
    assert span > cfg.VEST_SPAN_THRESH
    assert not is_vest_evidence(total, left, right, span)

    torso[:, 60:] = yellow
    total, left, right, span = _hsv_metrics(torso)
    assert is_vest_evidence(total, left, right, span)


def test_waist_strip_is_not_a_vest():
    torso = np.zeros((100, 100, 3), dtype=np.uint8)
    torso[72:80, :] = _fluorescent_bgr()
    total, left, right, span = _hsv_metrics(torso)
    assert not is_vest_evidence(total, left, right, span)


def test_uniform_stripes_are_not_a_vest():
    # Uniforme cinza: faixa no biceps + faixa na cintura.
    torso = np.zeros((100, 100, 3), dtype=np.uint8)
    yellow = _fluorescent_bgr()
    torso[18:26, :] = yellow
    torso[72:80, :] = yellow
    total, left, right, span = _hsv_metrics(torso)
    assert not is_vest_evidence(total, left, right, span)


def test_full_fluorescent_torso_is_a_vest():
    torso = np.zeros((100, 100, 3), dtype=np.uint8)
    torso[12:88, 8:92] = _fluorescent_bgr()
    total, left, right, span = _hsv_metrics(torso)
    assert is_vest_evidence(total, left, right, span)


def test_ok_color_is_blue_in_bgr():
    blue, green, red = cfg.COLOR_OK
    assert blue > red
    assert blue > green


def test_warning_color_is_orange_in_bgr():
    blue, green, red = cfg.COLOR_WARN
    assert red > blue
    assert red > green
