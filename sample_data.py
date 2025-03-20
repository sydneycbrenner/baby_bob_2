import pandas as pd
import pickle
import os
import numpy as np
from typing import List, Dict, Any, Optional, Union

# Path to store the pickle file
MASTER_DF_PATH = r"/Users/sydneyfiller/PycharmProjects/baby_bob/master_config.pkl"

# Actual data columns
data_columns = [
    'univ', 'experiment', 'implementation', 'frontier', 'frontier_keys',
    'frontier_values', 'backtest_name_2024', 'backtest_user_2024',
    'is_backtest_complete', 'is_approved_config_sydney', 'is_approved_config_joey',
    'is_approved_comparison_sydney', 'is_approved_comparison_joey',
    'is_approved_final_summary_sydney', 'is_approved_final_summary_joey'
]

def create_fake_master_config_df() -> pd.DataFrame:
    """
    Creates and returns a fake master config DataFrame for testing purposes.
    This function generates a more comprehensive dataset with various scenarios.
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
        is_approved_config_sydney = progress_state > 0 or i % 3 == 0
        is_approved_config_joey = progress_state > 0 or i % 3 == 1
        is_approved_comparison_sydney = progress_state > 1
        is_approved_comparison_joey = progress_state > 1
        is_approved_final_summary_sydney = progress_state > 2
        is_approved_final_summary_joey = progress_state > 3
        
        # Create record
        record = {
            'univ': univ,
            'experiment': experiment,
            'implementation': implementation,
            'frontier': frontier_name,
            'frontier_keys': frontier_keys,
            'frontier_values': frontier_values,
            'backtest_name_2024': backtest_name,
            'backtest_user_2024': backtest_user,
            'is_backtest_complete': is_backtest_complete,
            'is_approved_config_sydney': is_approved_config_sydney,
            'is_approved_config_joey': is_approved_config_joey,
            'is_approved_comparison_sydney': is_approved_comparison_sydney,
            'is_approved_comparison_joey': is_approved_comparison_joey,
            'is_approved_final_summary_sydney': is_approved_final_summary_sydney,
            'is_approved_final_summary_joey': is_approved_final_summary_joey
        }
        
        records.append(record)
    
    # Create DataFrame from records
    master_config_df = pd.DataFrame(records)
    
    return master_config_df

def save_master_config_df(df: pd.DataFrame) -> None:
    """
    Saves the master config DataFrame to a pickle file.
    
    Args:
        df: The DataFrame to save
    """
    pickle.dump(df, open(MASTER_DF_PATH, 'wb'))
    print(f"Saved master config to {MASTER_DF_PATH}")

def load_master_config_df() -> pd.DataFrame:
    """
    Loads the master config DataFrame from a pickle file.
    If the file doesn't exist, creates a fake DataFrame and saves it.
    
    Returns:
        The loaded or newly created DataFrame
    """
    if os.path.exists(MASTER_DF_PATH):
        return pd.read_pickle(MASTER_DF_PATH)
    else:
        # Create a fake DataFrame
        df = create_fake_master_config_df()
        # Save it for future use
        save_master_config_df(df)
        return df

def get_experiment_approval_status(df: pd.DataFrame, experiment: str, 
                                 implementation: str, user: str,
                                 approval_type: str='config') -> bool:
    """
    Checks if an experiment-implementation needs approval from a specific user.
    
    Args:
        df: The master config DataFrame
        experiment: The experiment name
        implementation: The implementation name
        user: Either 'sydney' or 'joey'
        approval_type: One of 'config', 'comparison', or 'final_summary'
    
    Returns:
        True if approved, False otherwise
    """
    # Validate input
    assert approval_type in ['config', 'comparison', 'final_summary']
    assert user in ['sydney', 'joey']
    
    # Filter the DataFrame
    filtered_df = df[(df['experiment'] == experiment) & (df['implementation'] == implementation)]
    
    if filtered_df.empty:
        return False
    
    # Get the approval status
    column_name = f'is_approved_{approval_type}_{user}'
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

def get_experiments_needing_approval(df: pd.DataFrame, user: str, 
                                     approval_type: str='config') -> List[Dict[str, str]]:
    """
    Returns a list of experiments and implementations that need approval from a specific user.
    
    Args:
        df: The master config DataFrame
        user: Either 'sydney' or 'joey'
        approval_type: One of 'config', 'comparison', or 'final_summary'
    
    Returns:
        List of dictionaries with experiment and implementation info
    """
    # Validate input
    assert approval_type in ['config', 'comparison', 'final_summary']
    assert user in ['sydney', 'joey']
    
    # Column to check
    column_name = f'is_approved_{approval_type}_{user}'
    
    # Filter for items not approved by this user
    needs_approval = df[df[column_name] == False]
    
    # For comparison and final approval, also check that prerequisites are met
    if approval_type == 'comparison':
        # Only include if backtest is complete
        needs_approval = needs_approval[needs_approval['is_backtest_complete'] == True]
    elif approval_type == 'final_summary':
        # Only include if comparison is approved by both users
        needs_approval = needs_approval[
            (needs_approval['is_approved_comparison_sydney'] == True) &
            (needs_approval['is_approved_comparison_joey'] == True)
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
    df = create_fake_master_config_df()
    save_master_config_df(df)
    print("Created and saved fake master config DataFrame.")
    
    # Show some data about the DataFrame
    print(f"\nTotal records: {len(df)}")
    print(f"Unique experiments: {df['experiment'].nunique()}")
    print(f"Unique implementations per experiment:")
    for exp in df['experiment'].unique():
        print(f"  {exp}: {df[df['experiment'] == exp]['implementation'].nunique()}")
    
    # Show approval needs
    sydney_config_needs = get_experiments_needing_approval(df, 'sydney', 'config')
    joey_config_needs = get_experiments_needing_approval(df, 'joey', 'config')
    
    print(f"\nSydney needs to approve {len(sydney_config_needs)} configs")
    print(f"Joey needs to approve {len(joey_config_needs)} configs")