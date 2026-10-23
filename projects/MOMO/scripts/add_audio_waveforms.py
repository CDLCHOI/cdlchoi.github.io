"""Append an audio waveform and playback cursor without changing source files.

Requires numpy, Pillow, OpenCV, and imageio-ffmpeg. Run from any directory:
    python projects/MOMO/scripts/add_audio_waveforms.py
Use --only FILENAME to render one example before processing the whole folder.
Existing outputs are verified and reused; use --overwrite to rebuild them.
Use --include-page-videos to also process comparisons and robot demonstrations.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "static/videos/gt_video"
DESTINATION = PROJECT / "static/videos/gt_video_bar"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
STYLE_VERSION = 2
PAGE_VIDEOS = {
    "baseline_compare_videos.mp4": "Baseline comparisons",
    "genre_alarm.mp4": "Alarm ringing",
    "genre_insect_bees.mp4": "Bees buzzing",
    "genre_train.mp4": "Train passing",
    "robot_sim_video.mp4": "Robot simulation",
    "robot_demonstration.mp4": "Robot demonstration",
}
PALETTES = {
    "lavender": {"wave": "#b9b0d6", "baseline": "#d5cfe6", "cursor": "#71658f"},
    "teal": {"wave": "#4a97ad", "baseline": "#c4dce3", "cursor": "#28566b"},
    "blue": {"wave": "#6c9acb", "baseline": "#cedced", "cursor": "#35577e"},
    "graphite": {"wave": "#8a929f", "baseline": "#d7dbe1", "cursor": "#424b5a"},
    "sage": {"wave": "#6fa58c", "baseline": "#d0e1d7", "cursor": "#3c6752"},
    "amber": {"wave": "#c49a51", "baseline": "#e9dfc9", "cursor": "#80622b"},
    "warm_gold": {"wave": "#dfbd69", "baseline": "#eee3c9", "cursor": "#977a36"},
    "sunflower": {"wave": "#f2c94c", "baseline": "#f4e9c3", "cursor": "#9a791c"},
    "coral": {"wave": "#c7857a", "baseline": "#ecd7d2", "cursor": "#875349"},
}
CATEGORIES = {
    "bicycle_bell": "Bicycle bell",
    "cat": "Cat meowing",
    "gun_machine": "Machine gun fire",
    "insect_flying": "Insect buzzing",
    "bark": "Dog barking",
    "firework": "Fireworks",
    "guitar_c": "Guitar playing",
    "horn_car": "Car horn",
    "insect_bees": "Bees buzzing",
    "train": "Train passing",
    "witch": "Witch laughter",
    "alarm": "Alarm ringing",
    "helicopter_c": "Helicopter",
    "rainstorm": "Rainstorm",
    "voice_danger_female": "Warning voice",
    "car_slow_c": "Car passing",
    "sneezing": "Sneezing",
}


def run(arguments):
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "error", *map(str, arguments)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def video_info(path):
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise RuntimeError(f"Cannot open {path}")
        return {
            "width": int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": capture.get(cv2.CAP_PROP_FPS),
            "frames": int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
        }
    finally:
        capture.release()


def audio_pcm(path, validate_video=False):
    args = ["-xerror", "-i", path]
    if validate_video:
        args += ["-map", "0:v:0", "-f", "null", os.devnull]
    # Keep stereo channels separate so opposite phases cannot cancel the waveform.
    args += ["-map", "0:a:0", "-ac", "2", "-ar", "48000", "-f", "f32le", "pipe:1"]
    return run(args)


def font(size, italic=False):
    names = (
        ["C:/Windows/Fonts/ariali.ttf", "DejaVuSans-Oblique.ttf"]
        if italic
        else ["C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def make_panel(info, pcm, category, directory, palette="sunflower", font_scale=1.0,
               title_font_size=None, time_font_size=None):
    colors = PALETTES[palette]
    width, height = info["width"], info["height"]
    duration = info["frames"] / info["fps"]
    scale = width / 1280
    panel_height = int(round(224 * scale / 2)) * 2
    margin = round(100 * scale)
    left, right = margin, width - margin - 1
    center = round(124 * scale)
    amplitude = round(44 * scale)
    panel = Image.new("RGB", (width, panel_height), "white")
    draw = ImageDraw.Draw(panel)
    title_font = font(round((title_font_size or 29 * font_scale) * scale), italic=True)
    time_font = font(round((time_font_size or 20 * font_scale) * scale))
    text_color, time_color = "#4c4b60", "#77768a"
    draw.text((left, round(20 * scale)), category, font=title_font, fill=text_color)
    duration_label = f"{duration:.2f}".rstrip("0").rstrip(".") + "s"
    time_y = panel_height - round(12 * scale)
    draw.text((left, time_y), "0s", font=time_font, fill=time_color, anchor="lb")
    draw.text((right, time_y), duration_label, font=time_font,
              fill=time_color, anchor="rb")

    samples = np.frombuffer(pcm, dtype="<f4").reshape(-1, 2)
    # One peak per horizontal pixel, taken over both channels in that time bin.
    # Pad only if the audio ends before the video; normalization is per clip.
    total_samples = round(duration * 48000)
    envelope = np.max(np.abs(samples[:total_samples]), axis=1)
    if len(envelope) < total_samples:
        envelope = np.pad(envelope, (0, total_samples - len(envelope)))
    edges = np.linspace(0, total_samples, right - left + 2, dtype=int)
    peaks = np.array([envelope[a:b].max(initial=0) for a, b in zip(edges[:-1], edges[1:])])
    largest = float(peaks.max(initial=0))
    if largest:
        peaks /= largest
    draw.line((left, center, right, center), fill=colors["baseline"], width=1)
    for x, peak in zip(range(left, right + 1), peaks):
        extent = float(peak) * amplitude
        draw.line((x, center - extent, x, center + extent), fill=colors["wave"], width=1)
    panel_path = directory / "waveform.png"
    panel.save(panel_path)

    cursor_height = round(108 * scale)
    cursor_width = max(2, round(3 * scale))
    cursor = Image.new("RGB", (cursor_width, cursor_height), colors["cursor"])
    cursor_path = directory / "cursor.png"
    cursor.save(cursor_path)
    return panel_path, cursor_path, panel_height, left, right, height + center - cursor_height // 2


def process(path, palette="sunflower", destination=DESTINATION, overwrite=False, font_scale=1.0,
            title_font_size=None, time_font_size=None):
    if path.parent.resolve() == destination.resolve():
        raise ValueError("Output directory must differ from the source directory")
    source_hash = sha256(path)
    info = video_info(path)
    duration = info["frames"] / info["fps"]
    category = PAGE_VIDEOS.get(path.name) or next(
        (title for key, title in CATEGORIES.items() if path.stem[9:].startswith(key + "_")), None)
    if category is None:
        raise ValueError(f"Missing sound category for {path.name}")
    pcm = audio_pcm(path)
    if not pcm:
        raise ValueError(f"No audio samples in {path.name}")
    output = destination / path.name
    panel_height = int(round(224 * info["width"] / 1280 / 2)) * 2
    if not output.exists() or overwrite:
        with tempfile.TemporaryDirectory(prefix=".waveform-", dir=destination) as directory:
            directory = Path(directory)
            panel, cursor, panel_height, left, right, cursor_y = make_panel(
                info, pcm, category, directory, palette, font_scale, title_font_size, time_font_size)
            filters = (
                f"[0:v:0]pad=iw:ih+{panel_height}:0:0:color=white[base];"
                f"[base][1:v:0]overlay=0:{info['height']}:shortest=1[waveform];"
                f"[waveform][2:v:0]overlay=x='{left}+{right-left}*min(t/{duration:.12f},1)'"
                f":y={cursor_y}:shortest=1[out]"
            )
            video_only = directory / "video.mp4"
            temporary_output = directory / "encoded.mp4"
            run([
                "-n", "-threads", "1", "-i", path,
                "-loop", "1", "-framerate", info["fps"], "-threads", "1", "-i", panel,
                "-loop", "1", "-framerate", info["fps"], "-threads", "1", "-i", cursor,
                "-filter_complex_threads", "1", "-filter_complex", filters,
                "-map", "[out]", "-an",
                "-frames:v", info["frames"], "-c:v", "libx264",
                "-crf", "18", "-preset", "fast", "-tune", "zerolatency", "-threads", "1",
                "-pix_fmt", "yuv420p", video_only,
            ])
            # Mux audio separately: -frames:v on a combined encode can truncate
            # the last audio packet when the audio is slightly longer than video.
            run([
                "-n", "-i", video_only, "-i", path,
                "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "1",
                "-c", "copy", "-movflags", "+faststart",
                temporary_output,
            ])
            verify(path, temporary_output, source_hash, info, panel_height, pcm)
            # Windows scanners can briefly hold newly encoded files open.
            for attempt in range(7):
                try:
                    temporary_output.replace(output)
                    break
                except PermissionError:
                    if attempt == 6:
                        raise
                    time.sleep(0.1 * 2 ** attempt)
    else:
        verify(path, output, source_hash, info, panel_height, pcm)
    return {
        "filename": path.name, "category": category,
        "source_sha256": source_hash, "output_sha256": sha256(output),
        "duration_seconds": duration, "fps": info["fps"], "frames": info["frames"],
        "source_size": [info["width"], info["height"]],
        "output_size": [info["width"], info["height"] + panel_height],
        "source_unchanged": True, "decoded_audio_identical": True,
        "palette": palette,
        "style_version": STYLE_VERSION,
        "font_scale": font_scale,
        "title_font_px": title_font_size or round(29 * font_scale),
        "time_font_px": time_font_size or round(20 * font_scale),
        "upper_right_duration": False,
        "duration_label": f"{duration:.2f}".rstrip("0").rstrip(".") + "s",
        "waveform": "Stereo absolute peak per time bin; normalized per clip",
    }


def verify(source, output, source_hash, info, panel_height, pcm):
    result = video_info(output)
    expected = {**info, "height": info["height"] + panel_height}
    if result != expected:
        raise ValueError(f"Video dimensions, frame count, or FPS changed: {result} != {expected}")
    if audio_pcm(output, validate_video=True) != pcm:
        raise ValueError(f"Audio differs from source: {output.name}")
    if sha256(source) != source_hash:
        raise ValueError(f"Source file changed: {source.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Process only this source filename")
    parser.add_argument("--palette", choices=PALETTES, default="sunflower")
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    parser.add_argument("--font-scale", type=float, default=1.0, help="Scale waveform title and time labels")
    parser.add_argument("--title-font-size", type=int, help="Title size in pixels at 1280px video width")
    parser.add_argument("--time-font-size", type=int, help="Time label size in pixels at 1280px video width")
    parser.add_argument("--overwrite", action="store_true", help="Replace previously generated outputs")
    parser.add_argument("--include-page-videos", action="store_true", help="Also process the six other homepage videos")
    args = parser.parse_args()
    if not 0 < args.font_scale <= 1.5:
        parser.error("Font scale must be greater than 0 and at most 1.5 to fit the waveform panel")
    destination = args.output_dir.resolve()
    if destination == SOURCE.resolve():
        parser.error("Output directory must differ from the source directory")
    files = sorted(SOURCE.glob("*.mp4"))
    if args.include_page_videos:
        files.extend(SOURCE.parent / filename for filename in PAGE_VIDEOS)
    if args.only:
        files = [path for path in files if path.name == args.only]
    if not files:
        parser.error("No matching source videos")
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "manifest.json"
    records = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    for index, path in enumerate(files, 1):
        print(f"[{index}/{len(files)}] {path.name}", flush=True)
        records[path.name] = process(path, args.palette, destination, args.overwrite,
                                     args.font_scale, args.title_font_size, args.time_font_size)
        report_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("  OK: source hash unchanged; all frames decode; audio is identical.", flush=True)
    print(f"Done: {len(files)} videos verified in {destination}", flush=True)


if __name__ == "__main__":
    main()
