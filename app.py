import streamlit as st
import pandas as pd
import plotly.express as px
from strategy import calculate_scalping_strategy

st.set_page_config(page_title="Dividend Scalping Analyzer", layout="wide")

st.title("Dividend Strategy Analyzer: Scalping")

st.markdown("""
**Strategy 1: Dividend Scalping**
- Buy stock on **Ex-Date - 1**.
- Sell stock **N days** after Ex-Date.
- Analyze Net Gain % (including Dividend).
""")

ticker = st.text_input("Enter Stock Ticker (e.g., KO, AAPL, T)", value="KO")

# Initialize session state for analysis results
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = None

if st.button("Analyze Strategy"):
    with st.spinner(f"Fetching and Analyzing data for {ticker}..."):
        df = calculate_scalping_strategy(ticker)
        
        if df.empty:
            st.error("No data found or no dividends in the last 5 years.")
            st.session_state['df'] = None
        else:
            st.success("Analysis Complete!")
            st.session_state['df'] = df
            st.session_state['current_ticker'] = ticker

# Rendering section - persists across re-runs
if st.session_state['df'] is not None:
    df = st.session_state['df']
    display_ticker = st.session_state['current_ticker']
    
    # Summary Statistics
    # Calculate multiple stats: Mean, Median, Count
    agg_stats = df.groupby("Days Held After Ex-Div")[["Net Gain %", "Dividend Gain %"]].agg(['mean', 'median', 'count'])
    # Flatten columns: 'Net Gain %_mean', etc.
    agg_stats.columns = ['_'.join(col).strip() for col in agg_stats.columns.values]
    agg_stats = agg_stats.reset_index()
    
    # Keep track of Cumulative Gain for the Optimal Strategy metric
    agg_stats["Cumulative Gain %"] = df.groupby("Days Held After Ex-Div")["Net Gain %"].sum().values
    
    col_chart, col_metric = st.columns([3, 1])
    
    with col_chart:
        st.subheader("Strategy Performance Analysis")
        
        # Metric Selection Dropdown
        stat_selection = st.selectbox("Select Visualization Metric", ["Average", "Median", "Count"], index=0)
        stat_map = {"Average": "mean", "Median": "median", "Count": "count"}
        selected_suffix = stat_map[stat_selection]
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Use grouped bar chart
        fig = go.Figure()

        # Add Net Gain % Bar
        fig.add_trace(
            go.Bar(
                x=agg_stats["Days Held After Ex-Div"], 
                y=agg_stats[f"Net Gain %_{selected_suffix}"], 
                name=f"{stat_selection} Net Gain %"
            )
        )

        # Add Dividend Gain % Bar
        fig.add_trace(
            go.Bar(
                x=agg_stats["Days Held After Ex-Div"], 
                y=agg_stats[f"Dividend Gain %_{selected_suffix}"], 
                name=f"{stat_selection} Div Gain %"
            )
        )

        # Set labels
        fig.update_layout(
            xaxis_title="Days Held After Ex-Date",
            yaxis_title="Percentage (%)" if stat_selection != "Count" else "Number of Instances",
            barmode='group',
            title=f"{stat_selection} Performance by Holding Period: {display_ticker}",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Annual Net Gains by Strategy (Last 5 Years)")
        
        # Calculate Annual Gains for each strategy
        # Ensure Ex-Date is datetime
        df["Ex-Date"] = pd.to_datetime(df["Ex-Date"])
        df["Year"] = df["Ex-Date"].dt.year
        
        # Group by Year and Days Held, then sum Net Gain %
        annual_df = df.groupby(["Year", "Days Held After Ex-Div"])["Net Gain %"].sum().reset_index()
        
        # Pivot for plotting: Index=Year, Columns=Days Held, Values=Sum of Net Gain %
        annual_pivot = annual_df.pivot(index="Year", columns="Days Held After Ex-Div", values="Net Gain %")
        annual_pivot = annual_pivot.fillna(0)
        
        # Plot Annual Gains
        fig_annual = px.line(annual_pivot, x=annual_pivot.index, y=annual_pivot.columns,
                          title=f"Annual Net Gain % by Strategy: {display_ticker}",
                          labels={"value": "Total Net Gain %", "Year": "Year", "variable": "Days Held"},
                          markers=True)
        # Ensure X-axis shows integer years
        fig_annual.update_xaxes(dtick="M12", tickformat="%Y")
        
        st.plotly_chart(fig_annual, use_container_width=True)
        
    with col_metric:
        st.subheader("Optimal Strategy")
        # find best day based on Average Net Gain %
        best_day_row = agg_stats.loc[agg_stats["Net Gain %_mean"].idxmax()]
        
        # Calculate Avg Annual Gain for the best strategy
        # Total Cumulative Gain for best day / Number of unique years
        total_gain_best = best_day_row["Cumulative Gain %"]
        num_years = df["Year"].nunique() if not df.empty else 5
        avg_annual_gain = total_gain_best / num_years
        
        st.metric("Best Selling Day", f"Day {int(best_day_row['Days Held After Ex-Div'])}")
        st.metric("Avg Net Gain (Per Trade)", f"{best_day_row['Net Gain %_mean']:.2f}%")
        st.metric("Avg Annual Gain", f"{avg_annual_gain:.2f}%")

    st.markdown("---")
    st.subheader("Detailed Transaction Log")
    st.dataframe(df.style.format({
        "Buy Price": "{:.2f}",
        "Sell Price": "{:.2f}",
        "Dividend": "{:.4f}",
        "Net Gain %": "{:.2f}%"
    }))

