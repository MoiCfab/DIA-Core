# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import pytest
from dia_core.alerts.telegram_alerts import TgConfig, build_payload, send


def test_build_payload_and_dry_send() -> None:
    cfg = TgConfig(token="T", chat_id="C", dry_run=True)  # noqa: S106
    url, body = build_payload(cfg, "hello")
    assert "botT" in url
    assert b'"chat_id": "C"' in body
    assert send(cfg, "hi") is True


def test_live_send_requires_transport() -> None:
    cfg = TgConfig(token="T", chat_id="C", dry_run=False)  # noqa: S106
    with pytest.raises(RuntimeError):
        send(cfg, "x")
