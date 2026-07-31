from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import jwt

try:
    from flask import request, current_app, has_app_context
except Exception:
    request = None
    current_app = None

    def has_app_context():
        return False


import nxcore.config as base_config


class JWTManager:
    """Flask extension for managing JWT authentication and authorization."""

    def __init__(
        self,
        app: Optional[Any] = None,
        secret_key: Optional[str] = None,
        audience: Optional[str] = None,
        expire_seconds: Optional[int] = None,
        algorithm: Optional[str] = None,
    ):
        self.app = app
        self._secret_key = secret_key
        self._audience = audience
        self._expire_seconds = expire_seconds
        self._algorithm = algorithm
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Any) -> None:
        """Initializes the extension with the Flask application.

        Registers default configuration parameters and stores the extension
        instance on the app.
        """
        app.config.setdefault(
            "JWT_SECRET_KEY", base_config.get("JWT_SECRET_KEY", "dev")
        )
        app.config.setdefault("JWT_AUD", base_config.get("JWT_AUD", "app"))
        app.config.setdefault("JWT_EXPIRE", base_config.get("JWT_EXPIRE", 1800))
        app.config.setdefault(
            "JWT_ALGORITHM", base_config.get("JWT_ALGORITHM", "HS256")
        )

        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["jwt_manager"] = self

    @classmethod
    def get_current_instance(cls) -> "JWTManager":
        """Retrieves the JWTManager instance from the active Flask application context.

        Returns:
            JWTManager: The active JWTManager instance.

        Raises:
            RuntimeError: If called outside application context or extension is not initialized.
        """
        if not has_app_context():
            raise RuntimeError(
                "Working outside of application context. "
                "Make sure a Flask application is active or use app.app_context()."
            )
        if (
            not hasattr(current_app, "extensions")
            or "jwt_manager" not in current_app.extensions
        ):
            raise RuntimeError(
                "JWTManager has not been initialized on this Flask application."
            )
        return current_app.extensions["jwt_manager"]

    @property
    def secret_key(self) -> str:
        """Retrieves the JWT secret key from active app config or global config."""
        if self._secret_key is not None:
            return self._secret_key
        if has_app_context():
            val = current_app.config.get("JWT_SECRET_KEY")
            if val is not None:
                return str(val)
        return str(base_config.get("JWT_SECRET_KEY", "dev"))

    @property
    def audience(self) -> str:
        """Retrieves the JWT audience from active app config or global config."""
        if self._audience is not None:
            return self._audience
        if has_app_context():
            val = current_app.config.get("JWT_AUD")
            if val is not None:
                return str(val)
        return str(base_config.get("JWT_AUD", "app"))

    @property
    def expire_seconds(self) -> int:
        """Retrieves the JWT expiration duration in seconds."""
        if self._expire_seconds is not None:
            return self._expire_seconds
        if has_app_context():
            val = current_app.config.get("JWT_EXPIRE")
            if val is not None:
                return int(val)
        return int(base_config.get("JWT_EXPIRE", 1800))

    @property
    def algorithm(self) -> str:
        """Retrieves the JWT hashing algorithm."""
        if self._algorithm is not None:
            return self._algorithm
        if has_app_context():
            val = current_app.config.get("JWT_ALGORITHM")
            if val is not None:
                return str(val)
        return "HS256"

    def normalize_token(self, t: str) -> str:
        """Normalizes the Authorization header token string.

        Removes leading/trailing whitespace, strips 'Bearer ' prefix,
        and validates JWT format structure.

        Args:
            t (str): Raw token string.

        Returns:
            str: Normalized token string.
        """
        if not t:
            raise Exception("Missing token")

        token = t.strip()

        if token.startswith("Bearer "):
            token = token[7:]

        if token.count(".") != 2:
            raise Exception(f"JWT malformed: {repr(token)}")

        return token

    def get_token_from_request(self) -> Optional[str]:
        """Extracts and normalizes the Authorization JWT token from request headers.

        Returns:
            str or None: Normalized token if present, else None.
        """
        token = request.headers.get("Authorization", None)
        if token:
            return self.normalize_token(token)
        return None

    def get_refresh_token_from_request(self) -> Optional[str]:
        """Extracts and normalizes the Refresh-Token JWT from request headers.

        Returns:
            str or None: Normalized refresh token if present, else None.
        """
        token = request.headers.get("Refresh-Token", None)
        if token:
            return self.normalize_token(token)
        return None

    def decode(self, token: str) -> Dict[str, Any]:
        """Decodes a JWT token using configured secret key and audience.

        Args:
            token (str): The JWT token to decode.

        Returns:
            dict: The decoded payload.
        """
        return jwt.decode(
            token, self.secret_key, algorithms=[self.algorithm], audience=self.audience
        )

    def create_access_token(
        self,
        sub: Any,
        profile: Optional[Dict[str, Any]] = None,
        authorities: Optional[List[str]] = None,
        extra_claims: Optional[Dict[str, Any]] = None,
        extra_clains: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates a new access token (JWT) for a subject.

        Args:
            sub (any): The subject of the token (e.g., user ID).
            profile (dict, optional): User profile dictionary. Defaults to None.
            authorities (list, optional): List of user authorities. Defaults to None.
            extra_claims (dict, optional): Additional custom claims to include. Defaults to None.
            extra_clains (dict, optional): Legacy alias for extra_claims. Defaults to None.

        Returns:
            str: The encoded JWT string.
        """
        now = datetime.now(base_config.get("TZ"))
        if profile:
            profile = profile.copy()
            profile.pop("created_at", None)
            profile.pop("updated_at", None)
            profile.pop("password", None)
        payload = {
            "exp": int((now + timedelta(seconds=self.expire_seconds)).timestamp()),
            "iat": int(now.timestamp()),
            "sub": str(sub),
            "profile": profile,
            "authorities": authorities,
            "aud": self.audience,
        }
        claims = extra_claims if extra_claims is not None else extra_clains
        if claims:
            payload.update(claims)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, sub: Any) -> str:
        """Generates a new refresh token (JWT) for a subject, valid for 24 hours.

        Args:
            sub (any): The subject of the token (e.g., user ID).

        Returns:
            str: The encoded refresh JWT string.
        """
        now = datetime.now(base_config.get("TZ")) + timedelta(hours=24)
        payload = {"exp": int(now.timestamp()), "sub": str(sub), "aud": self.audience}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def get_principal(self) -> Dict[str, Any]:
        """Retrieves the profile of the user from the JWT token in the request header.

        Returns:
            dict: The user profile dictionary, or an empty dict if not found.
        """
        token = self.get_token_from_request()
        if token:
            return self.decode(token).get("profile", {}) or {}
        return {}
