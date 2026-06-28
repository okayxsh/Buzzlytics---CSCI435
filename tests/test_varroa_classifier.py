"""Tests for the stage-2 VarroaClassifier (no real model required)."""
import numpy as np

from cv_pipeline.varroa_classifier import VarroaClassifier


class _Arr:
    def __init__(self, vec):
        self._v = vec

    def cpu(self):
        return self

    def numpy(self):
        return np.array(self._v)


class _Probs:
    def __init__(self, top1, conf, vec):
        self.top1 = top1
        self.top1conf = conf
        self.data = _Arr(vec)


class _Res:
    def __init__(self, probs):
        self.names = {0: "healthy", 1: "varroa"}
        self.probs = probs


class _FakeModel:
    def __init__(self, res):
        self._res = res

    def __call__(self, crop, verbose=False):
        return [self._res]


def _clf_with_fake_model(top_name, conf, threshold=0.5):
    """Build a VarroaClassifier whose model is a 2-class stub."""
    clf = VarroaClassifier.__new__(VarroaClassifier)
    clf.conf_threshold = threshold
    top1 = 1 if top_name == "varroa" else 0
    vec = [0.0, 0.0]
    vec[top1] = conf
    vec[1 - top1] = 1.0 - conf
    clf._model = _FakeModel(_Res(_Probs(top1, conf, vec)))
    return clf


def test_unavailable_when_no_model():
    clf = VarroaClassifier.__new__(VarroaClassifier)
    clf.conf_threshold = 0.5
    clf._model = None
    assert clf.available is False
    assert clf.is_varroa(np.zeros((10, 10, 3), dtype=np.uint8)) is False


def test_varroa_when_confident():
    clf = _clf_with_fake_model("varroa", 0.9)
    assert clf.available is True
    assert clf.is_varroa(np.zeros((10, 10, 3), dtype=np.uint8)) is True


def test_not_varroa_below_threshold():
    clf = _clf_with_fake_model("varroa", 0.4)  # below 0.5
    assert clf.is_varroa(np.zeros((10, 10, 3), dtype=np.uint8)) is False


def test_healthy_label_is_not_varroa():
    clf = _clf_with_fake_model("healthy", 0.99)
    assert clf.is_varroa(np.zeros((10, 10, 3), dtype=np.uint8)) is False


def test_empty_or_tiny_crop_is_safe():
    clf = _clf_with_fake_model("varroa", 0.99)
    assert clf.is_varroa(np.zeros((0, 0, 3), dtype=np.uint8)) is False
    assert clf.is_varroa(np.zeros((1, 1, 3), dtype=np.uint8)) is False


def test_classify_returns_detail_dict():
    clf = _clf_with_fake_model("varroa", 0.9)
    out = clf.classify(np.zeros((10, 10, 3), dtype=np.uint8))
    assert out["label"] == "varroa"
    assert out["is_varroa"] is True
    assert round(out["confidence"], 2) == 0.9
