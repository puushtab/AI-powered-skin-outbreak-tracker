import sqlite3
import pandas as pd
from scipy.stats import pearsonr
from datetime import datetime, timedelta
import numpy as np

def load_data(db_path: str) -> pd.DataFrame:
    """Load time-series data from SQLite database."""
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM timeseries"
    df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])
    conn.close()
    
    # Convert numerical columns to float
    numeric_columns = [
        'acne_severity_score', 'diet_sugar', 'diet_dairy', 'diet_alcohol',
        'sleep_hours', 'menstrual_cycle_day', 'humidity', 'pollution',
        'stress', 'sunlight_exposure'
    ]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
    return df

def compute_correlations(df: pd.DataFrame) -> dict:
    """Compute Pearson correlations between acne severity and each factor."""
    correlations = {}
    numeric_columns = [
        'diet_sugar', 'diet_dairy', 'diet_alcohol', 'sleep_hours',
        'menstrual_cycle_day', 'humidity', 'pollution', 'stress', 'sunlight_exposure'
    ]
    for col in numeric_columns:
        valid_data = df[['acne_severity_score', col]].dropna()
        if len(valid_data) > 1:
            corr, _ = pearsonr(valid_data['acne_severity_score'], valid_data[col])
            correlations[col] = corr
        else:
            correlations[col] = np.nan
    return correlations

def analyze_trend(df: pd.DataFrame, end_date: datetime = None) -> tuple:
    """Analyze acne severity trend for the past week."""
    if end_date is None:
        end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    weekly_data = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if weekly_data.empty:
        return "no data", 0, np.nan
    
    avg_severity = weekly_data['acne_severity_score'].mean()
    prev_week_start = start_date - timedelta(days=7)
    prev_week_data = df[(df['timestamp'] >= prev_week_start) & (df['timestamp'] < start_date)]
    prev_avg_severity = prev_week_data['acne_severity_score'].mean() if not prev_week_data.empty else np.nan
    
    if not np.isnan(prev_avg_severity):
        severity_change = avg_severity - prev_avg_severity
        trend = "increased" if severity_change > 0 else "decreased"
        change_magnitude = abs(severity_change)
    else:
        trend = "stable"
        change_magnitude = 0
    
    return trend, change_magnitude, avg_severity

def generate_summary(trend: str, change_magnitude: float, avg_severity: float, correlations: dict, k: int = 2) -> str:
    """Generate a summary sentence based on trend and top k correlated factors, including ties."""
    if trend == "no data":
        return "No data available for the past week to assess acne severity trends."
    
    # Format the severity score
    severity_text = f"with an average severity score of {avg_severity:.1f}"
    
    # Handle different trend cases
    if trend == "stable":
        base_text = f"Your acne severity has remained stable {severity_text}"
    else:
        # Format the change magnitude
        if change_magnitude < 0.1:
            change_text = "slightly"
        elif change_magnitude < 0.5:
            change_text = "moderately"
        else:
            change_text = "significantly"
        
        base_text = f"Your acne severity has {change_text} {trend} {severity_text}"
    
    valid_corrs = {k: v for k, v in correlations.items() if not np.isnan(v)}
    if valid_corrs:
        # Sort correlations by absolute value (descending)
        sorted_corrs = sorted(valid_corrs.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Select top k distinct correlation values, including ties
        selected_factors = []
        distinct_values = []
        for factor, corr in sorted_corrs:
            abs_corr = abs(corr)
            if len(distinct_values) < k or abs_corr in distinct_values:
                selected_factors.append((factor, corr))
                if abs_corr not in distinct_values:
                    distinct_values.append(abs_corr)
        
        # Map factor names to user-friendly terms
        factor_map = {
            'diet_sugar': 'sugar consumption',
            'diet_dairy': 'dairy intake',
            'diet_alcohol': 'alcohol consumption',
            'sleep_hours': 'sleep duration',
            'menstrual_cycle_day': 'menstrual cycle phase',
            'humidity': 'environmental humidity',
            'pollution': 'air pollution',
            'stress': 'stress levels',
            'sunlight_exposure': 'sunlight exposure'
        }
        
        # Generate attribution for multiple factors
        if selected_factors:
            factor_phrases = []
            for factor, corr in selected_factors:
                factor_name = factor_map.get(factor, factor)
                if corr > 0 and trend == "increased":
                    phrase = f"higher {factor_name}"
                elif corr > 0 and trend == "decreased":
                    phrase = f"lower {factor_name}"
                elif corr < 0 and trend == "increased":
                    phrase = f"lower {factor_name}"
                elif corr < 0 and trend == "decreased":
                    phrase = f"higher {factor_name}"
                else:
                    phrase = f"changes in {factor_name}"
                factor_phrases.append(phrase)
            
            # Combine phrases naturally
            if len(factor_phrases) == 1:
                attribution = factor_phrases[0]
            elif len(factor_phrases) == 2:
                attribution = f"{factor_phrases[0]} and {factor_phrases[1]}"
            else:
                attribution = f"{', '.join(factor_phrases[:-1])}, and {factor_phrases[-1]}"
            
            return f"{base_text}. This appears to be related to {attribution}."
    
    return f"{base_text}. No clear correlations with tracked factors were found."

def analyze_acne_data(db_path: str, end_date: datetime = None) -> tuple:
    """Main function to analyze acne data and return correlations and summary."""
    df = load_data(db_path)
    correlations = compute_correlations(df)
    trend, change_magnitude, avg_severity = analyze_trend(df, end_date)
    summary = generate_summary(trend, change_magnitude, avg_severity, correlations)
    return correlations, summary

if __name__ == "__main__":
    # Test the analysis with sample database
    db_path = "acne_tracker.db"
    correlations, summary = analyze_acne_data(db_path)
    
    print("Correlation Scores:")
    for factor, corr in correlations.items():
        print(f"{factor}: {corr:.4f}" if not np.isnan(corr) else f"{factor}: Insufficient data")
    print("\nSummary:")
    print(summary)