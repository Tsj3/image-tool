"""核心图片功能的单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from image_tool.core import (
    ImageInfo,
    ImageToolError,
    crop_image,
    flip_image,
    grayscale_image,
    open_image,
    read_image_info,
    resize_image,
    resolve_output_path,
    rotate_image,
    save_image,
)


class ImageToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self._temp_dir.name)

        self.rgb_path = self.temp_path / "rgb.jpg"
        Image.new("RGB", (100, 50), (10, 20, 30)).save(self.rgb_path)

        self.rgba_path = self.temp_path / "rgba.png"
        Image.new("RGBA", (100, 50), (10, 20, 30, 120)).save(self.rgba_path)

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def test_read_image_info(self) -> None:
        info = read_image_info(self.rgba_path)
        self.assertEqual(info.filename, "rgba.png")
        self.assertEqual(info.format, "PNG")
        self.assertEqual((info.width, info.height), (100, 50))
        self.assertEqual(info.mode, "RGBA")
        self.assertGreater(info.size_bytes, 0)
        self.assertTrue(info.size_text.endswith(("KB", "MB")))
        self.assertEqual(info.size_text.count("."), 1)

    def test_size_text_megabytes(self) -> None:
        info = ImageInfo("a.png", "PNG", 1, 1, "RGB", 2 * 1024 * 1024)
        self.assertEqual(info.size_text, "2.00 MB")

    def test_resize_with_width_keeps_aspect_ratio(self) -> None:
        result = resize_image(open_image(self.rgb_path), width=50)
        self.assertEqual(result.size, (50, 25))

    def test_resize_with_height_keeps_aspect_ratio(self) -> None:
        result = resize_image(open_image(self.rgb_path), height=25)
        self.assertEqual(result.size, (50, 25))

    def test_resize_requires_a_dimension(self) -> None:
        with self.assertRaises(ImageToolError):
            resize_image(open_image(self.rgb_path))

    def test_resize_rejects_non_positive_size(self) -> None:
        with self.assertRaises(ImageToolError):
            resize_image(open_image(self.rgb_path), width=0)

    def test_crop(self) -> None:
        result = crop_image(open_image(self.rgb_path), 10, 5, 60, 45)
        self.assertEqual(result.size, (50, 40))

    def test_crop_out_of_bounds(self) -> None:
        with self.assertRaises(ImageToolError):
            crop_image(open_image(self.rgb_path), 0, 0, 101, 50)

    def test_rotate_90(self) -> None:
        result = rotate_image(open_image(self.rgb_path), 90)
        self.assertEqual(result.size, (50, 100))

    def test_flip(self) -> None:
        image = open_image(self.rgb_path)
        self.assertEqual(flip_image(image, "horizontal").size, image.size)
        self.assertEqual(flip_image(image, "vertical").size, image.size)
        with self.assertRaises(ImageToolError):
            flip_image(image, "diagonal")

    def test_grayscale(self) -> None:
        result = grayscale_image(open_image(self.rgb_path))
        self.assertEqual(result.mode, "L")

    def test_save_rgba_as_jpeg_converts_to_rgb(self) -> None:
        destination = self.temp_path / "out.jpg"
        save_image(open_image(self.rgba_path), destination)
        with Image.open(destination) as saved:
            self.assertEqual(saved.mode, "RGB")
            self.assertEqual(saved.format, "JPEG")

    def test_default_output_path_is_unique(self) -> None:
        first = resolve_output_path(self.rgba_path, None, "resized")
        self.assertEqual(first, self.temp_path / "rgba_resized.png")
        first.write_bytes(b"x")
        second = resolve_output_path(self.rgba_path, None, "resized")
        self.assertEqual(second, self.temp_path / "rgba_resized_1.png")

    def test_output_cannot_overwrite_source(self) -> None:
        with self.assertRaises(ImageToolError):
            resolve_output_path(self.rgba_path, self.rgba_path, "resized")

    def test_invalid_image_file(self) -> None:
        invalid = self.temp_path / "broken.png"
        invalid.write_text("not an image", encoding="utf-8")
        with self.assertRaises(ImageToolError):
            read_image_info(invalid)

    def test_missing_file(self) -> None:
        with self.assertRaises(ImageToolError):
            read_image_info(self.temp_path / "missing.png")


if __name__ == "__main__":
    unittest.main()
