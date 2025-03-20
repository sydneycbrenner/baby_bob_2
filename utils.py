import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import uuid
import pickle
from sample_data import data_columns, save_master_config_df

def run_backtest(experiment: str, implementation: str) -> str:
    """
    Placeholder function for running a backtest.
    In a real implementation, this would trigger a backtest process.
    
    Args:
        experiment: The experiment name
        implementation: The implementation name
    
    Returns:
        A status message
    """
    st.session_state.master_config_df.loc[
        (st.session_state.master_config_df['experiment'] == experiment) & 
        (st.session_state.master_config_df['implementation'] == implementation),
        'is_backtest_complete'
    ] = True
    
    # In a real implementation, save the DataFrame back to the pickle file
    save_master_config_df(st.session_state.master_config_df)
    
    return f"Backtest completed for {experiment} - {implementation}"

def update_approval_status(experiment: str, implementation: str, user: str, approval_type: str, approve: bool = True) -> str:
    """
    Updates the approval status in the master config DataFrame.
    
    Args:
        experiment: The experiment name
        implementation: The implementation name
        user: Either 'sydney' or 'joey'
        approval_type: One of 'config', 'comparison', or 'final_summary'
        approve: True to approve, False to revoke approval
    
    Returns:
        A status message
    """
    column_name = f'is_approved_{approval_type}_{user}'
    
    # Update the status
    st.session_state.master_config_df.loc[
        (st.session_state.master_config_df['experiment'] == experiment) & 
        (st.session_state.master_config_df['implementation'] == implementation),
        column_name
    ] = approve
    
    # In a real implementation, save the DataFrame back to the pickle file
    save_master_config_df(st.session_state.master_config_df)
    
    action = "approved" if approve else "revoked"
    return f"{approval_type.capitalize()} {action} by {user} for {experiment} - {implementation}"

def helper_function(backtest_name: str, backtest_user: str) -> Dict[str, Any]:
    """
    Generate a sample config for display in the UI.
    This is a placeholder that would be replaced with actual config loading.
    
    Args:
        backtest_name: The name of the backtest
        backtest_user: The user who ran the backtest
    
    Returns:
        A dictionary containing the config data
    """
    # For demonstration purposes, returning a mock config
    config = {
        "strategy": f"Strategy_{backtest_name}",
        "timeframe": "1h",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 10000,
        "risk_percent": 2.0,
        "max_open_trades": 5,
        "leverage": 1.0,
        "user": backtest_user,
        "created_at": "2024-01-15",
        "version": np.random.randint(1, 5)  # Random version for demo difference
    }

    # Add a nested dictionary for some configs
    if np.random.random() > 0.5:  # 50% chance to add advanced params
        config["advanced_params"] = {
            "max_drawdown": np.random.randint(10, 30),
            "profit_factor": round(np.random.uniform(1.0, 2.5), 1),
            "recovery_factor": round(np.random.uniform(1.5, 3.0), 1),
            "sharpe_ratio": round(np.random.uniform(0.8, 2.0), 1),
            "sortino_ratio": round(np.random.uniform(1.0, 3.0), 1)
        }

    return config

