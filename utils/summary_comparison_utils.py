import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple

# Import from our utils modules
from utils.db_utils import load_master_config_df

def get_experiment_filters() -> Tuple[str, str, str, List[str]]:
    """
    Creates UI elements for filtering experiments and returns selected values.
    
    Returns:
        Tuple containing (experiment, universe, implementation, frontier_keys)
    """
    # Load master config DataFrame if not in session state
    if 'master_config_df' not in st.session_state:
        st.session_state.master_config_df = load_master_config_df()
    
    df = st.session_state.master_config_df
    
    # Get unique experiments
    experiments = sorted(df['experiment'].unique().tolist())
    
    selected_experiment = st.selectbox(
        "Select Experiment",
        options=experiments,
        key="summary_experiment_selector"
    )
    
    # Filter for the selected experiment
    exp_df = df[df['experiment'] == selected_experiment]
    
    # Get unique universes for this experiment
    universes = sorted(exp_df['univ'].unique().tolist())
    
    selected_universe = st.selectbox(
        "Select Universe",
        options=universes,
        key="summary_universe_selector"
    )
    
    # Filter for the selected universe
    exp_univ_df = exp_df[exp_df['univ'] == selected_universe]
    
    # Get unique implementations for this experiment and universe
    implementations = sorted(exp_univ_df['implementation'].unique().tolist())
    
    selected_implementation = st.selectbox(
        "Select Implementation",
        options=implementations,
        key="summary_implementation_selector"
    )
    
    # Get frontier keys for this experiment-implementation
    impl_row = exp_univ_df[exp_univ_df['implementation'] == selected_implementation].iloc[0]
    frontier_keys = impl_row['frontier_keys']
    frontier_values = impl_row['frontier_values']
    
    # Create multiselect for frontier keys
    if frontier_keys and isinstance(frontier_keys, list):
        # Create options that show both key and value
        frontier_options = [f"{key} = {value}" for key, value in zip(frontier_keys, frontier_values)]
        
        selected_frontiers = st.multiselect(
            "Select Frontier Parameters",
            options=frontier_options,
            default=frontier_options[:2] if len(frontier_options) > 1 else frontier_options,
            key="summary_frontier_selector"
        )
        
        # Extract just the keys from the selected options
        selected_frontier_keys = [option.split(" = ")[0] for option in selected_frontiers]
    else:
        selected_frontier_keys = []
    
    return selected_experiment, selected_universe, selected_implementation, selected_frontier_keys

def generate_summary_data_tables_comparison(
    experiment: str = None,
    universe: str = None,
    implementation: str = None,
    frontier_keys: List[str] = None,
    book_year: str = "2024"
) -> pd.DataFrame:
    """
    Generates dummy summary data tables for comparison.
    This function will be replaced with actual data loading code.
    
    Args:
        experiment: The selected experiment name
        universe: The selected universe
        implementation: The selected implementation
        frontier_keys: List of selected frontier keys
        book_year: The book year to retrieve (2023 or 2024)
        
    Returns:
        DataFrame containing data for the selected book year
    """
    # Log the requested parameters (for future reference when implementing real data fetching)
    if st.session_state.get('debug_mode', False):
        st.write(f"Requesting data for: {experiment} / {universe} / {implementation}")
        st.write(f"Selected frontier keys: {frontier_keys}")
        st.write(f"Book year: {book_year}")
    
    # Create a title for the strategy that includes the filters
    strategy_name = f"{experiment}_{implementation}_{universe}"
    
    # Add frontier keys to the name if provided
    if frontier_keys and len(frontier_keys) > 0:
        frontier_str = "_".join(frontier_keys)
        strategy_name = f"{strategy_name}_{frontier_str}"
    
    # Use pseudo-random seed based on strategy name for consistent results
    np.random.seed(hash(strategy_name) % 10000)
    
    # Create dummy metrics
    metrics = [
        'Total Return', 'Annualized Return', 'Sharpe Ratio', 'Sortino Ratio',
        'Max Drawdown', 'Volatility', 'Alpha', 'Beta', 'Information Ratio',
        'Tracking Error', 'Win Rate', 'Average Win', 'Average Loss', 'Profit Factor'
    ]
    
    # Create dummy values based on selected book year
    if book_year == "2023":
        values = [
            0.156, 0.129, 1.42, 1.89, -0.138, 0.091, 0.032, 0.86, 0.75,
            0.058, 0.62, 0.031, -0.019, 1.65
        ]
    else:  # 2024
        values = [
            0.183, 0.148, 1.56, 2.05, -0.112, 0.095, 0.041, 0.89, 0.82,
            0.062, 0.64, 0.034, -0.021, 1.71
        ]
    
    # Create DataFrame
    data = {
        'Metric': metrics,
        strategy_name: values
    }
    df = pd.DataFrame(data)
    
    # Format certain columns as percentages for display
    df[strategy_name] = df[strategy_name].apply(
        lambda x: f"{x:.2%}" if ('Rate' in df.loc[df[strategy_name] == x, 'Metric'].values[0] or x < 1) else f"{x:.2f}"
    )
    
    return df

