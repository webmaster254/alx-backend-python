#!/usr/bin/env python3
"""
Module that provides a generator function to stream users from the database
"""
import mysql.connector
from typing import Dict, Any, Generator
from seed import connect_to_prodev


def stream_users() -> Generator[Dict[str, Any], None, None]:
    """
    Generator function that yields one user at a time from the user_data table
    
    Returns:
        Generator yielding dictionaries containing user data
    """
    # Connect to the database
    connection = connect_to_prodev()
    
    try:
        # Create a cursor and execute the query
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_data")
        
        # Yield each row one at a time
        for row in cursor:
            yield row
            
    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    # Example usage
    for user in stream_users():
        print(f"User: {user['name']}, Email: {user['email']}, Age: {user['age']}")
