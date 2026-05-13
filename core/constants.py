
# Application identity
APP_NAME = "YT Stream 24/7 - Reencoder"
APP_VERSION = "1.0.0"

# Buffer size multiplier for CBR encoding
# 2x buffer is standard RTMP CBR behavior for quality stability.
BUFFER_SIZE_MULTIPLIER = 2

# Timeout values (in seconds)
FFMPEG_TIMEOUT = 5
FFPROBE_TIMEOUT = 10
FFPROBE_RESOLUTION_TIMEOUT = 10

# File size thresholds
MIN_OUTPUT_FILE_SIZE = 1024  # bytes - files smaller than this are considered corrupt/empty

# Process termination delays
TERMINATE_WAIT_TIME = 0.5  # seconds to wait before force kill
STOP_CHECK_INTERVAL = 0.05  # seconds between stop checks in worker loop

