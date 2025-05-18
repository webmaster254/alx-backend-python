# MySQL Database Seeder Script

This Python script (`seed.py`) sets up a MySQL database named `ALX_prodev` with a `user_data` table and populates it with sample data from a CSV file.

## Features

- Creates a MySQL database if it doesn't exist
- Creates a table with specified schema
- Reads data from a CSV file
- Populates the database with the CSV data
- Prevents duplicate entries
- Provides detailed error handling

## Table Schema

The `user_data` table has the following structure:

| Field   | Type         | Constraints       |
|---------|--------------|-------------------|
| user_id | VARCHAR(36)  | PRIMARY KEY, Indexed |
| name    | VARCHAR(255) | NOT NULL          |
| email   | VARCHAR(255) | NOT NULL          |
| age     | DECIMAL(5,2) | NOT NULL          |

## Requirements

- Python 3.x
- MySQL Server
- `mysql-connector-python` package

## Installation

1. Ensure MySQL server is installed and running
2. Install the required Python package:

```bash
pip install mysql-connector-python
```

## Usage

### Direct Execution

The script can be run directly:

```bash
./seed.py [options]
```

Command-line options:

- `--host`: MySQL server hostname (default: localhost)
- `--user`: MySQL username (default: root)
- `--password`: MySQL password (default: empty)
- `--port`: MySQL server port (default: 3306)
- `--csv`: Path to CSV file (default: user_data.csv)

### Import as Module

The script can also be imported as a module:

```python
import seed

# Connect to MySQL server
connection = seed.connect_db()

# Create database
seed.create_database(connection)
connection.close()

# Connect to the ALX_prodev database
connection = seed.connect_to_prodev()

# Create table
seed.create_table(connection)

# Insert data from CSV
seed.insert_data(connection, 'user_data.csv')
```

## CSV File Format

The CSV file should have the following headers:

```csv
user_id,name,email,age
```

Example:

```csv
user_id,name,email,age
550e8400-e29b-41d4-a716-446655440000,John Doe,john.doe@example.com,30.5
550e8400-e29b-41d4-a716-446655440001,Jane Smith,jane.smith@example.com,25.0
```

If `user_id` is not provided, the script will generate a UUID automatically.

## Functions

- `connect_db()`: Connects to the MySQL database server
- `create_database(connection)`: Creates the ALX_prodev database if it doesn't exist
- `connect_to_prodev()`: Connects to the ALX_prodev database
- `create_table(connection)`: Creates the user_data table if it doesn't exist
- `insert_data(connection, data)`: Inserts data into the database
- `read_csv(file_path)`: Reads data from a CSV file

## Error Handling

The script includes comprehensive error handling for:

- Database connection issues
- Database creation problems
- Table creation errors
- Data insertion failures
- CSV file reading errors

## License

This project is licensed under the MIT License.