def create_comparison_dataframe(configs: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a DataFrame from multiple configs with parameters as rows and configs as columns.
    Handles nested dictionaries by representing them as "[dict]" in the main dataframe.
    
    Args:
        configs: Dictionary of config dictionaries, keyed by config_id
    
    Returns:
        A pandas DataFrame for comparison
    """
    if not configs:
        return pd.DataFrame()

    # Get all unique keys from all configs
    all_keys = set()
    for config in configs.values():
        all_keys.update(config.keys())

    # Create DataFrame with parameters as index
    data = {}
    for config_id, config in configs.items():
        config_data = {}
        for key in all_keys:
            value = config.get(key, None)
            # Mark dictionary values for special handling
            if isinstance(value, dict):
                config_data[key] = "[dict]"
            else:
                config_data[key] = value
        data[config_id] = config_data

    df = pd.DataFrame(data)
    return df

def check_both_approved(exp: str, impl: str, approval_type: str) -> bool:
    """
    Checks if an experiment-implementation has been approved by both users.
    
    Args:
        exp: The experiment name
        impl: The implementation name
        approval_type: One of 'config', 'comparison', or 'final_summary'
    
    Returns:
        True if approved by both users, False otherwise
    """
    df = st.session_state.master_config_df
    sydney_col = f'is_approved_{approval_type}_sydney'
    joey_col = f'is_approved_{approval_type}_joey'
    
    filtered_df = df[(df['experiment'] == exp) & (df['implementation'] == impl)]
    if filtered_df.empty:
        return False
        
    return filtered_df[sydney_col].iloc[0] and filtered_df[joey_col].iloc[0]

def get_config_for_experiment(exp: str, impl: str) -> Dict[str, Any]:
    """
    Get config data for a specific experiment-implementation combination.
    In a real implementation, this would fetch the actual config data.
    
    Args:
        exp: The experiment name
        impl: The implementation name
    
    Returns:
        A dictionary containing the config data
    """
    df = st.session_state.master_config_df
    filtered_df = df[(df['experiment'] == exp) & (df['implementation'] == impl)]
    
    if filtered_df.empty:
        return {}
    
    # Get the backtest info
    backtest_name = filtered_df['backtest_name_2024'].iloc[0]
    backtest_user = filtered_df['backtest_user_2024'].iloc[0]
    
    # Generate a config based on the backtest info
    config = helper_function(backtest_name, backtest_user)
    
    # Add specific experiment/implementation info
    config.update({
        "experiment": exp,
        "implementation": impl,
        "universe": filtered_df['univ'].iloc[0],
        "frontier": filtered_df['frontier'].iloc[0],
    })
    
    return config

def prepare_configs_for_comparison(experiment: str) -> None:
    """
    Prepares the experiment configurations for viewing in the Config Comparison Tool.
    This function sets up session state variables that will be used by the
    Config Comparison Tool to display the relevant configurations.
    
    Args:
        experiment: The experiment name
    """
    # Get all implementations for this experiment
    df = st.session_state.master_config_df
    exp_df = df[df['experiment'] == experiment]
    
    # Clear existing configs
    st.session_state.configs = {}
    
    # Generate configs for each implementation
    for _, row in exp_df.iterrows():
        impl = row['implementation']
        backtest_name = row['backtest_name_2024']
        backtest_user = row['backtest_user_2024']
        
        # Create a unique config ID
        config_id = f"{backtest_name}_{backtest_user}_{impl}"
        
        # Generate a config
        config = helper_function(backtest_name, backtest_user)
        
        # Add specific experiment/implementation info
        config.update({
            "experiment": experiment,
            "implementation": impl,
            "universe": row['univ'],
            "frontier": row['frontier'],
        })
        
        # Store in session state
        st.session_state.configs[config_id] = config
    
    # Set flag to indicate configs are loaded
    st.session_state.configs_loaded = True
    
    # Set the page to Config Comparison Tool
    st.session_state.selected_page = "Config Comparison Tool"

def get_comparison_data(exp: str, impl: str) -> Dict[str, Any]:
    """
    Generate comparison data for a specific experiment-implementation.
    In a real implementation, this would fetch the actual comparison data.
    
    Args:
        exp: The experiment name
        impl: The implementation name
    
    Returns:
        A dictionary containing the comparison data
    """
    df = st.session_state.master_config_df
    filtered_df = df[(df['experiment'] == exp) & (df['implementation'] == impl)]
    
    if filtered_df.empty:
        return {}
    
    # Create sample comparison data
    comparison_data = {
        "frontier": filtered_df['frontier'].iloc[0],
        "frontier_keys": filtered_df['frontier_keys'].iloc[0],
        "frontier_values": filtered_df['frontier_values'].iloc[0],
        "metrics": {
            "sharpe_ratio": round(np.random.uniform(0.8, 2.0), 2),
            "sortino_ratio": round(np.random.uniform(1.0, 3.0), 2),
            "max_drawdown": f"{round(np.random.uniform(5, 25), 1)}%",
            "win_rate": f"{round(np.random.uniform(40, 70), 1)}%"
        }
    }
    
    return comparison_data

def get_final_summary(exp: str, impl: str) -> Dict[str, Any]:
    """
    Generate final summary data for a specific experiment-implementation.
    In a real implementation, this would fetch the actual summary data.
    
    Args:
        exp: The experiment name
        impl: The implementation name
    
    Returns:
        A dictionary containing the final summary data
    """
    df = st.session_state.master_config_df
    filtered_df = df[(df['experiment'] == exp) & (df['implementation'] == impl)]
    
    if filtered_df.empty:
        return {}
    
    # Create sample final summary data
    final_summary = {
        "implementation": impl,
        "experiment": exp,
        "universe": filtered_df['univ'].iloc[0],
        "recommendation": "Approve for production",
        "key_metrics": {
            "annual_return": f"{round(np.random.uniform(5, 15), 1)}%",
            "volatility": f"{round(np.random.uniform(5, 15), 1)}%",
            "sharpe_ratio": round(np.random.uniform(0.8, 2.0), 2),
            "max_drawdown": f"{round(np.random.uniform(5, 25), 1)}%",
        },
        "notes": "All performance metrics meet required thresholds."
    }
    
    return final_summary

def create_summary_dataframe() -> pd.DataFrame:
    """
    Creates a summary DataFrame showing the status of all experiments.
    
    Returns:
        A pandas DataFrame with the summary data
    """
    df = st.session_state.master_config_df
    unique_experiments = df['experiment'].unique()
    
    # Create a summary dataframe showing approval status for all experiments
    summary_data = []
    
    for experiment in unique_experiments:
        exp_df = df[df['experiment'] == experiment]
        for impl in exp_df['implementation'].unique():
            impl_df = exp_df[exp_df['implementation'] == impl]
            
            # Get approval statuses
            config_approved = check_both_approved(experiment, impl, 'config')
            backtest_complete = impl_df['is_backtest_complete'].iloc[0]
            comparison_approved = check_both_approved(experiment, impl, 'comparison')
            final_approved = check_both_approved(experiment, impl, 'final_summary')
            
            # Calculate overall status
            if final_approved:
                overall_status = "Complete"
            elif comparison_approved:
                overall_status = "Final Review Needed"
            elif backtest_complete:
                overall_status = "Comparison Review Needed"
            elif config_approved:
                overall_status = "Backtest Needed"
            else:
                overall_status = "Config Review Needed"
            
            # Add to summary data
            summary_data.append({
                "Experiment": experiment,
                "Implementation": impl,
                "Universe": impl_df['univ'].iloc[0],
                "Config Approved": "✅" if config_approved else "❌",
                "Backtest Complete": "✅" if backtest_complete else "❌",
                "Comparison Approved": "✅" if comparison_approved else "❌",
                "Final Approved": "✅" if final_approved else "❌",
                "Status": overall_status
            })
    
    # Create summary dataframe
    summary_df = pd.DataFrame(summary_data)
    return summary_df