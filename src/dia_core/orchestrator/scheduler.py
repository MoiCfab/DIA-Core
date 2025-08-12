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
    """Seuils CPU/RAM/IO pour l`ordonnancement."""

    max_cpu_pct: float = 85.0
    max_ram_pct: float = 85.0
    check_interval_s: float = 2.0


@dataclass(frozen=True)
class RetryPolicy:
    """Politique de retry exponentiel."""

    max_retries: int = 2
    base_backoff_s: float = 0.5  # backoff exponentiel


@dataclass(frozen=True)
class JobResult:
    """Résultat d`un job (succès, tentatives, durée)."""

    symbol: str
    ok: bool
    attempts: int
    duration_s: float
    error: str | None


@dataclass(frozen=True)
class SchedulerConfig:
    """Paramètres de scheduling et backoff."""

    max_workers: int = 2
    quotas: SystemQuotas = field(default_factory=SystemQuotas)
    retry: RetryPolicy = field(default_factory=RetryPolicy)


def _sys_ok(quotas: SystemQuotas) -> bool:
    """

    Args:
      quotas: SystemQuotas:

    Returns:

    """
    if psutil is None:
        return True
    cpu: float = float(psutil.cpu_percent(interval=None))
    ram: float = float(psutil.virtual_memory().percent)
    return (cpu <= quotas.max_cpu_pct) and (ram <= quotas.max_ram_pct)


def _backoff_sleep(base: float, n: int) -> None:
    """

    Args:
      base: float:
      n: int:

    Returns:

    """
    sleep(base * (2 ** max(0, n)))


def _run_one(
    symbol: str,
    fn: Callable[[str], None],
    retry: RetryPolicy,
    quotas: SystemQuotas,
) -> JobResult:
    """

    Args:
      symbol: str:
      fn: Callable[[str]:
      None]:
      retry: RetryPolicy:
      quotas: SystemQuotas:

    Returns:

    """
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
        except (OSError, TimeoutError, ValueError) as e:
            err = f"{type(e).__name__}: {e}"
            if k < retry.max_retries:
                _backoff_sleep(retry.base_backoff_s, k)
                continue
            break
    return JobResult(symbol, False, attempts, monotonic() - start, err)


def _run_batch_sequential(
    symbols: Sequence[str], worker: Callable[[str], None], cfg: SchedulerConfig
) -> list[JobResult]:
    """Run a batch of jobs sequentially.

    This helper encapsulates the sequential execution path. Each symbol
    is processed one after another without any concurrency.

    Args:
        symbols: Collection of trading symbols to process.
        worker: Function taking a symbol and performing the job.
        cfg: Scheduler configuration providing retry and quota settings.

    Returns:
        A list of :class:`JobResult` objects corresponding to each job.
    """
    results: list[JobResult] = []
    for sym in symbols:
        results.append(_run_one(sym, worker, cfg.retry, cfg.quotas))
    return results


def _run_batch_parallel(
    symbols: Sequence[str], worker: Callable[[str], None], cfg: SchedulerConfig
) -> list[JobResult]:
    """Run a batch of jobs in parallel using a thread pool.

    Args:
        symbols: Collection of trading symbols to process.
        worker: Function taking a symbol and performing the job.
        cfg: Scheduler configuration providing retry and quota settings.

    Returns:
        A list of :class:`JobResult` objects corresponding to each job
        in the order in which they completed.
    """
    results: list[JobResult] = []
    with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
        futures = {
            executor.submit(_run_one, sym, worker, cfg.retry, cfg.quotas): sym for sym in symbols
        }
        for future in as_completed(futures):
            results.append(future.result())
    return results


def run_batch(
    symbols: Sequence[str],
    *,
    worker: Callable[[str], None],
    cfg: SchedulerConfig | None = None,
) -> list[JobResult]:
    """Execute a batch of jobs either sequentially or concurrently.

    A thin wrapper around :func:`_run_batch_sequential` and
    :func:`_run_batch_parallel` that chooses the appropriate execution
    strategy based on ``cfg.max_workers``.

    Args:
        symbols: List of pairs to process.
        worker: Synchronous function taking a symbol and returning
            nothing. The scheduler wraps calls to this function with
            retry and quota checking.
        cfg: Scheduler configuration. When ``None`` a default
            configuration is used.

    Returns:
        A list of :class:`JobResult` instances. Order of the results
        corresponds to the order in which jobs completed.
    """
    config = cfg or SchedulerConfig()
    if config.max_workers <= 1:
        return _run_batch_sequential(symbols, worker, config)
    return _run_batch_parallel(symbols, worker, config)
