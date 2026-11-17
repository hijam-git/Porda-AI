"""PyQt5 desktop interface for Porda's offline video converter."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import threading

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from video_converter import (
    ConversionCancelled,
    ConvertOptions,
    VIDEO_FILTER,
    convert_video,
    default_output,
)


class ConversionWorker(QObject):
    progress = pyqtSignal(int, str)
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, input_path: str, output_path: str, options: ConvertOptions):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.options = options
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def _report_progress(self, processed: int, total: int | None, covered: int):
        percent = -1 if not total else min(100, round(processed / total * 100))
        total_text = str(total) if total else "unknown"
        self.progress.emit(
            percent,
            f"Processed {processed}/{total_text} frames; censored {covered} frames",
        )

    @pyqtSlot()
    def run(self):
        try:
            convert_video(
                self.input_path,
                self.output_path,
                self.options,
                progress_callback=self._report_progress,
                is_cancelled=self._cancel_event.is_set,
            )
        except ConversionCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.completed.emit(self.output_path)
        finally:
            QThread.currentThread().quit()


class VideoConverterDialog(QDialog):
    """Select, configure, and convert a video without using the command line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Porda AI - Video Converter")
        self.setMinimumWidth(620)
        self._thread = None
        self._worker = None
        self._color = (0, 0, 0)
        self._build_ui()
        self._cover_changed()
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.shutdown)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        intro = QLabel(
            "Create a permanently censored copy of a local video. "
            "Detection and conversion stay on this device."
        )
        intro.setWordWrap(True)
        main_layout.addWidget(intro)

        files_group = QGroupBox("Files")
        files_form = QFormLayout(files_group)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Select a video to censor")
        input_button = QPushButton("Browse...")
        input_button.clicked.connect(self._browse_input)
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(input_button)
        files_form.addRow("Input video:", input_row)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output MP4 path")
        output_button = QPushButton("Browse...")
        output_button.clicked.connect(self._browse_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(output_button)
        files_form.addRow("Output video:", output_row)
        main_layout.addWidget(files_group)

        censor_group = QGroupBox("Censorship")
        censor_form = QFormLayout(censor_group)
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Women", "female")
        self.gender_combo.addItem("Men", "male")
        self.gender_combo.addItem("All people", "both")
        censor_form.addRow("Censor:", self.gender_combo)

        self.cover_combo = QComboBox()
        for label, value in (
            ("Blur", "blur"),
            ("Mosaic", "mosaic"),
            ("Black", "black"),
            ("White", "white"),
            ("Custom color", "color"),
            ("Background color", "bgcolor"),
        ):
            self.cover_combo.addItem(label, value)
        self.cover_combo.currentIndexChanged.connect(self._cover_changed)
        censor_form.addRow("Cover style:", self.cover_combo)

        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(1, 301)
        self.blur_spin.setSingleStep(2)
        self.blur_spin.setValue(51)
        censor_form.addRow("Blur strength:", self.blur_spin)

        self.mosaic_spin = QSpinBox()
        self.mosaic_spin.setRange(1, 100)
        self.mosaic_spin.setValue(12)
        censor_form.addRow("Mosaic blocks:", self.mosaic_spin)

        self.color_button = QPushButton("Choose color...")
        self.color_button.clicked.connect(self._choose_color)
        self._update_color_button()
        censor_form.addRow("Custom color:", self.color_button)

        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.01, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setDecimals(2)
        self.confidence_spin.setValue(0.25)
        censor_form.addRow("Confidence:", self.confidence_spin)

        self.nms_spin = QDoubleSpinBox()
        self.nms_spin.setRange(0.01, 1.0)
        self.nms_spin.setSingleStep(0.05)
        self.nms_spin.setDecimals(2)
        self.nms_spin.setValue(0.10)
        censor_form.addRow("NMS threshold:", self.nms_spin)
        main_layout.addWidget(censor_group)

        range_group = QGroupBox("Range and output")
        range_form = QFormLayout(range_group)
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0, 86400)
        self.start_spin.setDecimals(1)
        self.start_spin.setSuffix(" seconds")
        range_form.addRow("Start at:", self.start_spin)

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0, 86400)
        self.duration_spin.setDecimals(1)
        self.duration_spin.setSuffix(" seconds")
        self.duration_spin.setSpecialValueText("Full remaining video")
        range_form.addRow("Duration:", self.duration_spin)

        self.engine_combo = QComboBox()
        self.engine_combo.addItem("CPU", "cpu")
        self.engine_combo.addItem("OpenCL GPU", "opencl")
        range_form.addRow("Engine:", self.engine_combo)

        self.keep_audio_check = QCheckBox("Keep source audio when available")
        self.keep_audio_check.setChecked(True)
        range_form.addRow("Audio:", self.keep_audio_check)
        main_layout.addWidget(range_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_conversion)
        self.convert_button = QPushButton("Convert video")
        self.convert_button.setDefault(True)
        self.convert_button.clicked.connect(self._start_conversion)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.convert_button)
        main_layout.addLayout(buttons)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select video to censor", "", VIDEO_FILTER)
        if not path:
            return
        self.input_edit.setText(path)
        self.output_edit.setText(default_output(path))

    def _browse_output(self):
        initial = self.output_edit.text().strip() or "protected.porda.mp4"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save censored video", initial, "MP4 video (*.mp4)"
        )
        if path:
            if not path.lower().endswith(".mp4"):
                path += ".mp4"
            self.output_edit.setText(path)

    def _choose_color(self):
        selected = QColorDialog.getColor(QColor(*self._color), self, "Choose cover color")
        if selected.isValid():
            self._color = (selected.red(), selected.green(), selected.blue())
            self._update_color_button()

    def _update_color_button(self):
        red, green, blue = self._color
        foreground = "white" if red * 0.299 + green * 0.587 + blue * 0.114 < 128 else "black"
        self.color_button.setText(f"RGB {red}, {green}, {blue}")
        self.color_button.setStyleSheet(
            f"background-color: rgb({red}, {green}, {blue}); color: {foreground};"
        )

    def _cover_changed(self):
        cover = self.cover_combo.currentData()
        self.blur_spin.setEnabled(cover == "blur")
        self.mosaic_spin.setEnabled(cover == "mosaic")
        self.color_button.setEnabled(cover == "color")

    def _options(self) -> ConvertOptions:
        duration = self.duration_spin.value() or None
        return ConvertOptions(
            gender=self.gender_combo.currentData(),
            cover=self.cover_combo.currentData(),
            color=self._color,
            blur_strength=self.blur_spin.value(),
            mosaic_blocks=self.mosaic_spin.value(),
            confidence=self.confidence_spin.value(),
            nms=self.nms_spin.value(),
            engine=self.engine_combo.currentData(),
            start=self.start_spin.value(),
            duration=duration,
            keep_audio=self.keep_audio_check.isChecked(),
        )

    def _validated_paths(self):
        input_path = os.path.abspath(os.path.expanduser(self.input_edit.text().strip()))
        output_path = os.path.abspath(os.path.expanduser(self.output_edit.text().strip()))
        if not self.input_edit.text().strip() or not os.path.isfile(input_path):
            QMessageBox.warning(self, "Invalid input", "Select an existing input video.")
            return None
        if not self.output_edit.text().strip():
            QMessageBox.warning(self, "Invalid output", "Choose an output file.")
            return None
        if os.path.normcase(input_path) == os.path.normcase(output_path):
            QMessageBox.warning(
                self, "Invalid output", "The output must be different from the input."
            )
            return None
        if not Path(output_path).parent.is_dir():
            QMessageBox.warning(self, "Invalid output", "The output folder does not exist.")
            return None
        if os.path.exists(output_path):
            answer = QMessageBox.question(
                self,
                "Replace output?",
                f"{output_path}\n\nalready exists. Replace it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return None
        return input_path, output_path

    def _start_conversion(self):
        paths = self._validated_paths()
        if not paths:
            return
        input_path, output_path = paths
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing model and video...")
        self.convert_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self._thread = QThread(self)
        self._worker = ConversionWorker(input_path, output_path, self._options())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread_finished)
        self._thread.start()

    @pyqtSlot(int, str)
    def _on_progress(self, percent: int, message: str):
        if percent < 0:
            self.progress_bar.setRange(0, 0)
        else:
            if self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    @pyqtSlot(str)
    def _on_completed(self, output_path: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Completed: {output_path}")
        QMessageBox.information(
            self, "Conversion complete", f"The censored video was saved to:\n{output_path}"
        )

    @pyqtSlot(str)
    def _on_failed(self, message: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Failed: {message}")
        QMessageBox.critical(self, "Conversion failed", message)

    @pyqtSlot()
    def _on_cancelled(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("Conversion cancelled; partial output removed.")

    def _cancel_conversion(self):
        if self._worker:
            self._worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling...")

    @pyqtSlot()
    def _thread_finished(self):
        thread = self._thread
        self._worker = None
        self._thread = None
        self.convert_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if thread:
            thread.deleteLater()

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            answer = QMessageBox.question(
                self,
                "Cancel conversion?",
                "A video is being converted. Cancel it and close this window?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer == QMessageBox.Yes:
                self._worker.cancel()
                self.hide()
            event.ignore()
            return
        super().closeEvent(event)

    def shutdown(self):
        """Cancel conversion and wait for the worker before the app exits."""
        if self._thread and self._thread.isRunning():
            if self._worker:
                self._worker.cancel()
            self._thread.quit()
            self._thread.wait()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = VideoConverterDialog()
    dialog.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
