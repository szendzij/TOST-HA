"""Tesla OAuth2 authentication utilities (non-interactive version for HA)."""

import os
import base64
import hashlib
import json
import time
import urllib.parse
from typing import Optional, Tuple
from pathlib import Path

# Import connection module - will be adapted for HA
try:
    from app.utils.connection import request_with_retry
except ImportError:
    # Fallback for when used outside app context
    import requests
    
    def request_with_retry(url, headers=None, data=None, json=None, max_retries=3, exit_on_error=True):
        """Fallback request function."""
        for attempt in range(max_retries):
            try:
                if data is None and json is None:
                    response = requests.get(url, headers=headers)
                else:
                    if json is not None:
                        response = requests.post(url, headers=headers, json=json)
                    else:
                        if isinstance(data, (dict, list)):
                            import json as jsonlib
                            response = requests.post(
                                url,
                                headers={"Content-Type": "application/json", **(headers or {})},
                                data=jsonlib.dumps(data, separators=(",", ":")),
                            )
                        else:
                            response = requests.post(url, headers=headers, data=data)
                
                response.raise_for_status()
                return response
            except Exception:
                if attempt == max_retries - 1:
                    if exit_on_error:
                        raise RuntimeError(f"Request failed after {max_retries} attempts")
                    raise
                time.sleep(2 ** attempt)
        return None

CLIENT_ID = 'ownerapi'
REDIRECT_URI = 'https://auth.tesla.com/void/callback'
AUTH_URL = 'https://auth.tesla.com/oauth2/v3/authorize'
TOKEN_URL = 'https://auth.tesla.com/oauth2/v3/token'
SCOPE = 'openid email offline_access'
CODE_CHALLENGE_METHOD = 'S256'


def generate_code_verifier_and_challenge() -> Tuple[str, str]:
    """Generate code verifier and challenge for OAuth2 PKCE flow.
    
    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).rstrip(
        b'=').decode('utf-8')
    return code_verifier, code_challenge


def get_auth_url(code_challenge: str, state: Optional[str] = None) -> str:
    """Generate authorization URL for OAuth2 flow.
    
    Args:
        code_challenge: PKCE code challenge
        state: Optional state parameter (will be generated if not provided)
    
    Returns:
        Authorization URL string
    """
    if state is None:
        state = os.urandom(16).hex()
    
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': SCOPE,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': CODE_CHALLENGE_METHOD,
    }
    
    return f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"


def extract_auth_code_from_url(redirected_url: str) -> str:
    """Extract authorization code from redirect URL.
    
    Args:
        redirected_url: The full URL from Tesla redirect
    
    Returns:
        Authorization code string
    
    Raises:
        ValueError: If no code found in URL
    """
    parsed_url = urllib.parse.urlparse(redirected_url)
    params = urllib.parse.parse_qs(parsed_url.query)
    code = params.get('code')
    if not code:
        raise ValueError("No authentication code found in the redirected URL.")
    return code[0]


def exchange_code_for_tokens(auth_code: str, code_verifier: str) -> dict:
    """Exchange authorization code for access and refresh tokens.
    
    Args:
        auth_code: Authorization code from redirect
        code_verifier: PKCE code verifier
    
    Returns:
        Dictionary containing tokens and other OAuth2 response data
    """
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier,
    }
    response = request_with_retry(TOKEN_URL, None, token_data, exit_on_error=False)
    if response is None:
        raise RuntimeError("Failed to exchange code for tokens")
    return response.json()


def is_token_valid(access_token: str) -> bool:
    """Check if access token is still valid.
    
    Args:
        access_token: JWT access token
    
    Returns:
        True if token is valid, False otherwise
    """
    try:
        jwt_decoded = json.loads(base64.b64decode(access_token.split('.')[1] + '==').decode('utf-8'))
        return jwt_decoded.get('exp', 0) > time.time()
    except Exception:
        return False


def refresh_tokens(refresh_token: str) -> dict:
    """Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token from previous authentication
    
    Returns:
        Dictionary containing new tokens
    """
    token_data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'refresh_token': refresh_token,
    }
    response = request_with_retry(TOKEN_URL, None, token_data, exit_on_error=False)
    if response is None:
        raise RuntimeError("Failed to refresh tokens")
    return response.json()


def save_tokens_to_file(tokens: dict, token_file_path: Path) -> None:
    """Save tokens to file.
    
    Args:
        tokens: Dictionary containing tokens
        token_file_path: Path to token file
    """
    token_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file_path, 'w') as f:
        json.dump(tokens, f)


def load_tokens_from_file(token_file_path: Path) -> Optional[dict]:
    """Load tokens from file.
    
    Args:
        token_file_path: Path to token file
    
    Returns:
        Dictionary containing tokens or None if file doesn't exist
    """
    if not token_file_path.exists():
        return None
    try:
        with open(token_file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


# Legacy function names for backward compatibility (if needed)
_generate_code_verifier_and_challenge = generate_code_verifier_and_challenge
_exchange_code_for_tokens = exchange_code_for_tokens
_is_token_valid = is_token_valid
_refresh_tokens = refresh_tokens
_save_tokens_to_file = save_tokens_to_file
_load_tokens_from_file = load_tokens_from_file