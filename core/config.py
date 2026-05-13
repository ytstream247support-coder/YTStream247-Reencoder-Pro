import json
import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.constants import FFMPEG_TIMEOUT, FFPROBE_TIMEOUT
from helpers import resource_path

GPU_PROBE_CACHE_TTL_SEC = 45.0
WINDOWS_GPU_QUERY_TIMEOUT_SEC = 3
MACOS_GPU_QUERY_TIMEOUT_SEC = 5

ENCODER_DISPLAY_NAMES: Dict[str, str] = {
    "h264_nvenc": "NVIDIA NVENC",
    "h264_amf": "AMD AMF",
    "h264_qsv": "Intel Quick Sync",
    "h264_videotoolbox": "Apple VideoToolbox",
}


@dataclass(frozen=True)
class GPUCapability:
    available: bool
    encoder: Optional[str]
    display_name: str
    vendor_hint: Optional[str]
    hardware_summary: Optional[str]
    reason: Optional[str]
    checked_at: float

# Helper to get subprocess creation flags (hide console window on Windows)
def get_subprocess_flags():
    """Get subprocess creation flags to hide console window on Windows."""
    if platform.system() == "Windows":
        return subprocess.CREATE_NO_WINDOW
    return 0

FFMPEG_BIN = shutil.which("ffmpeg")
FFPROBE_BIN = shutil.which("ffprobe")

YT_DEFAULT_KEY_S = 2  # Keyframe interval in seconds
YT_DEFAULT_BITRATE_KBPS = 6000
YT_DEFAULT_MIN_BITRATE_KBPS = 6000  # Minimum bitrate for output
YT_MIN_AUDIO_KBPS = 128  # Minimum audio bitrate for YouTube Live streaming
YT_MAX_AUDIO_KBPS = 256  # Maximum recommended audio bitrate for YouTube
YT_DEFAULT_AUDIO_SAMPLE_RATE = 48000  # Recommended sample rate for YouTube Live (48kHz)
YT_DEFAULT_PRESET = "medium"  # Changed from "veryfast" for better quality
YT_DEFAULT_PROFILE = "high"
YT_DEFAULT_LEVEL = "4.1"

def _platform_ffmpeg_binary_names() -> List[Tuple[str, str]]:
    """
    Return ordered FFmpeg/FFprobe filename candidates for the current platform.
    """
    system = platform.system()
    if system == "Windows":
        return [("ffmpeg.exe", "ffprobe.exe")]

    if system == "Darwin":
        machine = platform.machine().lower()
        if machine in {"arm64", "aarch64"}:
            return [
                ("ffmpeg-arm64", "ffprobe-arm64"),
                ("ffmpeg", "ffprobe"),
            ]
        return [
            ("ffmpeg-x86_64", "ffprobe-x86_64"),
            ("ffmpeg", "ffprobe"),
        ]

    return [("ffmpeg", "ffprobe")]

def get_bundled_ffmpeg_path() -> Optional[Tuple[Path, Path]]:
    """
    Check for bundled FFmpeg executables in ffmpeg-apps/ directory.
    
    Checks in order:
    1. Directory where executable is located (for installed apps)
    2. Resource path (for PyInstaller temp folder or development)
    
    Returns:
        Tuple of (ffmpeg_path, ffprobe_path) if found, None otherwise
    """
    import sys
    
    system = platform.system()
    
    # First, check directory where executable is located (for installed apps)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        if hasattr(sys, '_MEIPASS'):
            # Onefile mode - check executable's directory
            exe_dir = Path(sys.executable).parent
        else:
            # Onedir mode - executable is in the app directory
            exe_dir = Path(sys.executable).parent
    else:
        # Running from source - check current working directory
        exe_dir = Path.cwd()
    
    candidate_names = _platform_ffmpeg_binary_names()

    # Check in executable's directory first
    for ffmpeg_name, ffprobe_name in candidate_names:
        ffmpeg = exe_dir / "ffmpeg-apps" / ffmpeg_name
        ffprobe = exe_dir / "ffmpeg-apps" / ffprobe_name
        if ffmpeg.exists() and ffprobe.exists():
            return (ffmpeg, ffprobe)

    # Fallback: check resource path (for development or if in different location)
    base = resource_path("")
    for ffmpeg_name, ffprobe_name in candidate_names:
        ffmpeg = base / "ffmpeg-apps" / ffmpeg_name
        ffprobe = base / "ffmpeg-apps" / ffprobe_name
        if ffmpeg.exists() and ffprobe.exists():
            return (ffmpeg, ffprobe)

    return None


# Priority order: bundled → environment variables → system PATH
bundled = get_bundled_ffmpeg_path()
if bundled:
    FFMPEG_BIN = str(bundled[0])
    FFPROBE_BIN = str(bundled[1])
else:
    # Fall back to environment variables
    FFMPEG_BIN = os.environ.get("FFMPEG_BIN", FFMPEG_BIN)
    FFPROBE_BIN = os.environ.get("FFPROBE_BIN", FFPROBE_BIN)

if not FFMPEG_BIN:
    print("Warning: ffmpeg not found in PATH. Please install ffmpeg or set FFMPEG_BIN env var.")


