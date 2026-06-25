"""Tests for the stage-2 VarroaClassifier (no real model required)."""
import numpy as np

from cv_pipeline.varroa_classifier import VarroaClassifier


def _clf_with_fake_model(top_name, conf):
    """Build a VarroaClassifier whose model is a stub returning (name, conf)."""
    clf = VarroaClassifier.__new__(VarroaClassifier)
    clf.conf_threshold = 0.5

    class _Probs:
        top1 = 0
        top1conf = conf

    class _Res:
        names = {0: top_name}
        probs = _Probs()

    class _FakeModel:
        def __call__(self, crop, verbose=False):
            return [_Res()]

    clf._model = _FakeModel()
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
