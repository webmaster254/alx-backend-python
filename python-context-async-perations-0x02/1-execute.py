#!/usr/bin/env python3
"""
Module that provides a context manager for executing SQL queries
"""
import sqlite3
from typing import List, Tuple, Any, Optional, Union, Dict


class ExecuteQuery:
    """
    A context manager for executing SQL queries with parameters.
    
    This class manages both the database connection and query execution,
    automatically handling resources when used with the 'with' statement.
    """
    def __init__(self, query: str, params: Optional[Union[Tuple, List, Dict]] = None, 
                 db_name: str = 'users.db'):
        """
        Initialize with a query, optional parameters, and database name.
        
        Args:
            query: SQL query to execute
            params: Query parameters (default: None)
            db_name: Name of the database file (default: 'users.db')
        """
        self.query = query
        self.params = params if params is not None else ()
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.results = None
    
    def __enter__(self):
        """
        Enter the context manager, establish connection, and execute query.
        
        Returns:
            Self reference for accessing results or rowcount
        """
        # Open database connection
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        
        # Execute the query with parameters
        self.cursor.execute(self.query, self.params)
        
        # Initialize attributes
        self.rowcount = self.cursor.rowcount
        
        # Check if this is a SELECT query by seeing if it returns data
        if self.query.strip().upper().startswith("SELECT"):
            # Store the results for SELECT queries
            self.results = self.cursor.fetchall()
        else:
            # For non-SELECT queries, store None as results
            self.results = None
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager and clean up resources.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
            
        Returns:
            Boolean indicating whether an exception was handled
        """
        if self.cursor:
            self.cursor.close()
        
        if self.connection:
            # Commit any changes if no exception occurred
            if exc_type is None:
                self.connection.commit()
            else:
                # Rollback if an exception occurred
                self.connection.rollback()
                
            # Close the connection
            self.connection.close()
        
        # Return False to propagate exceptions, True to suppress them
        return False


if __name__ == "__main__":
    # Create test database and table if they don't exist
    with sqlite3.connect('users.db') as setup_conn:
        cursor = setup_conn.cursor()
        
        # Check if table exists and has the correct schema
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if not columns:  # Table doesn't exist
            # Create users table
            cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER NOT NULL
            )
            ''')
        elif 'age' not in columns:  # Table exists but needs age column
            # Add age column to existing table
            cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER NOT NULL DEFAULT 30")
            print("Added age column to existing users table")
        else:
            print("Using existing users table with age column")
        
        # Insert test users if not exists
        test_users = [
            (1, "John Doe", "john@example.com", 30),
            (2, "Jane Smith", "jane@example.com", 22),
            (3, "Bob Johnson", "bob@example.com", 45),
            (4, "Alice Williams", "alice@example.com", 19),
            (5, "Charlie Brown", "charlie@example.com", 27)
        ]
        
        for user in test_users:
            cursor.execute("INSERT OR REPLACE INTO users (id, name, email, age) VALUES (?, ?, ?, ?)", user)
        
        setup_conn.commit()
    
    # Use the ExecuteQuery context manager to filter users by age
    print("\n1. Executing SELECT query to find users with age > 25:")
    
    # The query and parameter as specified in the instructions
    query = "SELECT * FROM users WHERE age > ?"
    param = 25
    
    with ExecuteQuery(query, (param,)) as query_context:
        # Print the results
        print(f"\nUsers with age > {param}:")
        print("-" * 60)
        print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Age':<5}")
        print("-" * 60)
        
        if query_context.results:
            for user in query_context.results:
                print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {user[3]:<5}")
        else:
            print("No results found.")
    
    # Example 2: INSERT operation
    print("\n2. Executing INSERT query:")
    insert_query = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)"
    insert_params = ("David Miller", "david@example.com", 33)
    
    with ExecuteQuery(insert_query, insert_params) as query_context:
        print(f"Inserted {query_context.rowcount} row(s)")
    
    # Example 3: UPDATE operation
    print("\n3. Executing UPDATE query:")
    update_query = "UPDATE users SET age = ? WHERE name = ?"
    update_params = (50, "John Doe")
    
    with ExecuteQuery(update_query, update_params) as query_context:
        print(f"Updated {query_context.rowcount} row(s)")
    
    # Example 4: DELETE operation
    print("\n4. Executing DELETE query:")
    delete_query = "DELETE FROM users WHERE age < ?"
    delete_params = (20,)
    
    with ExecuteQuery(delete_query, delete_params) as query_context:
        print(f"Deleted {query_context.rowcount} row(s)")
    
    # Verify the changes with another SELECT query
    print("\n5. Verifying changes with SELECT query:")
    with ExecuteQuery("SELECT * FROM users ORDER BY id") as query_context:
        # Print the results
        print(f"\nCurrent users in database:")
        print("-" * 60)
        print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Age':<5}")
        print("-" * 60)
        
        for user in query_context.results:
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {user[3]:<5}")
