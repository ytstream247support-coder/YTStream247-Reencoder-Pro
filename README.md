# YT Stream 24/7 — Reencoder

A modern, cross-platform desktop application for re-encoding video files optimized for YouTube Live streaming. Built with PyQt6 and FFmpeg.

## Features

- 🎥 **Batch Processing** - Queue multiple videos for encoding
- 🚀 **GPU Acceleration** - Automatic detection and support for NVIDIA NVENC, AMD AMF, Intel Quick Sync, and Apple VideoToolbox
- 📊 **Real-time Progress** - Live progress tracking with ETA and encoding speed
- 🌍 **Multi-language** - English and Ukrainian support
- 🎨 **Modern UI** - Beautiful dark-themed interface with glassmorphism design
- ✅ **YouTube Optimized** - Automatically configures encoding parameters for YouTube Live streaming compatibility
- 🔄 **Auto Retry** - Automatic retry mechanism for failed encodings
- 📁 **Drag & Drop** - Intuitive file management with drag-and-drop support

## System Requirements

### Required
- **Python 3.8+** (if running from source)
- **FFmpeg**
  - Pre-built installers bundle FFmpeg in a sidecar `ffmpeg-apps/` folder (no separate install needed)
  - Source runs must provide FFmpeg via PATH, environment variables, or local `ffmpeg-apps/`

### Supported Platforms
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 20.04+, Fedora, etc.)

### Optional (for GPU acceleration)
- **NVIDIA GPU** with NVENC support (GTX 600 series or newer)
- **AMD GPU** with AMF support (GCN 1.0 or newer)
- **Intel CPU** with Quick Sync Video (4th gen Core or newer)
- **macOS GPU** with VideoToolbox hardware encode support

## Installation

### Option 1: Pre-built Installer (Recommended)

**Windows:**
1. Download `YTStream247Reencoder-Setup.exe` from the releases page
2. Run the installer and follow the setup wizard
3. Launch from Start Menu or desktop shortcut
4. **FFmpeg is bundled** - no additional installation required!

**macOS:**
1. Download `YT-FFmpeg-Stream-Reencoder-macOS.dmg`
2. Open the DMG and drag the app to Applications
3. Launch from Applications folder
4. **FFmpeg is bundled** - no additional installation required!
5. If macOS blocks launch (unsigned MVP build), right-click app -> `Open` -> confirm `Open`

**Linux:**
1. Download `YTStream247Reencoder.AppImage` from the releases page
2. Make it executable: `chmod +x YTStream247Reencoder.AppImage`
3. Run: `./YTStream247Reencoder.AppImage`
4. **FFmpeg is bundled** - no additional installation required!

### Option 2: From Source

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd "YT Stream 247 Reencoder"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required for source builds)
   - **Windows**: Download from https://ffmpeg.org/download.html and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo dnf install ffmpeg` (Fedora)
   
   **OR** stage local binaries in `ffmpeg-apps/`:
   - **Windows**: `ffmpeg-apps/ffmpeg.exe` and `ffmpeg-apps/ffprobe.exe`
   - **Linux**: `ffmpeg-apps/ffmpeg` and `ffmpeg-apps/ffprobe`
   - **macOS (universal app build)**:
     - `ffmpeg-apps/ffmpeg-arm64`
     - `ffmpeg-apps/ffprobe-arm64`
     - `ffmpeg-apps/ffmpeg-x86_64`
     - `ffmpeg-apps/ffprobe-x86_64`
   - The application automatically prefers local bundled binaries when present

4. **Run the application**
   ```bash
   python main.py
   ```

### Option 3: Build Your Own Installer

See [BUILD.md](BUILD.md) for detailed instructions on building installers for all platforms.

## Configuration

### FFmpeg Detection Priority

The application detects FFmpeg in the following order:
1. **Bundled FFmpeg** (in `ffmpeg-apps/` directory) - Used automatically in pre-built installers
   - macOS build prefers architecture-specific binaries (`*-arm64` or `*-x86_64`) when present
2. **Environment Variables** - `FFMPEG_BIN` and `FFPROBE_BIN`
3. **System PATH** - Standard system installation

**Override with Environment Variables:**

- `FFMPEG_BIN` - Path to ffmpeg executable
- `FFPROBE_BIN` - Path to ffprobe executable

**Example (Windows):**
```cmd
set FFMPEG_BIN=C:\ffmpeg\bin\ffmpeg.exe
set FFPROBE_BIN=C:\ffmpeg\bin\ffprobe.exe
```