_gpu_capability_cache: Optional[GPUCapability] = None
_gpu_capability_cache_ts: float = 0.0


def validate_ffmpeg() -> Tuple[bool, Optional[str]]:
    """
    Validate that FFmpeg and FFprobe are available and working.
    Returns (is_valid, error_message).
    If is_valid is False, error_message contains the reason.
    """
    if not FFMPEG_BIN:
        return (False, "FFmpeg not found in PATH. Please install FFmpeg or set FFMPEG_BIN environment variable.")
    
    if not FFPROBE_BIN:
        return (False, "FFprobe not found in PATH. Please install FFmpeg or set FFPROBE_BIN environment variable.")
    
    # Test FFmpeg by running version check
    try:
        subprocess.run(
            [FFMPEG_BIN, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=FFMPEG_TIMEOUT,
            creationflags=get_subprocess_flags()
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return (False, f"FFmpeg found but cannot be executed: {e}")
    except Exception as e:
        return (False, f"Error testing FFmpeg: {e}")
    
    # Test FFprobe by running version check
    try:
        subprocess.run(
            [FFPROBE_BIN, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=FFPROBE_TIMEOUT,
            creationflags=get_subprocess_flags()
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return (False, f"FFprobe found but cannot be executed: {e}")
    except Exception as e:
        return (False, f"Error testing FFprobe: {e}")
    
    return (True, None)


def macos_supports_vt_cbr() -> bool:
    """
    The h264_videotoolbox `-constant_bit_rate` option requires macOS 13 (Ventura)
    or newer. Returns False on Windows/Linux and on older macOS versions.
    """
    if platform.system() != "Darwin":
        return False
    try:
        version_str = platform.mac_ver()[0]
        if not version_str:
            return False
        major = int(version_str.split(".")[0])
        return major >= 13
    except (ValueError, AttributeError, IndexError):
        return False


def _normalize_vendor_hint(value: str) -> Optional[str]:
    low = value.lower()
    if "apple" in low:
        return "apple"
    if "nvidia" in low or "geforce" in low or "quadro" in low:
        return "nvidia"
    if "amd" in low or "radeon" in low:
        return "amd"
    if "intel" in low:
        return "intel"
    return None


def _detect_windows_gpu_hardware() -> Tuple[Optional[str], Optional[str]]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,DriverVersion | ConvertTo-Json -Compress"
        ),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=WINDOWS_GPU_QUERY_TIMEOUT_SEC,
            creationflags=get_subprocess_flags(),
        )
    except Exception:
        return None, None

    if result.returncode != 0 or not result.stdout.strip():
        return None, None

    try:
        parsed = json.loads(result.stdout.strip())
    except Exception:
        return None, None

    rows: List[dict]
    if isinstance(parsed, list):
        rows = [row for row in parsed if isinstance(row, dict)]
    elif isinstance(parsed, dict):
        rows = [parsed]
    else:
        rows = []

    if not rows:
        return None, None

    names: List[str] = []
    all_vendors: List[Optional[str]] = []
    for row in rows:
        name = str(row.get("Name") or "").strip()
        if not name:
            continue
        names.append(name)
        all_vendors.append(_normalize_vendor_hint(name))

    if not names:
        return None, None

    # Prefer discrete GPU vendors (nvidia/amd) over Intel integrated graphics
    preferred_order = ["nvidia", "amd", "intel", "apple"]
    vendor_hint: Optional[str] = None
    for preferred in preferred_order:
        if preferred in all_vendors:
            vendor_hint = preferred
            break
    if vendor_hint is None and all_vendors:
        vendor_hint = all_vendors[0]

    return vendor_hint, ", ".join(names[:3])


def _detect_macos_gpu_hardware() -> Tuple[Optional[str], Optional[str]]:
    cmd = ["system_profiler", "SPDisplaysDataType"]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=MACOS_GPU_QUERY_TIMEOUT_SEC,
            creationflags=get_subprocess_flags(),
        )
    except Exception:
        return None, None

    if result.returncode != 0:
        return None, None

    names: List[str] = []
    vendor_hint: Optional[str] = None
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("chipset model:"):
            _, value = line.split(":", 1)
            name = value.strip()
            if not name:
                continue
            names.append(name)
            if vendor_hint is None:
                vendor_hint = _normalize_vendor_hint(name)
        elif line.lower().startswith("model:"):
            _, value = line.split(":", 1)
            name = value.strip()
            if not name:
                continue
            names.append(name)
            if vendor_hint is None:
                vendor_hint = _normalize_vendor_hint(name)

    if not names:
        return vendor_hint, None
    return vendor_hint, ", ".join(names[:3])


def _detect_gpu_hardware_hint() -> Tuple[Optional[str], Optional[str]]:
    system_name = platform.system()
    if system_name == "Windows":
        return _detect_windows_gpu_hardware()
    if system_name == "Darwin":
        return _detect_macos_gpu_hardware()
    return None, None


def _candidate_encoders_for_vendor(
    vendor_hint: Optional[str], system_name: str
) -> List[Tuple[str, str]]:
    common_candidates: List[Tuple[str, str]] = [
        ("h264_nvenc", ENCODER_DISPLAY_NAMES["h264_nvenc"]),
        ("h264_amf", ENCODER_DISPLAY_NAMES["h264_amf"]),
        ("h264_qsv", ENCODER_DISPLAY_NAMES["h264_qsv"]),
    ]

    if system_name == "Darwin":
        darwin_candidates: List[Tuple[str, str]] = [
            ("h264_videotoolbox", ENCODER_DISPLAY_NAMES["h264_videotoolbox"]),
            ("h264_qsv", ENCODER_DISPLAY_NAMES["h264_qsv"]),
            ("h264_amf", ENCODER_DISPLAY_NAMES["h264_amf"]),
            ("h264_nvenc", ENCODER_DISPLAY_NAMES["h264_nvenc"]),
        ]
        return darwin_candidates

    if vendor_hint == "nvidia":
        return [common_candidates[0], common_candidates[1], common_candidates[2]]
    if vendor_hint == "amd":
        return [common_candidates[1], common_candidates[0], common_candidates[2]]
    if vendor_hint == "intel":
        return [common_candidates[2], common_candidates[0], common_candidates[1]]
    return common_candidates


def _ffmpeg_list_encoders() -> Optional[str]:
    if not FFMPEG_BIN:
        return None
    try:
        result = subprocess.run(
            [FFMPEG_BIN, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=FFMPEG_TIMEOUT,
            creationflags=get_subprocess_flags(),
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout




def get_gpu_capability(force_refresh: bool = False) -> GPUCapability:
    global _gpu_capability_cache
    global _gpu_capability_cache_ts

    now = time.monotonic()
    if (
        not force_refresh
        and _gpu_capability_cache is not None
        and (now - _gpu_capability_cache_ts) < GPU_PROBE_CACHE_TTL_SEC
    ):
        return _gpu_capability_cache

    checked_at = time.time()
    if not FFMPEG_BIN:
        capability = GPUCapability(
            available=False,
            encoder=None,
            display_name="CPU",
            vendor_hint=None,
            hardware_summary=None,
            reason="FFmpeg is not available",
            checked_at=checked_at,
        )
        _gpu_capability_cache = capability
        _gpu_capability_cache_ts = now
        return capability

    vendor_hint, hardware_summary = _detect_gpu_hardware_hint()
    candidates = _candidate_encoders_for_vendor(vendor_hint, platform.system())
    encoders_text = _ffmpeg_list_encoders()
    missing: List[str] = []

    for encoder_name, display_name in candidates:
        if not encoders_text or encoder_name not in encoders_text:
            missing.append(display_name)
            continue
        # Encoder is present in the FFmpeg build — trust it and let runtime
        # fallback handle any actual failure during encoding.
        capability = GPUCapability(
            available=True,
            encoder=encoder_name,
            display_name=display_name,
            vendor_hint=vendor_hint,
            hardware_summary=hardware_summary,
            reason=None,
            checked_at=checked_at,
        )
        _gpu_capability_cache = capability
        _gpu_capability_cache_ts = now
        return capability

    if not hardware_summary:
        reason = "No compatible GPU encoder detected"
    else:
        reason = "GPU detected but no supported encoder in FFmpeg build"
        if missing:
            reason += f" ({', '.join(missing[:2])} not compiled in)"

    capability = GPUCapability(
        available=False,
        encoder=None,
        display_name="CPU",
        vendor_hint=vendor_hint,
        hardware_summary=hardware_summary,
        reason=reason,
        checked_at=checked_at,
    )
    _gpu_capability_cache = capability
    _gpu_capability_cache_ts = now
    return capability


def detect_available_gpu_encoder(force_refresh: bool = False) -> Optional[Tuple[str, str]]:
    """
    Backward-compatible helper for legacy call sites.
    Returns (encoder_name, display_name) when GPU encoding is usable.
    """
    capability = get_gpu_capability(force_refresh=force_refresh)
    if capability.available and capability.encoder:
        return capability.encoder, capability.display_name
    return None


def is_valid_video_file(path: Path) -> Tuple[bool, Optional[str]]:

    if not path.exists():
        return (False, "File does not exist")
    
    if not path.is_file():
        return (False, "Path is not a file")
    
    if not FFPROBE_BIN:
        # If ffprobe not available, just check file extension
        video_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.flv', '.wmv', '.webm', '.m4v'}
        if path.suffix.lower() not in video_extensions:
            return (False, "File extension not recognized as video")
        return (True, None)
    
    try:
        # Use ffprobe to check if file has video stream
        result = subprocess.run(
            [FFPROBE_BIN, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=FFPROBE_TIMEOUT,
            text=True,
            creationflags=get_subprocess_flags()
        )
        
        if result.returncode != 0:
            return (False, "File is not a valid video file or cannot be read")
        
        if "video" not in result.stdout.lower():
            return (False, "File does not contain a video stream")
        
        return (True, None)
    except subprocess.TimeoutExpired:
        return (False, "File validation timed out")
    except Exception as e:
        return (False, f"Error validating file: {e}")