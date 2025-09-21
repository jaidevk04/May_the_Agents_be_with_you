import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def load_and_pivot_quality_data(quality_csv_path):
    """
    Load quality data in long format and pivot to wide format
    """
    df_quality = pd.read_csv(quality_csv_path)
    df_quality['Timestamp_Shifted'] = pd.to_datetime(df_quality['Timestamp_Shifted'])
    
    # Pivot to wide format
    df_pivoted = df_quality.pivot_table(
        index='Timestamp_Shifted', 
        columns='Parameter', 
        values='Value', 
        aggfunc='first'
    ).reset_index()
    
    # Rename timestamp column
    df_pivoted = df_pivoted.rename(columns={'Timestamp_Shifted': 'timestamp'})
    
    return df_pivoted

def load_process_data(process_csv_path):
    """
    Load process data - assuming it exists based on the original implementation
    If process data doesn't exist, we'll work with quality data only
    """
    try:
        df_proc = pd.read_csv(process_csv_path)
        df_proc['timestamp'] = pd.to_datetime(df_proc['timestamp'])
        return df_proc
    except FileNotFoundError:
        print("Process data not found. Working with quality data only.")
        return None

def prepare_freelime_dataset(quality_csv_path, process_csv_path=None):
    """
    Prepare dataset for Free Lime prediction
    """
    # Load quality data
    df_quality = load_and_pivot_quality_data(quality_csv_path)
    
    # Load process data if available
    df_proc = load_process_data(process_csv_path) if process_csv_path else None
    
    if df_proc is not None:
        # Merge process and quality data
        df = pd.merge_asof(
            df_proc.sort_values('timestamp'),
            df_quality.sort_values('timestamp'),
            on='timestamp',
            direction='backward'
        )
    else:
        # Use only quality data
        df = df_quality.copy()
    
    # Handle missing values by filling forward and then backward
    df = df.ffill().bfill()
    
    # Drop rows where the target is still missing
    if 'Output Parameter' in df.columns:
        df = df.dropna(subset=['Output Parameter'])
    
    return df

def extract_features_target(df):
    """
    Extract features and target from the prepared dataset
    """
    # Target is the 'Output Parameter' (Free Lime)
    if 'Output Parameter' in df.columns:
        target_col = 'Output Parameter'
    else:
        # If Output Parameter not found, assume it's the first quality parameter
        quality_cols = [col for col in df.columns if col.startswith('Quality')]
        if quality_cols:
            target_col = quality_cols[0]
        else:
            raise ValueError("No suitable target column found")
    
    # Features are all columns except timestamp and target
    feature_cols = [col for col in df.columns if col not in ['timestamp', target_col]]
    
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y, feature_cols, target_col

def prepare_training_data(quality_csv_path, process_csv_path=None, test_size=0.2):
    """
    Complete pipeline to prepare training data
    """
    df = prepare_freelime_dataset(quality_csv_path, process_csv_path)
    X, y, feature_cols, target_col = extract_features_target(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return (X_train_scaled, X_test_scaled, y_train, y_test, 
            scaler, feature_cols, target_col, df)
