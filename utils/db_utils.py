import sqlite3
import pandas as pd
import numpy as np
import os
from typing import List, Dict, Any, Optional, Union

# Path to store the SQLite database
DB_PATH = r"/Users/sydneyfiller/PycharmProjects/baby_bob/baby_bob.db"

# SQLite column names and types
data_columns = ['univ', 'experiment', 'implementation',
                'frontier', 'frontier_keys', 'frontier_values',
                'backtest_name_2024', 'backtest_user_2024', 'start_year', 'format_string',
                'backtest_name_2023', 'backtest_user_2023', 'eligible_for_2023_comparison', 'experiment_2023',
                'is_backtest_complete', 'backtest_branch', 'backtest_launch_date', 'backtest_finish_date',
                'is_backtest_summarized_in_omnitron',
                'is_approved_config', 'is_approved_comparison', 'is_approved_final_summary']

def get_connection():
    """
    Get a connection to the SQLite database
    
    Returns:
        sqlite3.Connection: A connection to the database
    """
    return sqlite3.connect(DB_PATH)

def create_db_from_scratch():
    """
    Create a fresh database with the master_config table
    
    Returns:
        None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop the table if it exists
    cursor.execute("DROP TABLE IF EXISTS master_config")
    
    # Create the table with appropriate columns and types
    # SQLite types are simple: TEXT, INTEGER, REAL, BLOB, NULL
    create_table_sql = """
    CREATE TABLE master_config (
        id INTEGER PRIMARY KEY,
        univ TEXT,
        experiment TEXT,
        implementation TEXT,
        frontier TEXT,
        frontier_keys TEXT,
        frontier_values TEXT,
        backtest_name_2024 TEXT,
        backtest_user_2024 TEXT,
        start_year INTEGER,
        format_string TEXT,
        backtest_name_2023 TEXT,
        backtest_user_2023 TEXT,
        eligible_for_2023_comparison INTEGER,
        is_backtest_complete INTEGER,
        backtest_branch TEXT,
        backtest_launch_date TEXT,
        backtest_finish_date TEXT,
        is_backtest_summarized_in_omnitron INTEGER,
        is_approved_config INTEGER,
        is_approved_comparison INTEGER,
        is_approved_final_summary INTEGER
    )
    """
    cursor.execute(create_table_sql)
    
    # Create indexes for frequently queried columns
    cursor.execute("CREATE INDEX idx_experiment ON master_config (experiment)")
    cursor.execute("CREATE INDEX idx_implementation ON master_config (implementation)")
    cursor.execute("CREATE INDEX idx_exp_impl ON master_config (experiment, implementation)")
    
    conn.commit()
    conn.close()
    
    print(f"Created fresh database at {DB_PATH}")

def create_fake_master_config_data() -> pd.DataFrame:
    """
    Creates and returns a fake master config DataFrame for testing purposes.
    This function generates a more comprehensive dataset with various scenarios.
    
    Returns:
        pd.DataFrame: A DataFrame with sample data
    """
    # Create more realistic test data with a variety of scenarios
    universes = ['US', 'EU', 'APAC', 'LATAM', 'GLOBAL']
    experiments = ['MoneyMarketModel', 'EquityStrategy', 'CommodityHedge', 'FXCarry', 'VolatilityArb']
    implementations = ['StandardImpl', 'AlternativeImpl', 'ExperimentalImpl']
    
    # Create a list to hold all data records
    records = []
    
    # Generate 15 different experiment-implementation combinations
    for i in range(15):
        univ = universes[i % len(universes)]
        experiment = experiments[i % len(experiments)]
        implementation = implementations[i % len(implementations)]
        
        # Generate frontier data
        frontier_name = f"frontier_{i+1}"
        frontier_keys = [f"param_{j}" for j in range(1, 4)]
        frontier_values = [round(np.random.uniform(0.1, 5.0), 2) for _ in range(3)]
        
        # Generate backtest info
        backtest_name = f"bt_{experiment[:3]}_{implementation[:3]}_{i+1}"
        backtest_user = "sydney" if i % 2 == 0 else "joey"
        
        # Set up different progress states for testing:
        # - Some are complete through all stages
        # - Some have partial approvals
        # - Some are just starting
        progress_state = i % 5  # 0-4 different states
        
        is_backtest_complete = progress_state > 0
        is_approved_config = progress_state > 0 or i % 3 == 0
        is_approved_comparison = progress_state > 1
        is_approved_final_summary = progress_state > 2
        
        # Create record
        record = {
            'univ': univ,
            'experiment': experiment,
            'implementation': implementation,
            'frontier': frontier_name,
            'frontier_keys': str(frontier_keys),  # Convert list to string for SQLite
            'frontier_values': str(frontier_values),  # Convert list to string for SQLite
            'backtest_name_2024': backtest_name,
            'backtest_user_2024': backtest_user,
            'start_year': 2024,
            'format_string': None,
            'backtest_name_2023': None,
            'backtest_user_2023': None,
            'eligible_for_2023_comparison': 0,
            'is_backtest_complete': 1 if is_backtest_complete else 0,  # SQLite uses 1/0 for boolean
            'backtest_branch': 'main',
            'backtest_launch_date': None,
            'backtest_finish_date': None,
            'is_backtest_summarized_in_omnitron': 0,
            'is_approved_config': 1 if is_approved_config else 0,
            'is_approved_comparison': 1 if is_approved_comparison else 0,
            'is_approved_final_summary': 1 if is_approved_final_summary else 0
        }
        
        records.append(record)
    
    # Create DataFrame from records
    master_config_df = pd.DataFrame(records)
    
    return master_config_df

def populate_db_with_fake_data():
    """
    Creates and populates the database with fake data
    
    Returns:
        None
    """
    # First create the database structure
    create_db_from_scratch()
    
    # Generate fake data
    df = create_fake_master_config_data()
    
    # Save to database
    save_master_config_df(df)
    
    print(f"Populated database with {len(df)} fake records")
    
def save_master_config_df(df: pd.DataFrame) -> None:
    """
    Saves the master config DataFrame to the SQLite database.
    
    Args:
        df: The DataFrame to save
    """
    conn = get_connection()
    
    # Convert boolean columns to SQLite integer format (1/0)
    bool_columns = [
        'is_backtest_complete', 'eligible_for_2023_comparison', 
        'is_backtest_summarized_in_omnitron',
        'is_approved_config', 'is_approved_comparison', 'is_approved_final_summary'
    ]
    
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(int)
    
    # Convert list columns to string for storage
    list_columns = ['frontier_keys', 'frontier_values']
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, tuple)) else x)
    
    # Remove the primary key column if it exists
    if 'id' in df.columns:
        df = df.drop('id', axis=1)
    
    # First clear the existing data
    conn.execute("DELETE FROM master_config")
    
    # Then insert the new data
    df.to_sql('master_config', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    
    print(f"Saved master config to {DB_PATH}")

def load_master_config_df() -> pd.DataFrame:
    """
    Loads the master config DataFrame from the SQLite database.
    If the database doesn't exist, creates it with fake data.
    
    Returns:
        The loaded or newly created DataFrame
    """
    if not os.path.exists(DB_PATH):
        # Create a new database with fake data
        populate_db_with_fake_data()
    
    conn = get_connection()
    
    # Read the data into a DataFrame
    df = pd.read_sql("SELECT * FROM master_config", conn)
    
    # Convert string representations of lists back to Python lists
    list_columns = ['frontier_keys', 'frontier_values']
    for col in list_columns:
        if col in df.columns:
            # Parse string representation of lists back to actual lists
            df[col] = df[col].apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else x)
    
    # Convert integer boolean columns to actual booleans
    bool_columns = [
        'is_backtest_complete', 'eligible_for_2023_comparison', 
        'is_backtest_summarized_in_omnitron',
        'is_approved_config', 'is_approved_comparison', 'is_approved_final_summary'
    ]
    
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    conn.close()
    
    return df

def update_experiment_approval(experiment: str, implementation: str, 
                             approval_type: str, approve: bool = True) -> bool:
    """
    Updates the approval status for a specific experiment and implementation
    
    Args:
        experiment: The experiment name
        implementation: The implementation name
        approval_type: One of 'config', 'comparison', or 'final_summary'
        approve: True to approve, False to revoke approval
        
    Returns:
        True if update was successful, False otherwise
    """
    column_name = f'is_approved_{approval_type}'
    
    # Validate inputs
    if approval_type not in ['config', 'comparison', 'final_summary']:
        print(f"Invalid approval_type: {approval_type}. Must be 'config', 'comparison', or 'final_summary'")
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Update the approval status
    cursor.execute(
        f"""
        UPDATE master_config 
        SET {column_name} = ? 
        WHERE experiment = ? AND implementation = ?
        """, 
        (1 if approve else 0, experiment, implementation)
    )
    
    # Check if any rows were updated
    rows_updated = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return rows_updated > 0

def update_backtest_status(experiment: str, implementation: str, is_complete: bool = True) -> bool:
    """
    Updates the backtest completion status for a specific experiment and implementation
    
    Args:
        experiment: The experiment name
        implementation: The implementation name
        is_complete: True if backtest is complete, False otherwise
        
    Returns:
        True if update was successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Update the backtest status
    cursor.execute(
        """
        UPDATE master_config 
        SET is_backtest_complete = ? 
        WHERE experiment = ? AND implementation = ?
        """, 
        (1 if is_complete else 0, experiment, implementation)
    )
    
    # Check if any rows were updated
    rows_updated = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return rows_updated > 0

