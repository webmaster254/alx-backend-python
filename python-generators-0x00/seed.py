#!/usr/bin/env python3
"""
Script to set up MySQL database ALX_prodev with user_data table
and populate it with sample data from user_data.csv

Before running this script:
1. Ensure MySQL server is installed and running
2. Update the MySQL credentials (user, password) if needed

Installation instructions:
- Ubuntu/Debian: sudo apt install mysql-server && sudo systemctl start mysql
- macOS: brew install mysql && brew services start mysql
- Windows: Download and install MySQL from https://dev.mysql.com/downloads/installer/
"""

import mysql.connector
import csv
import uuid
import os
from typing import Dict, List, Any, Optional, Tuple


def connect_db(host="localhost", user="root", password="", port=3306) -> mysql.connector.connection.MySQLConnection:
    """
    Connects to the MySQL database server
    Args:
        host: MySQL server hostname
        user: MySQL username
        password: MySQL password
        port: MySQL server port
    Returns:
        MySQL connection object
    """
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        print("Successfully connected to MySQL server")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        print("\nPlease ensure MySQL server is installed and running.")
        print("Installation instructions:")
        print("- Ubuntu/Debian: sudo apt install mysql-server && sudo systemctl start mysql")
        print("- macOS: brew install mysql && brew services start mysql")
        print("- Windows: Download and install from https://dev.mysql.com/downloads/installer/")
        exit(1)


def create_database(connection: mysql.connector.connection.MySQLConnection) -> None:
    """
    Creates the database ALX_prodev if it does not exist
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database ALX_prodev created or already exists")
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        exit(1)


def connect_to_prodev(host="localhost", user="root", password="", port=3306) -> mysql.connector.connection.MySQLConnection:
    """
    Connects to the ALX_prodev database in MySQL
    Args:
        host: MySQL server hostname
        user: MySQL username
        password: MySQL password
        port: MySQL server port
    Returns:
        MySQL connection object to ALX_prodev database
    """
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database="ALX_prodev"
        )
        print("Successfully connected to ALX_prodev database")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to ALX_prodev database: {err}")
        exit(1)


def create_table(connection: mysql.connector.connection.MySQLConnection) -> None:
    """
    Creates a table user_data if it does not exist with the required fields
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            user_id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            age DECIMAL(5,2) NOT NULL,
            INDEX (user_id)
        )
        """)
        print("Table user_data created or already exists")
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
        exit(1)


def insert_data(connection: mysql.connector.connection.MySQLConnection, data) -> None:
    """
    Inserts data in the database if it does not exist
    Args:
        connection: MySQL connection object
        data: Either a string path to a CSV file or a list of dictionaries containing user data
    """
    try:
        # If data is a string, assume it's a path to a CSV file
        if isinstance(data, str):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = data if os.path.isabs(data) else os.path.join(script_dir, data)
            data = read_csv(csv_path)
        
        cursor = connection.cursor()
        
        # Check for existing records and insert only new ones
        for user in data:
            # Check if user with this ID already exists
            cursor.execute("SELECT COUNT(*) FROM user_data WHERE user_id = %s", (user['user_id'],))
            count = cursor.fetchone()[0]
            
            if count == 0:
                cursor.execute("""
                INSERT INTO user_data (user_id, name, email, age)
                VALUES (%s, %s, %s, %s)
                """, (user['user_id'], user['name'], user['email'], user['age']))
                print(f"Inserted user: {user['name']}")
            else:
                print(f"User {user['name']} with ID {user['user_id']} already exists")
        
        connection.commit()
        cursor.close()
        print("Data insertion completed")
    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
        connection.rollback()


def read_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Reads data from a CSV file
    Args:
        file_path: Path to the CSV file
    Returns:
        List of dictionaries containing user data
    """
    data = []
    try:
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Ensure user_id is UUID format
                if 'user_id' not in row or not row['user_id']:
                    row['user_id'] = str(uuid.uuid4())
                data.append(row)
        return data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        exit(1)


def main():
    """
    Main function to execute the database setup and data population
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Set up MySQL database and populate it with data from CSV')
    parser.add_argument('--host', default='localhost', help='MySQL server hostname')
    parser.add_argument('--user', default='root', help='MySQL username')
    parser.add_argument('--password', default='', help='MySQL password')
    parser.add_argument('--port', type=int, default=3306, help='MySQL server port')
    parser.add_argument('--csv', default='user_data.csv', help='Path to CSV file with user data')
    
    args = parser.parse_args()
    
    # Connect to MySQL server
    connection = connect_db(host=args.host, user=args.user, password=args.password, port=args.port)
    
    # Create database if it doesn't exist
    create_database(connection)
    connection.close()
    
    # Connect to the ALX_prodev database
    prodev_connection = connect_to_prodev(host=args.host, user=args.user, password=args.password, port=args.port)
    
    # Create table if it doesn't exist
    create_table(prodev_connection)
    
    # Read data from CSV file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = args.csv if os.path.isabs(args.csv) else os.path.join(script_dir, args.csv)
    user_data = read_csv(csv_path)
    
    # Insert data into the database
    insert_data(prodev_connection, user_data)
    
    # Close the connection
    prodev_connection.close()
    print("Database setup and data population completed successfully")


if __name__ == "__main__":
    main()
