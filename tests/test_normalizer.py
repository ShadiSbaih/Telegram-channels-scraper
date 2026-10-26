import unittest
from scraper.normalizer import normalize_channel_input, get_web_preview_url


class TestNormalizer(unittest.TestCase):

    def test_clean_handle(self):
        chan, msg_id = normalize_channel_input("durov")
        self.assertEqual(chan, "durov")
        self.assertIsNone(msg_id)

    def test_at_handle(self):
        chan, msg_id = normalize_channel_input("@durov")
        self.assertEqual(chan, "durov")
        self.assertIsNone(msg_id)

    def test_https_t_me(self):
        chan, msg_id = normalize_channel_input("https://t.me/durov")
        self.assertEqual(chan, "durov")
        self.assertIsNone(msg_id)

    def test_https_preview_url(self):
        chan, msg_id = normalize_channel_input("https://t.me/s/telegram")
        self.assertEqual(chan, "telegram")
        self.assertIsNone(msg_id)

    def test_post_url(self):
        chan, msg_id = normalize_channel_input("https://t.me/durov/531")
        self.assertEqual(chan, "durov")
        self.assertEqual(msg_id, 531)

    def test_post_preview_url(self):
        chan, msg_id = normalize_channel_input("https://t.me/s/durov/531")
        self.assertEqual(chan, "durov")
        self.assertEqual(msg_id, 531)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            normalize_channel_input("")

        with self.assertRaises(ValueError):
            normalize_channel_input("!@#$%^")

    def test_web_preview_url_builder(self):
        url = get_web_preview_url("durov")
        self.assertEqual(url, "https://t.me/s/durov")

        url_before = get_web_preview_url("durov", before_id=531)
        self.assertEqual(url_before, "https://t.me/s/durov?before=531")


if __name__ == "__main__":
    unittest.main()
