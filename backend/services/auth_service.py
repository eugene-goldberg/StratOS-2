import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from uuid import UUID

# Use azure.cosmos.aio for asynchronous operations
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions # Keep sync exceptions for now
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from ..models.user import UserBase, UserCreate, UserUpdate, UserInDB, UserResponse, TokenData
from ..core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for authentication and user management"""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("auth_service")
        
        # In-memory storage (used as cache and fallback)
        self.users_cache = {} # UserInDB objects keyed by str(user_id)
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.cosmos_client: Optional[AsyncCosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.users_container: Optional[ContainerProxy] = None
        
        # Cosmos DB connection details from environment variables
        self.cosmos_endpoint = settings.AZURE_COSMOS_ENDPOINT
        self.cosmos_key = settings.AZURE_COSMOS_KEY
        self.cosmos_database_name = settings.AZURE_COSMOS_DATABASE_NAME

        self._initialize_cosmos_db_sync()

    def _initialize_cosmos_db_sync(self):
        """Synchronous part of Cosmos DB initialization for async client."""
        if not self.cosmos_endpoint or not self.cosmos_key:
            self.logger.warning("Cosmos DB credentials not found. Using in-memory storage.")
            return

        try:
            self.cosmos_client = AsyncCosmosClient(url=self.cosmos_endpoint, credential=self.cosmos_key)
            self.database = self.cosmos_client.get_database_client(self.cosmos_database_name)
            self.users_container = self.database.get_container_client("Users")
            
            # Ideally, container creation (if needed) should be an async app startup task.
            # Example:
            # async def ensure_users_container():
            #     try:
            #         await self.database.create_container_if_not_exists(
            #             id="Users", partition_key=PartitionKey(path="/email"), offer_throughput=400
            #         )
            #         self.logger.info("Users container ensured.")
            #     except Exception as e:
            #         self.logger.error(f"Failed to ensure Users container: {e}")
            # asyncio.run(ensure_users_container()) # This is problematic in __init__

            self.cosmos_db_available = True
            self.logger.info("Cosmos DB async client initialized (proxies ready).")
        except Exception as e:
            self.logger.warning(f"Cosmos DB async client initialization failed: {str(e)}. Using in-memory storage.")
            self.cosmos_db_available = False
            self.cosmos_client = None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate a password hash"""
        return pwd_context.hash(password)
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get a user by email (partition key)."""
        # Try from memory first (simple cache)
        for user_in_cache in self.users_cache.values():
            if user_in_cache.email == email:
                return user_in_cache

        if self.cosmos_db_available and self.users_container:
            try:
                # Read item directly using email as item id and partition key
                # This assumes 'id' field in Cosmos is the email for Users container
                # If 'id' is a UUID, then query is needed.
                # Based on PartitionKey(path="/email"), email is the PK.
                # Cosmos DB items have an 'id' property. If this 'id' is set to the email,
                # then read_item is efficient. Otherwise, a query is needed.
                # Let's assume 'id' in Cosmos is the email for this container.
                # If not, this needs to be a query:
                # query = "SELECT * FROM c WHERE c.email = @email"
                # params = [{"name": "@email", "value": email}]
                # items = []
                # async for item_data in self.users_container.query_items(query=query, parameters=params, partition_key=email):
                #    items.append(item_data)
                # if items: ...
                
                # Assuming the item 'id' in Cosmos is the email for this specific container setup
                item_data = await self.users_container.read_item(item=email, partition_key=email)
                
                # Convert string ID to UUID if your UserInDB model expects UUID for 'id' field
                # but the actual 'id' in Cosmos for Users is the email.
                # This part depends on how UserInDB model and Cosmos data are structured.
                # If UserInDB.id is UUID, but Cosmos 'id' is email, we need to map.
                # For now, let's assume UserInDB can handle 'id' being email or a separate UUID field.
                # If UserInDB.id must be UUID, and Cosmos 'id' is email, then UserInDB needs an email field
                # and its 'id' field should be populated from a separate 'user_uuid' field in Cosmos.
                
                # Let's assume the item_data has a UUID 'id' field and an 'email' field.
                if 'id' in item_data and isinstance(item_data['id'], str):
                    item_data['id'] = UUID(item_data['id']) # Convert if 'id' is UUID stored as string
                
                user = UserInDB(**item_data)
                self.users_cache[str(user.id)] = user # Cache by UUID
                return user
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error retrieving user by email '{email}' from Cosmos DB: {str(e)}")
        
        return None # Fallback if not found or DB error
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        """Get a user by their UUID."""
        if str(user_id) in self.users_cache:
            return self.users_cache[str(user_id)]

        if self.cosmos_db_available and self.users_container:
            try:
                # Query for the user by UUID (this will be a cross-partition query if 'id' is not email)
                query = "SELECT * FROM c WHERE c.id = @id" # Assuming 'id' field in Cosmos stores the UUID
                params = [{"name": "@id", "value": str(user_id)}]
                
                items = []
                async for item_data in self.users_container.query_items(
                    query=query, parameters=params, enable_cross_partition_query=True
                ):
                    if 'id' in item_data and isinstance(item_data['id'], str):
                         item_data['id'] = UUID(item_data['id'])
                    items.append(UserInDB(**item_data))
                
                if items:
                    user = items[0]
                    self.users_cache[str(user.id)] = user
                    return user
            except Exception as e:
                self.logger.error(f"Error retrieving user by ID '{user_id}' from Cosmos DB: {str(e)}")
        
        return None
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user."""
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        hashed_password = self.get_password_hash(user_data.password)
        current_time = datetime.now()
        
        # UserInDB model should have an 'id' field of type UUID, default_factory=uuid.uuid4
        # and all other fields.
        user_in_db = UserInDB(
            # id will be auto-generated by UserInDB model if default_factory=uuid.uuid4
            email=user_data.email,
            full_name=user_data.full_name,
            company_name=user_data.company_name,
            job_title=user_data.job_title,
            hashed_password=hashed_password,
            created_at=current_time,
            updated_at=current_time
        )
        
        user_dict_for_db = user_in_db.dict()
        # Ensure 'id' (UUID) is string for Cosmos, and 'email' is present for partition key.
        user_dict_for_db["id"] = str(user_in_db.id) 
        # The 'email' field itself is the partition key value.
        # If Cosmos item 'id' must be unique and is different from email,
        # then the item 'id' for Cosmos could be user_in_db.email or user_in_db.id (as string).
        # Let's assume the Cosmos item 'id' is set to the email for Users container.
        # This means the document in Cosmos will have its 'id' field as the email.
        # And a separate field, say 'user_uuid', will store str(user_in_db.id).
        # Or, if UserInDB.id is the primary unique ID, and email is just PK,
        # then the document 'id' in Cosmos is str(user_in_db.id).

        # Assuming document 'id' in Cosmos is the user's email for this container
        # and UserInDB.id is a separate UUID.
        # This requires UserInDB model to be flexible or Cosmos document to have both.
        # For simplicity with PartitionKey(path="/email"), we'll make the Cosmos document 'id' the email.
        # This means UserInDB.id (UUID) is stored as a separate field, e.g., 'user_uuid'.
        
        # Revised approach: UserInDB.id is the UUID. Cosmos document 'id' is also this UUID as string.
        # Email is the partition key.
        
        if self.cosmos_db_available and self.users_container:
            try:
                await self.users_container.create_item(body=user_dict_for_db)
                self.logger.info(f"Created user {user_in_db.email} (ID: {user_in_db.id}) in Cosmos DB")
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error creating user in Cosmos DB: {str(e)}")
                self.users_cache[str(user_in_db.id)] = user_in_db # Fallback
                return user_in_db # Return even on DB error if cached
            except Exception as e: # Catch other potential errors
                self.logger.error(f"Unexpected error creating user in Cosmos DB: {str(e)}")
                self.users_cache[str(user_in_db.id)] = user_in_db
                return user_in_db
        else:
            self.users_cache[str(user_in_db.id)] = user_in_db
            self.logger.info(f"Created user {user_in_db.email} (ID: {user_in_db.id}) in memory")
        
        return user_in_db
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user."""
        user = await self.get_user_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire_time = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire_time})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        return self.create_access_token(data, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id_str: Optional[str] = payload.get("sub")
            email_str: Optional[str] = payload.get("email")
            if user_id_str is None or email_str is None:
                raise credentials_exception
            return TokenData(user_id=UUID(user_id_str), email=email_str)
        except JWTError:
            raise credentials_exception
        
    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[UserInDB]:
        """Update a user's information."""
        existing_user = await self.get_user_by_id(user_id)
        if not existing_user:
            return None

        update_data_dict = user_update.dict(exclude_unset=True)
        if "password" in update_data_dict and update_data_dict["password"]:
            update_data_dict["hashed_password"] = self.get_password_hash(update_data_dict.pop("password"))
        
        # Create a new UserInDB instance with updated fields
        # This ensures that Pydantic model validation is applied
        updated_user_model_data = existing_user.dict()
        updated_user_model_data.update(update_data_dict)
        updated_user_model_data["updated_at"] = datetime.now()
        
        # Ensure 'id' is not changed by update_data_dict if it was accidentally included
        updated_user_model_data['id'] = existing_user.id 
        
        updated_user = UserInDB(**updated_user_model_data)

        # Prepare dict for Cosmos DB, ensuring 'id' is string
        user_dict_for_db = updated_user.dict()
        user_dict_for_db["id"] = str(updated_user.id)
        # Email (partition key) should not change, it's taken from existing_user.email

        if self.cosmos_db_available and self.users_container:
            try:
                # Replace item using its 'id' (which is the UUID as string) and partition_key (email)
                await self.users_container.replace_item(
                    item=user_dict_for_db["id"], # The 'id' of the document in Cosmos
                    body=user_dict_for_db,
                    partition_key=existing_user.email # Crucial: use the email as partition key
                )
                self.logger.info(f"Updated user {updated_user.email} (ID: {updated_user.id}) in Cosmos DB")
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error updating user in Cosmos DB: {str(e)}")
                self.users_cache[str(user_id)] = updated_user # Fallback
                return updated_user # Return even on DB error if cached
            except Exception as e:
                self.logger.error(f"Unexpected error updating user in Cosmos DB: {str(e)}")
                self.users_cache[str(user_id)] = updated_user
                return updated_user
        else:
            self.users_cache[str(user_id)] = updated_user
            self.logger.info(f"Updated user {updated_user.email} (ID: {updated_user.id}) in memory")
        
        return updated_user
