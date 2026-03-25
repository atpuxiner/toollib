"""
@author axiner
@version v1.0.0
@created 2026/3/24 10:00
@abstract 任务调度器
@description
@history
"""

import asyncio
import importlib
import logging
import signal
import uuid
from collections.abc import Callable
from functools import wraps
from hashlib import sha1
from pkgutil import walk_packages
from typing import Any, Literal

from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

logger = logging.getLogger(__name__)

__all__ = ["SchedulerManager"]


class SchedulerManager:
    """
    Scheduler Manager

    e.g.::

        your_project/
        ├─ app/
        │  ├─ __init__.py
        │  ├─ scheduler/
        │  │  ├─ __init__.py
        │  │  └─ jobs
        │  │     ├─ __init__.py
        │  │     ├─ j1.py
        │  │     └─ ...
        │  └─ ...
        └─ main.py

        # app/scheduler/__init__.py
        from toollib.apsched import SchedulerManager

        sched = SchedulerManager(
            mode="blocking",
            autodiscover=["app.scheduler.jobs"],
        )

        # app/scheduler/jobs/j1.py
        from app.scheduler import sched

        @sched.job(trigger="interval", seconds=10)
        def job1():
            print("job1 executed")

        # main.py
        import asyncio

        from toollib.log import init_logger

        from app.scheduler import sched

        logger = init_logger()

        async def main():
            await sched.start_async_forever()


        if __name__ == "__main__":
            asyncio.run(main())

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
        self,
        mode: Literal["blocking", "asyncio"] = "blocking",
        timezone: str = "Asia/Shanghai",
        jobstores: dict[str, Any] | None = None,
        executors: dict[str, Any] | None = None,
        job_defaults: dict[str, Any] | None = None,
        include: list[str] | None = None,
        autodiscover: list[str] | None = None,
        keep_next_run_time: bool = False,
        id_strategy: Literal["sha1", "name", "uuid"] = "sha1",
        **kwargs: Any,
    ):
        self.mode = mode
        self.timezone = timezone
        self.include_modules = include or []
        self.autodiscover_packages = autodiscover or []
        self.keep_next_run_time = keep_next_run_time
        self.id_strategy = id_strategy
        self._bootstrapped = False
        self._job_registry = []
        self._job_ids = set()
        self._valid_job_ids = set()

        self.scheduler: BlockingScheduler | AsyncIOScheduler
        if mode == "blocking" and jobstores is None:
            jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///.apscheduler_jobs.db")}
        if job_defaults is None:
            job_defaults = {
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,
            }
        if mode == "blocking":
            self.scheduler = BlockingScheduler(
                timezone=timezone,
                jobstores=jobstores,
                executors=executors or {},
                job_defaults=job_defaults,
                **kwargs,
            )
        else:
            self.scheduler = AsyncIOScheduler(
                timezone=timezone,
                jobstores=jobstores or {},
                executors=executors or {},
                job_defaults=job_defaults or {},
                **kwargs,
            )

    def job(
        self,
        func: Callable | None = None,
        trigger: Literal["interval", "cron", "date"] = "interval",
        *,
        jid: str | None = None,
        name: str | None = None,
        active: bool = True,
        **trigger_kwargs: Any,
    ) -> Callable[[Callable], Callable]:
        """Decorator to register a job with the scheduler"""
        if func is not None and callable(func):
            return self.job(trigger=trigger, jid=jid, name=name, active=active, **trigger_kwargs)(func)

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any):
                return func(*args, **kwargs)

            job_id = jid or self._gen_job_id(func, id_strategy=self.id_strategy)
            if job_id not in self._job_ids:
                self._job_ids.add(job_id)
                self._job_registry.append(
                    {
                        "func": func,
                        "trigger": trigger,
                        "id": job_id,
                        "name": name or f"{func.__module__}.{func.__name__}",
                        "active": active,
                        **trigger_kwargs,
                    }
                )
            return wrapper

        return decorator

    def add_job(
        self,
        func: Callable,
        trigger: Literal["interval", "cron", "date"] = "interval",
        *,
        jid: str | None = None,
        name: str | None = None,
        keep_next_run_time: bool | None = None,
        **trigger_kwargs: Any,
    ):
        """Add a job with the scheduler"""
        keep_next_run_time = self.keep_next_run_time if keep_next_run_time is None else keep_next_run_time
        jid = jid or self._gen_job_id(func, id_strategy=self.id_strategy)
        name = name or f"{func.__module__}.{func.__name__}"

        existing_job = self.scheduler.get_job(jid)

        if existing_job:
            if keep_next_run_time:
                next_run_time = existing_job.next_run_time
                self.scheduler.remove_job(jid)
                self.scheduler.add_job(
                    func=func,
                    trigger=trigger,
                    id=jid,
                    name=name,
                    next_run_time=next_run_time,
                    replace_existing=False,
                    **trigger_kwargs,
                )
            else:
                self.scheduler.add_job(
                    func=func,
                    trigger=trigger,
                    id=jid,
                    name=name,
                    replace_existing=True,
                    **trigger_kwargs,
                )
        else:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=jid,
                name=name,
                replace_existing=True,
                **trigger_kwargs,
            )

    @staticmethod
    def _gen_job_id(
        func: Callable,
        id_strategy: Literal["sha1", "name", "uuid"] = "sha1",
    ) -> str:
        key = f"{func.__module__}.{func.__name__}"
        if id_strategy == "sha1":
            return sha1(key.encode("utf-8")).hexdigest()
        elif id_strategy == "name":
            return key
        else:
            return uuid.uuid4().hex

    def _load_includes(self):
        for module_path in self.include_modules:
            before_job_count = len(self._job_registry)
            try:
                importlib.import_module(module_path)
            except Exception as e:
                raise RuntimeError(f"Failed to import module {module_path}: {e}") from None
            after_job_count = len(self._job_registry)
            if after_job_count == before_job_count:
                logger.warning(
                    f"Module {module_path} imported successfully but no jobs were registered.\n"
                    f"Possible reasons: circular import, decorator not executed, or no jobs defined.\n"
                )

    def _autodiscover(self):
        for package_name in self.autodiscover_packages:
            try:
                pkg = importlib.import_module(package_name)
            except Exception as e:
                raise RuntimeError(f"Failed to import package {package_name}: {e}") from None

            if not hasattr(pkg, "__path__"):
                continue

            for module_info in walk_packages(pkg.__path__, prefix=f"{package_name}."):
                modname = module_info.name.split(".")[-1]
                if module_info.ispkg or modname.startswith("_"):
                    continue

                before_job_count = len(self._job_registry)
                try:
                    importlib.import_module(module_info.name)
                except Exception as e:
                    raise RuntimeError(f"Failed to import module {module_info.name}: {e}") from None
                after_job_count = len(self._job_registry)
                if after_job_count == before_job_count:
                    logger.warning(
                        f"Module {modname} imported successfully but no jobs were registered.\n"
                        f"Possible reasons: circular import, decorator not executed, or no jobs defined.\n"
                    )

    def _register_jobs(self, keep_next_run_time: bool | None = None):
        keep_next_run_time = self.keep_next_run_time if keep_next_run_time is None else keep_next_run_time

        self._valid_job_ids.clear()
        for job in self._job_registry:
            job_id = job["id"]
            func = job["func"]
            trigger = job["trigger"]
            active = job.get("active", True)
            trigger_kwargs = {k: v for k, v in job.items() if k not in ("func", "trigger", "active")}

            if not active:
                continue

            self._valid_job_ids.add(job_id)

            existing_job = self.scheduler.get_job(job_id)
            try:
                if existing_job and keep_next_run_time:
                    next_run_time = existing_job.next_run_time
                    self.scheduler.add_job(
                        func=func, trigger=trigger, next_run_time=next_run_time, replace_existing=True, **trigger_kwargs
                    )
                else:
                    self.scheduler.add_job(func=func, trigger=trigger, replace_existing=True, **trigger_kwargs)
            except Exception as e:
                logger.error(f"Failed to register job {job_id}: {e}")

        lock = getattr(self.scheduler, "_jobstores_lock", None)
        jobstores = getattr(self.scheduler, "_jobstores", {})

        def _cleanup():
            for store_alias, job_store in jobstores.items():
                try:
                    for job in job_store.get_all_jobs():
                        if job.id not in self._valid_job_ids:
                            try:
                                job_store.remove_job(job.id)
                                logger.info(f"Cleaned up job: {job.id} (inactive or missing) [{store_alias}]")
                            except JobLookupError:
                                logger.debug(f"Job {job.id} already removed")
                            except Exception as e:
                                logger.error(f"Remove job {job.id} error: {e}")
                except Exception as e:
                    logger.error(f"Clean jobs from jobstore {store_alias} error: {e}")

        if lock:
            with lock:
                _cleanup()
        else:
            _cleanup()

    def _bootstrap(self, keep_next_run_time: bool | None = None):
        logger.info(f"Scheduler bootstrapping in {self.mode} mode")
        if self._bootstrapped:
            return
        self._bootstrapped = True

        self._load_includes()
        self._autodiscover()
        self._register_jobs(keep_next_run_time=keep_next_run_time)

    def _register_shutdown(self):
        def handle_shutdown(signum, frame):
            logger.info("Received shutdown signal, stopping scheduler gracefully...")
            self.scheduler.shutdown()

        try:
            signal.signal(signal.SIGINT, handle_shutdown)
            signal.signal(signal.SIGTERM, handle_shutdown)
        except ValueError:
            pass

    def start(self, keep_next_run_time: bool | None = None):
        """Sync start (for blocking scheduler)"""
        if self.mode != "blocking":
            raise RuntimeError("Use start_async() for asyncio scheduler")

        self._register_shutdown()
        self._bootstrap(keep_next_run_time=keep_next_run_time)

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()

    def start_async(self, keep_next_run_time: bool | None = None):
        """Async run (for embedded async app, e.g. FastAPI)"""
        if self.mode != "asyncio":
            raise RuntimeError("Use start() for blocking scheduler")

        self._bootstrap(keep_next_run_time=keep_next_run_time)
        self.scheduler.start()

    async def start_async_forever(self, keep_next_run_time: bool | None = None):
        """Async run forever (for standalone async app)"""
        if self.mode != "asyncio":
            raise RuntimeError("Use start() for blocking scheduler")

        self._register_shutdown()
        self._bootstrap(keep_next_run_time=keep_next_run_time)
        self.scheduler.start()

        while True:
            await asyncio.sleep(3600)

    def stop(self):
        """Stop scheduler manually"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped successfully")

    def clear_jobs(self):
        """Clear all jobs (use with caution)"""
        self.scheduler.remove_all_jobs()
        self._job_ids.clear()
        self._job_registry.clear()
        self._valid_job_ids.clear()
        logger.warning("All jobs have been cleared")

    def get_jobs_info(self) -> list[dict[str, Any]]:
        """Get all jobs info (for monitoring/management)"""
        jobs = self.scheduler.get_jobs()
        jobs_info = []
        for job in jobs:
            trigger_type = "unknown"
            trigger_rule = {}
            trigger_cls = job.trigger.__class__.__name__

            if "IntervalTrigger" in trigger_cls:
                trigger_type = "interval"
                trig = job.trigger
                trigger_rule = {
                    "seconds": trig.interval.total_seconds(),
                    "start_date": trig.start_date,
                    "end_date": trig.end_date,
                }
            elif "CronTrigger" in trigger_cls:
                trigger_type = "cron"
                trig = job.trigger
                trigger_rule = {
                    "second": trig.fields[0].expressions,
                    "minute": trig.fields[1].expressions,
                    "hour": trig.fields[2].expressions,
                    "day": trig.fields[3].expressions,
                    "month": trig.fields[4].expressions,
                    "day_of_week": trig.fields[5].expressions,
                    "start_date": trig.start_date,
                    "end_date": trig.end_date,
                }
            elif "DateTrigger" in trigger_cls:
                trigger_type = "date"
                trig = job.trigger
                trigger_rule = {"run_date": trig.run_date}

            jobs_info.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                    "trigger": trigger_type,
                    "trigger_rule": trigger_rule,
                }
            )
        return jobs_info