**Example (Linux/macOS):**
```bash
export FFMPEG_BIN=/usr/local/bin/ffmpeg
export FFPROBE_BIN=/usr/local/bin/ffprobe
```

### Encoding Settings (Hardcoded Constants)

The application uses optimized settings for YouTube Live streaming. These are defined in `core/config.py`:

| Setting | Value | Description |
|---------|-------|-------------|
| **Keyframe Interval** | 2 seconds | YouTube Live requirement |
| **Video Bitrate** | 6000 kbps | Minimum for YouTube Live |
| **Audio Bitrate** | 128-256 kbps | Auto-adjusted based on input |
| **Audio Sample Rate** | 48 kHz | YouTube Live requirement |
| **Encoding Preset** | medium | Balance between speed and quality |
| **H.264 Profile** | high | YouTube Live compatible |
| **H.264 Level** | Auto | Calculated based on resolution/FPS |

### Application Settings (Saved in QSettings)

The application saves user preferences:

- **Output Folder** - Default output directory for encoded files
- **GPU Acceleration** - Enable/disable GPU encoding
- **Language** - UI language preference (English/Ukrainian)

Settings are stored in:
- **Windows**: `HKEY_CURRENT_USER\Software\HhhHSoft\YTStream247Reencoder`
- **macOS**: `~/Library/Preferences/com.HhhHSoft.YTStream247Reencoder.plist`
- **Linux**: `~/.config/HhhHSoft/YTStream247Reencoder.conf`

## Usage

### Basic Workflow

1. **Launch the application**
   - The app will validate FFmpeg installation on startup
   - If FFmpeg is not found, you'll see an error message with instructions

2. **Add video files**
   - Click "Add Files" button, or
   - Drag and drop video files into the queue area
   - Supported formats: MP4, MOV, MKV, AVI, FLV, WMV, WEBM, M4V, TS

3. **Configure output** (optional)
   - Set output folder in settings panel
   - Leave empty to save in same folder as source files
   - Double-click queue items to set custom output paths

4. **Enable GPU acceleration** (optional)
   - Check "Use GPU Acceleration" if available
   - The app validates real FFmpeg hardware encode capability before enabling GPU

5. **Start encoding**
   - Click "START PROCESSING" button
   - Monitor progress with real-time ETA and speed
   - Files are processed sequentially

6. **View results**
   - Click "Open Output Folder" to view encoded files
   - Output files are named: `original_name_re.ts`

### Queue Management

- **Add Files**: Click "Add Files" or drag & drop
- **Remove Item**: Right-click on queue item → "Remove"
- **Clear All**: Click "Clear All" button
- **Edit Output Path**: Double-click queue item to set custom output path

### Progress Information

During encoding, you'll see:
- **Progress Bar**: Visual percentage completion
- **Status**: Current file being processed
- **Progress Info**: Elapsed time, ETA, and encoding speed (e.g., "1.5x")

### Error Handling

The application includes automatic error recovery:
- **Retry Mechanism**: Failed jobs are automatically retried up to 2 times
- **Partial File Cleanup**: Corrupted or incomplete files are automatically deleted
- **Error Messages**: Clear error messages with actionable information

## Technical Details

### Architecture

```
YT Stream 247 Reencoder/
├── main.py                 # Application entry point
├── core/                   # Core business logic
│   ├── config.py          # Configuration constants
│   ├── constants.py       # Magic numbers and timeouts
│   ├── job.py             # Job dataclass
│   ├── ffmpeg_worker.py   # FFmpeg encoding worker thread
│   └── translator.py      # Internationalization
├── ui/                     # User interface
│   ├── main_window.py     # Main window
│   ├── panels.py          # UI panels (queue, settings)
│   ├── custom_widgets.py  # Custom widgets
│   ├── style.py           # UI styling (QSS)
│   ├── utils.py           # UI utilities
│   └── icon_utils.py      # Icon management
├── assets/                 # Resources
│   └── lang/              # Translation files
│       ├── en.json        # English
│       └── uk.json        # Ukrainian
└── helpers.py             # Helper functions
```

### Encoding Pipeline

1. **File Validation**
   - Check file exists and is readable
   - Validate video stream using ffprobe
   - Check disk space (1.5x input file size)

2. **Video Probing**
   - Single optimized ffprobe call to get:
     - Frame rate (FPS)
     - Resolution (width × height)
     - Video bitrate
     - Audio bitrate

