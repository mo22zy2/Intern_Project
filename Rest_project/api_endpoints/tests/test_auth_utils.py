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
from api_endpoints.models import User


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
    @patch("api_endpoints.auth_utils.jwt.decode")
    def test_get_current_user_valid_token_returns_user(self, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user_id": 1}
        mock_db = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"

        result = get_current_user(credentials=mock_credentials, db=mock_db)

        assert result == mock_user
        mock_jwt_decode.assert_called_once_with(
            "valid_token", SECRET_KEY, algorithms=[ALGORITHM]
        )

    @patch("api_endpoints.auth_utils.jwt.decode")
    def test_get_current_user_invalid_token_raises(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = jwt.JWTError("bad token")
        mock_db = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "bad_token"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)
        assert exc_info.value.status_code == 401

    @patch("api_endpoints.auth_utils.jwt.decode")
    def test_get_current_user_missing_user_id_raises(self, mock_jwt_decode):
        mock_jwt_decode.return_value = {"sub": "123"}  # no user_id
        mock_db = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token_no_userid"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)
        assert exc_info.value.status_code == 401

    @patch("api_endpoints.auth_utils.jwt.decode")
    def test_get_current_user_user_not_found_raises(self, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user_id": 999}
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token_for_missing_user"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)
        assert exc_info.value.status_code == 401
