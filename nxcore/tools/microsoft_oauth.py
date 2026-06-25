from typing import Any, Dict, List, Optional

import requests

from nxcore.middleware.logging_manager import logger


class MicrosoftOAuth:
    """OAuth2 handler for Microsoft authentication."""

    SCOPE: List[str] = [
        "https://graph.microsoft.com/Chat.Read.All",
        "https://graph.microsoft.com/Contacts.Read",
        "https://graph.microsoft.com/User.Read.All",
        "https://graph.microsoft.com/People.Read.All",
        "https://graph.microsoft.com/Directory.Read.All",
        "offline_access",
    ]

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initializes MicrosoftOAuth client credentials.

        Args:
            client_id (str): Microsoft Client ID.
            client_secret (str): Microsoft Client Secret.
            redirect_uri (str): Authorized redirect URI.
        """
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__redirect_uri = redirect_uri

        self.authority: str = "https://login.microsoftonline.com/common"
        self.scope: List[str] = MicrosoftOAuth.SCOPE

    def tokeninfo(self, access_token: str) -> Dict[str, Any]:
        """Retrieves user profile metadata from Microsoft Graph.

        Args:
            access_token (str): Microsoft Graph access token.

        Returns:
            dict: The response payload.
        """
        user_info_url = "https://graph.microsoft.com/v1.0/me"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_response.json()

    def user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetches profile information for the authenticated user.

        Args:
            access_token (str): Microsoft Graph access token.

        Returns:
            dict: User profile info dictionary.
        """
        user_info_url = "https://graph.microsoft.com/v1.0/me"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_response.json()

    def authorization_code(self, code: str) -> Dict[str, Any]:
        """Exchanges an authorization code for Microsoft Graph tokens.

        Args:
            code (str): Authorization code returned by Microsoft OAuth.

        Returns:
            dict: The token response payload.
        """
        token_url = f"{self.authority}/oauth2/v2.0/token"
        token_data = {
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "code": code,
            "redirect_uri": self.__redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        return token_response.json()

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh the access token using the refresh token.

        Args:
            refresh_token (str): The Microsoft refresh token.

        Returns:
            dict or None: Token response payload if successful, otherwise None.
        """
        try:
            token_url = f"{self.authority}/oauth2/v2.0/token"
            token_data = {
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(self.scope),
            }
            response = requests.post(token_url, data=token_data)
            if response.status_code != 200:
                logger.error(
                    f"Token refresh failed with status code {response.status_code}: {response.text}"
                )
                return None

            token_info = response.json()
            if "access_token" not in token_info:
                logger.error("No access token in refresh response")
                return None

            return token_info

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None

    def is_valid(self, access_token: str) -> bool:
        """Validate if the access token is valid by making a test request to Microsoft Graph API.

        Args:
            access_token (str): Access token to validate.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        try:
            if not access_token:
                logger.error("Access token is empty or None")
                return False

            test_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(test_url, headers=headers)
            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Access token validation failed with status code: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Access token validation failed: {str(e)}")
            return False
