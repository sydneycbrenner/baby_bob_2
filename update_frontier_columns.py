import sqlite3
import json
from collections import OrderedDict

# Path to the SQLite database
DB_PATH = "baby_bob.db"

def update_frontier_columns():
    """
    Updates the SQLite table to support lists, tuples, and OrderedDict for 
    frontier, frontier_keys, and frontier_values columns.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current data
    cursor.execute("""
        SELECT id, frontier, frontier_keys, frontier_values 
        FROM master_config
    """)
    rows = cursor.fetchall()
    
    # Update each row with complex data types
    for idx, (id_val, frontier, frontier_keys, frontier_values) in enumerate(rows):
        # Create a mix of data types based on the row index
        if idx % 3 == 0:
            # Use string for frontier, list for keys and values
            new_frontier = frontier
            new_frontier_keys = eval(frontier_keys)  # Convert string back to list
            new_frontier_values = eval(frontier_values)  # Convert string back to list
        elif idx % 3 == 1:
            # Use OrderedDict for frontier, tuple for keys and values
            new_frontier = OrderedDict([('name', frontier), ('category', f"cat_{idx % 5}")])
            new_frontier_keys = tuple(eval(frontier_keys))  # Convert to tuple
            new_frontier_values = tuple(eval(frontier_values))  # Convert to tuple
        else:
            # Use OrderedDict for all fields
            new_frontier = OrderedDict([('name', frontier), ('category', f"cat_{idx % 5}")])
            keys_list = eval(frontier_keys)
            values_list = eval(frontier_values)
            new_frontier_keys = OrderedDict([(k, f"desc_{i}") for i, k in enumerate(keys_list)])
            new_frontier_values = OrderedDict(zip(keys_list, values_list))
        
        # Serialize to JSON
        new_frontier_json = json.dumps(new_frontier)
        new_frontier_keys_json = json.dumps(new_frontier_keys)
        new_frontier_values_json = json.dumps(new_frontier_values)
        
        # Update the row
        cursor.execute("""
            UPDATE master_config
            SET frontier = ?, frontier_keys = ?, frontier_values = ?
            WHERE id = ?
        """, (new_frontier_json, new_frontier_keys_json, new_frontier_values_json, id_val))
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"Updated {len(rows)} rows to support complex data types in frontier columns")

def check_frontier_columns():
    """
    Displays the current frontier columns to verify the update
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, frontier, frontier_keys, frontier_values 
        FROM master_config
        LIMIT 10
    """)
    rows = cursor.fetchall()
    
    print("\nCurrent frontier column data (JSON format):")
    for id_val, frontier, frontier_keys, frontier_values in rows:
        print(f"ID: {id_val}")
        print(f"  frontier: {frontier}")
        print(f"  frontier_keys: {frontier_keys}")
        print(f"  frontier_values: {frontier_values}")
        print()
    
    conn.close()

if __name__ == "__main__":
    # Update the frontier columns
    update_frontier_columns()
    
    # Check the results
    check_frontier_columns()