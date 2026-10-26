import unittest
from scraper.parser import TelegramHTMLParser

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Channel</title></head>
<body>
  <div class="tgme_channel_info">
    <div class="tgme_channel_info_header_title">Tech Insights</div>
    <div class="tgme_channel_info_description">Daily tech news and AI research</div>
    <div class="tgme_channel_info_counter"><span class="counter_value">150.5K</span></div>
  </div>

  <div class="tgme_widget_message_wrap js-widget_message_wrap">
    <div class="tgme_widget_message" data-post="tech_insights/101">
      <div class="tgme_widget_message_bubble">
        <div class="tgme_widget_message_forwarded_from">
          Forwarded from <a class="tgme_widget_message_forwarded_from_name" href="https://t.me/ai_source">AI Source</a>
        </div>
        <div class="tgme_widget_message_text">Breaking: New multimodal models released today!<br/>Read more at telegram.org</div>
        <div class="tgme_widget_message_footer">
          <div class="tgme_widget_message_info">
            <span class="tgme_widget_message_views">12.5K</span>
            <span class="tgme_widget_message_meta">
              <a class="tgme_widget_message_date" href="https://t.me/tech_insights/101">
                <time datetime="2026-05-10T14:30:00+00:00">14:30</time>
              </a>
            </span>
          </div>
          <div class="tgme_widget_message_reactions">
            <span class="tgme_reaction tgme_reaction_paid"><i class="icon icon-telegram-stars"></i>250</span>
            <span class="tgme_reaction"><span class="tgme_widget_message_reaction_emoji">🔥</span><span class="tgme_widget_message_reaction_count">1.2K</span></span>
            <span class="tgme_reaction"><span class="tgme_widget_message_reaction_emoji">👍</span><span class="tgme_widget_message_reaction_count">850</span></span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="tgme_widget_message_wrap js-widget_message_wrap">
    <div class="tgme_widget_message" data-post="tech_insights/102">
      <div class="tgme_widget_message_bubble">
        <a class="tgme_widget_message_photo_wrap" style="background-image:url('https://cdn.example.com/photo1.jpg')"></a>
        <div class="tgme_widget_message_footer">
          <div class="tgme_widget_message_info">
            <span class="tgme_widget_message_views">5.8M</span>
            <span class="tgme_widget_message_meta">
              <a class="tgme_widget_message_date" href="https://t.me/tech_insights/102">
                <time datetime="2026-05-10T16:00:00+00:00">16:00</time>
              </a>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <a class="tme_messages_more" href="/s/tech_insights?before=101">Load more</a>
</body>
</html>
"""


class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = TelegramHTMLParser()

    def test_parse_channel_metadata(self):
        meta = self.parser.parse_channel_metadata(SAMPLE_HTML, "tech_insights")
        self.assertEqual(meta.username, "tech_insights")
        self.assertEqual(meta.title, "Tech Insights")
        self.assertEqual(meta.description, "Daily tech news and AI research")
        self.assertEqual(meta.subscribers, "150.5K")
        self.assertEqual(meta.subscribers_count, 150500)

    def test_parse_messages(self):
        messages = self.parser.parse_messages(SAMPLE_HTML, "tech_insights")
        self.assertEqual(len(messages), 2)

        # Message 1
        m1 = messages[0]
        self.assertEqual(m1.id, 101)
        self.assertEqual(m1.channel, "tech_insights")
        self.assertEqual(m1.views, 12500)
        self.assertEqual(m1.views_raw, "12.5K")
        self.assertTrue(m1.is_forward)
        self.assertEqual(m1.forwarded_from_title, "AI Source")
        self.assertIn("Breaking: New multimodal models", m1.text_clean)
        self.assertEqual(m1.paid_reactions, 250)
        self.assertEqual(m1.reactions.get("🔥"), 1200)
        self.assertEqual(m1.reactions.get("👍"), 850)
        self.assertEqual(m1.total_reactions, 250 + 1200 + 850)

        # Message 2 (Media only)
        m2 = messages[1]
        self.assertEqual(m2.id, 102)
        self.assertEqual(m2.text_clean, "")
        self.assertEqual(m2.media_type, "photo")
        self.assertEqual(len(m2.media), 1)
        self.assertEqual(m2.media[0].url, "https://cdn.example.com/photo1.jpg")
        self.assertEqual(m2.views, 5800000)

    def test_pagination_parsing(self):
        before_id, after_id = self.parser.parse_pagination(SAMPLE_HTML)
        self.assertEqual(before_id, 101)
        self.assertIsNone(after_id)

    def test_numeric_count_conversion(self):
        self.assertEqual(TelegramHTMLParser._parse_numeric_count("5.84M"), 5840000)
        self.assertEqual(TelegramHTMLParser._parse_numeric_count("12.3K"), 12300)
        self.assertEqual(TelegramHTMLParser._parse_numeric_count("950"), 950)
        self.assertEqual(TelegramHTMLParser._parse_numeric_count("1,234"), 1234)
        self.assertEqual(TelegramHTMLParser._parse_numeric_count(""), 0)


if __name__ == "__main__":
    unittest.main()
