from datetime import datetime, timezone
from typing import List, Optional, Tuple

from core.config import FFMPEG_BIN, macos_supports_vt_cbr
from core.constants import APP_NAME, APP_VERSION
from core.ffmpeg.encode_profile import (
    AAC_BITRATE_KBPS,
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    FFLAGS_IN,
    H264_PROFILE,
    KEYFRAME_INTERVAL_SEC,
    MOVFLAGS,
    NVENC_AQ_STRENGTH,
    NVENC_RC_LOOKAHEAD,
    NVENC_TUNE,
    QUALITY_TIER_DEFAULT,
    RESOLUTION_DEFAULT,
    snap_to_standard_fps,
    amf_quality_for_mode,
    get_h264_level,
    get_resolution_dims,
    get_tier_bitrate_kbps,
    get_tier_bufsize_kbps,
    get_tier_fps,
    get_tier_gop_frames,
    needs_full_scale,
    normalize_resolution,
    nvenc_preset_for_mode,
    normalize_probe_fps,
    qsv_lookahead_depth_for_mode,
    qsv_lookahead_enabled_for_mode,
    qsv_preset_for_mode,
    video_filter_graph_cpu,
    video_filter_graph_cuda_hybrid,
    videotoolbox_realtime_for_mode,
    vf_branch,
    x264_preset_for_mode,
)
from core.job import Job


def _resolve_gpu_encoder(job: Job) -> Tuple[bool, Optional[str]]:
    if not job.use_gpu:
        return False, None
    if not job.gpu_encoder:
        return False, None
    return True, job.gpu_encoder


def _cbr_bitrate_args(bitrate_kbps: int, bufsize_kbps: int) -> List[str]:
    return [
        "-b:v", f"{bitrate_kbps}k",
        "-minrate", f"{bitrate_kbps}k",
        "-maxrate", f"{bitrate_kbps}k",
        "-bufsize", f"{bufsize_kbps}k",
    ]


def _args_h264_nvenc(speed_mode: Optional[str], gop: int, bitrate_kbps: int, bufsize_kbps: int, h264_level: str) -> List[str]:
    g = str(gop)
    return [
        "-c:v", "h264_nvenc",
        "-preset", nvenc_preset_for_mode(speed_mode),
        "-tune", NVENC_TUNE,
        "-rc", "cbr",
        "-rc-lookahead", str(NVENC_RC_LOOKAHEAD),
        "-gpu", "0",
        "-g", g,
        "-keyint_min", g,
        "-no-scenecut", "1",
        "-strict_gop", "1",
        "-pix_fmt", "yuv420p",
        "-profile:v", H264_PROFILE,
        "-level:v", h264_level,
        *_cbr_bitrate_args(bitrate_kbps, bufsize_kbps),
        "-bf", "2",
        "-spatial-aq", "1",
        "-temporal-aq", "1",
        "-aq-strength", str(NVENC_AQ_STRENGTH),
    ]


def _args_h264_amf(speed_mode: Optional[str], gop: int, bitrate_kbps: int, bufsize_kbps: int, h264_level: str) -> List[str]:
    g = str(gop)
    return [
        "-c:v", "h264_amf",
        "-usage", "transcoding",
        "-quality", amf_quality_for_mode(speed_mode),
        "-rc", "cbr",
        "-enforce_hrd", "1",
        "-g", g,
        "-keyint_min", g,
        "-pix_fmt", "yuv420p",
        "-profile:v", H264_PROFILE,
        "-level:v", h264_level,
        *_cbr_bitrate_args(bitrate_kbps, bufsize_kbps),
        "-bf", "2",
        "-header_insertion_mode", "idr",
        "-preanalysis", "1",
        "-vbaq", "1",
    ]


def _args_h264_qsv(speed_mode: Optional[str], gop: int, bitrate_kbps: int, bufsize_kbps: int, h264_level: str) -> List[str]:
    g = str(gop)
    return [
        "-c:v", "h264_qsv",
        "-preset", qsv_preset_for_mode(speed_mode),
        "-g", g,
        "-keyint_min", g,
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-profile:v", H264_PROFILE,
        "-level:v", h264_level,
        *_cbr_bitrate_args(bitrate_kbps, bufsize_kbps),
        "-bf", "2",
        "-look_ahead", qsv_lookahead_enabled_for_mode(speed_mode),
        *(["-look_ahead_depth", qsv_lookahead_depth_for_mode(speed_mode)]
          if qsv_lookahead_enabled_for_mode(speed_mode) == "1" else []),
    ]


def _args_h264_videotoolbox(speed_mode: Optional[str], gop: int, bitrate_kbps: int, bufsize_kbps: int, h264_level: str) -> List[str]:
    g = str(gop)
    args = [
        "-c:v", "h264_videotoolbox",
        "-allow_sw", "0",
        "-realtime", videotoolbox_realtime_for_mode(speed_mode),
        "-coder", "cabac",
        "-b:v", f"{bitrate_kbps}k",
    ]
    if macos_supports_vt_cbr():
        args += ["-constant_bit_rate", "true"]
    else:
        args += ["-maxrate", f"{bitrate_kbps}k", "-bufsize", f"{bufsize_kbps}k"]
    args += [
        "-g", g,
        "-keyint_min", g,
        "-pix_fmt", "yuv420p",
        "-profile:v", H264_PROFILE,
        "-level:v", h264_level,
    ]
    return args


