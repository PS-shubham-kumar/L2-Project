import unittest

from nlp.query_parser import QueryParser


class QueryParserTests(unittest.TestCase):
    def test_extracts_sections_and_entities(self):
        parser = QueryParser()
        query = "I'm leaving from Chicago. Give me today's weather and UV, quick news, commute advice, and a 10-minute breakfast idea with eggs."

        result = parser.parse(query)

        self.assertEqual(result["location"], "Chicago")
        self.assertIn("weather", result["sections"])
        self.assertIn("uv", result["sections"])
        self.assertIn("news", result["sections"])
        self.assertIn("commute", result["sections"])
        self.assertIn("breakfast", result["sections"])
        self.assertIn("eggs", result["ingredients"])
        self.assertEqual(result["time_constraint"], "10 minutes")
        self.assertIn("leaving", result["travel_intent"])


if __name__ == "__main__":
    unittest.main()
