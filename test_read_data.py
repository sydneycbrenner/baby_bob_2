import sqlite3
import json
from collections import OrderedDict
import sys

# Path to the SQLite database
DB_PATH = "baby_bob.db"

def get_connection():
    """
    Get a connection to the SQLite database
    
    Returns:
        sqlite3.Connection: A connection to the database
    """
    return sqlite3.connect(DB_PATH)

def test_read_data():
    """
    Test reading the data from SQLite with the updated handling of complex data types
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Read the data
        cursor.execute("SELECT id, frontier, frontier_keys, frontier_values FROM master_config")
        rows = cursor.fetchall()
        
        # Process each row
        for i, (id_val, frontier, frontier_keys, frontier_values) in enumerate(rows):
            # Parse JSON strings to Python objects
            try:
                frontier_obj = json.loads(frontier) if frontier.startswith('{') or frontier.startswith('[') else frontier
                frontier_keys_obj = json.loads(frontier_keys)
                frontier_values_obj = json.loads(frontier_values)
                
                print(f"Row {i + 1}:")
                print(f"  ID: {id_val}")
                print(f"  frontier: {frontier_obj} (type: {type(frontier_obj).__name__})")
                print(f"  frontier_keys: {frontier_keys_obj} (type: {type(frontier_keys_obj).__name__})")
                print(f"  frontier_values: {frontier_values_obj} (type: {type(frontier_values_obj).__name__})")
                print()
                
                # Only show first 5 rows
                if i >= 4:
                    break
            except json.JSONDecodeError as e:
                print(f"JSON decode error in row {i+1}: {e}")
            except Exception as e:
                print(f"Error processing row {i+1}: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    # Test reading the data
    test_read_data()