def _args_libx264(speed_mode: Optional[str], gop: int, bitrate_kbps: int, bufsize_kbps: int, h264_level: str) -> List[str]:
    g = str(gop)
    return [
        "-c:v", "libx264",
        "-preset", x264_preset_for_mode(speed_mode),
        "-g", g,
        "-keyint_min", g,
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-profile:v", H264_PROFILE,
        "-level:v", h264_level,
        "-x264-params", "nal-hrd=cbr:force-cfr=1:bframes=2",
        "-bf", "2",
        *_cbr_bitrate_args(bitrate_kbps, bufsize_kbps),
    ]


def _args_audio_tail() -> List[str]:
    return [
        "-c:a", "aac",
        "-b:a", f"{AAC_BITRATE_KBPS}k",
        "-ac", str(AUDIO_CHANNELS),
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-aac_coder", "twoloop",
    ]


def _args_mux_metadata(job: Job) -> List[str]:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        "-metadata", f"comment=Re-encoded by {APP_NAME} v{APP_VERSION}",
        "-metadata", f"encoded_by={APP_NAME}/{APP_VERSION} {ts}",
        "-max_muxing_queue_size", "9999",
        "-avoid_negative_ts", "make_zero",
        "-write_tmcd", "0",
        "-movflags", MOVFLAGS,
        str(job.out),
    ]


def build_cmd(
    job: Job,
    width: Optional[int] = None,
    height: Optional[int] = None,
    fps: float = 30.0,
    rotation: int = 0,
    prefer_cuda_hwaccel: bool = True,
) -> Tuple[List[str], bool]:
    """
    FFmpeg argv for YouTube profile (CBR, 2s GOP).
    Resolution and fps are job-level settings, independent of tier.

    Returns (argv, used_cuda_hwaccel). When used_cuda_hwaccel is True, a failed
    run may be retried with prefer_cuda_hwaccel=False for CPU decode/filters.
    """
    tier = getattr(job, "quality_tier", QUALITY_TIER_DEFAULT)
    resolution = normalize_resolution(getattr(job, "output_resolution", RESOLUTION_DEFAULT))
    bitrate_kbps = get_tier_bitrate_kbps(tier)
    bufsize_kbps = get_tier_bufsize_kbps(tier)
    out_w, out_h = get_resolution_dims(resolution)

    fps_n = normalize_probe_fps(fps)
    fps_override = getattr(job, "fps_override", None)
    out_fps = fps_override if fps_override is not None else snap_to_standard_fps(fps_n)

    gop_frames = int(out_fps * KEYFRAME_INTERVAL_SEC)
    h264_level = get_h264_level(resolution, out_fps)
    branch = vf_branch(width, height, fps_n, out_fps, out_w, out_h)
    print(
        f"[FFMPEG] Profile: {out_w}x{out_h} @ {out_fps}fps, "
        f"{bitrate_kbps}kbps, GOP {gop_frames}f ({KEYFRAME_INTERVAL_SEC}s); "
        f"vf_branch={branch}"
    )

    use_gpu, gpu_encoder = _resolve_gpu_encoder(job)

    use_cuda_decode = (
        prefer_cuda_hwaccel
        and use_gpu
        and gpu_encoder == "h264_nvenc"
        and needs_full_scale(width, height, fps_n, out_fps, out_w, out_h)
        and rotation == 0  # CUDA decode skips autorotate; handle rotated videos on CPU
    )

    if use_cuda_decode:
        head: List[str] = [
            FFMPEG_BIN,
            "-y",
            "-hwaccel",
            "cuda",
            "-hwaccel_output_format",
            "cuda",
            "-fflags",
            FFLAGS_IN,
            "-i",
            str(job.src),
        ]
        vf = video_filter_graph_cuda_hybrid(width, height, out_fps, out_w, out_h)
        used_cuda = True
        print("[FFMPEG] Using CUDA hwaccel + scale_cuda (hybrid pad/fps on CPU)")
    else:
        head = [
            FFMPEG_BIN,
            "-y",
            "-fflags",
            FFLAGS_IN,
            "-i",
            str(job.src),
        ]
        vf = video_filter_graph_cpu(width, height, fps_n, out_fps, out_w, out_h)
        used_cuda = False

    cmd: List[str] = head + [
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-fps_mode",
        "cfr",
        "-r",
        str(out_fps),
        "-flags",
        "+cgop",
        "-vf",
        vf,
        "-af",
        "aresample=async=1:first_pts=0",
    ]

    speed_mode = job.preset
    enc_args = (speed_mode, gop_frames, bitrate_kbps, bufsize_kbps, h264_level)
    if use_gpu and gpu_encoder == "h264_nvenc":
        cmd += _args_h264_nvenc(*enc_args)
    elif use_gpu and gpu_encoder == "h264_amf":
        cmd += _args_h264_amf(*enc_args)
    elif use_gpu and gpu_encoder == "h264_qsv":
        cmd += _args_h264_qsv(*enc_args)
    elif use_gpu and gpu_encoder == "h264_videotoolbox":
        cmd += _args_h264_videotoolbox(*enc_args)
    else:
        if use_gpu and gpu_encoder:
            print(f"[FFMPEG] Unknown GPU encoder '{gpu_encoder}', using libx264")
        cmd += _args_libx264(*enc_args)

    cmd += _args_audio_tail()
    cmd += _args_mux_metadata(job)
    return cmd, used_cuda
