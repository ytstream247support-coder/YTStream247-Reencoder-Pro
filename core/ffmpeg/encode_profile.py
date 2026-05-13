"""
YouTube delivery profiles: CBR, 2 s GOP.
6k tier:  1920x1080, 30fps.
10k tier: 2560x1440 (upscaled), auto fps — avoids YouTube's aggressive 1080p recompression.
All encode-related literals live here; builder.py only assembles argv lists.
"""

from typing import Optional, Tuple

from core.constants import BUFFER_SIZE_MULTIPLIER

# --- Output geometry (6k / 1080p tier) ---
OUT_WIDTH = 1920
OUT_HEIGHT = 1080
# --- Output geometry (10k / 1440p tier) ---
OUT_WIDTH_10K = 2560
OUT_HEIGHT_10K = 1440
KEYFRAME_INTERVAL_SEC = 2

# --- Legacy defaults (6k tier) kept for backward-compat imports ---
OUT_FPS = 30
GOP_FRAMES = int(OUT_FPS * KEYFRAME_INTERVAL_SEC)

# --- H.264 ---
H264_PROFILE = "high"
H264_LEVEL = "4.1"  # default for 6k/1080p tier
VIDEO_BITRATE_KBPS = 6000  # default for 6k tier


def video_bufsize_kbps() -> int:
    return VIDEO_BITRATE_KBPS * BUFFER_SIZE_MULTIPLIER


# --- Quality tiers ---
QUALITY_TIER_6K = "6k"
QUALITY_TIER_10K = "10k"
QUALITY_TIER_DEFAULT = QUALITY_TIER_6K
QUALITY_TIER_KEYS = (QUALITY_TIER_6K, QUALITY_TIER_10K)

_TIER_PARAMS = {
    QUALITY_TIER_6K:  {"bitrate_kbps": 6000,  "fps": 30},
    QUALITY_TIER_10K: {"bitrate_kbps": 10000, "fps": 60},
}


def normalize_quality_tier(tier: Optional[str]) -> str:
    if tier in QUALITY_TIER_KEYS:
        return str(tier)
    return QUALITY_TIER_DEFAULT


def get_tier_bitrate_kbps(tier: Optional[str]) -> int:
    return _TIER_PARAMS[normalize_quality_tier(tier)]["bitrate_kbps"]


def get_tier_fps(tier: Optional[str]) -> int:
    return _TIER_PARAMS[normalize_quality_tier(tier)]["fps"]


def get_tier_gop_frames(tier: Optional[str]) -> int:
    return int(get_tier_fps(tier) * KEYFRAME_INTERVAL_SEC)


def get_tier_bufsize_kbps(tier: Optional[str]) -> int:
    return get_tier_bitrate_kbps(tier) * BUFFER_SIZE_MULTIPLIER


# --- Output resolution (user-selectable, independent of tier) ---
RESOLUTION_1080P = "1080p"
RESOLUTION_1440P = "1440p"
RESOLUTION_DEFAULT = RESOLUTION_1440P  # 1440p by default — avoids YouTube 1080p recompression
RESOLUTION_KEYS = (RESOLUTION_1080P, RESOLUTION_1440P)

_RESOLUTION_DIMS: dict = {
    RESOLUTION_1080P: (OUT_WIDTH,     OUT_HEIGHT),
    RESOLUTION_1440P: (OUT_WIDTH_10K, OUT_HEIGHT_10K),
}

# H.264 level by (resolution, fps_bucket): 1440p needs level 5.x
_H264_LEVEL_MAP: dict = {
    (RESOLUTION_1080P, 30): "4.1",
    (RESOLUTION_1080P, 60): "4.2",
    (RESOLUTION_1440P, 30): "5.0",
    (RESOLUTION_1440P, 60): "5.1",
}


def normalize_resolution(res: Optional[str]) -> str:
    if res in RESOLUTION_KEYS:
        return str(res)
    return RESOLUTION_DEFAULT


def get_resolution_dims(res: Optional[str]) -> Tuple[int, int]:
    return _RESOLUTION_DIMS[normalize_resolution(res)]


def get_h264_level(res: Optional[str], out_fps: int) -> str:
    """Return correct H.264 level for the given resolution + fps combination."""
    fps_key = 60 if out_fps >= 60 else 30
    return _H264_LEVEL_MAP.get((normalize_resolution(res), fps_key), "4.1")


