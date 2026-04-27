import jwt
import requests
from jwt.algorithms import RSAAlgorithm

from nxcore.middleware.logging import logger


class GoogleOauth:
    SCOPE = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
        "https://www.googleapis.com/auth/contacts",
    ]

    def __init__(self, client_id, client_secret, redirect_uri):
        config_res = requests.get(
            "https://accounts.google.com/.well-known/openid-configuration"
        )
        self.config = config_res.json()
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__redirect_uri = redirect_uri

    def _get_cert(self, id_token_str):
        # header, payload, signature = id_token_str.split('.')
        decoded_header = jwt.get_unverified_header(id_token_str)
        kid = decoded_header["kid"]
        response = requests.get(self.config["jwks_uri"])
        certs = response.json()
        kid = decoded_header["kid"]
        for cert in certs["keys"]:
            if cert["kid"] == kid:
                return cert
        return None

    def decode(self, id_token):
        crt = self._get_cert(id_token)
        rsa_key = RSAAlgorithm.from_jwk(crt)
        return jwt.decode(
            id_token, rsa_key, algorithms=[crt["alg"]], audience=self.__client_id
        )

    def is_valid(self, id_token_str):
        try:
            self.decode(id_token_str)
            return True
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return False

    def tokeninfo(self, access_token):
        user_info_url = f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_response.json()

    def user_info(self, access_token):
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_response.json()

    def authorization_code(self, code):
        _headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_data = None
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "redirect_uri": self.__redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data, headers=_headers)
        token_json = token_response.json()
        return token_json

    def refresh_access_token(self, refresh_token):
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
