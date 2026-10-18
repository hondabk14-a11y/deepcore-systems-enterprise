import unittest
from tracked_secret_check import findings


class SecretChecks(unittest.TestCase):
    def test_empty_environment_template_allowed(self):
        self.assertEqual(findings("app/.env.example", "OPENAI_API_KEY=\nDEEPCORE_AI_MODEL=gpt-6-astra\n"), [])
        self.assertEqual(findings("app/.env.example", 'OPENAI_API_KEY=""\n'), [])

    def test_populated_environment_template_rejected(self):
        self.assertTrue(findings("app/.env.example", "OPENAI_API_KEY=example-value\n"))

    def test_other_environment_paths_and_keys_rejected(self):
        for path in (".env", "app/.env.production", "app/private.pem", "secrets/data.txt"):
            self.assertTrue(findings(path, ""))

    def test_private_material_rejected_in_any_file(self):
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        self.assertTrue(findings("config.txt", marker))

    def test_code_expression_is_not_literal_secret(self):
        self.assertEqual(findings("key.py", "private_key = Ed25519PrivateKey.generate()"), [])

    def test_literal_secret_rejected_without_disclosing_value(self):
        issues = findings("config.py", 'password = "' + "s" * 32 + '"')
        self.assertTrue(issues)
        self.assertNotIn("s" * 32, repr(issues))
