# /app/utils/signature.py
import base64
import hmac
import hashlib
import time
import random
import string
import json

def generate_signature(api_key: str, api_secret: str, path: str, body: dict) -> tuple[dict, str]:
    """
    Generates the required signature and headers for the multimodal API.
    """
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    timestamp = str(int(time.time()))
    
    # The body must be a string for the signature.
    # Ensure compact, sorted JSON for consistency.
    body_str = json.dumps(body, separators=(',', ':'), sort_keys=True)

    data_to_sign = f"{path}{body_str}{nonce}{timestamp}".encode('utf-8')
    
    signature_digest = hmac.new(
        api_secret.encode('utf-8'),
        data_to_sign,
        hashlib.sha256
    ).digest()
    
    signature = base64.b64encode(signature_digest).decode('utf-8')

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-OPENAPI-NONCE": nonce,
        "X-OPENAPI-TIMESTAMP": timestamp,
        "X-OPENAPI-SIGN": signature,
        "Content-Type": "application/json"
    }
    
    return headers, body_str
