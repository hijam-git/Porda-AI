import argparse
from pathlib import Path
import unittest

import numpy as np

from video_converter import (
    ConvertOptions,
    censor_frame,
    cover_region,
    default_output,
    letterbox,
    parse_color,
)


class FakeModel:
    def __init__(self, classes, boxes):
        self.classes = np.asarray(classes)
        self.boxes = np.asarray(boxes)

    def detect(self, _frame, **_kwargs):
        return self.classes, np.ones(len(self.classes)), self.boxes


class VideoConverterTests(unittest.TestCase):
    def test_parse_color(self):
        self.assertEqual(parse_color("10, 20,30"), (10, 20, 30))
        with self.assertRaises(argparse.ArgumentTypeError):
            parse_color("0,256,0")

    def test_default_output_is_next_to_input(self):
        self.assertEqual(Path(default_output("clips/example.mov")), Path("clips/example.porda.mp4"))

    def test_letterbox_preserves_aspect_ratio(self):
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        padded, x_ratio, y_ratio = letterbox(image, 320, 320)
        self.assertEqual(padded.shape, (320, 320, 3))
        self.assertAlmostEqual(x_ratio, 0.625)
        self.assertAlmostEqual(y_ratio, 0.625)
        self.assertTrue(np.all(padded[160:] == 114))

    def test_all_cover_styles_preserve_shape_and_type(self):
        region = np.arange(30 * 20 * 3, dtype=np.uint8).reshape(20, 30, 3)
        for style in ("blur", "mosaic", "black", "white", "color", "bgcolor"):
            with self.subTest(style=style):
                covered = cover_region(region, ConvertOptions(cover=style, color=(1, 2, 3)))
                self.assertEqual(covered.shape, region.shape)
                self.assertEqual(covered.dtype, region.dtype)

    def test_gender_filter_only_covers_selected_class(self):
        frame = np.full((100, 100, 3), 200, dtype=np.uint8)
        model = FakeModel(classes=[0, 1], boxes=[[0, 0, 20, 20], [40, 0, 20, 20]])
        output, count = censor_frame(
            frame, model, ConvertOptions(gender="female", cover="black", width=100, height=100)
        )
        self.assertEqual(count, 1)
        self.assertTrue(np.all(output[:20, :20] == 200))
        self.assertTrue(np.all(output[:20, 40:60] == 0))


if __name__ == "__main__":
    unittest.main()
