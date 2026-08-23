import unittest

from creator_images import content_decision


class ContentDecisionTest(unittest.TestCase):
    def test_large_creator_image_is_bounded_without_upscaling(self):
        self.assertEqual(content_decision(3200, 1200), (1600, 600))
        self.assertEqual(content_decision(800, 600), (800, 600))


if __name__ == "__main__":
    unittest.main()
