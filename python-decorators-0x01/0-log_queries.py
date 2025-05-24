import sqlite3
import functools
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#### decorator to log SQL queries

def log_queries(func):
    """
    Decorator that logs SQL queries before they are executed.
    Assumes the first argument of the decorated function is the SQL query.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from arguments
        if args:
            query = args[0] if isinstance(args[0], str) else None
        elif 'query' in kwargs:
            query = kwargs['query']
        else:
            query = None
        
        # Log the query if found
        if query:
            logging.info(f"Executing SQL Query: {query}")
        else:
            logging.warning("No SQL query found to log")
        
        # Execute the original function
        return func(*args, **kwargs)
    
    return wrapper

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")