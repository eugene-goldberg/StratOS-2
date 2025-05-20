import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from uuid import UUID

from azure.cosmos import CosmosClient, PartitionKey, exceptions
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
        self.users_cache = {}
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.database = None
        self.users_container = None
        
        # Try to initialize Cosmos DB connection
        try:
            # Get Cosmos DB connection details from environment variables
            cosmos_endpoint = settings.AZURE_COSMOS_ENDPOINT
            cosmos_key = settings.AZURE_COSMOS_KEY
            cosmos_database_name = settings.AZURE_COSMOS_DATABASE_NAME
            
            if not cosmos_endpoint or not cosmos_key:
                self.logger.warning("Cosmos DB credentials not found in environment variables. Using in-memory storage.")
                return
            
            # Initialize Cosmos DB client
            self.cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
            
            # Get or create database
            self.database = self.cosmos_client.get_database_client(cosmos_database_name)
            
            # Get or create container for users
            try:
                self.users_container = self.database.get_container_client("Users")
                self.logger.info("Connected to existing Cosmos DB Users container")
            except exceptions.CosmosResourceNotFoundError:
                # Create container if it doesn't exist
                self.users_container = self.database.create_container_if_not_exists(
                    id="Users",
                    partition_key=PartitionKey(path="/email"),
                    offer_throughput=400
                )
                self.logger.info("Created Cosmos DB container for Users")
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB connection established successfully")
        except Exception as e:
            self.logger.warning(f"Cosmos DB connection failed: {str(e)}. Using in-memory storage.")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate a password hash"""
        return pwd_context.hash(password)
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get a user by email
        
        Args:
            email: The email address to look up
            
        Returns:
            The user if found, None otherwise
        """
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                # Query for the user
                query = "SELECT * FROM c WHERE c.email = @email"
                params = [{"name": "@email", "value": email}]
                
                results = []
                async for item in self.users_container.query_items(
                    query=query, 
                    parameters=params, 
                    enable_cross_partition_query=False # Email is the partition key
                ):
                    # Convert string ID to UUID
                    item["id"] = UUID(item["id"])
                    
                    # Create UserInDB object from dict
                    user = UserInDB(**item)
                    results.append(user)
                
                if results:
                    return results[0]
            except Exception as e:
                self.logger.error(f"Error retrieving user from Cosmos DB: {str(e)}")
        
        # Try from memory if not found in database or if database is unavailable
        for user_id, user in self.users_cache.items():
            if user.email == email:
                return user
        
        # Not found
        return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        """
        Get a user by ID
        
        Args:
            user_id: The UUID of the user to retrieve
            
        Returns:
            The user if found, None otherwise
        """
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                # Query for the user
                query = "SELECT * FROM c WHERE c.id = @id"
                params = [{"name": "@id", "value": str(user_id)}]
                
                results = []
                async for item in self.users_container.query_items(
                    query=query, 
                    parameters=params, 
                    enable_cross_partition_query=True # Need to search across partitions for ID
                ):
                    # Convert string ID to UUID
                    item["id"] = UUID(item["id"])
                    
                    # Create UserInDB object from dict
                    user = UserInDB(**item)
                    results.append(user)
                
                if results:
                    return results[0]
            except Exception as e:
                self.logger.error(f"Error retrieving user from Cosmos DB: {str(e)}")
        
        # Try from memory if not found in database or if database is unavailable
        if str(user_id) in self.users_cache:
            return self.users_cache[str(user_id)]
        
        # Not found
        return None
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create a new user
        
        Args:
            user_data: The user data for registration
            
        Returns:
            The created user
            
        Raises:
            HTTPException: If the email is already registered
        """
        # Check if email is already registered
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Current timestamp
        current_time = datetime.now()
        
        # Create the user
        user = UserInDB(
            email=user_data.email,
            full_name=user_data.full_name,
            company_name=user_data.company_name,
            job_title=user_data.job_title,
            hashed_password=hashed_password,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Store in database or memory
        if self.cosmos_db_available:
            try:
                user_dict = user.dict()
                # Convert UUID to string for Cosmos DB
                user_dict["id"] = str(user_dict["id"])
                
                # Store in Cosmos DB
                await self.users_container.create_item(body=user_dict)
                self.logger.info(f"Created user in Cosmos DB: {user.email}")
            except Exception as e:
                self.logger.error(f"Error creating user in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.users_cache[str(user.id)] = user
        else:
            # Store in memory
            self.users_cache[str(user.id)] = user
            self.logger.info(f"Created user in memory: {user.email}")
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with email and password
        
        Args:
            email: The user's email
            password: The password to verify
            
        Returns:
            The authenticated user or None if authentication fails
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: The data to encode in the token payload
            expires_delta: Optional custom expiration time
            
        Returns:
            The encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token with longer expiration
        
        Args:
            data: The data to encode in the token payload
            
        Returns:
            The encoded JWT refresh token
        """
        refresh_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return self.create_access_token(data, expires_delta=refresh_expires)
    
    def decode_token(self, token: str) -> TokenData:
        """
        Decode and validate a JWT token
        
        Args:
            token: The JWT token to decode
            
        Returns:
            The token data
            
        Raises:
            HTTPException: If the token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return TokenData(user_id=UUID(user_id), email=email)
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[UserInDB]:
        """
        Update a user's information
        
        Args:
            user_id: The UUID of the user to update
            user_update: The user data to update
            
        Returns:
            The updated user or None if user not found
        """
        # Get the existing user
        existing_user = await self.get_user_by_id(user_id)
        if not existing_user:
            return None
        
        # Update user fields
        update_dict = user_update.dict(exclude_unset=True)
        
        # Special handling for password
        if "password" in update_dict:
            hashed_password = self.get_password_hash(update_dict.pop("password"))
            update_dict["hashed_password"] = hashed_password
        
        # Create updated user object
        updated_user_data = existing_user.dict()
        updated_user_data.update(update_dict)
        updated_user_data["updated_at"] = datetime.now()
        
        updated_user = UserInDB(**updated_user_data)
        
        # Update in database or memory
        if self.cosmos_db_available:
            try:
                user_dict = updated_user.dict()
                # Convert UUID to string for Cosmos DB
                user_dict["id"] = str(user_dict["id"])
                
                # Update in Cosmos DB
                await self.users_container.replace_item(
                    item=str(user_id),
                    body=user_dict
                )
                self.logger.info(f"Updated user in Cosmos DB: {updated_user.email}")
            except Exception as e:
                self.logger.error(f"Error updating user in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.users_cache[str(user_id)] = updated_user
        else:
            # Update in memory
            self.users_cache[str(user_id)] = updated_user
            self.logger.info(f"Updated user in memory: {updated_user.email}")
        
        return updated_user