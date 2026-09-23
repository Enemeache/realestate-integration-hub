"""Verificación de firma HMAC para el webhook, como hacen los portales reales
(ZonaProp, Mercado Libre, Stripe, etc.): el emisor firma el body crudo con un
secreto compartido y lo manda en un header; nosotros recalculamos la firma y
comparamos en tiempo constante para evitar timing attacks.
"""
import hashlib
import hmac


def compute_signature(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_signature(secret: str, payload: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = compute_signature(secret, payload)
    return hmac.compare_digest(expected, signature)
