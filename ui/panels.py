from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFrame, QCheckBox, QFileDialog, QListWidgetItem, QComboBox, QSizePolicy, QToolButton,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFontMetrics
from pathlib import Path
from typing import List, Optional
from ui.custom_widgets import DropListWidget, NoScrollComboBox
from ui.icon_utils import get_icon, ICON_SIZE, BROWSE_ICON_SIZE
from ui import theme
from core.translator import tr
from core.config import GPUCapability, get_gpu_capability, is_valid_video_file
from core.ffmpeg.encode_profile import (
    ENCODE_MODE_BALANCED,
    ENCODE_MODE_DEFAULT,
    ENCODE_MODE_FAST,
    ENCODE_MODE_MAX_QUALITY,
    normalize_encode_mode,
    QUALITY_TIER_6K,
    QUALITY_TIER_10K,
    QUALITY_TIER_DEFAULT,
    QUALITY_TIER_KEYS,
    normalize_quality_tier,
    STANDARD_FPS_OPTIONS,
    RESOLUTION_1080P,
    RESOLUTION_1440P,
    RESOLUTION_DEFAULT,
    RESOLUTION_KEYS,
    normalize_resolution,
)

class QueuePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.listw = DropListWidget()
        self.listw.setObjectName("dropQueueList")
        self.listw.setAcceptDrops(True)
        self.listw.setSpacing(4)
        self.listw.setToolTip(tr.t("drop_tooltip"))
        self.listw.setDragEnabled(False)
        self.listw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.listw.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.listw, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.btn_add = QPushButton()
        self.btn_add.setObjectName("btnAdd")
        self.btn_add.setIcon(get_icon("add", theme.INFO_LIGHT))
        self.btn_add.setIconSize(ICON_SIZE)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self.on_add_clicked)
        self.btn_add.setMinimumHeight(44)

        self.btn_clear = QPushButton()
        self.btn_clear.setObjectName("btnClear")
        self.btn_clear.setIcon(get_icon("clear", theme.ERROR_SOFT))
        self.btn_clear.setIconSize(ICON_SIZE)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_queue)
        self.btn_clear.setMinimumHeight(44)

        btn_row.addWidget(self.btn_add, 2)
        btn_row.addWidget(self.btn_clear, 1)
        layout.addLayout(btn_row)

        self.listw.dragEnterEvent = self._drag_enter
        self.listw.dragMoveEvent = self._drag_move
        self.listw.dropEvent = self._drop
        self._row_remove_buttons: List[QToolButton] = []
        
        # Subscribe to language changes
        tr.languageChanged.connect(self.retranslate_ui)
        self.retranslate_ui() # Initial text

    def retranslate_ui(self):
        self.btn_add.setText(tr.t("btn_add"))
        self.btn_clear.setText(tr.t("btn_clear"))
        self.listw.setToolTip(tr.t("drop_tooltip"))

    def _drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.acceptProposedAction()

    def _drag_move(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.acceptProposedAction()

    def _drop(self, event):
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            self.add_files(files)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.acceptProposedAction()

    def on_add_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr.t("btn_add"), str(Path.home()), "Videos (*.mp4 *.mov *.mkv *.avi);;All (*)")
        if files: self.add_files(files)

    def add_files(self, paths: List[str]):
        from PyQt6.QtWidgets import QMessageBox
        
        added_count = 0
        skipped_count = 0
        skipped_files = []
        
        for p in paths:
            path = Path(p.strip())
            if not path.exists() or not path.is_file():
                skipped_count += 1
                skipped_files.append(path.name)
                continue
            
            # Validate video file
            is_valid, error_msg = is_valid_video_file(path)
            if not is_valid:
                skipped_count += 1
                skipped_files.append(f"{path.name} ({error_msg})")
                continue
            
            # Check if already in queue
            already_exists = False
            for i in range(self.listw.count()):
                existing_path = Path(self.listw.item(i).data(Qt.ItemDataRole.UserRole))
                if existing_path == path:
                    already_exists = True
                    break
            
            if already_exists:
                skipped_count += 1
                skipped_files.append(f"{path.name} ({tr.t('skip_already_in_queue')})")
                continue
            
            # Add to queue
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.listw.addItem(item)
            self._bind_item_widget(item)
            added_count += 1
        
        self.listw.viewport().update()
        
        # Show message if some files were skipped
        if skipped_count > 0 and added_count == 0:
            # All files were skipped
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle(tr.t("msg_no_files"))
            msg.setText(tr.t("msg_files_skipped_all").format(count=skipped_count))
            msg.setDetailedText("\n".join(skipped_files))
            msg.exec()
        elif skipped_count > 0:
            # Some files were skipped
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(tr.t("msg_files_added"))
            msg.setText(tr.t("msg_files_added_partial").format(added=added_count, skipped=skipped_count))
            msg.setDetailedText("\n".join(skipped_files))
            msg.exec()

    def clear_queue(self):
        """Clear all items from the queue."""
        self.listw.clear()
        self._row_remove_buttons.clear()
        self.listw.viewport().update()
    
    def set_locked(self, locked: bool):
        """Lock or unlock queue modification (used during encoding)."""
        self._locked = locked
        self.btn_add.setEnabled(not locked)
        self.btn_clear.setEnabled(not locked and self.listw.count() > 0)
        self.listw.setAcceptDrops(not locked)
        self._refresh_row_buttons()

    def _bind_item_widget(self, item: QListWidgetItem):
        row_widget = QWidget(self.listw)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(8, 2, 8, 2)
        row_layout.setSpacing(8)

        title = QLabel(item.text(), row_widget)
        title.setObjectName("queueRowTitle")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        btn_remove = QToolButton(row_widget)
        btn_remove.setObjectName("queueRowRemoveBtn")
        btn_remove.setIcon(get_icon("remove", theme.ERROR_SOFT))
        btn_remove.setToolTip(tr.t("btn_remove"))
        btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_remove.clicked.connect(lambda _checked=False, target=item: self._remove_item(target))

        row_layout.addWidget(title, 1)
        row_layout.addWidget(btn_remove, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.listw.setItemWidget(item, row_widget)
        item.setText("")
        self._row_remove_buttons.append(btn_remove)
        self._refresh_row_buttons()

    def _remove_item(self, item: QListWidgetItem):
        if getattr(self, "_locked", False):
            return
        row = self.listw.row(item)
        if row < 0:
            return
        self.listw.takeItem(row)
        self._refresh_row_buttons()
        self.listw.viewport().update()

    def _refresh_row_buttons(self):
        locked = getattr(self, "_locked", False)
        active_buttons: List[QToolButton] = []
        for i in range(self.listw.count()):
            item = self.listw.item(i)
            row_widget = self.listw.itemWidget(item)
            if not row_widget:
                continue
            btn = row_widget.findChild(QToolButton, "queueRowRemoveBtn")
            if btn is None:
                continue
            btn.setEnabled(not locked)
            btn.setVisible(not locked)
            active_buttons.append(btn)
        self._row_remove_buttons = active_buttons

class SettingsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._locked = False
        self._gpu_initialized = False
        self._gpu_status_raw = ""
        self._gpu_capability: GPUCapability | None = None
        self._mode_keys = [
            ENCODE_MODE_FAST,
            ENCODE_MODE_BALANCED,
            ENCODE_MODE_MAX_QUALITY,
        ]
        layout = QVBoxLayout(self)
        self.main_layout = layout
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Output folder section
        self.lbl_output = QLabel()
        self.lbl_output.setObjectName("sectionLabel")
        layout.addWidget(self.lbl_output)

        out_row = QHBoxLayout()
        self.out_row_layout = out_row
        out_row.setSpacing(12)
        self.out_edit = QLineEdit()
        self.out_edit.setReadOnly(True)
        self.out_edit.setMinimumHeight(44)
        self.out_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_browse = QPushButton()
        self.btn_browse.setObjectName("btnBrowse")
        self.btn_browse.setIcon(get_icon("folder", theme.INFO_LIGHT))
        self.btn_browse.setIconSize(BROWSE_ICON_SIZE)
        self.btn_browse.setMinimumSize(44, 44)
        self.btn_browse.setMaximumSize(52, 52)
        self.btn_browse.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.clicked.connect(self.browse_folder)
        out_row.addWidget(self.out_edit)
        out_row.addWidget(self.btn_browse)
        layout.addLayout(out_row)

        # Subtle separator between output and GPU sections
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {theme.BORDER_STRONG}; border: none;")
        layout.addWidget(separator)

        # GPU checkbox
        self.chk_gpu = QCheckBox()
        self.chk_gpu.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.chk_gpu)
        
        # GPU status label (shows detected GPU type)
        self.lbl_gpu_status = QLabel()
        self.lbl_gpu_status.setObjectName("gpuStatusLabel")
        self.lbl_gpu_status.setWordWrap(True)
        layout.addWidget(self.lbl_gpu_status)

        # Subtle separator between GPU and mode sections
        separator_mode = QFrame()
        separator_mode.setFrameShape(QFrame.Shape.HLine)
        separator_mode.setFixedHeight(1)
        separator_mode.setStyleSheet(f"background-color: {theme.BORDER_STRONG}; border: none;")
        layout.addWidget(separator_mode)

        # Reencode speed mode section
        self.lbl_mode = QLabel()
        self.lbl_mode.setObjectName("sectionLabel")
        self.lbl_mode.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.lbl_mode)

        self.mode_combo = NoScrollComboBox()
        self.mode_combo.setObjectName("modeCombo")
        self.mode_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_combo.setMinimumHeight(48)
        self.mode_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.mode_combo.setToolTip(tr.t("mode_help_balanced"))
        layout.addWidget(self.mode_combo)

        self.lbl_mode_help = QLabel()
        self.lbl_mode_help.setObjectName("modeHelpLabel")
        self.lbl_mode_help.setWordWrap(True)
        self.lbl_mode_help.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_mode_help.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.lbl_mode_help.setMinimumHeight(24)
        layout.addWidget(self.lbl_mode_help)

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._rebuild_mode_options()

        # Subtle separator before quality tier section
        separator_tier = QFrame()
        separator_tier.setFrameShape(QFrame.Shape.HLine)
        separator_tier.setFixedHeight(1)
        separator_tier.setStyleSheet(f"background-color: {theme.BORDER_STRONG}; border: none;")
        layout.addWidget(separator_tier)

        # Quality tier section
        self._tier_keys = [QUALITY_TIER_6K, QUALITY_TIER_10K]

        self.lbl_tier = QLabel()
        self.lbl_tier.setObjectName("sectionLabel")
        self.lbl_tier.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.lbl_tier)

        self.tier_combo = NoScrollComboBox()
        self.tier_combo.setObjectName("tierCombo")
        self.tier_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tier_combo.setMinimumHeight(48)
        self.tier_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.tier_combo)

        self.lbl_tier_help = QLabel()
        self.lbl_tier_help.setObjectName("modeHelpLabel")
        self.lbl_tier_help.setWordWrap(True)
        self.lbl_tier_help.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_tier_help.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.lbl_tier_help.setMinimumHeight(24)
        layout.addWidget(self.lbl_tier_help)

        self.tier_combo.currentIndexChanged.connect(self._on_tier_changed)
        self._rebuild_tier_options()

        # Output resolution selector (always visible)
        self._res_options = [RESOLUTION_1440P, RESOLUTION_1080P]

        self.res_container = QWidget()
        res_cl = QVBoxLayout(self.res_container)
        res_cl.setContentsMargins(0, 0, 0, 0)
        res_cl.setSpacing(6)

        res_sep = QFrame()
        res_sep.setFrameShape(QFrame.Shape.HLine)
        res_sep.setFixedHeight(1)
        res_sep.setStyleSheet(f"background-color: {theme.BORDER_STRONG}; border: none;")
        res_cl.addWidget(res_sep)

        self.lbl_res = QLabel()
        self.lbl_res.setObjectName("sectionLabel")
        self.lbl_res.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        res_cl.addWidget(self.lbl_res)

        self.res_combo = NoScrollComboBox()
        self.res_combo.setObjectName("resCombo")
        self.res_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.res_combo.setMinimumHeight(48)
        self.res_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        res_cl.addWidget(self.res_combo)

        self.lbl_res_help = QLabel()
        self.lbl_res_help.setObjectName("modeHelpLabel")
        self.lbl_res_help.setWordWrap(True)
        self.lbl_res_help.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_res_help.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.lbl_res_help.setMinimumHeight(24)
        res_cl.addWidget(self.lbl_res_help)

        layout.addWidget(self.res_container)
        self.res_combo.currentIndexChanged.connect(self._on_res_changed)
        self._rebuild_res_options()

        # FPS override (always visible for both tiers)
        self._fps_options: List[Optional[int]] = [None] + STANDARD_FPS_OPTIONS  # None = auto-detect

        self.fps_container = QWidget()
        fps_cl = QVBoxLayout(self.fps_container)
        fps_cl.setContentsMargins(0, 0, 0, 0)
        fps_cl.setSpacing(6)

        fps_sep = QFrame()
        fps_sep.setFrameShape(QFrame.Shape.HLine)
        fps_sep.setFixedHeight(1)
        fps_sep.setStyleSheet(f"background-color: {theme.BORDER_STRONG}; border: none;")
        fps_cl.addWidget(fps_sep)

        self.lbl_fps = QLabel()
        self.lbl_fps.setObjectName("sectionLabel")
        self.lbl_fps.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        fps_cl.addWidget(self.lbl_fps)

        self.fps_combo = NoScrollComboBox()
        self.fps_combo.setObjectName("fpsCombo")
        self.fps_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fps_combo.setMinimumHeight(48)
        self.fps_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        fps_cl.addWidget(self.fps_combo)

        layout.addWidget(self.fps_container)
        self._rebuild_fps_options()

        tr.languageChanged.connect(self.retranslate_ui)
        self.update_gpu_status()
        self.retranslate_ui()
        self.set_compact_mode(False, False)

    def _elide_gpu_text(self, text: str) -> str:
        if not text:
            return text
        fm = QFontMetrics(self.lbl_gpu_status.font())
        width = max(120, self.lbl_gpu_status.width() - 8)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, width)

    def set_compact_mode(self, compact: bool, very_compact: bool):
        if very_compact:
            self.main_layout.setContentsMargins(14, 14, 14, 14)
            self.main_layout.setSpacing(6)
            self.out_row_layout.setSpacing(6)
            self.lbl_mode_help.setVisible(False)
            self.lbl_tier_help.setVisible(False)
            self.lbl_res_help.setVisible(False)
        elif compact:
            self.main_layout.setContentsMargins(18, 18, 18, 18)
            self.main_layout.setSpacing(9)
            self.out_row_layout.setSpacing(9)
            self.lbl_mode_help.setVisible(True)
            self.lbl_tier_help.setVisible(True)
            self.lbl_res_help.setVisible(True)
        else:
            self.main_layout.setContentsMargins(22, 22, 22, 22)
            self.main_layout.setSpacing(12)
            self.out_row_layout.setSpacing(10)
            self.lbl_mode_help.setVisible(True)
            self.lbl_tier_help.setVisible(True)
            self.lbl_res_help.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._gpu_status_raw:
            self.lbl_gpu_status.setText(self._elide_gpu_text(self._gpu_status_raw))

    def update_gpu_status(self):
        capability = get_gpu_capability()
        self._gpu_capability = capability
        if not self._gpu_initialized:
            self.chk_gpu.setChecked(True)
            self._gpu_initialized = True
        self.chk_gpu.setEnabled(True)
        self.chk_gpu.setToolTip("")
        self.lbl_gpu_status.setVisible(False)
        self._gpu_status_raw = ""
        self._update_gpu_checkbox_text()

    def _update_gpu_checkbox_text(self, capability: GPUCapability | None = None):
        self.chk_gpu.setText(tr.t("chk_gpu"))
    
    def retranslate_ui(self):
        self.lbl_output.setText(tr.t("sec_output"))
        self.out_edit.setPlaceholderText(tr.t("out_placeholder"))
        self.update_gpu_status()
        self.lbl_mode.setText(tr.t("sec_reencode_speed"))
        self._rebuild_mode_options()
        self._update_mode_help_text()
        self.lbl_tier.setText(tr.t("sec_quality_tier"))
        self._rebuild_tier_options()
        self._update_tier_help_text()
        self.lbl_res.setText(tr.t("sec_resolution"))
        self._rebuild_res_options()
        self._update_res_help_text()
        self.lbl_fps.setText(tr.t("sec_fps_output"))
        self._rebuild_fps_options()
        self._apply_lock_state()

    def set_locked(self, locked: bool):
        """Lock or unlock settings controls used to build jobs."""
        self._locked = locked
        self._apply_lock_state()

    def _apply_lock_state(self):
        """Apply lock state while preserving hardware availability constraints."""
        locked = self._locked
        self.btn_browse.setEnabled(not locked)
        self.mode_combo.setEnabled(not locked)
        self.tier_combo.setEnabled(not locked)
        self.res_combo.setEnabled(not locked)
        self.fps_combo.setEnabled(not locked)
        self.out_edit.setEnabled(not locked)

        self.chk_gpu.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, locked)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr.t("sec_output"))
        if folder: 
            self.out_edit.setText(folder)

    def load_state(self, settings: QSettings):
        """Load settings from QSettings."""
        # GPU mode is intentionally auto-enabled on each app start when available.
        # We do not restore persisted use_gpu preference.
        self.out_edit.setText(settings.value("out_folder", ""))
        saved_mode = normalize_encode_mode(
            settings.value("encode_mode", ENCODE_MODE_DEFAULT, type=str)
        )
        idx = self._mode_keys.index(saved_mode)
        self.mode_combo.setCurrentIndex(idx)
        saved_tier = normalize_quality_tier(
            settings.value("quality_tier", QUALITY_TIER_DEFAULT, type=str)
        )
        tidx = self._tier_keys.index(saved_tier)
        self.tier_combo.setCurrentIndex(tidx)
        saved_res = normalize_resolution(settings.value("output_resolution", RESOLUTION_DEFAULT, type=str))
        ridx = self._res_options.index(saved_res) if saved_res in self._res_options else 0
        self.res_combo.setCurrentIndex(ridx)
        saved_fps_raw = settings.value("fps_override", None)
        if saved_fps_raw is not None:
            try:
                saved_fps = int(saved_fps_raw)
                fps_idx = self._fps_options.index(saved_fps) if saved_fps in self._fps_options else 0
                self.fps_combo.setCurrentIndex(fps_idx)
            except (ValueError, TypeError):
                self.fps_combo.setCurrentIndex(0)
        else:
            self.fps_combo.setCurrentIndex(0)
        self.retranslate_ui()

    def save_state(self, settings: QSettings):
        """Save settings to QSettings."""
        settings.setValue("out_folder", self.out_edit.text())
        settings.setValue("encode_mode", self.get_selected_encode_mode())
        settings.setValue("quality_tier", self.get_selected_quality_tier())
        settings.setValue("output_resolution", self.get_selected_resolution())
        fps_override = self.get_selected_fps_override()
        if fps_override is not None:
            settings.setValue("fps_override", fps_override)
        else:
            settings.remove("fps_override")

    def get_selected_encode_mode(self) -> str:
        idx = self.mode_combo.currentIndex()
        if 0 <= idx < len(self._mode_keys):
            return self._mode_keys[idx]
        return ENCODE_MODE_DEFAULT

    def get_selected_quality_tier(self) -> str:
        idx = self.tier_combo.currentIndex()
        if 0 <= idx < len(self._tier_keys):
            return self._tier_keys[idx]
        return QUALITY_TIER_DEFAULT

    def _on_mode_changed(self, _index: int):
        self._update_mode_help_text()

    def _rebuild_mode_options(self):
        current_mode = self.get_selected_encode_mode() if self.mode_combo.count() else ENCODE_MODE_DEFAULT
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItems(
            [
                tr.t("mode_fast"),
                tr.t("mode_balanced"),
                tr.t("mode_max_quality"),
            ]
        )
        idx = self._mode_keys.index(normalize_encode_mode(current_mode))
        self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.blockSignals(False)

    def _update_mode_help_text(self):
        mode = self.get_selected_encode_mode()
        if mode == ENCODE_MODE_FAST:
            txt = tr.t("mode_help_fast")
        elif mode == ENCODE_MODE_MAX_QUALITY:
            txt = tr.t("mode_help_max_quality")
        else:
            txt = tr.t("mode_help_balanced")
        self.lbl_mode_help.setText(txt)
        self.mode_combo.setToolTip(txt)

    def _rebuild_tier_options(self):
        current_tier = self.get_selected_quality_tier() if self.tier_combo.count() else QUALITY_TIER_DEFAULT
        self.tier_combo.blockSignals(True)
        self.tier_combo.clear()
        self.tier_combo.addItems([
            tr.t("quality_tier_6k"),
            tr.t("quality_tier_10k"),
        ])
        idx = self._tier_keys.index(normalize_quality_tier(current_tier))
        self.tier_combo.setCurrentIndex(idx)
        self.tier_combo.blockSignals(False)

    def _on_tier_changed(self, _index: int):
        self._update_tier_help_text()

    def _update_tier_help_text(self):
        tier = self.get_selected_quality_tier()
        txt = tr.t("quality_tier_help_10k") if tier == QUALITY_TIER_10K else tr.t("quality_tier_help_6k")
        self.lbl_tier_help.setText(txt)
        self.tier_combo.setToolTip(txt)

    def _on_res_changed(self, _index: int):
        self._update_res_help_text()

    def _rebuild_res_options(self):
        current = self.get_selected_resolution() if self.res_combo.count() else RESOLUTION_DEFAULT
        self.res_combo.blockSignals(True)
        self.res_combo.clear()
        for opt in self._res_options:
            label = tr.t("res_1440p") if opt == RESOLUTION_1440P else tr.t("res_1080p")
            self.res_combo.addItem(label)
        target_idx = 0
        for i, opt in enumerate(self._res_options):
            if opt == current:
                target_idx = i
                break
        self.res_combo.setCurrentIndex(target_idx)
        self.res_combo.blockSignals(False)

    def _update_res_help_text(self):
        res = self.get_selected_resolution()
        txt = tr.t("res_help_1440p") if res == RESOLUTION_1440P else tr.t("res_help_1080p")
        self.lbl_res_help.setText(txt)
        self.res_combo.setToolTip(txt)

    def get_selected_resolution(self) -> str:
        idx = self.res_combo.currentIndex()
        if 0 <= idx < len(self._res_options):
            return self._res_options[idx]
        return RESOLUTION_DEFAULT

    def _rebuild_fps_options(self):
        current = self.get_selected_fps_override() if self.fps_combo.count() else None
        self.fps_combo.blockSignals(True)
        self.fps_combo.clear()
        for opt in self._fps_options:
            label = tr.t("fps_auto") if opt is None else f"{opt} fps"
            self.fps_combo.addItem(label)
        target_idx = 0
        for i, opt in enumerate(self._fps_options):
            if opt == current:
                target_idx = i
                break
        self.fps_combo.setCurrentIndex(target_idx)
        self.fps_combo.blockSignals(False)

    def get_selected_fps_override(self) -> Optional[int]:
        """None = auto-detect from source; int = user-forced fps (applies to both tiers)."""
        idx = self.fps_combo.currentIndex()
        if 0 <= idx < len(self._fps_options):
            return self._fps_options[idx]
        return None