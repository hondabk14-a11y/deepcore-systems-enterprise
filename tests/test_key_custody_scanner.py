"""Keep credential detection while avoiding expressions and cross-line matches."""
import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[1] / 'PRODUCTION-READINESS-GATES' / 'key-custody-check.py'
spec = importlib.util.spec_from_file_location('key_custody_check', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('text', [
    'OPENAI_API_KEY=\nDEEPCORE_AI_MODEL=example-model-name\n',
    'private_key: Ed25519PrivateKey',
    'private_key = Ed25519PrivateKey.generate()',
    'const apiKey = process.env.OPENAI_API_KEY || "";',
])
def test_nonliteral_values_are_not_credentials(text):
    assert not module.contains_secret(text, '.py')


@pytest.mark.parametrize('style,suffix', [('quoted', '.py'), ('env', '.example'), ('yaml', '.yml')])
def test_literal_credential_is_detected(style, suffix):
    # Construct synthetic detector input without embedding credential-shaped assignments.
    value = 'synthetic' * 4
    text = {'quoted': 'api_key = ' + repr(value),
            'env': 'OPENAI_API_KEY=' + value,
            'yaml': 'api_key: ' + value}[style]
    assert module.contains_secret(text, suffix)
