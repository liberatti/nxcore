#!/usr/bin/env python3
"""CLI test script for JWTManager.

Demonstrates and verifies:
1. Instantiation and token operations (encode/decode) completely outside of a Flask context.
2. Token operations within an active Flask application context using app.app_context().
"""

import sys

from nxcore.middleware.jwt_manager import JWTManager


def test_jwt_outside_flask():
    """Test JWTManager standalone execution (completely outside Flask)."""
    print("--- Running Test: JWTManager Standalone (Outside Flask) ---")

    # Instantiate JWTManager manually with custom parameters
    jwt_mgr = JWTManager()

    print(f"Configured Secret Key: {jwt_mgr.secret_key}")
    print(f"Configured Audience: {jwt_mgr.audience}")
    print(f"Configured Expiration (seconds): {jwt_mgr.expire_seconds}")
    print(f"Configured Algorithm: {jwt_mgr.algorithm}")

    # Generate an access token
    sub = "user_12345"
    profile = {
        "id": "12345",
        "username": "johndoe",
        "email": "johndoe@example.com",
        "role": "admin",
    }
    authorities = ["READ_PRIVILEGE", "WRITE_PRIVILEGE"]
    extra_claims = {"tenant_id": "tenant-xyz"}

    print("\nGenerating access token...")
    token = jwt_mgr.create_access_token(
        sub=sub, profile=profile, authorities=authorities, extra_claims=extra_claims
    )
    print(f"Generated Token: {token}")

    # Decode and verify the access token
    print("\nDecoding token...")
    decoded = jwt_mgr.decode(token)
    print(f"Decoded Payload: {decoded}")

    # Assertions
    assert decoded["sub"] == sub, f"Expected subject {sub}, got {decoded['sub']}"
    assert (
        decoded["aud"] == jwt_mgr.audience
    ), f"Expected audience {jwt_mgr.audience}, got {decoded['aud']}"
    assert decoded["profile"]["username"] == "johndoe", "Profile info mismatch"
    assert decoded["authorities"] == authorities, "Authorities mismatch"
    assert decoded["tenant_id"] == "tenant-xyz", "Extra claims mismatch"

    # Test refresh token
    print("\nGenerating refresh token...")
    refresh_token = jwt_mgr.create_refresh_token(sub=sub)
    print(f"Generated Refresh Token: {refresh_token}")

    decoded_refresh = jwt_mgr.decode(refresh_token)
    assert decoded_refresh["sub"] == sub
    assert decoded_refresh["aud"] == jwt_mgr.audience

    print("\n[SUCCESS] Standalone JWT token operations completed successfully!")


def test_jwt_inside_flask():
    """Test JWTManager dynamic lookup and configuration within active Flask app context."""
    print("\n--- Running Test: JWTManager within Flask App Context ---")
    try:
        from flask import Flask
    except ImportError:
        print(
            "[SKIP] Flask is not installed in the environment. Skipping Flask context test."
        )
        return

    # Create a Flask app and configure JWT parameters
    app = Flask("test_app")
    app.config["JWT_SECRET_KEY"] = "flask-app-context-secret-key"
    app.config["JWT_AUD"] = "flask-audience"
    app.config["JWT_EXPIRE"] = 600
    app.config["JWT_ALGORITHM"] = "HS256"

    # Initialize the extension
    JWTManager(app)

    # Use the app context to simulate an active request/context environment
    with app.app_context():
        # Retrieve the current manager dynamically from the application context
        current_jwt_mgr = JWTManager.get_current_instance()

        print(f"Active App Context Secret Key: {current_jwt_mgr.secret_key}")
        print(f"Active App Context Audience: {current_jwt_mgr.audience}")

        # Assert correct properties are resolved from app config
        assert current_jwt_mgr.secret_key == "flask-app-context-secret-key"
        assert current_jwt_mgr.audience == "flask-audience"
        assert current_jwt_mgr.expire_seconds == 600

        # Encode and decode in app context
        token = current_jwt_mgr.create_access_token(sub="flask_user_99")
        decoded = current_jwt_mgr.decode(token)
        print(f"Decoded Context Token Payload: {decoded}")

        assert decoded["sub"] == "flask_user_99"
        assert decoded["aud"] == "flask-audience"

    print("\n[SUCCESS] Flask-bound JWT token operations completed successfully!")


if __name__ == "__main__":
    try:
        test_jwt_outside_flask()
        test_jwt_inside_flask()
        print("\nAll JWT CLI tests passed successfully!")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during execution: {e}", file=sys.stderr)
        sys.exit(1)
