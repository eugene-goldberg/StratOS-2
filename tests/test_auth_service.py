import pytest
import pytest_asyncio
from uuid import uuid4 # uuid7 from uuid_extensions was not used

from fastapi import HTTPException, status
from jose import jwt

from backend.services.auth_service import AuthService
from backend.models.user import UserCreate, UserUpdate, TokenData
from backend.core.config import settings # For JWT settings

# Mock settings for JWT if they are not easily accessible or to ensure test consistency
# This might require adjusting how settings are loaded in AuthService or mocking them via monkeypatch
MOCK_SECRET_KEY = "test_secret_key_for_auth_service"
MOCK_ALGORITHM = "HS256"
MOCK_ACCESS_TOKEN_EXPIRE_MINUTES = 30

@pytest_asyncio.fixture
async def auth_service(monkeypatch):
    # Monkeypatch settings used by AuthService for JWT
    monkeypatch.setattr(settings, 'SECRET_KEY', MOCK_SECRET_KEY)
    monkeypatch.setattr(settings, 'ALGORITHM', MOCK_ALGORITHM)
    monkeypatch.setattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', MOCK_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    service = AuthService()
    # Ensure in-memory cache is used for tests
    service.cosmos_db_available = False 
    service.users_cache = {} # Reset cache for each test
    return service

@pytest.mark.asyncio
async def test_create_user_success(auth_service: AuthService):
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        company_name="Test Inc.",
        job_title="Tester"
    )
    created_user = await auth_service.create_user(user_data)
    
    assert created_user is not None
    assert created_user.email == user_data.email
    assert created_user.full_name == user_data.full_name
    assert created_user.is_active is True
    assert auth_service.verify_password(user_data.password, created_user.hashed_password)
    
    # Verify user is in cache
    assert str(created_user.id) in auth_service.users_cache

@pytest.mark.asyncio
async def test_create_user_duplicate_email(auth_service: AuthService):
    user_data = UserCreate(email="test@example.com", password="password123")
    await auth_service.create_user(user_data) # Create first user
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.create_user(user_data) # Attempt to create duplicate
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in exc_info.value.detail

@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service: AuthService):
    user_data = UserCreate(email="auth_user@example.com", password="password123")
    await auth_service.create_user(user_data)
    
    authenticated_user = await auth_service.authenticate_user(user_data.email, user_data.password)
    assert authenticated_user is not None
    assert authenticated_user.email == user_data.email

@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(auth_service: AuthService):
    user_data = UserCreate(email="auth_user_wp@example.com", password="password123")
    await auth_service.create_user(user_data)
    
    authenticated_user = await auth_service.authenticate_user(user_data.email, "wrongpassword")
    assert authenticated_user is None

@pytest.mark.asyncio
async def test_authenticate_user_not_found(auth_service: AuthService):
    authenticated_user = await auth_service.authenticate_user("nonexistent@example.com", "password")
    assert authenticated_user is None

@pytest.mark.asyncio
async def test_get_user_by_email(auth_service: AuthService):
    user_data = UserCreate(email="get_user@example.com", password="password123")
    created_user = await auth_service.create_user(user_data)
    
    fetched_user = await auth_service.get_user_by_email(created_user.email)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id

@pytest.mark.asyncio
async def test_get_user_by_id(auth_service: AuthService):
    user_data = UserCreate(email="get_user_id@example.com", password="password123")
    created_user = await auth_service.create_user(user_data)
    
    fetched_user = await auth_service.get_user_by_id(created_user.id)
    assert fetched_user is not None
    assert fetched_user.email == created_user.email

@pytest.mark.asyncio
async def test_create_and_decode_access_token(auth_service: AuthService):
    user_id = uuid4()
    email = "token_user@example.com"
    token_data_payload = {"sub": str(user_id), "email": email}
    
    token = auth_service.create_access_token(data=token_data_payload)
    assert token is not None
    
    decoded_token_data = auth_service.decode_token(token)
    assert decoded_token_data.user_id == user_id
    assert decoded_token_data.email == email

@pytest.mark.asyncio
async def test_decode_invalid_token(auth_service: AuthService):
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decode_token("invalidtokenstring")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_update_user_profile(auth_service: AuthService):
    user_data = UserCreate(email="update_user@example.com", password="password123", full_name="Original Name")
    created_user = await auth_service.create_user(user_data)
    
    update_payload = UserUpdate(full_name="Updated Name", job_title="Senior Tester")
    updated_user = await auth_service.update_user(created_user.id, update_payload)
    
    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.job_title == "Senior Tester"
    assert updated_user.email == created_user.email # Email should not change here
    assert updated_user.updated_at > created_user.updated_at

@pytest.mark.asyncio
async def test_update_user_password(auth_service: AuthService):
    user_data = UserCreate(email="update_pw@example.com", password="oldpassword")
    created_user = await auth_service.create_user(user_data)
    
    update_payload = UserUpdate(password="newpassword")
    updated_user = await auth_service.update_user(created_user.id, update_payload)
    
    assert updated_user is not None
    assert auth_service.verify_password("newpassword", updated_user.hashed_password)
    assert not auth_service.verify_password("oldpassword", updated_user.hashed_password)

    # Authenticate with new password
    re_authenticated_user = await auth_service.authenticate_user(updated_user.email, "newpassword")
    assert re_authenticated_user is not None
    assert re_authenticated_user.id == created_user.id

@pytest.mark.asyncio
async def test_update_nonexistent_user(auth_service: AuthService):
    non_existent_id = uuid4()
    update_payload = UserUpdate(full_name="Ghost User")
    updated_user = await auth_service.update_user(non_existent_id, update_payload)
    assert updated_user is None