# --- Demux / mux ---
FFLAGS_IN = "+genpts+discardcorrupt"
MOVFLAGS = "+faststart"

# --- Full pipeline (CPU): high-quality downscale + pad + CFR ---
SCALE_FLAGS = "lanczos+accurate_rnd+full_chroma_int"
PAD_COLOR = "black"


def normalize_probe_fps(fps: float) -> float:
    if fps < 1.0 or fps > 120.0:
        return float(OUT_FPS)
    return fps


STANDARD_FPS_OPTIONS = [30, 60]


def snap_to_standard_fps(fps: float) -> int:
    """Snap a measured source fps to either 30 or 60 (threshold at 45fps)."""
    return 60 if fps >= 45.0 else 30


def vf_branch(width: Optional[int], height: Optional[int], fps: float, out_fps: int = OUT_FPS,
              out_width: int = OUT_WIDTH, out_height: int = OUT_HEIGHT) -> str:
    """
    fast_native30     — source already matches output dims+fps (landscape): yuv420p only.
    fast_native_fps   — source matches output dims, fps conversion needed.
    fast_portrait30   — portrait source matches output dims+fps: yuv420p only.
    fast_portrait_fps — portrait source matches output dims, fps conversion needed.
    full_scale        — resize/pad + fps (any other size or upscale to 1440p).
    """
    fps = normalize_probe_fps(fps)
    fps_lo = out_fps - 0.5
    fps_hi = out_fps + 0.5
    if width is None or height is None:
        return "full_scale"
    if width == out_width and height == out_height:
        if fps_lo <= fps <= fps_hi:
            return "fast_native30"
        return "fast_native_fps"
    if width == out_height and height == out_width:
        if fps_lo <= fps <= fps_hi:
            return "fast_portrait30"
        return "fast_portrait_fps"
    return "full_scale"


def needs_full_scale(width: Optional[int], height: Optional[int], fps: float, out_fps: int = OUT_FPS,
                     out_width: int = OUT_WIDTH, out_height: int = OUT_HEIGHT) -> bool:
    return vf_branch(width, height, fps, out_fps, out_width, out_height) == "full_scale"


def video_filter_graph_cpu(width: Optional[int], height: Optional[int], fps: float, out_fps: int = OUT_FPS,
                            out_width: int = OUT_WIDTH, out_height: int = OUT_HEIGHT) -> str:
    """CPU filter chain for all branches (used when not using CUDA decode+scale hybrid)."""
    fps = normalize_probe_fps(fps)
    b = vf_branch(width, height, fps, out_fps, out_width, out_height)
    if b == "fast_native30":
        return "format=yuv420p"
    if b == "fast_native_fps":
        return f"fps={out_fps},format=yuv420p"
    if b == "fast_portrait30":
        return "format=yuv420p"
    if b == "fast_portrait_fps":
        return f"fps={out_fps},format=yuv420p"
    is_portrait = width is not None and height is not None and height > width
    eff_w = out_height if is_portrait else out_width
    eff_h = out_width if is_portrait else out_height
    return (
        f"scale={eff_w}:{eff_h}:force_original_aspect_ratio=decrease:flags={SCALE_FLAGS},"
        f"pad={eff_w}:{eff_h}:(ow-iw)/2:(oh-ih)/2:color={PAD_COLOR},"
        f"format=yuv420p,fps={out_fps}"
    )


def video_filter_graph_cuda_hybrid(width: Optional[int] = None, height: Optional[int] = None,
                                    out_fps: int = OUT_FPS,
                                    out_width: int = OUT_WIDTH, out_height: int = OUT_HEIGHT) -> str:
    """
    NVDEC + scale on GPU, pad/fps on CPU. Use only with -hwaccel cuda and NVENC output.
    """
    is_portrait = width is not None and height is not None and height > width
    eff_w = out_height if is_portrait else out_width
    eff_h = out_width if is_portrait else out_height
    return (
        f"scale_cuda={eff_w}:{eff_h}:force_original_aspect_ratio=decrease:interp_algo=lanczos,"
        # CUDA hwdownload cannot emit yuv420p directly; download as nv12,
        # then convert after the CPU-side pad/fps filters.
        f"hwdownload,format=nv12,"
        f"pad={eff_w}:{eff_h}:(ow-iw)/2:(oh-ih)/2:color={PAD_COLOR},"
        f"fps={out_fps},format=yuv420p"
    )


