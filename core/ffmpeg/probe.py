import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from core.config import FFPROBE_BIN
from core.constants import FFPROBE_RESOLUTION_TIMEOUT
from core.ffmpeg.utils import get_subprocess_flags

def probe_video_info(path: Path) -> Tuple[float, Optional[Tuple[int, int]], Optional[int], Optional[int], int]:
    """
    Probe video file for FPS, resolution, video bitrate, audio bitrate, and rotation.

    Returns:
        Tuple of (fps, resolution, video_bitrate_kbps, audio_bitrate_kbps, rotation_degrees)
        - fps: Frame rate (defaults to 30.0 if probe fails)
        - resolution: (width, height) already swapped for display orientation, or None
        - video_bitrate_kbps: Video bitrate in kbps or None
        - audio_bitrate_kbps: Audio bitrate in kbps or None
        - rotation_degrees: rotation metadata value (0, 90, 180, 270); 0 if none found
    """
    if not FFPROBE_BIN:
        return (30.0, None, None, None, 0)

    try:
        cmd = [
            FFPROBE_BIN, "-v", "error",
            "-show_entries", "stream=codec_type,avg_frame_rate,width,height,bit_rate:stream_tags=rotate",
            "-of", "json",
            str(path)
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=FFPROBE_RESOLUTION_TIMEOUT, creationflags=get_subprocess_flags())
        data = json.loads(out)

        fps = 30.0
        resolution = None
        video_bitrate = None
        audio_bitrate = None
        rotation = 0

        if "streams" in data and len(data["streams"]) > 0:
            for stream in data["streams"]:
                if stream.get("codec_type") == "video":
                    if "avg_frame_rate" in stream:
                        fps_str = stream["avg_frame_rate"]
                        if "/" in fps_str:
                            a, b = fps_str.split("/")
                            denom = float(b) if float(b) != 0 else 1.0
                            fps = float(a) / denom
                        else:
                            try:
                                fps = float(fps_str)
                            except:
                                fps = 30.0

                    if "width" in stream and "height" in stream:
                        try:
                            width = int(stream["width"])
                            height = int(stream["height"])
                            if width > 0 and height > 0:
                                # Read rotation tag so we can return display dimensions
                                try:
                                    rot = int(stream.get("tags", {}).get("rotate", 0))
                                    rotation = rot % 360
                                except (ValueError, TypeError):
                                    rotation = 0
                                # 90° or 270° rotation means w/h are swapped vs display
                                if rotation in (90, 270):
                                    resolution = (height, width)
                                else:
                                    resolution = (width, height)
                        except (ValueError, TypeError):
                            pass

                    if "bit_rate" in stream:
                        try:
                            bitrate_bps = int(stream["bit_rate"])
                            video_bitrate = bitrate_bps // 1000
                        except (ValueError, TypeError):
                            pass

                elif stream.get("codec_type") == "audio":
                    if "bit_rate" in stream:
                        try:
                            bitrate_bps = int(stream["bit_rate"])
                            audio_bitrate = bitrate_bps // 1000
                        except (ValueError, TypeError):
                            pass

        return (fps, resolution, video_bitrate, audio_bitrate, rotation)
    except subprocess.TimeoutExpired:
        print(f"[DEBUG] Video probe timed out")
    except json.JSONDecodeError as e:
        print(f"[DEBUG] Failed to parse JSON from ffprobe: {e}")
    except KeyError as e:
        print(f"[DEBUG] Missing expected key in ffprobe JSON: {e}")
    except Exception as e:
        print(f"[DEBUG] Video probe failed: {e}")

    return (_probe_fps_fallback(path), _probe_resolution_fallback(path),
            _probe_bitrate_fallback(path), _probe_audio_bitrate_fallback(path), 0)

def _probe_fps_fallback(path: Path) -> float:
    """Fallback FPS probe method."""
    if not FFPROBE_BIN:
        return 30.0
    try:
        cmd = [FFPROBE_BIN, "-v", "0", "-select_streams", "v:0",
               "-show_entries", "stream=avg_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        out = subprocess.check_output(cmd, text=True, creationflags=get_subprocess_flags()).strip()
        if "/" in out:
            a, b = out.split("/")
            denom = float(b) if float(b) != 0 else 1.0
            return float(a) / denom
        try:
            return float(out)
        except:
            return 30.0
    except Exception:
        return 30.0

def _probe_bitrate_fallback(path: Path) -> Optional[int]:
    """Fallback video bitrate probe method."""
    if not FFPROBE_BIN:
        return None
    try:
        cmd = [FFPROBE_BIN, "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=bit_rate", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        out = subprocess.check_output(cmd, text=True, creationflags=get_subprocess_flags()).strip()
        if out:
            bitrate_bps = int(float(out))
            return bitrate_bps // 1000
    except Exception:
        pass
    return None

def _probe_audio_bitrate_fallback(path: Path) -> Optional[int]:
    """Fallback audio bitrate probe method."""
    if not FFPROBE_BIN:
        return None
    try:
        cmd = [FFPROBE_BIN, "-v", "error", "-select_streams", "a:0",
               "-show_entries", "stream=bit_rate", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        out = subprocess.check_output(cmd, text=True, creationflags=get_subprocess_flags()).strip()
        if out:
            bitrate_bps = int(float(out))
            return bitrate_bps // 1000
    except Exception:
        pass
    return None

def _probe_resolution_fallback(path: Path) -> Optional[Tuple[int, int]]:
    """Fallback resolution probe method."""
    if not FFPROBE_BIN:
        return None
    try:
        cmd = [FFPROBE_BIN, "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=FFPROBE_RESOLUTION_TIMEOUT, creationflags=get_subprocess_flags()).strip()
        if out:
            lines = [l.strip() for l in out.split('\n') if l.strip()]
            if len(lines) >= 2:
                try:
                    width = int(lines[0])
                    height = int(lines[1])
                    if width > 0 and height > 0:
                        return (width, height)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse resolution from: {lines}, error: {e}")
            else:
                print(f"[DEBUG] Unexpected probe output format: {out}")
    except subprocess.TimeoutExpired:
        print(f"[DEBUG] Resolution probe timed out")
    except Exception as e:
        print(f"[DEBUG] Resolution probe failed: {e}")
    return None

def get_video_duration(path: Path) -> Optional[float]:
    """Get video duration in seconds using ffprobe."""
    if not FFPROBE_BIN:
        return None
    try:
        cmd = [
            FFPROBE_BIN, "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(path)
        ]
        out = subprocess.check_output(
            cmd, 
            text=True,
            creationflags=get_subprocess_flags()
        )
        return float(out.strip()) if out.strip() else None
    except Exception:
        return None
