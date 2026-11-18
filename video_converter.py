"""Convert a local video to a permanently censored copy with Porda AI.

The converter reuses the model shipped with the desktop application and keeps
all frames on the local machine. Run without an input path to choose a video
with a native file picker, or pass a path for scripting and batch workflows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Callable, Optional, Tuple

import cv2
import numpy as np


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
CONFIG = ROOT / "model" / "pordav4x3.cfg"
WEIGHTS = ROOT / "model" / "porda-19200-lr-0005-909.weights"
CLASS_IDS = {"male": (0,), "female": (1,), "both": (0, 1)}
VIDEO_FILTER = "Videos (*.mp4 *.mkv *.mov *.avi *.webm *.m4v);;All files (*)"
SUBPROCESS_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ProgressCallback = Callable[[int, Optional[int], int], None]
CancelCheck = Callable[[], bool]


@dataclass(frozen=True)
class ConvertOptions:
    gender: str = "both"
    cover: str = "blur"
    color: Tuple[int, int, int] = (0, 0, 0)
    blur_strength: int = 51
    mosaic_blocks: int = 12
    confidence: float = 0.25
    nms: float = 0.10
    width: int = 544
    height: int = 320
    engine: str = "cpu"
    start: float = 0.0
    duration: Optional[float] = None
    keep_audio: bool = True


class ConversionCancelled(RuntimeError):
    """Raised when a caller requests a clean conversion cancellation."""


def parse_color(value: str) -> Tuple[int, int, int]:
    """Parse an R,G,B command-line color."""
    try:
        values = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("color must be R,G,B") from exc
    if len(values) != 3 or any(value < 0 or value > 255 for value in values):
        raise argparse.ArgumentTypeError("color must contain three values from 0 to 255")
    return values


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def probability(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("value must be greater than 0 and at most 1")
    return parsed


def non_negative(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value cannot be negative")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select a local video and create an offline censored copy."
    )
    parser.add_argument("input", nargs="?", help="video to convert; omit to open a file picker")
    parser.add_argument("-o", "--output", help="output MP4 path (default: INPUT.porda.mp4)")
    parser.add_argument("--gender", choices=CLASS_IDS, default="both")
    parser.add_argument(
        "--cover", choices=("blur", "mosaic", "black", "white", "color", "bgcolor"),
        default="blur",
    )
    parser.add_argument("--color", type=parse_color, default=(0, 0, 0), metavar="R,G,B")
    parser.add_argument("--blur-strength", type=positive_int, default=51)
    parser.add_argument("--mosaic-blocks", type=positive_int, default=12)
    parser.add_argument("--confidence", type=probability, default=0.25)
    parser.add_argument("--nms", type=probability, default=0.10)
    parser.add_argument("--model-width", type=positive_int, default=544)
    parser.add_argument("--model-height", type=positive_int, default=320)
    parser.add_argument("--engine", choices=("cpu", "opencl"), default="cpu")
    parser.add_argument("--start", type=non_negative, default=0.0, help="start time in seconds")
    parser.add_argument("--duration", type=positive_float, help="maximum seconds to convert")
    parser.add_argument("--no-audio", action="store_true", help="do not copy the source audio")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output")
    return parser.parse_args(argv)


def choose_input() -> Optional[str]:
    """Open the lightweight native picker without starting the main Porda window."""
    from PyQt5.QtWidgets import QApplication, QFileDialog

    app = QApplication.instance() or QApplication([])
    path, _ = QFileDialog.getOpenFileName(None, "Select video to censor", "", VIDEO_FILTER)
    return path or None


def default_output(input_path: str) -> str:
    path = Path(input_path)
    return str(path.with_name(f"{path.stem}.porda.mp4"))


def load_model(options: ConvertOptions):
    if not CONFIG.is_file() or not WEIGHTS.is_file():
        raise FileNotFoundError("Porda model files were not found in the model directory")
    darknet_loader = getattr(cv2.dnn, "readNetFromDarknet", None)
    if darknet_loader is None:
        raise RuntimeError(
            "Porda's Darknet model requires OpenCV 4.x; install the versions "
            "from requirements.txt"
        )
    net = darknet_loader(str(CONFIG), str(WEIGHTS))
    if options.engine == "opencl":
        if not cv2.ocl.haveOpenCL():
            raise RuntimeError("OpenCL is not available; use --engine cpu")
        cv2.ocl.setUseOpenCL(True)
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
    model = cv2.dnn_DetectionModel(net)
    model.setInputParams(size=(options.width, options.height), scale=1 / 255)
    return model


def letterbox(frame: np.ndarray, width: int, height: int):
    """Resize without stretching and return ratios back to the source frame."""
    source_h, source_w = frame.shape[:2]
    scale = min(width / source_w, height / source_h)
    resized_w = max(1, int(source_w * scale))
    resized_h = max(1, int(source_h * scale))
    resized = cv2.resize(frame, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((height, width, 3), 114, dtype=np.uint8)
    canvas[:resized_h, :resized_w] = resized
    return canvas, source_w / resized_w, source_h / resized_h


def cover_region(region: np.ndarray, options: ConvertOptions) -> np.ndarray:
    if region.size == 0:
        return region
    height, width = region.shape[:2]
    if options.cover == "black":
        return np.zeros_like(region)
    if options.cover == "white":
        return np.full_like(region, 255)
    if options.cover == "color":
        # OpenCV frames use BGR; the public option intentionally uses RGB.
        return np.full_like(region, options.color[::-1])
    if options.cover == "bgcolor":
        return np.full_like(region, region.mean(axis=(0, 1)).astype(np.uint8))
    if options.cover == "mosaic":
        blocks = max(1, options.mosaic_blocks)
        small_w, small_h = max(1, width // blocks), max(1, height // blocks)
        small = cv2.resize(region, (small_w, small_h), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
    kernel = min(options.blur_strength, max(1, min(width, height)))
    kernel = kernel if kernel % 2 else kernel - 1
    return cv2.GaussianBlur(region, (max(1, kernel), max(1, kernel)), 0)


def censor_frame(frame: np.ndarray, model, options: ConvertOptions) -> Tuple[np.ndarray, int]:
    padded, x_ratio, y_ratio = letterbox(frame, options.width, options.height)
    classes, _, boxes = model.detect(
        padded, confThreshold=options.confidence, nmsThreshold=options.nms
    )
    output = frame.copy()
    frame_h, frame_w = frame.shape[:2]
    covered = 0
    allowed = CLASS_IDS[options.gender]
    for class_id, box in zip(np.asarray(classes).reshape(-1), boxes):
        if int(class_id) not in allowed:
            continue
        x = max(0, int(box[0] * x_ratio))
        y = max(0, int(box[1] * y_ratio))
        right = min(frame_w, int((box[0] + box[2]) * x_ratio))
        bottom = min(frame_h, int((box[1] + box[3]) * y_ratio))
        if right <= x or bottom <= y:
            continue
        output[y:bottom, x:right] = cover_region(output[y:bottom, x:right], options)
        covered += 1
    return output, covered


def ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError("imageio-ffmpeg is required for video conversion") from exc


def probe_video(ffmpeg: str, input_path: str) -> Tuple[int, int, float, Optional[float]]:
    import re

    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", input_path],
        capture_output=True,
        text=True,
        creationflags=SUBPROCESS_FLAGS,
    )
    dimensions = re.search(r"Video:.*?,\s*(?:[^,]+,\s*)?(\d{2,5})x(\d{2,5})", result.stderr)
    fps_match = re.search(r"(\d+(?:\.\d+)?) fps", result.stderr)
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not dimensions or not fps_match:
        raise ValueError(f"could not read a video stream from {input_path}")
    duration = None
    if duration_match:
        duration = (
            int(duration_match.group(1)) * 3600
            + int(duration_match.group(2)) * 60
            + float(duration_match.group(3))
        )
    return (
        int(dimensions.group(1)),
        int(dimensions.group(2)),
        float(fps_match.group(1)),
        duration,
    )


def convert_video(
    input_path: str,
    output_path: str,
    options: ConvertOptions,
    progress_callback: Optional[ProgressCallback] = None,
    is_cancelled: Optional[CancelCheck] = None,
) -> int:
    input_file = Path(input_path).resolve()
    output_file = Path(output_path).resolve()
    if not input_file.is_file():
        raise ValueError(f"input file does not exist: {input_file}")
    same_file = input_file == output_file
    if output_file.exists():
        same_file = same_file or os.path.samefile(input_file, output_file)
    if same_file:
        raise ValueError("output must be different from input")
    if output_file.is_dir():
        raise ValueError("output path must be a file")
    if output_file.suffix.lower() != ".mp4":
        raise ValueError("output must use the .mp4 extension")
    if not output_file.parent.is_dir():
        raise ValueError(f"output folder does not exist: {output_file.parent}")

    ffmpeg = ffmpeg_executable()
    width, height, fps, source_duration = probe_video(ffmpeg, str(input_file))
    if source_duration is not None and options.start >= source_duration:
        raise ValueError("start time must be before the end of the video")
    available = max(0, source_duration - options.start) if source_duration is not None else None
    duration = options.duration
    if available is not None:
        duration = min(duration, available) if duration is not None else available
    total = max(1, int(round(duration * fps))) if duration is not None else None
    model = load_model(options)
    seek = ["-ss", str(options.start)] if options.start else []
    limit = ["-t", str(options.duration)] if options.duration else []

    temporary = tempfile.NamedTemporaryFile(
        prefix=f".{output_file.stem}.",
        suffix=".mp4",
        dir=str(output_file.parent),
        delete=False,
    )
    temporary_output = Path(temporary.name)
    temporary.close()
    command = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
    ]
    if options.keep_audio:
        command += [
            *seek,
            "-i",
            str(input_file),
            *limit,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0?",
            "-c:a",
            "copy",
        ]
    pixel_format = "yuv420p" if width % 2 == 0 and height % 2 == 0 else "yuv444p"
    command += [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        pixel_format,
        "-shortest",
        str(temporary_output),
    ]

    decoder = None
    encoder = None
    try:
        decoder = subprocess.Popen(
            [
                ffmpeg,
                "-v",
                "error",
                *seek,
                "-i",
                str(input_file),
                *limit,
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgr24",
                "pipe:1",
            ],
            stdout=subprocess.PIPE,
            creationflags=SUBPROCESS_FLAGS,
        )
        encoder = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            creationflags=SUBPROCESS_FLAGS,
        )
    except Exception:
        if decoder and decoder.poll() is None:
            decoder.terminate()
            decoder.wait()
        temporary_output.unlink(missing_ok=True)
        raise

    frame_bytes = width * height * 3
    processed = covered_frames = 0
    started = last_report = time.monotonic()
    cancelled = False
    processing_error = None
    if progress_callback:
        progress_callback(0, total, 0)
    try:
        while True:
            if is_cancelled and is_cancelled():
                cancelled = True
                break
            data = decoder.stdout.read(frame_bytes)
            if len(data) != frame_bytes:
                break
            frame = np.frombuffer(data, np.uint8).reshape(height, width, 3)
            censored, covered = censor_frame(frame, model, options)
            encoder.stdin.write(censored.tobytes())
            processed += 1
            covered_frames += bool(covered)
            if progress_callback:
                progress_callback(processed, total, covered_frames)
            now = time.monotonic()
            if processed == 1 or now - last_report >= 2:
                progress = f"{processed}/{total}" if total else str(processed)
                print(f"[progress] frames {progress} | covered {covered_frames}", flush=True)
                last_report = now
    except Exception as exc:
        processing_error = exc
    finally:
        if decoder.stdout:
            decoder.stdout.close()
        if encoder.stdin:
            try:
                encoder.stdin.close()
            except OSError:
                pass
        if cancelled or processing_error:
            if decoder.poll() is None:
                decoder.terminate()
            if encoder.poll() is None:
                encoder.terminate()
    decoder_code = decoder.wait()
    encoder_code = encoder.wait()
    if cancelled:
        temporary_output.unlink(missing_ok=True)
        raise ConversionCancelled("video conversion cancelled")
    if processing_error:
        temporary_output.unlink(missing_ok=True)
        raise RuntimeError(f"video processing failed: {processing_error}") from processing_error
    if decoder_code or encoder_code:
        temporary_output.unlink(missing_ok=True)
        raise RuntimeError(
            f"video conversion failed (decoder {decoder_code}, encoder {encoder_code})"
        )
    try:
        os.replace(temporary_output, output_file)
    except OSError:
        temporary_output.unlink(missing_ok=True)
        raise
    elapsed = time.monotonic() - started
    print(f"[done] {processed} frames in {elapsed:.1f}s -> {output_file}")
    return processed


def main(argv=None) -> int:
    args = parse_args(argv)
    input_path = args.input or choose_input()
    if not input_path:
        print("No video selected.", file=sys.stderr)
        return 2
    input_path = os.path.abspath(os.path.expanduser(input_path))
    if not os.path.isfile(input_path):
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        return 2
    output_path = os.path.abspath(
        os.path.expanduser(args.output or default_output(input_path))
    )
    if os.path.normcase(input_path) == os.path.normcase(output_path):
        print("Output must be different from input.", file=sys.stderr)
        return 2
    if os.path.exists(output_path) and not args.overwrite:
        print(
            f"Output already exists (pass --overwrite to replace it): {output_path}",
            file=sys.stderr,
        )
        return 2
    options = ConvertOptions(
        gender=args.gender,
        cover=args.cover,
        color=args.color,
        blur_strength=args.blur_strength,
        mosaic_blocks=args.mosaic_blocks,
        confidence=args.confidence,
        nms=args.nms,
        width=args.model_width,
        height=args.model_height,
        engine=args.engine,
        start=args.start,
        duration=args.duration,
        keep_audio=not args.no_audio,
    )
    try:
        convert_video(input_path, output_path, options)
    except (OSError, RuntimeError, ValueError, cv2.error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
