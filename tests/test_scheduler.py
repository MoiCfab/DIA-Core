# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from dia_core.orchestrator.scheduler import SchedulerConfig, SystemQuotas, run_batch


def _worker(symbol: str) -> None:
    # travail CPU minimal
    sum(i * i for i in range(1000))


def test_run_batch_sequential() -> None:
    cfg = SchedulerConfig(max_workers=1, quotas=SystemQuotas(max_cpu_pct=100.0, max_ram_pct=100.0))
    syms = ["BTC/EUR", "ETH/EUR"]
    out = run_batch(syms, worker=_worker, cfg=cfg)
    assert len(out) == len(syms)
    assert all(r.ok for r in out)


def test_run_batch_parallel() -> None:
    cfg = SchedulerConfig(max_workers=2, quotas=SystemQuotas(max_cpu_pct=100.0, max_ram_pct=100.0))
    syms = ["BTC/EUR", "ETH/EUR", "SOL/EUR"]
    out = run_batch(syms, worker=_worker, cfg=cfg)
    assert len(out) == len(syms)
    assert any(r.attempts == 1 for r in out)
