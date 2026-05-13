import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui.main_window import ReencoderWindow
from helpers import set_app_user_model_id, get_icon_path
from core.config import validate_ffmpeg

def main():
    set_app_user_model_id('HhhH.YTStream247Reencoder.1')

    app = QApplication(sys.argv)
    
    # Validate FFmpeg/FFprobe before starting
    is_valid, error_msg = validate_ffmpeg()
    if not is_valid:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("FFmpeg Not Found")
        msg.setText("FFmpeg or FFprobe is not available")
        msg.setInformativeText(
            error_msg + "\n\n"
            "This application requires FFmpeg to be installed and available in your system PATH, "
            "or set via FFMPEG_BIN and FFPROBE_BIN environment variables.\n\n"
            "Please install FFmpeg from https://ffmpeg.org/download.html"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        sys.exit(1)
    
    # Set application icon (cross-platform)
    icon_path = get_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    w = ReencoderWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
