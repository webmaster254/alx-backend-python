#!/usr/bin/env python3
"""
Module that uses a generator to compute the average age of users
in a memory-efficient way
"""
import mysql.connector
from typing import Generator, Dict, Any, Union, Tuple
from seed import connect_to_prodev


def stream_user_ages() -> Generator[float, None, None]:
    """
    Generator function that yields user ages one by one
    
    Returns:
        Generator yielding user ages as floats
    """
    # Connect to the database
    connection = connect_to_prodev()
    
    try:
        # Create a cursor and execute the query
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT age FROM user_data")
        
        # Yield each age one at a time
        for row in cursor:
            yield float(row['age'])
            
    except mysql.connector.Error as err:
        print(f"Error fetching user ages: {err}")
    finally:
        # Clean up resources
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()


def calculate_average_age() -> float:
    """
    Calculate the average age of users without loading the entire dataset into memory
    
    Returns:
        The average age as a float
    """
    total_age = 0
    count = 0
    
    # Use the generator to process ages one by one
    for age in stream_user_ages():
        total_age += age
        count += 1
    
    # Calculate and return the average
    return total_age / count if count > 0 else 0


if __name__ == "__main__":
    # Calculate and print the average age
    avg_age = calculate_average_age()
    print(f"Average age of users: {avg_age:.2f}")