def get_experiment_data(experiment: str) -> pd.DataFrame:
    """
    Get all data for a specific experiment
    
    Args:
        experiment: The experiment name
        
    Returns:
        DataFrame containing all implementations for the experiment
    """
    conn = get_connection()
    
    query = "SELECT * FROM master_config WHERE experiment = ?"
    df = pd.read_sql(query, conn, params=(experiment,))
    
    # Convert list columns from string to actual lists
    list_columns = ['frontier_keys', 'frontier_values']
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else x)
    
    # Convert boolean columns from integers to booleans
    bool_columns = [
        'is_backtest_complete', 'eligible_for_2023_comparison', 
        'is_backtest_summarized_in_omnitron',
        'is_approved_config', 'is_approved_comparison', 'is_approved_final_summary'
    ]
    
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    conn.close()
    
    return df

def get_experiment_implementation(experiment: str, implementation: str) -> Optional[pd.Series]:
    """
    Get data for a specific experiment and implementation
    
    Args:
        experiment: The experiment name
        implementation: The implementation name
        
    Returns:
        Series containing the data for the experiment-implementation, or None if not found
    """
    conn = get_connection()
    
    query = "SELECT * FROM master_config WHERE experiment = ? AND implementation = ?"
    df = pd.read_sql(query, conn, params=(experiment, implementation))
    
    conn.close()
    
    if df.empty:
        return None
    
    # Convert list columns from string to actual lists
    list_columns = ['frontier_keys', 'frontier_values']
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else x)
    
    # Convert boolean columns from integers to booleans
    bool_columns = [
        'is_backtest_complete', 'eligible_for_2023_comparison', 
        'is_backtest_summarized_in_omnitron',
        'is_approved_config', 'is_approved_comparison', 'is_approved_final_summary'
    ]
    
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    # Return the first row as a Series
    return df.iloc[0]

def map_2024_backtest_to_2023_backtest():
    """
    Maps 2024 backtests to 2023 backtests
    
    Returns:
        None
    """
    # End user will create, do not touch
    pass

def create_format_string():
    """
    Creates summarization format string
    
    Returns:
        None
    """
    # End user will create this
    pass

# If this file is run directly, create and populate the database
if __name__ == "__main__":
    populate_db_with_fake_data()
    
    # Show some data about the database
    df = load_master_config_df()
    print(f"\nTotal records: {len(df)}")
    print(f"Unique experiments: {df['experiment'].nunique()}")
    print(f"Unique implementations per experiment:")
    for exp in df['experiment'].unique():
        print(f"  {exp}: {df[df['experiment'] == exp]['implementation'].nunique()}")
