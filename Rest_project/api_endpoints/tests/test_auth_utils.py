from datetime import timedelta, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt

from api_endpoints.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
)


class DoesNotExist(Exception):
    pass


class FakeUser:
    def __init__(self, id, is_active=True):
        self.id = id
        self.is_active = is_active


class FakeUserManager:
    def get(self, id):
        if id == 1:
            return FakeUser(1, is_active=True)
        if id == 2:
            return FakeUser(2, is_active=False)
        raise DoesNotExist


class FakeUserModel:
    DoesNotExist = DoesNotExist
    objects = FakeUserManager()


class TestHashPassword:
    def test_hash_password_returns_string(self):
        result = hash_password("testpass123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_password_different_each_time(self):
        pwd = "testpass123"
        hash1 = hash_password(pwd)
        hash2 = hash_password(pwd)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        pwd = "testpass123"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("testpass123")
        assert verify_password("wrongpass", hashed) is False


class TestCreateAccessToken:
    def test_create_access_token_returns_string(self):
        token = create_access_token({"user_id": 1})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_user_id(self):
        token = create_access_token({"user_id": 42})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 42

    def test_create_access_token_custom_expiry(self):
        custom_delta = timedelta(hours=1)
        token = create_access_token({"user_id": 1}, expires_delta=custom_delta)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        assert exp is not None
        expected_ts = (datetime.now(timezone.utc) + custom_delta).timestamp()
        assert abs(exp - expected_ts) < 5

    def test_create_access_token_can_be_decoded(self):
        token = create_access_token({"user_id": 99})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "user_id" in payload
        assert "exp" in payload
        assert payload["user_id"] == 99


class TestGetCurrentUser:
    @staticmethod
    def _credentials(token):
        creds = MagicMock()
        creds.credentials = token
        return creds

    @patch("api_endpoints.auth_utils._get_user_model")
    def test_get_current_user_valid_token_returns_user(self, mock_get_user_model):
        mock_get_user_model.return_value = FakeUserModel
        token = create_access_token({"user_id": 1})

        result = get_current_user(credentials=self._credentials(token))

        assert result.id == 1
        assert result.is_active is True

    def test_get_current_user_invalid_token_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=self._credentials("bad_token"))
        assert exc_info.value.status_code == 401

    @patch("api_endpoints.auth_utils._get_user_model")
    def test_get_current_user_missing_user_id_raises(self, mock_get_user_model):
        mock_get_user_model.return_value = FakeUserModel
        token = create_access_token({"sub": "123"})  # no user_id

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=self._credentials(token))
        assert exc_info.value.status_code == 401

    @patch("api_endpoints.auth_utils._get_user_model")
    def test_get_current_user_user_not_found_raises(self, mock_get_user_model):
        mock_get_user_model.return_value = FakeUserModel
        token = create_access_token({"user_id": 999})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=self._credentials(token))
        assert exc_info.value.status_code == 401

    @patch("api_endpoints.auth_utils._get_user_model")
    def test_get_current_user_inactive_user_raises(self, mock_get_user_model):
        mock_get_user_model.return_value = FakeUserModel
        token = create_access_token({"user_id": 2})  # user exists but is inactive

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=self._credentials(token))
        assert exc_info.value.status_code == 401
