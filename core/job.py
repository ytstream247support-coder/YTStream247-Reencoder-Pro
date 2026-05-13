from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class Job:
    src: Path
    out: Path
    key_s: float
    preset: str
    target_kbps: Optional[int]
    use_gpu: bool  # User preference - will fall back to CPU if GPU not available
    gpu_encoder: Optional[str] = None  # Detected GPU encoder name (h264_nvenc, h264_amf, h264_qsv)
    quality_tier: str = "6k"          # "6k" = 6000 kbps, "10k" = 10000 kbps
    output_resolution: str = "1440p"   # "1080p" or "1440p" — independent of tier
    fps_override: Optional[int] = None  # None=auto-detect from source, int=forced fps
    retry_count: int = field(default=0)  # Number of retry attempts
    max_retries: int = field(default=2)  # Maximum retry attempts
