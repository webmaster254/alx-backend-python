#!/usr/bin/env python3
"""
Module that provides a context manager for database connections
"""
import sqlite3
from typing import List, Tuple, Any


class DatabaseConnection:
    """
    A context manager for handling database connections.
    
    This class automatically manages the opening and closing of
    database connections when used with the 'with' statement.
    """
    def __init__(self, db_name: str = 'users.db'):
        """
        Initialize the DatabaseConnection with a database name.
        
        Args:
            db_name: Name of the database file to connect to
        """
        self.db_name = db_name
        self.connection = None
    
    def __enter__(self) -> sqlite3.Connection:
        """
        Enter the context manager and establish a database connection.
        
        Returns:
            The active database connection
        """
        self.connection = sqlite3.connect(self.db_name)
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context manager and close the database connection.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
            
        Returns:
            Boolean indicating whether an exception was handled
        """
        if self.connection:
            # Close the connection
            self.connection.close()
            self.connection = None
        
        # Return False to propagate exceptions, True to suppress them
        return False


if __name__ == "__main__":
    # Create test database and table if they don't exist
    with sqlite3.connect('users.db') as setup_conn:
        cursor = setup_conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
        ''')
        
        # Insert test users if not exists
        test_users = [
            (1, "John Doe", "john@example.com"),
            (2, "Jane Smith", "jane@example.com"),
            (3, "Bob Johnson", "bob@example.com")
        ]
        
        for user in test_users:
            cursor.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (?, ?, ?)", user)
        
        setup_conn.commit()
    
    # Use the context manager to perform a query
    print("Fetching users with the DatabaseConnection context manager:")
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        
        # Print the results
        print("\nUser Results:")
        print("-" * 50)
        print(f"{'ID':<5} {'Name':<20} {'Email':<30}")
        print("-" * 50)
        for user in results:
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30}")