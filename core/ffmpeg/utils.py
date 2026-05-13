import platform
import subprocess

def get_subprocess_flags():
    """Get subprocess creation flags to hide console window on Windows."""
    if platform.system() == "Windows":
        return subprocess.CREATE_NO_WINDOW
    return 0

def parse_time_str(time_str: str) -> float:
    """Parse FFmpeg time string (HH:MM:SS.ms or MM:SS.ms) into seconds."""
    try:
        if "=" in time_str:
            time_str = time_str.split("=", 1)[1]
            
        h, m, s = 0, 0, 0.0
        if ":" in time_str:
            segs = time_str.split(":")
            if len(segs) == 3:
                h = int(segs[0])
                m = int(segs[1])
                s = float(segs[2])
            elif len(segs) == 2:
                m = int(segs[0])
                s = float(segs[1])
        else:
            s = float(time_str)
        return h * 3600 + m * 60 + s
    except Exception:
        return 0.0
