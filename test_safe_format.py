import unittest
from utils import safe_format

class TestSafeFormat(unittest.TestCase):
    def test_safe_format_basic(self):
        template = "Hello {name}!"
        result = safe_format(template, name="Alice")
        self.assertEqual(result, "Hello Alice!")

    def test_safe_format_missing_keys(self):
        template = "Hello {name}! Your age is {age}."
        result = safe_format(template, name="Alice")
        self.assertEqual(result, "Hello Alice! Your age is {age}.")

    def test_safe_format_extra_keys(self):
        template = "Hello {name}!"
        result = safe_format(template, name="Alice", age=30)
        self.assertEqual(result, "Hello Alice!")

    def test_safe_format_missing_key_with_format_spec(self):
        template = "Rating is {rating:.1f}, missing is {missing:.2f}"
        result = safe_format(template, rating=4.56)
        self.assertEqual(result, "Rating is 4.6, missing is {missing}")

    def test_safe_format_malformed_braces(self):
        template = "Hello {name! Your age is {age}."
        result = safe_format(template, name="Alice", age=30)
        # Malformed template should fall back to returning template
        self.assertEqual(result, template)

    def test_settings_merging_logic(self):
        # Emulate Database.get_settings merging logic
        default_setgs = {
            'template': 'default',
            'tutorial': 't_default',
            'tutorial_name': 'tn_default',
            'links': True
        }
        
        # Scenario 1: Chat exists but has outdated settings document (missing 'tutorial_name')
        chat_db_settings = {
            'template': 'custom',
            'tutorial': 't_custom',
            'links': False
        }
        
        merged = default_setgs.copy()
        merged.update(chat_db_settings)
        
        self.assertEqual(merged['template'], 'custom')
        self.assertEqual(merged['tutorial'], 't_custom')
        self.assertEqual(merged['tutorial_name'], 'tn_default')
        self.assertEqual(merged['links'], False)

if __name__ == "__main__":
    unittest.main()
