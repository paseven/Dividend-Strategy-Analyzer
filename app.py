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

if st.button("Analyze Strategy"):
    with st.spinner(f"Fetching and Analyzing data for {ticker}..."):
        df = calculate_scalping_strategy(ticker)
        
        if df.empty:
            st.error("No data found or no dividends in the last 5 years.")
        else:
            st.success("Analysis Complete!")
            
            # Summary Statistics
            # Group by "Days Held" to get Average Net Gain and Average Div Gain
            agg_df = df.groupby("Days Held After Ex-Div")[["Net Gain %", "Dividend Gain %"]].mean()
            # Also calculate Cumulative Gain (Sum of Net Gain %) for the 5-year period for each strategy
            agg_df["Cumulative Gain %"] = df.groupby("Days Held After Ex-Div")["Net Gain %"].sum()
            agg_df = agg_df.reset_index()
            
            col1, col2 = st.columns([3, 1]) # Increase chart width ratio
            
            with col1:
                st.subheader("Strategy Performance Analysis")
                
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots

                # Create figure with secondary y-axis
                fig = make_subplots(specs=[[{"secondary_y": True}]])

                # Add Average Net Gain %
                fig.add_trace(
                    go.Scatter(x=agg_df["Days Held After Ex-Div"], y=agg_df["Net Gain %"], name="Avg Net Gain %", mode='lines+markers'),
                    secondary_y=False,
                )

                # Add Average Dividend Gain %
                fig.add_trace(
                    go.Scatter(x=agg_df["Days Held After Ex-Div"], y=agg_df["Dividend Gain %"], name="Avg Div Gain %", mode='lines+markers', line=dict(dash='dash')),
                    secondary_y=False,
                )

                # Set x-axis title
                fig.update_xaxes(title_text="Days Held After Ex-Date")

                # Set y-axes titles
                fig.update_yaxes(title_text="Average Gain %", secondary_y=False)
                
                fig.update_layout(title=f"Performance by Holding Period: {ticker} (Last 5 Years)", hovermode="x unified")

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
                                  title=f"Annual Net Gain % by Strategy: {ticker}",
                                  labels={"value": "Total Net Gain %", "Year": "Year", "variable": "Days Held"},
                                  markers=True)
                # Ensure X-axis shows integer years
                fig_annual.update_xaxes(dtick="M12", tickformat="%Y")
                
                st.plotly_chart(fig_annual, use_container_width=True)
                
            with col2:
                st.subheader("Optimal Strategy")
                # find best day
                best_day_row = agg_df.loc[agg_df["Net Gain %"].idxmax()]
                
                # Calculate Avg Annual Gain for the best strategy
                # Total Cumulative Gain for best day / Number of unique years
                total_gain_best = best_day_row["Cumulative Gain %"]
                num_years = df["Year"].nunique() if not df.empty else 5
                avg_annual_gain = total_gain_best / num_years
                
                st.metric("Best Selling Day", f"Day {int(best_day_row['Days Held After Ex-Div'])}")
                st.metric("Avg Net Gain (Per Trade)", f"{best_day_row['Net Gain %']:.2f}%")
                st.metric("Avg Annual Gain", f"{avg_annual_gain:.2f}%")

            
            st.markdown("---")
            st.subheader("Detailed Transaction Log")
            st.dataframe(df.style.format({
                "Buy Price": "{:.2f}",
                "Sell Price": "{:.2f}",
                "Dividend": "{:.4f}",
                "Net Gain %": "{:.2f}%"
            }))
