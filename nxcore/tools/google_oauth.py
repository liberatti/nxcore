from typing import Any, Dict, List, Optional

import jwt
import requests
from jwt.algorithms import RSAAlgorithm

from nxcore.middleware.logging_manager import logger


class GoogleOAuth:
    """OAuth2 handler for Google authentication."""

    SCOPE: List[str] = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
        "https://www.googleapis.com/auth/contacts",
    ]

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initializes GoogleOAuth client by fetching OpenID configuration metadata.

        Args:
            client_id (str): Google Client ID.
            client_secret (str): Google Client Secret.
            redirect_uri (str): Authorized redirect URI.
        """
        config_res = requests.get(
            "https://accounts.google.com/.well-known/openid-configuration"
        )
        self.config: Dict[str, Any] = config_res.json()
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__redirect_uri = redirect_uri

    def _get_cert(self, id_token_str: str) -> Optional[Dict[str, Any]]:
        """Retrieves matching JWK signature key from Google's certs endpoint.

        Args:
            id_token_str (str): Raw JWT token.

        Returns:
            dict or None: The JWK signature dictionary if found, otherwise None.
        """
        decoded_header = jwt.get_unverified_header(id_token_str)
        kid = decoded_header.get("kid")
        if not kid:
            return None
        response = requests.get(self.config["jwks_uri"])
        certs = response.json()
        for cert in certs.get("keys", []):
            if cert.get("kid") == kid:
                return cert
        return None

    def decode(self, id_token: str) -> Dict[str, Any]:
        """Decodes and validates a Google OpenID ID token.

        Args:
            id_token (str): Raw ID token.

        Returns:
            dict: The decoded token claims.
        """
        crt = self._get_cert(id_token)
        if not crt:
            raise ValueError("Matching signature key certificate not found.")
        rsa_key = RSAAlgorithm.from_jwk(crt)
        return jwt.decode(
            id_token, rsa_key, algorithms=[crt["alg"]], audience=self.__client_id
        )

    def is_valid(self, id_token_str: str) -> bool:
        """Checks if a Google ID token is valid.

        Args:
            id_token_str (str): Raw ID token string.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            self.decode(id_token_str)
            return True
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return False

    def tokeninfo(self, access_token: str) -> Dict[str, Any]:
        """Retrieves status and metadata information for a given access token.

        Args:
            access_token (str): The Google access token.

        Returns:
            dict: Token info response metadata.
        """
        user_info_url = f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_response.json()

    def user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetches profile information for the authenticated user.

        Args:
            access_token (str): The Google access token.

        Returns:
            dict: User profile info dictionary.
        """
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_response.json()

    def authorization_code(self, code: str) -> Dict[str, Any]:
        """Exchanges an authorization code for access and ID tokens.

        Args:
            code (str): Authorization code returned by Google OAuth.

        Returns:
            dict: Google API token response payload.
        """
        _headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "redirect_uri": self.__redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data, headers=_headers)
        return token_response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refreshes the access token using a Google refresh token.

        Args:
            refresh_token (str): The Google refresh token.

        Returns:
            dict: Refresh response payload.
        """
        _headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post(token_url, data=token_data, headers=_headers)
        return response.json()


# Backward compatibility alias
GoogleOauth = GoogleOAuth
