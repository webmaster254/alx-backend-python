#!/usr/bin/env python3
"""
Module that provides lazy pagination functionality for user data
"""
import mysql.connector
from typing import Dict, Any, Generator, List
from seed import connect_to_prodev


def paginate_users(page_size: int, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Fetch a page of users from the database
    
    Args:
        page_size: Number of users to fetch per page
        offset: Starting position for fetching users
        
    Returns:
        List of dictionaries containing user data for the requested page
    """
    # Connect to the database
    connection = connect_to_prodev()
    result = []
    
    try:
        # Create a cursor and execute the query with LIMIT and OFFSET
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM user_data LIMIT %s OFFSET %s"
        cursor.execute(query, (page_size, offset))
        
        # Fetch all rows for this page
        result = cursor.fetchall()
            
    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")
    finally:
        # Clean up resources
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()
    
    return result


def lazy_paginate(page_size: int) -> Generator[Dict[str, Any], None, None]:
    """
    Generator function that lazily fetches pages of users
    
    Args:
        page_size: Number of users to fetch per page
        
    Returns:
        Generator yielding user dictionaries one at a time
    """
    offset = 0
    
    while True:
        # Fetch the next page
        page = paginate_users(page_size, offset)
        
        # If no more results, stop iteration
        if not page:
            break
        
        # Update offset for next page
        offset += page_size
        
        # Yield each user in the page
        for user in page:
            yield user


if __name__ == "__main__":
    # Example usage
    print("Lazily paginating through users:")
    for i, user in enumerate(lazy_paginate(2)):
        print(f"{i+1}. User: {user['name']}, Email: {user['email']}, Age: {user['age']}")
        # Simulate processing each user
        if i >= 9:  # Stop after 10 users to demonstrate
            print("Stopping pagination after 10 users...")
            break
