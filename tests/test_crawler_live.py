import unittest
import asyncio
import os
from scraper.crawler import TelegramCrawler
from scraper.exporter import export_messages


class TestCrawlerIntegration(unittest.TestCase):

    def test_live_scrape_durov(self):
        crawler = TelegramCrawler(base_delay=0.5)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            metadata, messages = loop.run_until_complete(
                crawler.scrape_channel(channel_input="durov", max_messages=15)
            )
        finally:
            loop.close()

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.username, "durov")
        self.assertGreater(len(messages), 0)
        self.assertLessEqual(len(messages), 15)

        first_msg = messages[0]
        self.assertGreater(first_msg.id, 0)
        self.assertTrue(first_msg.url.startswith("https://t.me/durov/"))
        self.assertGreater(first_msg.views, 0)

        # Test exporters
        os.makedirs("exports_test", exist_ok=True)
        csv_path = export_messages(messages, "csv", "exports_test/test.csv")
        json_path = export_messages(messages, "json", "exports_test/test.json", metadata)
        xlsx_path = export_messages(messages, "xlsx", "exports_test/test.xlsx", metadata)

        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(xlsx_path))
        self.assertGreater(os.path.getsize(csv_path), 0)
        self.assertGreater(os.path.getsize(json_path), 0)
        self.assertGreater(os.path.getsize(xlsx_path), 0)

        # Clean up test files
        for p in [csv_path, json_path, xlsx_path]:
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            os.rmdir("exports_test")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
