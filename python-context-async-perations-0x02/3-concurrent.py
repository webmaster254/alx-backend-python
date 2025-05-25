#!/usr/bin/env python3
"""
Module that demonstrates concurrent database operations using asyncio and aiosqlite
"""
import asyncio
import aiosqlite
import time
from typing import List, Dict, Any


async def async_fetch_users() -> List[Dict[str, Any]]:
    """
    Asynchronously fetch all users from the database
    
    Returns:
        List of dictionaries containing user information
    """
    start_time = time.time()
    async with aiosqlite.connect('users.db') as db:
        # Enable dictionary rows
        db.row_factory = aiosqlite.Row
        
        # Execute the query
        cursor = await db.execute("SELECT * FROM users")
        
        # Fetch all results
        rows = await cursor.fetchall()
        
        # Convert rows to dictionaries
        results = [
            {
                'id': row['id'],
                'name': row['name'], 
                'email': row['email'],
                'age': row['age']
            } for row in rows
        ]
        
        # Log execution time
        execution_time = time.time() - start_time
        print(f"Fetched all users in {execution_time:.4f} seconds")
        
        return results


async def async_fetch_older_users() -> List[Dict[str, Any]]:
    """
    Asynchronously fetch users older than 40 from the database
    
    Returns:
        List of dictionaries containing older user information
    """
    start_time = time.time()
    async with aiosqlite.connect('users.db') as db:
        # Enable dictionary rows
        db.row_factory = aiosqlite.Row
        
        # Execute the query with parameter
        cursor = await db.execute("SELECT * FROM users WHERE age > 40")
        
        # Fetch all results
        rows = await cursor.fetchall()
        
        # Convert rows to dictionaries
        results = [
            {
                'id': row['id'],
                'name': row['name'], 
                'email': row['email'],
                'age': row['age']
            } for row in rows
        ]
        
        # Log execution time
        execution_time = time.time() - start_time
        print(f"Fetched older users in {execution_time:.4f} seconds")
        
        return results


async def fetch_concurrently() -> tuple:
    """
    Execute both fetch operations concurrently using asyncio.gather
    
    Returns:
        Tuple containing results from both queries
    """
    print("Starting concurrent fetch operations...")
    start_time = time.time()
    
    # Run both queries concurrently
    all_users, older_users = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
    # Calculate and log total execution time
    total_time = time.time() - start_time
    print(f"\nAll concurrent operations completed in {total_time:.4f} seconds")
    
    return all_users, older_users


# Ensure the database exists with proper schema and data before running async operations
async def setup_database():
    """
    Set up the database with test data if it doesn't exist
    """
    async with aiosqlite.connect('users.db') as db:
        # Create users table if it doesn't exist
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            age INTEGER NOT NULL
        )
        ''')
        
        # Check if we need to insert test data
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = await cursor.fetchone()
        
        if count[0] == 0:
            # Insert test users
            test_users = [
                (1, "John Doe", "john@example.com", 50),
                (2, "Jane Smith", "jane@example.com", 22),
                (3, "Bob Johnson", "bob@example.com", 45),
                (4, "Alice Williams", "alice@example.com", 35),
                (5, "Charlie Brown", "charlie@example.com", 27),
                (6, "David Miller", "david@example.com", 33),
                (7, "Emily Davis", "emily@example.com", 41),
                (8, "Frank Wilson", "frank@example.com", 55)
            ]
            
            # Insert test data
            await db.executemany(
                "INSERT OR REPLACE INTO users (id, name, email, age) VALUES (?, ?, ?, ?)",
                test_users
            )
            
            await db.commit()
            print("Database initialized with test data")
        else:
            print("Using existing database")


async def main():
    """
    Main async function to setup database and run concurrent operations
    """
    # Setup the database first
    await setup_database()
    
    # Run concurrent operations
    all_users, older_users = await fetch_concurrently()
    
    # Display results
    print(f"\nTotal users: {len(all_users)}")
    print(f"Users older than 40: {len(older_users)}")
    
    print("\nAll Users:")
    print("-" * 60)
    for user in all_users:
        print(f"{user['id']:<5} {user['name']:<20} {user['email']:<30} {user['age']:<5}")
    
    print("\nUsers Older Than 40:")
    print("-" * 60)
    for user in older_users:
        print(f"{user['id']:<5} {user['name']:<20} {user['email']:<30} {user['age']:<5}")


if __name__ == "__main__":
    # Run the async program
    asyncio.run(main())
