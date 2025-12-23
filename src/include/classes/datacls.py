from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DownloadTaskStatus(Enum):
    """Status enum for download tasks."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DECRYPTING = "decrypting"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Represents a download task."""
    task_id: str
    file_id: str
    filename: str
    file_path: str
    status: DownloadTaskStatus = DownloadTaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    current_bytes: int = 0
    total_bytes: int = 0
    error: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    stage: int = 0  # 0: downloading, 1: decrypting, 2: cleaning, 3: verifying


@dataclass
class User:
    username: str
    nickname: str
    created_at: float  # <- created_time
    last_login: float
    permissions: list[str]
    groups: list[str]