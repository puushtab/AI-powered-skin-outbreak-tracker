import sqlite3
import pandas as pd

def view_database(db_path: str, output_csv: str = "timeseries_data.csv") -> pd.DataFrame:
    """Load the timeseries table from SQLite database into a Pandas DataFrame and display it."""
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    # Query the timeseries table
    query = "SELECT * FROM timeseries"
    df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])
    
    # Close the connection
    conn.close()
    
    # Display the DataFrame
    print("Time-Series DataFrame:")
    print(df)
    
    # Save to CSV for external viewing
    df.to_csv(output_csv, index=False)
    print(f"\nDataFrame saved to {output_csv}")
    
    return df

if __name__ == "__main__":
    # Path to the database
    db_path = "acne_tracker.db"
    
    # View the database
    df = view_database(db_path)