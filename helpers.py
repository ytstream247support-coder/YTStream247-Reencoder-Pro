import sys
import platform
from pathlib import Path
from typing import Optional, Tuple

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller.
    
    When running as a PyInstaller bundle, resources are extracted to _MEIPASS.
    In development, resources are relative to the current working directory.
    
    Args:
        relative_path: Relative path to resource file
    
    Returns:
        Absolute Path object to the resource
    """
    base_path = getattr(sys, '_MEIPASS', Path.cwd())
    return Path(base_path) / relative_path

def get_icon_path():
    """
    Path to the app window icon (Qt QIcon).

    Prefers bundled assets/icons/icon.png, then platform fallbacks under
    assets/icons/ and legacy root files for older layouts.
    """
    base = resource_path("")
    png = base / "assets" / "icons" / "icon.png"
    if png.exists():
        return png

    system = platform.system()
    if system == "Windows":
        ico = base / "assets" / "icons" / "icon.ico"
        if ico.exists():
            return ico
        for name in ("icon.ico", "icon.png"):
            p = base / name
            if p.exists():
                return p
        return base / "icon.ico"

    if system == "Darwin":
        for name in ("icon.icns", "icon.ico", "icon.png"):
            p = base / name
            if p.exists():
                return p
        return base / "icon.icns"

    for name in ("icon.png", "icon.ico"):
        p = base / name
        if p.exists():
            return p
    return base / "icon.png"

def set_app_user_model_id(appid: str = "HhhH.YoutubeStreamingMaxTools.1"):
    """Set Windows app user model ID (Windows only)."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
        except Exception:
            pass

def get_disk_space(path: Path) -> Optional[int]:
    """
    Get available disk space in bytes for the given path.
    Returns None if unable to determine.
    """
    try:
        import shutil
        # Ensure path exists or use parent directory
        check_path = path if path.exists() else path.parent if path.parent.exists() else Path.cwd()
        stat = shutil.disk_usage(check_path)
        return stat.free
    except Exception:
        return None

def validate_output_path(path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate output path for invalid characters and basic sanity checks.
    Returns (is_valid, error_message).
    """
    if path is None:
        return (False, "Path is None")
    
    path_str = str(path)
    
    # Check if path is empty
    if not path_str or not path_str.strip():
        return (False, "Path is empty")
    
    # Check for invalid characters (OS-specific)
    if sys.platform == "win32":
        invalid_chars = '<>"|?*'
        # Check for invalid characters
        for char in invalid_chars:
            if char in path_str:
                return (False, f"Path contains invalid character: {char}")
        
        # Check for colon - valid only in drive letters (C:), invalid elsewhere
        if ':' in path_str:
            # Colon is valid only if it's at position 1 (drive letter format: X:)
            # Check if colon exists at position 1 with a letter before it
            if not (len(path_str) >= 2 and path_str[1] == ':' and path_str[0].isalpha()):
                return (False, "Path contains invalid colon character (colon only allowed in drive letters like C:)")
    
    # Check path length (Windows has 260 char limit for some paths)
    if sys.platform == "win32" and len(path_str) > 260:
        return (False, "Path exceeds maximum length (260 characters)")
    
    return (True, None)


def generate_unique_path(out_folder: Path, stem: str, suffix: str = "_re", ext: str = ".mp4", claimed: set = None) -> Path:
    """
    Generate a unique output file path that won't overwrite existing files.

    Naming scheme:
        {stem}_re.mp4  ->  {stem}_1_re.mp4  ->  {stem}_2_re.mp4  -> ...

    Args:
        out_folder: Directory for the output file
        stem:       Base name of the source file (without extension)
        suffix:     Suffix appended before the extension (default "_re")
        ext:        File extension including the dot (default ".mp4")
        claimed:    Optional set of Paths already reserved in the current batch,
                    so two jobs in the same queue don't pick the same name

    Returns:
        A Path that does not exist on disk and is not in *claimed*.
    """
    candidate = out_folder / f"{stem}{suffix}{ext}"
    if not candidate.exists() and (claimed is None or candidate not in claimed):
        return candidate

    counter = 1
    while True:
        candidate = out_folder / f"{stem}_{counter}{suffix}{ext}"
        if not candidate.exists() and (claimed is None or candidate not in claimed):
            return candidate
        counter += 1