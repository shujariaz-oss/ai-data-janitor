"""Unit tests for security utilities."""
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    encrypt_value,
    decrypt_value,
    hash_password,
    verify_password,
    verify_webhook_signature,
    generate_webhook_signature,
    mask_pii,
)


class TestSecurity:
    def test_password_hashing(self):
        hashed = hash_password("supersecret")
        assert verify_password("supersecret", hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_jwt_roundtrip(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"

    def test_jwt_invalid(self):
        assert decode_access_token("bad.token.here") is None

    def test_encryption_roundtrip(self):
        original = "my-secret-oauth-token"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_webhook_signature(self):
        payload = b'{"event": "test"}'
        secret = "whsec_test"
        sig = generate_webhook_signature(payload, secret)
        assert verify_webhook_signature(payload, sig, secret) is True
        assert verify_webhook_signature(payload, "wrong", secret) is False

    def test_mask_pii(self):
        assert mask_pii("alice@example.com") == "al****om"
        assert mask_pii("+14155552671") == "+1****71"
        assert mask_pii("hi") == "****"
