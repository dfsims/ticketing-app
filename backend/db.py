import os
import asyncpg
import logging
import base64
from typing import Optional
from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages connection to Lakebase Postgres database"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_string: Optional[str] = None
    
    async def initialize(self):
        """Initialize database connection using Lakebase_url secret"""
        try:
            # Get the Lakebase URL from Databricks secrets
            w = WorkspaceClient()
            
            # Retrieve the secret - update scope name if different
            # Common scopes: 'lakebase', 'app-secrets', or custom scope name
            try:
                secret_response = w.secrets.get_secret(
                    scope="lakebase",
                    key="Lakebase_url"
                )
                # Decode base64 encoded secret value
                encoded_value = secret_response.value
                self.connection_string = base64.b64decode(encoded_value).decode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to get secret from 'lakebase' scope: {e}")
                # Try alternative common scope names
                try:
                    secret_response = w.secrets.get_secret(
                        scope="app-secrets",
                        key="Lakebase_url"
                    )
                    encoded_value = secret_response.value
                    self.connection_string = base64.b64decode(encoded_value).decode('utf-8')
                except Exception:
                    # Last resort: try the secret as an environment variable
                    self.connection_string = os.getenv("LAKEBASE_URL")
                    if not self.connection_string:
                        raise ValueError(
                            "Could not retrieve Lakebase_url secret. "
                            "Please ensure it exists in a secret scope named 'lakebase' or 'app-secrets'"
                        )
            
            if not self.connection_string:
                raise ValueError("Lakebase_url secret is empty")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("Successfully connected to Lakebase database")
            
            # Initialize database schema
            await self._initialize_schema()
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def _initialize_schema(self):
        """Create tickets and ticket_messages tables if they don't exist"""
        create_tables_query = """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'open',
            created_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS ticket_messages (
            message_id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
            message_text TEXT NOT NULL,
            author VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
        CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_tables_query)
            logger.info("Database schema initialized successfully")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")
    
    async def get_connection(self):
        """Get a connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool.acquire()

# Global database connection instance
db = DatabaseConnection()