def style_summary_table(df: pd.DataFrame, tolerance: float = 0.1) -> pd.DataFrame:
    """
    Apply styling to the summary dataframe based on percent difference.
    Highlights rows where the percent difference exceeds the tolerance level.
    
    Args:
        df: DataFrame with comparison data
        tolerance: Maximum allowed percentage difference (as a decimal)
    
    Returns:
        Styled DataFrame
    """
    # Create a copy for styling
    styled_df = df.copy()
    
    # Function to determine if a row should be highlighted
    def highlight_row(row):
        # Check if 'Pct Difference' is in the row
        if 'Pct Difference' not in row:
            return False
        
        # Convert percentage string to float
        pct_diff = row['Pct Difference'].strip('%')
        try:
            pct_diff = float(pct_diff) / 100
        except ValueError:
            return False
        
        return abs(pct_diff) > tolerance
    
    # Create mask for rows with differences exceeding tolerance
    mask = styled_df.apply(highlight_row, axis=1)
    
    # Create style DataFrame
    style_df = pd.DataFrame('', index=styled_df.index, columns=styled_df.columns)
    style_df.loc[mask, :] = 'background-color: rgba(255, 0, 0, 0.2)'
    
    return style_df

def render_summary_table_comparison():
    """
    Renders the Summary Table Comparison Tool page
    """
    st.title("Summary Table Comparison Tool")
    st.markdown("Compare summary tables between different strategy versions and highlight significant differences")
    
    # Setup layout with a sidebar and main content area
    with st.sidebar:
        st.header("Strategy Selection")
        
        # Add experiment filtering controls
        experiment, universe, implementation, frontier_keys = get_experiment_filters()
        
        # Book Year selection
        book_year = st.selectbox(
            "Book Year",
            options=["2024", "2023"],
            index=0,
            key="book_year_selector"
        )
        
        st.header("Display Settings")
        
        # Tolerance setting
        tolerance = st.slider(
            "Difference Tolerance (%)", 
            min_value=1.0, 
            max_value=50.0, 
            value=10.0, 
            step=1.0,
            help="Highlight differences greater than this percentage"
        ) / 100
        
        # Compare multiple strategies
        st.header("Compare Multiple Strategies")
        
        # Store comparison selections in session state
        if 'comparison_strategies' not in st.session_state:
            st.session_state.comparison_strategies = []
        
        # Button to add current selection to comparison
        if st.button("Add Current Selection to Comparison"):
            # Create a strategy identifier
            strategy_id = f"{experiment} - {implementation} - {universe}"
            
            # Only add if not already in the list
            if strategy_id not in [s['id'] for s in st.session_state.comparison_strategies]:
                st.session_state.comparison_strategies.append({
                    'id': strategy_id,
                    'experiment': experiment,
                    'universe': universe,
                    'implementation': implementation,
                    'frontier_keys': frontier_keys.copy() if frontier_keys else [],
                    'book_year': book_year
                })
                st.success(f"Added {strategy_id} ({book_year}) to comparison")
        
        # Show currently selected strategies
        if st.session_state.comparison_strategies:
            st.subheader("Selected Strategies")
            
            for i, strategy in enumerate(st.session_state.comparison_strategies):
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{i+1}. {strategy['id']} ({strategy.get('book_year', '2024')})**")
                with col2:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.comparison_strategies.pop(i)
                        st.rerun()
            
            if st.button("Clear All Comparisons"):
                st.session_state.comparison_strategies = []
                st.rerun()
        
        # Debug mode toggle
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=False)
        
        # Refresh data button
        if st.button("Refresh Data"):
            if 'summary_data' in st.session_state:
                del st.session_state.summary_data
            st.success("Data refreshed!")
    
    # Main content area
    st.subheader("Strategy Comparison")
    
    # We'll show one table with all selected strategies
    if 'comparison_strategies' not in st.session_state:
        st.session_state.comparison_strategies = []
    
    if not st.session_state.comparison_strategies:
        # If no strategies are in comparison yet, add the current one to start
        if st.button("Add Current Selection to Start Comparison"):
            strategy_id = f"{experiment}_{implementation}_{universe}"
            st.session_state.comparison_strategies.append({
                'id': strategy_id,
                'experiment': experiment,
                'universe': universe,
                'implementation': implementation,
                'frontier_keys': frontier_keys.copy() if frontier_keys else [],
                'book_year': book_year
            })
            st.rerun()
        
        # Show message when no strategies are selected
        st.info("Select a strategy and add it to the comparison using the controls in the sidebar.")
    else:
        # Collect data for all strategies in comparison
        comparison_dfs = []
        
        for strategy in st.session_state.comparison_strategies:
            # Get data for this strategy
            strategy_df = generate_summary_data_tables_comparison(
                experiment=strategy['experiment'],
                universe=strategy['universe'],
                implementation=strategy['implementation'],
                frontier_keys=strategy['frontier_keys'],
                book_year=strategy.get('book_year', '2024')
            )
            
            if strategy_df is not None:
                # Get the strategy column (the one that's not 'Metric')
                strategy_col = [col for col in strategy_df.columns if col != 'Metric'][0]
                
                # Rename it to include book year for clarity
                display_name = f"{strategy['id']} ({strategy.get('book_year', '2024')})"
                strategy_df = strategy_df.rename(columns={strategy_col: display_name})
                
                comparison_dfs.append(strategy_df[['Metric', display_name]])
        
        if comparison_dfs:
            # Merge all dataframes on the Metric column
            merged_df = comparison_dfs[0]
            for df in comparison_dfs[1:]:
                merged_df = pd.merge(merged_df, df, on='Metric')
            
            # Display the merged dataframe
            st.dataframe(
                merged_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Add explanatory text
            st.markdown("""
            **Note**: Add more strategies to compare using the controls in the sidebar. 
            You can select different experiments, implementations, and book years.
            """)
    
