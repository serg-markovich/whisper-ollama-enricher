import pytest
import src.config as cfg


def test_require_exits_on_missing_key(monkeypatch):
    monkeypatch.delenv("__NO_SUCH_KEY__", raising=False)
    with pytest.raises(SystemExit, match="__NO_SUCH_KEY__"):
        cfg._require("__NO_SUCH_KEY__")
