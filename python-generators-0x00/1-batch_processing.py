#!/usr/bin/env python3
"""
Module that provides batch processing functionality for user data
"""
import mysql.connector
from typing import Dict, Any, Generator, List
from seed import connect_to_prodev


def stream_users_in_batches(batch_size: int) -> Generator[List[Dict[str, Any]], None, int]:
    """
    Generator function that yields batches of users from the user_data table
    
    Args:
        batch_size: Number of users to fetch in each batch
        
    Returns:
        Generator yielding lists of dictionaries containing user data
    """
    # Connect to the database
    connection = connect_to_prodev()
    
    try:
        # Create a cursor and execute the query
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_data")
        
        # Process rows in batches
        batch = []
        for row in cursor:
            batch.append(row)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield any remaining rows
        if batch:
            yield batch
            
    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")
    finally:
        # Clean up resources
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()


def batch_processing(batch_size: int) -> Generator[Dict[str, Any], None, Dict[str, int]]:
    """
    Process batches of users and filter those over the age of 25
    
    Args:
        batch_size: Number of users to process in each batch
        
    Returns:
        Generator yielding dictionaries of users over 25 years old
        After iteration completes, returns a summary dictionary with statistics
    """
    total_users = 0
    filtered_users = 0
    
    # Stream users in batches
    for batch in stream_users_in_batches(batch_size):
        # Process each batch to filter users over age 25
        for user in batch:
            total_users += 1
            if float(user['age']) > 25:
                filtered_users += 1
                yield user
    
    # Return summary statistics after all users have been processed
    return {"total_users": total_users, "filtered_users": filtered_users}


if __name__ == "__main__":
    # Example usage
    print("Users over 25 years old:")
    
    # Create the generator
    users_over_25 = batch_processing(2)  # Process in batches of 2
    
    # Iterate through the generator
    for user in users_over_25:
        print(f"User: {user['name']}, Email: {user['email']}, Age: {user['age']}")
    
    # Get the summary statistics (return value after generator is exhausted)
    summary = users_over_25.gi_frame.f_locals if hasattr(users_over_25, 'gi_frame') and users_over_25.gi_frame else {"total_users": 0, "filtered_users": 0}
    print(f"\nProcessing summary:\n- Total users processed: {summary.get('total_users', 0)}\n- Users over 25: {summary.get('filtered_users', 0)}")
