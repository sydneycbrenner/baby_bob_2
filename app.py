import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import uuid

# Import from our modules
from utils.db_utils import load_master_config_df
from utils.core_utils import (
    run_backtest, update_approval_status, helper_function, 
    create_comparison_dataframe, check_approved,
    get_config_for_experiment, get_comparison_data, 
    get_final_summary, create_summary_dataframe
)

# Set page configuration for a cleaner look
st.set_page_config(
    page_title="Config Comparison Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .config-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .st-emotion-cache-1y4p8pa {
        max-width: 100%;
    }
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
    
    /* Status indicator styling */
    .status-green {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
    }
    .status-red {
        background-color: #f44336;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
    }

    /* Custom styling for the highlighted rows */
    [data-testid="stDataFrameRow"]:has([data-diff="true"]) {
        background-color: rgba(255, 255, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for storing configs and selected page
if 'configs' not in st.session_state:
    st.session_state.configs = {}

if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "Config Comparison Tool"

if 'master_config_df' not in st.session_state:
    # Load the master config DataFrame from SQLite
    st.session_state.master_config_df = load_master_config_df()

# Sidebar for selecting the page
with st.sidebar:
    page_options = ["Config Comparison Tool", "2024 Refresh", "Summary Table Comparison Tool"]
    selected_page = st.radio("Navigation", page_options)
    st.session_state.selected_page = selected_page

# Page 1: Original Config Comparison Tool
if st.session_state.selected_page == "Config Comparison Tool":
    # App title
    st.title("Config Comparison Tool")
    st.markdown("Compare configuration parameters across different backtests")

    # Sidebar for input controls
    with st.sidebar:
        st.header("Load Config")

        # Add tabs for custom config and official books
        load_tab1, load_tab2 = st.tabs(["Custom Config", "Official Book"])

        with load_tab1:
            backtest_name = st.text_input("Backtest Name", placeholder="Enter backtest name")
            backtest_user = st.text_input("Backtest User", placeholder="Enter user name")

            # Generate a unique ID for this config
            if st.button("Load Config", key="load_custom_config"):
                if backtest_name and backtest_user:
                    config_id = f"{backtest_name}_{backtest_user}_{uuid.uuid4().hex[:8]}"
                    config_data = helper_function(backtest_name, backtest_user)
                    st.session_state.configs[config_id] = config_data
                    st.success(f"Loaded config for {backtest_name} by {backtest_user}")
                else:
                    st.error("Please enter both backtest name and user.")

        with load_tab2:
            official_book_options = ["RC EDI", "RC AE", "RC AEP"]
            selected_book = st.selectbox(
                "Select Official Book",
                options=["Select an option"] + official_book_options
            )

            if st.button("Load Official Book", key="load_official_book") and selected_book != "Select an option":
                # Predefined configurations for official books
                official_configs = {
                    "RC EDI": {
                        "strategy": "Strategy_RC_EDI",
                        "timeframe": "1h",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                        "initial_capital": 10000,
                        "risk_percent": 1.5,
                        "max_open_trades": 3,
                        "leverage": 1.0,
                        "user": "official",
                        "created_at": "2024-01-15",
                        "version": 2,
                        "advanced_params": {
                            "max_drawdown": 25.0,
                            "profit_factor": 1.5,
                            "recovery_factor": 2.0,
                            "sharpe_ratio": 1.2,
                            "sortino_ratio": 1.8
                        }
                    },
                    "RC AE": {
                        "strategy": "Strategy_RC_AE",
                        "timeframe": "4h",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                        "initial_capital": 15000,
                        "risk_percent": 2.0,
                        "max_open_trades": 4,
                        "leverage": 1.5,
                        "user": "official",
                        "created_at": "2024-01-15",
                        "version": 3,
                        "advanced_params": {
                            "max_drawdown": 20.0,
                            "profit_factor": 1.8,
                            "recovery_factor": 2.2,
                            "sharpe_ratio": 1.5,
                            "sortino_ratio": 2.1
                        }
                    },
                    "RC AEP": {
                        "strategy": "Strategy_RC_AEP",
                        "timeframe": "1d",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                        "initial_capital": 20000,
                        "risk_percent": 2.5,
                        "max_open_trades": 5,
                        "leverage": 2.0,
                        "user": "official",
                        "created_at": "2024-01-15",
                        "version": 1,
                        "advanced_params": {
                            "max_drawdown": 15.0,
                            "profit_factor": 2.0,
                            "recovery_factor": 2.5,
                            "sharpe_ratio": 1.7,
                            "sortino_ratio": 2.3
                        }
                    }
                }

                if selected_book in official_configs:
                    config_id = f"Official_{selected_book}_{uuid.uuid4().hex[:8]}"
                    st.session_state.configs[config_id] = official_configs[selected_book]
                    st.success(f"Loaded official book: {selected_book}")

        # Config removal section
        if st.session_state.configs:
            st.header("Remove Config")
            configs_to_remove = st.multiselect(
                "Select configs to remove",
                options=list(st.session_state.configs.keys()),
                format_func=lambda x: f"{x.split('_')[0]} by {x.split('_')[1]}"
            )

            if st.button("Remove Selected", key="remove_config"):
                for config_id in configs_to_remove:
                    if config_id in st.session_state.configs:
                        del st.session_state.configs[config_id]
                st.success("Selected configs removed")

        # Clear All section
        st.header("Clear All Configs")
        if st.button("Clear All Configs", key="clear_all_configs"):
            st.session_state.configs = {}
            st.success("All configs cleared")

    # Main content area for displaying config comparison
    if st.session_state.configs:
        st.subheader("Config Comparison")

        # Create dataframe from configs
        df = create_comparison_dataframe(st.session_state.configs)

        # Track any nested dictionaries in the configs
        nested_dict_params = {}

        # Identify parameters that contain dictionaries
        for config_id, config in st.session_state.configs.items():
            for key, value in config.items():
                if isinstance(value, dict):
                    if key not in nested_dict_params:
                        nested_dict_params[key] = {}
                    nested_dict_params[key][config_id] = value

        # Find rows with differences
        rows_with_diffs = []
        if df.shape[1] > 1:  # Only check for differences if there's more than one config
            for idx in df.index:
                row = df.loc[idx]
                unique_values = set(str(val) for val in row if not pd.isna(val))
                if len(unique_values) > 1:
                    rows_with_diffs.append(idx)

            if rows_with_diffs:
                st.markdown("**Rows highlighted in yellow contain differences across configs**")

        # Format the column headers to show backtest name and user
        column_config = {
            col: st.column_config.Column(
                f"{col.split('_')[0]} by {col.split('_')[1]}"
            ) for col in df.columns
        }

        # Highlight differences by using a custom styled DataFrame
        # Convert rows_with_diffs to a set for faster lookups
        diff_rows_set = set(rows_with_diffs)

        # This function will apply styling directly
        def style_df(data):
            # Create a copy of the DataFrame
            styled = pd.DataFrame('', index=data.index, columns=data.columns)

            # Apply background color to rows with differences
            for idx in data.index:
                if idx in diff_rows_set:
                    styled.loc[idx, :] = 'background-color: rgba(255, 255, 0, 0.3)'

            return styled

        # Apply styling if there are differences and more than one column
        if rows_with_diffs and df.shape[1] > 1:
            display_df = df.style.apply(lambda _: style_df(df), axis=None)
        else:
            display_df = df

        # Use the Streamlit data editor
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=False,
            column_config=column_config,
            key="config_editor",
            disabled=False
        )

        # Export option
        st.markdown("### Export Options")

        if st.button("Copy Dataframe"):
            # Display as a simple table format for easy copy-paste
            st.code(df.to_string(), language="text")

        # Display nested dictionary comparisons if any exist
        if nested_dict_params:
            st.markdown("---")
            st.subheader("Nested Configuration Parameters")

            # Create a dropdown to select which nested parameter to view
            if len(nested_dict_params) > 1:
                selected_nested_param = st.selectbox(
                    "Select parameter to compare nested values",
                    options=list(nested_dict_params.keys())
                )
            else:
                selected_nested_param = list(nested_dict_params.keys())[0]

            st.markdown(f"**Comparing nested values for: {selected_nested_param}**")

            # Get all unique keys from the nested dictionaries
            all_nested_keys = set()
            for config_nested_dict in nested_dict_params[selected_nested_param].values():
                all_nested_keys.update(config_nested_dict.keys())

            # Create a dataframe for the nested parameter
            nested_data = {}
            for config_id, nested_dict in nested_dict_params[selected_nested_param].items():
                config_nested_data = {}
                for key in all_nested_keys:
                    config_nested_data[key] = nested_dict.get(key, None)
                nested_data[config_id] = config_nested_data

            nested_df = pd.DataFrame(nested_data)

            # Find rows with differences in the nested dataframe
            nested_rows_with_diffs = []
            if nested_df.shape[1] > 1:  # Only check for differences if there's more than one config
                for idx in nested_df.index:
                    row = nested_df.loc[idx]
                    unique_values = set(str(val) for val in row if not pd.isna(val))
                    if len(unique_values) > 1:
                        nested_rows_with_diffs.append(idx)

                if nested_rows_with_diffs:
                    st.markdown("**Rows highlighted in yellow contain differences across configs**")

            # Convert nested_rows_with_diffs to a set for faster lookups
            nested_diff_rows_set = set(nested_rows_with_diffs)

            # Function to style nested dataframe
            def style_nested_df(data):
                styled = pd.DataFrame('', index=data.index, columns=data.columns)
                for idx in data.index:
                    if idx in nested_diff_rows_set:
                        styled.loc[idx, :] = 'background-color: rgba(255, 255, 0, 0.3)'
                return styled

            # Apply styling if there are differences
            if nested_rows_with_diffs and nested_df.shape[1] > 1:
                nested_display_df = nested_df.style.apply(lambda _: style_nested_df(nested_df), axis=None)
            else:
                nested_display_df = nested_df

            # Display the nested dataframe
            nested_column_config = {
                col: st.column_config.Column(
                    f"{col.split('_')[0]} by {col.split('_')[1]}"
                ) for col in nested_df.columns
            }

            st.data_editor(
                nested_display_df,
                use_container_width=True,
                height=400,  # Slightly smaller than the main dataframe
                hide_index=False,
                column_config=nested_column_config,
                key="nested_config_editor",
                disabled=False
            )

            # Add export option for nested dataframe
            if st.button("Copy Nested Dataframe"):
                st.code(nested_df.to_string(), language="text")

    else:
        st.info("No configs loaded. Please use the sidebar to load configs.")

# Page 2: 2024 Refresh
elif st.session_state.selected_page == "2024 Refresh":
    # Import and render the 2024 Refresh page from the separate module
    from refresh_2024 import render_2024_refresh_page
    render_2024_refresh_page()

# Page 3: Summary Table Comparison Tool
elif st.session_state.selected_page == "Summary Table Comparison Tool":
    # Import and render the Summary Table Comparison Tool page from the utils module
    from utils.summary_comparison_utils import render_summary_table_comparison
    render_summary_table_comparison()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888;">
        Trading Strategy Comparison Suite v2.1 | Made with Streamlit
    </div>
    """,
    unsafe_allow_html=True
)