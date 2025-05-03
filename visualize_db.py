import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import streamlit as st
from datetime import datetime

def get_db_path():
    """Get the path to the database file"""
    db_dir = Path(__file__).parent / "back" / "src" / "db"
    return str(db_dir / "acne_tracker.db")

def get_table_names(conn):
    """Get all table names in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [table[0] for table in cursor.fetchall()]

def get_table_data(conn, table_name):
    """Get all data from a specific table"""
    query = f"SELECT * FROM {table_name}"
    return pd.read_sql_query(query, conn)

def visualize_timeseries_data(df):
    """Visualize timeseries data with plots"""
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create a figure with multiple subplots
    fig, axes = plt.subplots(3, 2, figsize=(15, 15))
    fig.suptitle('Timeseries Analysis', fontsize=16)
    
    # Plot 1: Acne Severity Over Time
    sns.lineplot(data=df, x='timestamp', y='acne_severity_score', ax=axes[0, 0])
    axes[0, 0].set_title('Acne Severity Over Time')
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Severity Score')
    
    # Plot 2: Diet Factors
    sns.lineplot(data=df, x='timestamp', y='diet_sugar', label='Sugar', ax=axes[0, 1])
    sns.lineplot(data=df, x='timestamp', y='diet_dairy', label='Dairy', ax=axes[0, 1])
    axes[0, 1].set_title('Diet Factors Over Time')
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('Score (1-10)')
    axes[0, 1].legend()
    
    # Plot 3: Sleep and Stress
    sns.lineplot(data=df, x='timestamp', y='sleep_hours', label='Sleep Hours', ax=axes[1, 0])
    sns.lineplot(data=df, x='timestamp', y='stress', label='Stress', ax=axes[1, 0])
    axes[1, 0].set_title('Sleep and Stress Over Time')
    axes[1, 0].set_xlabel('Date')
    axes[1, 0].set_ylabel('Score')
    axes[1, 0].legend()
    
    # Plot 4: Environmental Factors
    sns.lineplot(data=df, x='timestamp', y='humidity', label='Humidity', ax=axes[1, 1])
    sns.lineplot(data=df, x='timestamp', y='pollution', label='Pollution', ax=axes[1, 1])
    axes[1, 1].set_title('Environmental Factors Over Time')
    axes[1, 1].set_xlabel('Date')
    axes[1, 1].set_ylabel('Score')
    axes[1, 1].legend()
    
    # Plot 5: Correlation Heatmap
    numeric_columns = ['acne_severity_score', 'diet_sugar', 'diet_dairy', 
                      'sleep_hours', 'stress', 'humidity', 'pollution']
    corr_matrix = df[numeric_columns].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=axes[2, 0])
    axes[2, 0].set_title('Correlation Heatmap')
    
    # Plot 6: Sunlight Exposure
    sns.lineplot(data=df, x='timestamp', y='sunlight_exposure', ax=axes[2, 1])
    axes[2, 1].set_title('Sunlight Exposure Over Time')
    axes[2, 1].set_xlabel('Date')
    axes[2, 1].set_ylabel('Hours')
    
    plt.tight_layout()
    return fig

def main():
    st.set_page_config(page_title="Database Visualizer", layout="wide")
    st.title("Database Visualizer")
    
    try:
        # Connect to database
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        
        # Get all tables
        tables = get_table_names(conn)
        
        # Create tabs for each table
        tabs = st.tabs(tables)
        
        for tab, table_name in zip(tabs, tables):
            with tab:
                st.subheader(f"Table: {table_name}")
                
                # Get table data
                df = get_table_data(conn, table_name)
                
                # Display raw data
                st.write("Raw Data:")
                st.dataframe(df)
                
                # If it's the timeseries table, show visualizations
                if table_name == "timeseries":
                    st.write("Visualizations:")
                    fig = visualize_timeseries_data(df)
                    st.pyplot(fig)
                
                # Show table statistics
                st.write("Statistics:")
                st.write(df.describe())
                
                # Show data types
                st.write("Data Types:")
                st.write(df.dtypes)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error accessing database: {str(e)}")
        st.error("Make sure the database exists and is in the correct location.")

if __name__ == "__main__":
    main() 