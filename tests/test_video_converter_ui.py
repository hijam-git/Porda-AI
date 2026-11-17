import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from video_converter_ui import VideoConverterDialog


class VideoConverterDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dialog = VideoConverterDialog()

    def tearDown(self):
        self.dialog.close()

    def test_default_options_match_desktop_defaults(self):
        options = self.dialog._options()
        self.assertEqual(options.gender, "female")
        self.assertEqual(options.cover, "blur")
        self.assertEqual(options.confidence, 0.25)
        self.assertIsNone(options.duration)
        self.assertTrue(options.keep_audio)

    def test_cover_specific_controls_follow_selected_style(self):
        self.assertTrue(self.dialog.blur_spin.isEnabled())
        self.assertFalse(self.dialog.mosaic_spin.isEnabled())
        self.assertFalse(self.dialog.color_button.isEnabled())

        self.dialog.cover_combo.setCurrentIndex(
            self.dialog.cover_combo.findData("mosaic")
        )
        self.assertFalse(self.dialog.blur_spin.isEnabled())
        self.assertTrue(self.dialog.mosaic_spin.isEnabled())

        self.dialog.cover_combo.setCurrentIndex(
            self.dialog.cover_combo.findData("color")
        )
        self.assertTrue(self.dialog.color_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
