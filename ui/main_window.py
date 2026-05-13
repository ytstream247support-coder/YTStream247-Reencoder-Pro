from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QProgressBar, QMessageBox,
    QListWidgetItem, QComboBox, QSizePolicy, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QSize, QSettings, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QResizeEvent
from pathlib import Path
import sys, time, os, subprocess
from typing import List, Optional

from core.job import Job
from core.ffmpeg import FFmpegWorker
from core.config import (
    ENCODER_DISPLAY_NAMES,
    YT_DEFAULT_KEY_S, YT_DEFAULT_BITRATE_KBPS,
    get_gpu_capability
)
from helpers import get_disk_space, validate_output_path, generate_unique_path
from ui.style import STYLE_QSS
from ui import theme
from ui.utils import format_duration
from ui.panels import QueuePanel, SettingsPanel
from ui.custom_widgets import NoScrollComboBox
from ui.icon_utils import get_icon, ICON_SIZE
from ui.custom_widgets import YTPlayTileWidget
from core.translator import tr 

class ReencoderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("HhhHSoft", "YTStream247Reencoder")
        
        # 1. Load Language FIRST
        saved_lang = self.settings.value("language", "en", type=str)
        tr.load_language(saved_lang)

        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint)
        
        # Set window icon (for title bar and taskbar)
        from helpers import get_icon_path
        icon_path = get_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._worker: Optional[FFmpegWorker] = None
        self._queue_start_ts: Optional[float] = None
        self._current_job_start_ts: Optional[float] = None
        self._total_jobs = 0
        self._completed_jobs = 0
        self._failed_jobs = 0
        self._stop_requested = False
        self._active_encoder_info = " [CPU]"

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # --- HEADER ROW (YTLogo-style brand + Language Switcher) ---
        header_layout = QHBoxLayout()

        header_brand = QWidget()
        brand_layout = QHBoxLayout(header_brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(0)

        self.yt_logo_tile = YTPlayTileWidget()
        brand_layout.addWidget(self.yt_logo_tile, 0, Qt.AlignmentFlag.AlignVCenter)

        self.brand_wordmark = QLabel()
        self.brand_wordmark.setObjectName("brandTitleWordmark")
        self.brand_wordmark.setTextFormat(Qt.TextFormat.RichText)
        self.brand_wordmark.setText(self._brand_wordmark_html())
        brand_layout.addWidget(self.brand_wordmark, 0, Qt.AlignmentFlag.AlignVCenter)

        self.brand_suffix = QLabel()
        self.brand_suffix.setObjectName("brandTitleSuffix")
        brand_layout.addWidget(self.brand_suffix, 0, Qt.AlignmentFlag.AlignVCenter)

        # Language ComboBox
        self.lang_combo = NoScrollComboBox()
        self.lang_combo.setObjectName("langCombo")
        self.lang_combo.addItems(["English", "Українська", "Русский"])
        self.lang_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.lang_combo.setMinimumWidth(140)
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        # Set initial index
        lang_index = {"en": 0, "uk": 1, "ru": 2}.get(saved_lang, 0)
        self.lang_combo.setCurrentIndex(lang_index)
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        
        # Stream Site Button
        self.btn_stream = QPushButton("  YT Stream 24/7")
        self.btn_stream.setObjectName("btnStream")
        self.btn_stream.setIcon(get_icon("web", theme.TEXT))
        self.btn_stream.setIconSize(QSize(18, 18))
        self.btn_stream.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stream.setToolTip("Stream your videos 24/7 on YouTube")
        self.btn_stream.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://ytstream247.com/"))
        )

        header_layout.addWidget(header_brand)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_stream)
        header_layout.addWidget(self.lang_combo)
        
        main_layout.addLayout(header_layout)

        self.queue_panel = QueuePanel()
        
        self.settings_panel = SettingsPanel()

        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(16)

        action_layout = QHBoxLayout()
        self.action_layout = action_layout
        action_layout.setSpacing(12)
        self.btn_start = QPushButton()
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setIcon(get_icon("start", "#ffffff"))
        self.btn_start.setIconSize(QSize(22, 22))
        self.btn_start.setMinimumHeight(52)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.on_start)

        self.btn_stop = QPushButton()
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setIcon(get_icon("stop", "#fca5a5"))
        self.btn_stop.setIconSize(QSize(22, 22))
        self.btn_stop.setMinimumHeight(52)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.on_stop)

        action_layout.addWidget(self.btn_start, 2)
        action_layout.addWidget(self.btn_stop, 1)
        
        right_column_layout = QVBoxLayout()
        self.right_column_layout = right_column_layout
        right_column_layout.setSpacing(14)
        right_column_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for settings panel — prevents clipping on smaller screens
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setObjectName("settingsScroll")
        self.settings_scroll.setWidget(self.settings_panel)
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.settings_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.settings_scroll.viewport().setStyleSheet("background: transparent;")
        right_column_layout.addWidget(self.settings_scroll, 1)

        right_column_layout.addLayout(action_layout)

        self.btn_open = QPushButton()
        self.btn_open.setIcon(get_icon("open"))
        self.btn_open.setIconSize(ICON_SIZE)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self.on_view_output)
        self.btn_open.setMinimumHeight(44)
        right_column_layout.addWidget(self.btn_open)

        right_wrapper = QWidget()
        self.right_wrapper = right_wrapper
        right_wrapper.setLayout(right_column_layout)
        right_wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        right_wrapper.setMinimumWidth(400)
        right_wrapper.setMaximumWidth(560)
        
        content_final = QHBoxLayout()
        self.content_final = content_final
        content_final.setSpacing(28)
        content_final.addWidget(self.queue_panel, 55)
        content_final.addWidget(right_wrapper, 45)
        main_layout.addLayout(content_final)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        bottom_layout.addWidget(self.progress)

        main_layout.addLayout(bottom_layout)

        self.setStyleSheet(STYLE_QSS())
        self.settings_panel.load_state(self.settings)
        
        # Update GPU status after loading settings
        self.settings_panel.update_gpu_status()

        # Connect queue model signals to UI state updates
        self.queue_panel.listw.model().rowsInserted.connect(self._update_ui_state)
        self.queue_panel.listw.model().rowsRemoved.connect(self._update_ui_state)
        self.queue_panel.listw.model().modelReset.connect(self._update_ui_state)

        # Apply translations
        tr.languageChanged.connect(self.retranslate_ui)
        self.retranslate_ui()

        # Set initial button/status state
        self._update_ui_state()
        self._apply_compact_layout_mode()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._apply_compact_layout_mode()

    def _apply_compact_layout_mode(self):
        w = self.width()
        compact = w < 1360
        very_compact = w < 1220

        if very_compact:
            self.right_wrapper.setMinimumWidth(360)
            self.right_wrapper.setMaximumWidth(460)
            self.content_final.setSpacing(10)
            self.right_column_layout.setSpacing(8)
            self.action_layout.setSpacing(8)
            self.content_final.setStretch(0, 56)
            self.content_final.setStretch(1, 44)
        elif compact:
            self.right_wrapper.setMinimumWidth(390)
            self.right_wrapper.setMaximumWidth(510)
            self.content_final.setSpacing(16)
            self.right_column_layout.setSpacing(10)
            self.action_layout.setSpacing(10)
            self.content_final.setStretch(0, 55)
            self.content_final.setStretch(1, 45)
        else:
            self.right_wrapper.setMinimumWidth(420)
            self.right_wrapper.setMaximumWidth(580)
            self.content_final.setSpacing(24)
            self.right_column_layout.setSpacing(12)
            self.action_layout.setSpacing(12)
            self.content_final.setStretch(0, 55)
            self.content_final.setStretch(1, 45)

        self.settings_panel.set_compact_mode(compact, very_compact)

    def _brand_wordmark_html(self) -> str:
        fg, red = theme.TEXT, theme.PRIMARY
        fs, ff = "20px", "'Inter Variable', Inter, 'Segoe UI', sans-serif"
        w7 = f"color:{fg};font-weight:700;font-size:{fs};letter-spacing:-0.02em;font-family:{ff}"
        w8 = f"color:{red};font-weight:800;font-size:{fs};letter-spacing:-0.02em;font-family:{ff}"
        # Thin spaces (U+2009) between icon-adjacent parts — readable, not cramped.
        sp = "&#x2009;"
        return (
            f'<span style="{w7}">YT</span>{sp}'
            f'<span style="{w7}">Stream</span>{sp}'
            f'<span style="{w8}">24/7</span>'
        )

    def on_lang_changed(self, index):
        code = ["en", "uk", "ru"][index]
        tr.load_language(code)
        self.settings.setValue("language", code)

    def retranslate_ui(self):
        self.setWindowTitle(tr.t("app_title"))
        self.brand_suffix.setText(tr.t("app_title_suffix"))
        self.btn_start.setText(tr.t("btn_start"))
        self.btn_stop.setText(tr.t("btn_stop"))
        self.btn_open.setText(tr.t("btn_open_out"))

        # Refresh status and button states for new language
        self._update_ui_state()

    def _update_ui_state(self):
        """Centralized UI state management with three states: idle, running, stopping."""
        has_videos = self.queue_panel.listw.count() > 0
        is_running = self._worker is not None and self._worker.isRunning()
        is_stopping = is_running and self._stop_requested

        # Button states: Start only when idle + has videos; Stop only when running (not stopping)
        self.btn_start.setEnabled(has_videos and not is_running)
        self.btn_stop.setEnabled(is_running and not is_stopping)

        # Lock queue during running or stopping
        self.queue_panel.set_locked(is_running)
        self.settings_panel.set_locked(is_running)
        if not has_videos:
            self.queue_panel.btn_clear.setEnabled(False)

        # Status label (only update for idle states; encoding/stopping text is set elsewhere)
        if not is_running:
            if has_videos:
                self.status_label.setText(tr.t("status_ready"))
            else:
                self.status_label.setText(tr.t("status_add_videos"))

    def on_view_output(self):
        out_txt = self.settings_panel.out_edit.text().strip()
        folder = Path(out_txt) if out_txt else Path.cwd()
        if not out_txt and self.queue_panel.listw.count() > 0:
             item = self.queue_panel.listw.item(0)
             folder = Path(item.data(Qt.ItemDataRole.UserRole)).parent
        
        if folder.exists():
            if sys.platform == "win32": 
                os.startfile(str(folder))
            elif sys.platform == "darwin": 
                subprocess.Popen(["open", str(folder)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else: 
                subprocess.Popen(["xdg-open", str(folder)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def build_jobs(self) -> List[Job]:
        """
        Build list of encoding jobs from queue items.
        
        This method:
        1. Validates output directory and creates it if needed
        2. Checks disk space for each job
        3. Validates output paths
        4. Detects GPU encoder if requested
        5. Creates Job objects with user-configured parameters
        
        Returns:
            List of Job objects ready for encoding
        """
        jobs = []
        listw = self.queue_panel.listw
        
        sp = self.settings_panel
        out_dir_txt = sp.out_edit.text().strip()
        use_gpu = sp.chk_gpu.isChecked()
        encode_mode = sp.get_selected_encode_mode()
        quality_tier = sp.get_selected_quality_tier()
        fps_override = sp.get_selected_fps_override()
        output_resolution = sp.get_selected_resolution()
        
        # Validate and prepare output directory
        default_out_dir = None
        if out_dir_txt:
            out_dir = Path(out_dir_txt)
            if not out_dir.exists():
                try:
                    out_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.warning(
                        self, 
                        tr.t("msg_no_files"),
                        tr.t("error_cannot_create_dir").format(path=str(out_dir)) + f"\n{str(e)}"
                    )
                    return []  # Return empty list if directory creation fails
            
            if not out_dir.is_dir():
                QMessageBox.warning(
                    self,
                    tr.t("msg_no_files"),
                    tr.t("error_not_directory").format(path=str(out_dir))
                )
                return []
            
            # Check if directory is writable
            try:
                test_file = out_dir / ".write_test"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    tr.t("msg_no_files"),
                    tr.t("error_not_writable").format(path=str(out_dir)) + f"\n{str(e)}"
                )
                return []
            
            default_out_dir = out_dir
        
        # Detect GPU encoder if user wants GPU; fall back to CPU silently if unavailable
        gpu_encoder = None
        if use_gpu:
            gpu_capability = get_gpu_capability(force_refresh=True)
            if gpu_capability.available and gpu_capability.encoder:
                gpu_encoder = gpu_capability.encoder

        claimed_paths: set = set()

        for i in range(listw.count()):
            it = listw.item(i)
            src = Path(it.data(Qt.ItemDataRole.UserRole))
            override = it.data(Qt.ItemDataRole.UserRole + 1)
            
            # Determine output path
            if override:
                out = Path(str(override))
                # Validate output path
                is_valid, error_msg = validate_output_path(out)
                if not is_valid:
                    QMessageBox.warning(
                        self,
                        tr.t("msg_no_files"),
                        tr.t("error_invalid_path").format(path=str(out)) + f": {error_msg}"
                    )
                    continue  # Skip this job
                
                # Ensure output directory exists for override paths
                if not out.parent.exists():
                    try:
                        out.parent.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        QMessageBox.warning(
                            self,
                            tr.t("msg_no_files"),
                            tr.t("error_cannot_create_dir").format(path=str(out.parent)) + f"\n{str(e)}"
                        )
                        continue  # Skip this job
            else:
                out_folder = default_out_dir if default_out_dir else src.parent
                out = generate_unique_path(out_folder, src.stem, claimed=claimed_paths)
            
            # Validate output path
            is_valid, error_msg = validate_output_path(out)
            if not is_valid:
                QMessageBox.warning(
                    self,
                    tr.t("msg_no_files"),
                    tr.t("error_invalid_path").format(path=str(out)) + f": {error_msg}"
                )
                continue  # Skip this job
            
            # Check disk space (rough estimate: assume output will be similar size to input)
            # For safety, check for at least 1.5x input file size
            try:
                src_size = src.stat().st_size
                estimated_output_size = int(src_size * 1.5)  # Conservative estimate
                
                available_space = get_disk_space(out.parent if out.parent.exists() else Path.cwd())
                if available_space is not None and available_space < estimated_output_size:
                    required_mb = estimated_output_size / (1024 * 1024)
                    available_mb = available_space / (1024 * 1024)
                    QMessageBox.warning(
                        self,
                        tr.t("msg_no_files"),
                        tr.t("error_insufficient_space").format(
                            required=f"{required_mb:.1f} MB",
                            available=f"{available_mb:.1f} MB"
                        )
                    )
                    continue  # Skip this job
            except Exception:
                # If we can't check disk space, continue anyway (better than blocking)
                pass

            claimed_paths.add(out)
            jobs.append(Job(
                src=src,
                out=out,
                key_s=YT_DEFAULT_KEY_S,
                preset=encode_mode,
                target_kbps=YT_DEFAULT_BITRATE_KBPS,
                use_gpu=use_gpu,
                gpu_encoder=gpu_encoder,
                quality_tier=quality_tier,
                output_resolution=output_resolution,
                fps_override=fps_override,
            ))
        return jobs

    def on_start(self):
        if self._worker and self._worker.isRunning():
            return
        if self.queue_panel.listw.count() == 0:
            return

        self.settings_panel.save_state(self.settings)
        jobs = self.build_jobs()
        if not jobs:
            return
        
        self._total_jobs = len(jobs)
        self._completed_jobs = 0
        self._failed_jobs = 0
        self._queue_start_ts = time.time()
        self._stop_requested = False
        first_job = jobs[0]
        if first_job.use_gpu and first_job.gpu_encoder:
            display_name = ENCODER_DISPLAY_NAMES.get(first_job.gpu_encoder, first_job.gpu_encoder)
            self._active_encoder_info = f" [{display_name}]"
        else:
            self._active_encoder_info = " [CPU]"
        
        self.progress.setValue(0)
        self.status_label.setText(tr.t("status_ready"))
        
        self._worker = FFmpegWorker(jobs)
        self._worker.log_line.connect(self._on_worker_log_message)
        self._worker.gpu_fallback_activated.connect(self._on_gpu_fallback_activated)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.job_started.connect(self._on_job_start)
        self._worker.job_finished.connect(self._on_job_finish)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
        
        self._update_ui_state()

    def on_stop(self):
        """Handle stop button click - enter 'stopping' state."""
        self._stop_requested = True

        if self._worker:
            self._worker.stop()

        self.status_label.setText(tr.t("status_stopping"))
        self.progress.setValue(0)
        self._update_ui_state()

    def _on_worker_log_message(self, message: str):
        """Handle worker log messages and show concise status updates."""
        if message.startswith("[INFO]"):
            if "GPU fallback active" in message:
                self.status_label.setText(tr.t("status_gpu_fallback_next_jobs_cpu"))
            else:
                self.status_label.setText(message.replace("[INFO]", "").strip())
            return
        # Keep warning indicator for errors and unknown critical lines.
        self.status_label.setText(f"⚠ {message}")

    def _on_gpu_fallback_activated(self, _reason: str):
        """Update UI when runtime failover switches queue from GPU to CPU."""
        self._active_encoder_info = " [CPU]"
        self.status_label.setText(tr.t("status_gpu_fallback_active"))
    
    def _on_job_start(self, p):
        self._current_job_start_ts = time.time()
        encoder_info = self._active_encoder_info
        if self._total_jobs > 1:
            current = self._completed_jobs + 1
            self.status_label.setText(f"{tr.t('status_encoding')} [{current}/{self._total_jobs}]: {p.name}{encoder_info}")
        else:
            self.status_label.setText(f"{tr.t('status_encoding')}: {p.name}{encoder_info}")

    def _on_job_finish(self, out, success):
        # If stopped, ignore individual job results (worker.finished handles final state)
        if self._stop_requested:
            return
        
        self._completed_jobs += 1
        if not success:
            self._failed_jobs += 1
        elapsed = time.time() - self._current_job_start_ts if self._current_job_start_ts else 0
        dur = format_duration(elapsed)
        
        if success:
            self.status_label.setText(f"✓ {out.name} ({dur})")
        else:
            self.status_label.setText(f"✗ {out.name} - {tr.t('status_failed')}")

    def _on_worker_finished(self):
        """Called when the worker thread actually terminates (QThread.finished signal)."""
        if self._stop_requested:
            self.status_label.setText(tr.t("status_stopped"))
            self.progress.setValue(0)
        else:
            total_dur = format_duration(time.time() - self._queue_start_ts)
            self.status_label.setText(f"{tr.t('msg_all_done')} {total_dur}")
            self.progress.setValue(100)
            self._show_done_dialog(total_dur)
        self._update_ui_state()

    def _show_done_dialog(self, duration: str):
        """Show a summary dialog when all encoding jobs have finished."""
        success_count = self._completed_jobs - self._failed_jobs
        msg = QMessageBox(self)
        msg.setWindowTitle(tr.t("dlg_done_title"))

        if self._failed_jobs == 0:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(tr.t("dlg_done_all_success").format(
                count=self._completed_jobs, duration=duration
            ))
        else:
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(tr.t("dlg_done_partial").format(
                success=success_count, total=self._total_jobs,
                failed=self._failed_jobs, duration=duration
            ))

        msg.exec()

    def closeEvent(self, event):
        """Handle window close event - ensure worker thread is properly cleaned up."""
        if self._worker and self._worker.isRunning():
            # Stop the worker if it's running
            self._worker.stop()
            # Wait for thread to finish (with timeout)
            if not self._worker.wait(3000):  # Wait up to 3 seconds
                # Force terminate if it doesn't stop gracefully
                self._worker.terminate()
                self._worker.wait()
        
        self.settings_panel.save_state(self.settings)
        event.accept()