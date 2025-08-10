# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : orchestrator/scheduler.py

Description :
    Orchestrateur multi-actifs léger. Planifie l'exécution séquentielle ou
    concurrente de jobs (une paire = un job), avec quotas CPU/RAM et
    kill-switch de sécurité. Conçu pour fonctionner en local (Raspberry/mini-PC),
    sans dépendance réseau hors API exchange déjà gérée par KrakenClient.

    Le scheduler n'exécute pas d'IO réseau lui-même : il appelle des
    *callables* que l'application lui fournit (ex. une fonction run_bot(symbol)).

Caractéristiques :
    Limitation du parallélisme (max_workers)
    Contrôles périodiques CPU/RAM (psutil facultatif)
    Kill-switch si seuils dépassés (lève SchedulerOverloadError)
    Politique de retries simple avec backoff

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from time import monotonic, sleep

try:  # psutil est optionnel
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - absent en CI
    psutil = None


class SchedulerOverloadError(RuntimeError):
    """Erreur levée si les quotas système sont dépassés."""


@dataclass(frozen=True)
class SystemQuotas:
    max_cpu_pct: float = 85.0
    max_ram_pct: float = 85.0
    check_interval_s: float = 2.0


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 2
    base_backoff_s: float = 0.5  # backoff exponentiel


@dataclass(frozen=True)
class JobResult:
    symbol: str
    ok: bool
    attempts: int
    duration_s: float
    error: str | None


@dataclass(frozen=True)
class SchedulerConfig:
    max_workers: int = 2
    quotas: SystemQuotas = field(default_factory=SystemQuotas)
    retry: RetryPolicy = field(default_factory=RetryPolicy)


def _sys_ok(quotas: SystemQuotas) -> bool:
    if psutil is None:
        return True
    cpu: float = float(psutil.cpu_percent(interval=None))
    ram: float = float(psutil.virtual_memory().percent)
    return (cpu <= quotas.max_cpu_pct) and (ram <= quotas.max_ram_pct)


def _backoff_sleep(base: float, n: int) -> None:
    sleep(base * (2 ** max(0, n)))


def _run_one(
    symbol: str,
    fn: Callable[[str], None],
    retry: RetryPolicy,
    quotas: SystemQuotas,
) -> JobResult:
    start = monotonic()
    err: str | None = None
    attempts = 0
    for k in range(retry.max_retries + 1):
        attempts = k + 1
        if not _sys_ok(quotas):
            raise SchedulerOverloadError("System quotas exceeded")
        try:
            fn(symbol)
            return JobResult(symbol, True, attempts, monotonic() - start, None)
        except SchedulerOverloadError:
            raise
        except Exception as e:  # noqa: BLE001  # pragma: no cover - chemins d'exception
            err = f"{type(e).__name__}: {e}"
            if k < retry.max_retries:
                _backoff_sleep(retry.base_backoff_s, k)
                continue
            break
    return JobResult(symbol, False, attempts, monotonic() - start, err)


def run_batch(
    symbols: Sequence[str],
    *,
    worker: Callable[[str], None],
    cfg: SchedulerConfig | None = None,
) -> list[JobResult]:
    """Exécute un lot de jobs.

    Args:
        symbols: liste des paires à traiter
        worker: fonction synchrone prenant un symbole et ne renvoyant rien
        cfg: configuration du scheduler

    Returns:
        Liste de JobResult, dans l'ordre d'achèvement des jobs.
    """
    cfg = cfg or SchedulerConfig()

    if cfg.max_workers <= 1:
        out: list[JobResult] = []
        for s in symbols:
            out.append(_run_one(s, worker, cfg.retry, cfg.quotas))
        return out

    out2: list[JobResult] = []
    with ThreadPoolExecutor(max_workers=cfg.max_workers) as ex:
        futs = {ex.submit(_run_one, s, worker, cfg.retry, cfg.quotas): s for s in symbols}
        for fut in as_completed(futs):
            out2.append(fut.result())
    return out2
