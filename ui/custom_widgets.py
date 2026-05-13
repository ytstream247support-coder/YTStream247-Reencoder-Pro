from PyQt6.QtWidgets import QListWidget, QLabel, QWidget, QComboBox
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPixmap,
    QPolygonF,
    QPainterPath,
    QRegion,
)
from PyQt6.QtCore import Qt, QRect, QPointF, QRectF, QEvent, QTimer
from typing import Optional
from core.translator import tr
from helpers import resource_path
from . import theme

import qtawesome as qta


class NoScrollComboBox(QComboBox):
    """QComboBox that ignores mouse-wheel events to prevent accidental selection changes."""

    def wheelEvent(self, event):
        event.ignore()


class YTPlayTileWidget(QWidget):
    """Header brand: ICO/PNG from assets/icons at device pixel ratio, else vector fallback."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(theme.LOGO_TILE_PX, theme.LOGO_TILE_PX)
        self._logo_pixmap: Optional[QPixmap] = None
        self._logo_cache_dpr: Optional[float] = None

    def _load_brand_pixmap_for_dpr(self, dpr: float) -> Optional[QPixmap]:
        side = max(1, int(round(theme.LOGO_TILE_PX * dpr)))
        ico_path = resource_path("assets/icons/icon.ico")
        if ico_path.exists():
            pm = QIcon(str(ico_path)).pixmap(side, side)
            if not pm.isNull():
                pm.setDevicePixelRatio(dpr)
                return pm
        png_path = resource_path("assets/icons/icon.png")
        if png_path.exists():
            raw = QPixmap(str(png_path))
            if not raw.isNull():
                pm = raw.scaled(
                    side,
                    side,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                pm.setDevicePixelRatio(dpr)
                return pm
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        dpr = max(1.0, float(self.devicePixelRatio()))
        if self._logo_cache_dpr != dpr:
            self._logo_pixmap = self._load_brand_pixmap_for_dpr(dpr)
            self._logo_cache_dpr = dpr

        if self._logo_pixmap is not None and not self._logo_pixmap.isNull():
            pm = self._logo_pixmap
            dpm = pm.devicePixelRatio() or 1.0
            lw = max(1, round(pm.width() / dpm))
            lh = max(1, round(pm.height() / dpm))
            x = (self.width() - lw) // 2
            y = (self.height() - lh) // 2
            painter.drawPixmap(x, y, pm)
            return

        r = theme.LOGO_TILE_RADIUS_PX
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.PRIMARY))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), r, r)

        cx_svg = 13.5
        cy_svg = 12.0
        scale = theme.LOGO_PLAY_PX / 24.0
        nudge = 1.0
        painter.translate(self.width() / 2.0 + nudge, self.height() / 2.0)
        painter.scale(scale, scale)
        painter.translate(-cx_svg, -cy_svg)

        poly = QPolygonF(
            [
                QPointF(8, 5),
                QPointF(8, 19),
                QPointF(19, 12),
            ]
        )
        painter.setBrush(QColor(theme.TEXT))
        painter.drawPolygon(poly)


class DropListWidget(QListWidget):
    """QListWidget with an inviting empty-state placeholder (icon + text)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drop_hover = False
        self.installEventFilter(self)
        self.viewport().installEventFilter(self)

        tr.languageChanged.connect(self.viewport().update)

        # Pre-render the cloud-upload icon as a pixmap
        self._upload_pixmap: Optional[QPixmap] = None
        self._build_upload_icon()
        self._update_viewport_rounded_mask()

    def _build_upload_icon(self):
        try:
            icon = qta.icon("mdi6.cloud-upload-outline", color=theme.DROPZONE_ICON)
            self._upload_pixmap = icon.pixmap(64, 64)
        except Exception:
            self._upload_pixmap = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_viewport_rounded_mask()

    def eventFilter(self, watched, event):
        if watched is self or watched is self.viewport():
            if event.type() == QEvent.Type.Enter:
                self._set_drop_hover(True)
            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(0, self._sync_drop_hover_after_leave)
        return super().eventFilter(watched, event)

    def _sync_drop_hover_after_leave(self):
        if self.underMouse() or self.viewport().underMouse():
            self._set_drop_hover(True)
        else:
            self._set_drop_hover(False)

    def _set_drop_hover(self, on: bool) -> None:
        if self._drop_hover == on:
            return
        self._drop_hover = on
        self.setProperty("dropHover", on)
        self.style().unpolish(self)
        self.style().polish(self)

    def _update_viewport_rounded_mask(self) -> None:
        """Clip the viewport to rounded corners so the fill matches the dashed border."""
        vp = self.viewport()
        if vp.width() <= 0 or vp.height() <= 0:
            return
        bw = float(max(theme.DROPZONE_BORDER_PX, theme.DROPZONE_BORDER_HOVER_PX))
        # Keep viewport clipping fully inside the dashed stroke to avoid corner artifacts.
        inner_r = max(4.0, float(theme.RADIUS_BLOB) - bw - 1.0)
        path = QPainterPath()
        path.addRoundedRect(QRectF(vp.rect()), inner_r, inner_r)
        vp.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            rect = self.viewport().rect()
            center_y = rect.center().y()

            # Draw upload icon above the text
            icon_size = 64
            text_gap = 12
            if self._upload_pixmap and not self._upload_pixmap.isNull():
                ix = rect.center().x() - icon_size // 2
                iy = center_y - icon_size - text_gap
                painter.setOpacity(0.55)
                painter.drawPixmap(ix, iy, self._upload_pixmap)
                painter.setOpacity(1.0)

            # Draw placeholder text
            font = QFont("Inter", 15, QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.setPen(QColor(theme.DROPZONE_TEXT))

            text = tr.t("drop_text")
            fm = QFontMetrics(font)
            text_rect = QRect(
                rect.x(),
                center_y + text_gap // 2,
                rect.width(),
                fm.height() + 8,
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)

            # Draw a smaller subtitle hint
            sub_font = QFont("Inter", 11, QFont.Weight.Normal)
            painter.setFont(sub_font)
            painter.setPen(QColor(theme.DROPZONE_SUBTEXT))
            sub_text = tr.t("drop_subtitle") if tr.t("drop_subtitle") != "drop_subtitle" else "or click + Add Files"
            sub_rect = QRect(
                rect.x(),
                text_rect.bottom() + 2,
                rect.width(),
                fm.height() + 8,
            )
            painter.drawText(sub_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, sub_text)