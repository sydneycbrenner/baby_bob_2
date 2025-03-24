import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

# Import from our modules
from utils.db_utils import load_master_config_df
from utils.core_utils import (
    run_backtest, update_approval_status, 
    get_config_for_experiment, get_comparison_data,
    get_final_summary, create_summary_dataframe,
    prepare_configs_for_comparison
)

def render_2024_refresh_page():
    """
    Renders the 2024 Refresh page with experiments listed sequentially
    """
    st.title("2024 Refresh")
    st.markdown("Review and approve experiments for the 2024 refresh")
    
    # Get unique experiments
    unique_experiments = st.session_state.master_config_df['experiment'].unique().tolist()
    
    # Sidebar options
    with st.sidebar:
        # Add option to regenerate test data
        st.header("Data Options")
        if st.button("Regenerate Test Data"):
            st.session_state.master_config_df = load_master_config_df()
            st.success("Regenerated test data")
            st.rerun()
    
    if not unique_experiments:
        st.warning("No experiments found in the database. Please regenerate test data.")
    else:
        # Calculate overall progress
        total_backtests = len(st.session_state.master_config_df)
        completed_backtests = st.session_state.master_config_df['is_backtest_complete'].sum()
        completion_pct = completed_backtests / total_backtests
        
        # Display overall progress bar
        st.subheader("Overall Backtest Progress")
        st.progress(completion_pct)
        st.caption(f"{int(completion_pct * 100)}% complete ({completed_backtests} of {total_backtests} backtests)")
        
        # Dashboard summary view of all experiments
        st.subheader("Experiment Dashboard")
        
        # Create summary dataframe
        summary_df = create_summary_dataframe()
        
        # Apply custom styling for the Status column
        def color_status(df):
            # Create a styler object
            styler = df.style
            
            # Apply formatting to the Status column
            styler = styler.applymap(
                lambda v: "background-color: #4CAF50; color: white" if v == "Complete" else
                          "background-color: #f44336; color: white" if v == "Config Review Needed" else
                          "background-color: #ff9800; color: white" if "Needed" in str(v) else "",
                subset=['Status']
            )
            
            # Apply formatting to approval columns using icons instead of HTML text
            for col in ["Config Approved", "Backtest Complete", "Comparison Approved", "Final Approved"]:
                styler = styler.format(
                    {col: lambda x: "✅" if x == "✅" else "❌"},
                )
            
            return styler
        
        st.write("View the status of all experiments at a glance")
        
        # Apply styling to the dataframe
        styled_df = color_status(summary_df)
        
        # Display the interactive summary table
        selection = st.dataframe(
            styled_df,
            use_container_width=True,
            height=300,
            hide_index=True,
            column_config={
                "Config Approved": st.column_config.Column("Config Approved", width="small"),
                "Backtest Complete": st.column_config.Column("Backtest Complete", width="small"),
                "Comparison Approved": st.column_config.Column("Comparison Approved", width="small"),
                "Final Approved": st.column_config.Column("Final Approved", width="small"),
            }
        )
            
        # Detail view - list all experiments sequentially
        st.subheader("Experiment Details")
        
        # Process each experiment
        for experiment in unique_experiments:
            # Create an expander for each experiment
            with st.expander(f"Experiment: {experiment}", expanded=True):
                # Filter dataframe for this experiment
                exp_df = st.session_state.master_config_df[st.session_state.master_config_df['experiment'] == experiment]
                unique_implementations = exp_df['implementation'].unique().tolist()
                
                # Calculate experiment-specific progress
                exp_total = len(exp_df)
                exp_completed = exp_df['is_backtest_complete'].sum()
                exp_progress = exp_completed / exp_total if exp_total > 0 else 0
                
                # Show experiment progress
                st.progress(exp_progress)
                st.caption(f"{int(exp_progress * 100)}% complete ({exp_completed} of {exp_total} implementations)")
                
                # Get status values for this experiment
                config_approved = all(exp_df['is_approved_config'])
                backtest_complete = all(exp_df['is_backtest_complete'])
                comparison_approved = all(exp_df['is_approved_comparison'])
                final_approved = all(exp_df['is_approved_final_summary'])
                
                # Create columns for the workflow stages
                col1, col2, col3, col4 = st.columns(4)
            
                # Stage 1: Config Review
                with col1:
                    st.markdown("#### Config Review")
                    
                    if config_approved:
                        st.markdown('<div class="status-green">Approved</div>', unsafe_allow_html=True)
                        # Show revoke button
                        if st.button("Revoke", key=f"config_revoke_{experiment}"):
                            # Update all implementations for this experiment
                            for impl in unique_implementations:
                                update_approval_status(experiment, impl, 'config', approve=False)
                            st.success(f"Config approval revoked for {experiment}")
                            st.rerun()
                    else:
                        st.markdown('<div class="status-red">Pending</div>', unsafe_allow_html=True)
                        # Show approval button
                        if st.button("Approve", key=f"config_{experiment}"):
                            # Update all implementations for this experiment
                            for impl in unique_implementations:
                                update_approval_status(experiment, impl, 'config')
                            st.success(f"Config approved for {experiment}")
                            st.rerun()
                                
                    # Show config details button that redirects to Config Comparison Tool
                    if st.button("View Config in Comparison Tool", key=f"view_config_{experiment}"):
                        # Prepare data for the Config Comparison Tool
                        prepare_configs_for_comparison(experiment)
                        st.rerun()
                
                # Stage 2: Run Backtest
                with col2:
                    st.markdown("#### Run Backtest")
                    
                    if backtest_complete:
                        st.markdown('<div class="status-green">Complete</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="status-red">Not Run</div>', unsafe_allow_html=True)
                        
                        # Only enable run backtest if config is approved
                        if config_approved:
                            if st.button(f"Run Backtest", key=f"run_backtest_{experiment}"):
                                # Run backtest for all implementations
                                for impl in unique_implementations:
                                    result = run_backtest(experiment, impl)
                                st.success(f"Backtests completed for {experiment}")
                                st.rerun()
                        else:
                            st.warning("Config needs approval from all reviewers")
                    
                    # Add Check Backtests button
                    if st.button("Check Backtests", key=f"check_backtests_{experiment}"):
                        st.info("Calling check_backtests() function - Implement this functionality")
                        # In a real implementation, you would call:
                        # result = check_backtests(experiment)
                        # st.success(result)
                
                # Stage 3: Comparison Review
                with col3:
                    st.markdown("#### Comparison Review")
                    
                    if comparison_approved:
                        st.markdown('<div class="status-green">Approved</div>', unsafe_allow_html=True)
                        # Show revoke button
                        if st.button("Revoke", key=f"comparison_revoke_{experiment}"):
                            # Update all implementations for this experiment
                            for impl in unique_implementations:
                                update_approval_status(experiment, impl, 'comparison', approve=False)
                            st.success(f"Comparison approval revoked for {experiment}")
                            st.rerun()
                    else:
                        st.markdown('<div class="status-red">Pending</div>', unsafe_allow_html=True)
                        # Only show approval button if backtest is complete
                        if backtest_complete:
                            if st.button("Approve", key=f"comparison_{experiment}"):
                                # Update all implementations for this experiment
                                for impl in unique_implementations:
                                    update_approval_status(experiment, impl, 'comparison')
                                st.success(f"Comparison approved for {experiment}")
                                st.rerun()
                    
                    # Show comparison details button if backtest is complete
                    if backtest_complete:
                        if st.button("View Comparison", key=f"view_comparison_{experiment}"):
                            st.session_state[f"show_comparison_{experiment}"] = True
                        
                        # Add Summarize Comparison button
                        if st.button("Summarize Comparison Table", key=f"summarize_comparison_{experiment}"):
                            st.info("Calling summarize_comparison_review() function - Implement this functionality")
                            # In a real implementation, you would call:
                            # result = summarize_comparison_review(experiment)
                            # st.success(result)
                        
                        # Display comparison if button was clicked
                        if st.session_state.get(f"show_comparison_{experiment}", False):
                            # Show a representative comparison from the first implementation
                            impl = unique_implementations[0]
                            comparison_data = get_comparison_data(experiment, impl)
                            st.json(comparison_data)
                            if st.button("Hide Comparison", key=f"hide_comparison_{experiment}"):
                                st.session_state[f"show_comparison_{experiment}"] = False
                                st.rerun()
                    else:
                        st.warning("Backtest needs to be run first")
                
                # Stage 4: Final Review
                with col4:
                    st.markdown("#### Final Review")
                    
                    if final_approved:
                        st.markdown('<div class="status-green">Approved</div>', unsafe_allow_html=True)
                        # Show revoke button
                        if st.button("Revoke", key=f"final_revoke_{experiment}"):
                            # Update all implementations for this experiment
                            for impl in unique_implementations:
                                update_approval_status(experiment, impl, 'final_summary', approve=False)
                            st.success(f"Final summary approval revoked for {experiment}")
                            st.rerun()
                    else:
                        st.markdown('<div class="status-red">Pending</div>', unsafe_allow_html=True)
                        # Only show approval button if comparison is approved
                        if comparison_approved:
                            if st.button("Approve", key=f"final_{experiment}"):
                                # Update all implementations for this experiment
                                for impl in unique_implementations:
                                    update_approval_status(experiment, impl, 'final_summary')
                                st.success(f"Final summary approved for {experiment}")
                                st.rerun()
                    
                    # Show final summary details button if comparison is approved
                    if comparison_approved:
                        if st.button("View Final Summary", key=f"view_final_{experiment}"):
                            st.session_state[f"show_final_{experiment}"] = True
                        
                        # Add Summarize Final Review button 
                        if st.button("Summarize Comparison Review", key=f"summarize_final_{experiment}"):
                            st.info("Calling summarize_comparison_review() function - Implement this functionality")
                            # In a real implementation, you would call:
                            # result = summarize_comparison_review(experiment)
                            # st.success(result)
                        
                        # Display final summary if button was clicked
                        if st.session_state.get(f"show_final_{experiment}", False):
                            # Show a representative final summary from the first implementation
                            impl = unique_implementations[0]
                            final_summary = get_final_summary(experiment, impl)
                            st.json(final_summary)
                            if st.button("Hide Final Summary", key=f"hide_final_{experiment}"):
                                st.session_state[f"show_final_{experiment}"] = False
                                st.rerun()
                    else:
                        st.warning("Comparison needs approval from all reviewers")