# --- Audio ---
AAC_BITRATE_KBPS = 192
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2

# --- NVENC ---
NVENC_PRESET = "p7"
NVENC_TUNE = "hq"
NVENC_RC_LOOKAHEAD = 32
NVENC_AQ_STRENGTH = 8

# --- AMD AMF ---
AMF_QUALITY = "quality"

# --- Intel QSV (preset names from FFmpeg h264_qsv) ---
QSV_PRESET = "slow"

# --- libx264 (CPU) ---
X264_PRESET = "slow"

# --- User-facing speed modes (app-level, FFmpeg-agnostic) ---
ENCODE_MODE_FAST = "fast"
ENCODE_MODE_BALANCED = "balanced"
ENCODE_MODE_MAX_QUALITY = "max_quality"
ENCODE_MODE_DEFAULT = ENCODE_MODE_BALANCED

ENCODE_MODE_KEYS = (
    ENCODE_MODE_FAST,
    ENCODE_MODE_BALANCED,
    ENCODE_MODE_MAX_QUALITY,
)

# Encoder-specific mappings for the 3 speed modes.
# Keep these values centralized so UI uses friendly names while builder resolves
# concrete FFmpeg flags per encoder backend.
_NVENC_PRESET_BY_MODE = {
    ENCODE_MODE_FAST: "p2",
    ENCODE_MODE_BALANCED: "p4",
    ENCODE_MODE_MAX_QUALITY: "p7",
}
_AMF_QUALITY_BY_MODE = {
    ENCODE_MODE_FAST: "speed",
    ENCODE_MODE_BALANCED: "balanced",
    ENCODE_MODE_MAX_QUALITY: "quality",
}
_QSV_PRESET_BY_MODE = {
    ENCODE_MODE_FAST: "veryfast",
    ENCODE_MODE_BALANCED: "medium",
    ENCODE_MODE_MAX_QUALITY: "slow",
}
# (enabled, depth): fast stays realtime with no lookahead; balanced/max_quality use it
_QSV_LOOKAHEAD_BY_MODE = {
    ENCODE_MODE_FAST:        (0,  0),
    ENCODE_MODE_BALANCED:    (1, 20),
    ENCODE_MODE_MAX_QUALITY: (1, 40),
}
_X264_PRESET_BY_MODE = {
    ENCODE_MODE_FAST: "veryfast",
    ENCODE_MODE_BALANCED: "medium",
    ENCODE_MODE_MAX_QUALITY: "slow",
}
# VideoToolbox uses a binary realtime toggle instead of named presets:
#   true  -> fastest, undershoots target bitrate (live streaming)
#   false -> normal, hits target bitrate, higher quality
_VT_REALTIME_BY_MODE = {
    ENCODE_MODE_FAST: "false",
    ENCODE_MODE_BALANCED: "false",
    ENCODE_MODE_MAX_QUALITY: "false",
}


def normalize_encode_mode(mode: Optional[str]) -> str:
    if mode in ENCODE_MODE_KEYS:
        return str(mode)
    return ENCODE_MODE_DEFAULT


def nvenc_preset_for_mode(mode: Optional[str]) -> str:
    return _NVENC_PRESET_BY_MODE.get(normalize_encode_mode(mode), NVENC_PRESET)


def amf_quality_for_mode(mode: Optional[str]) -> str:
    return _AMF_QUALITY_BY_MODE.get(normalize_encode_mode(mode), AMF_QUALITY)


def qsv_preset_for_mode(mode: Optional[str]) -> str:
    return _QSV_PRESET_BY_MODE.get(normalize_encode_mode(mode), QSV_PRESET)


def qsv_lookahead_enabled_for_mode(mode: Optional[str]) -> str:
    return str(_QSV_LOOKAHEAD_BY_MODE[normalize_encode_mode(mode)][0])


def qsv_lookahead_depth_for_mode(mode: Optional[str]) -> str:
    return str(_QSV_LOOKAHEAD_BY_MODE[normalize_encode_mode(mode)][1])


def x264_preset_for_mode(mode: Optional[str]) -> str:
    return _X264_PRESET_BY_MODE.get(normalize_encode_mode(mode), X264_PRESET)


def videotoolbox_realtime_for_mode(mode: Optional[str]) -> str:
    return _VT_REALTIME_BY_MODE.get(normalize_encode_mode(mode), "false")