3. **H.264 Level Calculation**
   - Automatically calculates appropriate H.264 level:
     - 4K@60fps → Level 5.2
     - 4K@30fps → Level 5.1
     - 1080p@60fps → Level 4.2
     - 1080p@30fps → Level 4.1
     - Lower resolutions → Level 4.0

4. **Encoding**
   - GPU encoder (if available): NVENC, AMF, QSV, or VideoToolbox
   - CPU encoder (fallback): libx264
   - Constant Bitrate (CBR) mode for streaming
   - 2x buffer size for network stability

5. **Output**
   - MPEG-TS container (stream ready)
   - AAC audio codec
   - H.264 video codec

### GPU Detection

The application automatically detects available GPU encoders in priority order:
1. **NVIDIA NVENC** (h264_nvenc)
2. **AMD AMF** (h264_amf)
3. **Intel Quick Sync** (h264_qsv)
4. **Apple VideoToolbox** (h264_videotoolbox)

If no GPU encoder is found, it falls back to CPU encoding (libx264).

## Troubleshooting

### FFmpeg Not Found

**Problem**: Application shows "FFmpeg Not Found" error on startup.

**Solutions**:
1. **For pre-built installers**: This should not happen - FFmpeg is bundled as `ffmpeg-apps/`. Re-download the installer if this occurs.
2. **For source builds**: 
   - Install FFmpeg and add to system PATH
   - Or set `FFMPEG_BIN` and `FFPROBE_BIN` environment variables
   - Or place FFmpeg executables in `ffmpeg-apps/` directory
3. Verify installation: `ffmpeg -version` in terminal

### GPU Not Detected

**Problem**: GPU acceleration checkbox is disabled.

**Solutions**:
1. Ensure GPU drivers are up to date
2. Verify GPU encoder support in FFmpeg: `ffmpeg -encoders | grep nvenc` (or amf/qsv)
3. Some GPUs may not support hardware encoding
4. Application will automatically use CPU encoding

### Encoding Fails

**Problem**: Files fail to encode.

**Solutions**:
1. Check input file is not corrupted
2. Ensure sufficient disk space (1.5x input file size)
3. Verify output path is writable
4. Check FFmpeg logs in console output
5. Application will automatically retry failed jobs

### Slow Encoding

**Problem**: Encoding is very slow.

**Solutions**:
1. Enable GPU acceleration if available
2. Close other resource-intensive applications
3. CPU encoding is slower but more compatible
4. Consider using faster preset (requires code modification)

### Output Files Too Large

**Problem**: Output files are larger than expected.

**Note**: The application uses constant bitrate (CBR) mode optimized for streaming. Output size depends on:
- Video duration
- Bitrate (6000 kbps minimum)
- Resolution and frame rate

## Advanced Configuration

### Modifying Encoding Parameters

To change encoding settings, edit `core/config.py`:

```python
YT_DEFAULT_KEY_S = 2  # Keyframe interval (seconds)
YT_DEFAULT_BITRATE_KBPS = 6000  # Video bitrate (kbps)
YT_DEFAULT_PRESET = "medium"  # Encoding preset (ultrafast to veryslow)
YT_DEFAULT_PROFILE = "high"  # H.264 profile
```

### Adding New Languages

1. Create new JSON file in `assets/lang/` (e.g., `de.json`)
2. Copy structure from `en.json`
3. Translate all strings
4. Add language option to `ui/main_window.py`:
   ```python
   self.lang_combo.addItems(["English", "Українська", "Deutsch"])
   ```

### Customizing UI Theme

Edit `ui/style.py` to modify colors, fonts, and styling. The application uses QSS (Qt Style Sheets) for theming.

## Performance Tips

1. **Use GPU Acceleration**: Significantly faster encoding (5-10x speedup)
2. **Close Other Apps**: Free up CPU/GPU resources
3. **Batch Processing**: Process multiple files in one session
4. **SSD Storage**: Faster read/write speeds improve performance

## Limitations

- **Sequential Processing**: Files are encoded one at a time (not parallel)
- **Fixed Settings**: Encoding parameters are hardcoded (not user-configurable)
- **MPEG-TS Output Only**: Output format is fixed to MPEG-TS (.ts)
- **H.264 Only**: Only H.264 video codec supported

## License

[Add your license information here]

## Credits

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Powered by [FFmpeg](https://ffmpeg.org/)
- Icons: Unicode symbols and emoji

## Support

For issues, questions, or contributions:
- [GitHub Issues](https://github.com/yourusername/yourrepo/issues)
- [Documentation](https://github.com/yourusername/yourrepo/wiki)

---

**Version**: 1.0.2  
**Last Updated**: 2026

