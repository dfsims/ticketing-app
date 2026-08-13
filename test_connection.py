#!/usr/bin/env python3
"""
Test script to verify Lakebase database connection.
Run this before deploying the app to ensure your secret is configured correctly.

Usage:
    python test_connection.py
"""

import asyncio
import sys
from backend.db import db

async def test_connection():
    """Test the database connection"""
    print("Testing Lakebase database connection...\n")
    
    try:
        # Initialize connection
        print("[1/3] Initializing database connection...")
        await db.initialize()
        print("✓ Database connection established successfully!\n")
        
        # Test query
        print("[2/3] Running test query...")
        async with db.pool.acquire() as conn:
            result = await conn.fetchval("SELECT version()")
            print(f"✓ PostgreSQL Version: {result}\n")
            
            # Check if tickets table exists
            tickets_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tickets')"
            )
            
            messages_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ticket_messages')"
            )
            
            if tickets_exists and messages_exists:
                print("✓ Tickets table exists")
                print("✓ Ticket_messages table exists")
                
                # Get counts
                ticket_count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
                message_count = await conn.fetchval("SELECT COUNT(*) FROM ticket_messages")
                print(f"✓ Current ticket count: {ticket_count}")
                print(f"✓ Current message count: {message_count}\n")
            else:
                print("⚠ Tables will be created on first app startup\n")
        
        # Close connection
        print("[3/3] Closing connection...")
        await db.close()
        print("✓ Connection closed\n")
        
        print("=" * 60)
        print("SUCCESS: Lakebase connection is configured correctly!")
        print("You can now deploy your ticketing app.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        print("=" * 60)
        print("CONNECTION FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Ensure the 'Lakebase_url' secret exists:")
        print("   databricks secrets list-secrets lakebase")
        print("\n2. Verify the connection string format:")
        print("   postgresql://user:pass@host:port/db?sslmode=require")
        print("\n3. Check Lakebase endpoint is running and accessible")
        print("\n4. Verify network connectivity to Lakebase")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)