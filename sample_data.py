import pandas as pd
import os
import numpy as np
from typing import List, Dict, Any, Optional, Union

# Import the SQLite utilities
from sqlite_utils import (
    load_master_config_df, save_master_config_df, 
    create_fake_master_config_data, populate_db_with_fake_data,
    update_experiment_approval, update_backtest_status, 
    get_experiment_data, get_experiment_implementation,
    data_columns
)

def get_experiment_approval_status(df: pd.DataFrame, experiment: str, 
                                 implementation: str,
                                 approval_type: str='config') -> bool:
    """
    Checks if an experiment-implementation is approved.
    
    Args:
        df: The master config DataFrame
        experiment: The experiment name
        implementation: The implementation name
        approval_type: One of 'config', 'comparison', or 'final_summary'
    
    Returns:
        True if approved, False otherwise
    """
    # Validate input
    assert approval_type in ['config', 'comparison', 'final_summary']
    
    # Filter the DataFrame
    filtered_df = df[(df['experiment'] == experiment) & (df['implementation'] == implementation)]
    
    if filtered_df.empty:
        return False
    
    # Get the approval status
    column_name = f'is_approved_{approval_type}'
    return filtered_df[column_name].iloc[0]

def get_pct_of_experiment_completed(df: pd.DataFrame, experiment: str) -> float:
    """
    Calculates the percentage of completed backtests for a given experiment.
    
    Args:
        df: The master config DataFrame
        experiment: The experiment name
    
    Returns:
        The percentage of completed backtests (0.0 to 1.0)
    """
    experiment_df = df[df['experiment'] == experiment]
    
    if experiment_df.empty:
        return 0.0
    
    total_impls = len(experiment_df)
    completed_impls = experiment_df['is_backtest_complete'].sum()
    
    return completed_impls / total_impls

def get_experiments_needing_approval(df: pd.DataFrame, 
                                     approval_type: str='config') -> List[Dict[str, str]]:
    """
    Returns a list of experiments and implementations that need approval.
    
    Args:
        df: The master config DataFrame
        approval_type: One of 'config', 'comparison', or 'final_summary'
    
    Returns:
        List of dictionaries with experiment and implementation info
    """
    # Validate input
    assert approval_type in ['config', 'comparison', 'final_summary']
    
    # Column to check
    column_name = f'is_approved_{approval_type}'
    
    # Filter for items not approved
    needs_approval = df[df[column_name] == False]
    
    # For comparison and final approval, also check that prerequisites are met
    if approval_type == 'comparison':
        # Only include if backtest is complete
        needs_approval = needs_approval[needs_approval['is_backtest_complete'] == True]
    elif approval_type == 'final_summary':
        # Only include if comparison is approved
        needs_approval = needs_approval[
            (needs_approval['is_approved_comparison'] == True)
        ]
    
    # Create result list
    result = []
    for _, row in needs_approval.iterrows():
        result.append({
            'experiment': row['experiment'],
            'implementation': row['implementation'],
            'universe': row['univ']
        })
    
    return result

# Create and save a fake DataFrame if running this file directly
if __name__ == "__main__":
    # This will create the SQLite database and populate it with fake data
    populate_db_with_fake_data()
    
    # Load the data to show information about it
    df = load_master_config_df()
    
    # Show some data about the DataFrame
    print(f"\nTotal records: {len(df)}")
    print(f"Unique experiments: {df['experiment'].nunique()}")
    print(f"Unique implementations per experiment:")
    for exp in df['experiment'].unique():
        print(f"  {exp}: {df[df['experiment'] == exp]['implementation'].nunique()}")
    
    # Show approval needs
    config_needs = get_experiments_needing_approval(df, 'config')
    
    print(f"\nNeeds to approve {len(config_needs)} configs")