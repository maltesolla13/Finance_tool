from dataclasses import dataclass
from typing import Callable, Optional, Dict


@dataclass(frozen=True)
class JobDef:
    name: str
    fn: Callable[[str | None], object]
    cron: Optional[str] = None      # z.B. "30 23 * * *"
    description: str = ""


_REG: Dict[str, JobDef] = {}


def register(job: JobDef):
    _REG[job.name] = job


def all_jobs() -> Dict[str, JobDef]:
    return dict(_REG)
