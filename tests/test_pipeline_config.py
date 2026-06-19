"""Pipeline wires config values into sub-modules."""
from unittest.mock import patch, MagicMock

from cv_pipeline.pipeline import CVPipeline


def test_pipeline_uses_config_conf_threshold():
    cfg = {
        "detector": {"model_path": "missing.pt", "conf_threshold": 0.31,
                     "iou_threshold": 0.4, "imgsz": 640},
        "tracker": {"track_buffer": 30, "match_thresh": 0.8},
        "analytics": {
            "pollen_good_threshold": 0.1, "varroa_warn_threshold": 0.15,
            "wasp_threat_threshold": 0.05, "low_activity_threshold": 0.3,
            "health_weights": {"base": 70, "pollen_bonus": 10,
                               "varroa_penalty": 20, "wasp_penalty": 25,
                               "low_activity_penalty": 10},
        },
        "visualize": {"colors": {"bee": [0, 200, 0], "pollen_bee": [0, 220, 255],
                                 "varroa_bee": [0, 0, 220], "wasp": [0, 140, 255]}},
        "video": {"frame_skip": 2},
        "motion": {"history": 500, "var_threshold": 16, "detect_shadows": True, "kernel_size": 3},
        "preprocess": {"white_balance": True, "clahe_clip_limit": 2.0, "denoise_strength": 10},
    }
    # Patch ultralytics.YOLO so no model file is needed in the test environment.
    with patch("ultralytics.YOLO", return_value=MagicMock()):
        pipe = CVPipeline(config=cfg)
    assert pipe.conf_threshold == 0.31
    assert pipe.detector.conf_threshold == 0.31
    assert pipe.visualizer.color_map["wasp"] == (0, 140, 255)
