import os
import json
import tempfile
from zignal.config import SignalConfig


def test_default_config():
    cfg = SignalConfig(config_dir=tempfile.mkdtemp())
    assert "palace" in cfg.palace_path
    assert cfg.collection_name == "signal_drawers"


def test_config_from_file():
    tmpdir = tempfile.mkdtemp()
    with open(os.path.join(tmpdir, "config.json"), "w") as f:
        json.dump({"palace_path": "/custom/palace"}, f)
    cfg = SignalConfig(config_dir=tmpdir)
    assert cfg.palace_path == "/custom/palace"


def test_env_override():
    os.environ["MEMPALACE_PALACE_PATH"] = "/env/palace"
    cfg = SignalConfig(config_dir=tempfile.mkdtemp())
    assert cfg.palace_path == "/env/palace"
    del os.environ["MEMPALACE_PALACE_PATH"]


def test_init():
    tmpdir = tempfile.mkdtemp()
    cfg = SignalConfig(config_dir=tmpdir)
    cfg.init()
    assert os.path.exists(os.path.join(tmpdir, "config.json"))
