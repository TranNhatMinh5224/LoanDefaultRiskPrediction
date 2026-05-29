import os
import pandas as pd
from utils import setup_logging, reduce_mem_usage

def create_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct domain-specific features as defined in the training notebook:
    AGE, CREDIT_INCOME_PERCENT, ANNUITY_INCOME_PERCENT, CREDIT_TERM, and DAYS_EMPLOYED_PERCENT.
    """
    df_copy = df.copy()
    
    # 1. Age (positive value)
    if 'DAYS_BIRTH' in df_copy:
        df_copy['AGE'] = df_copy['DAYS_BIRTH'] / -365.0
        
    # 2. Financial ratios
    if 'AMT_CREDIT' in df_copy and 'AMT_INCOME_TOTAL' in df_copy:
        df_copy['CREDIT_INCOME_PERCENT'] = df_copy['AMT_CREDIT'] / df_copy['AMT_INCOME_TOTAL']
        
    if 'AMT_ANNUITY' in df_copy and 'AMT_INCOME_TOTAL' in df_copy:
        df_copy['ANNUITY_INCOME_PERCENT'] = df_copy['AMT_ANNUITY'] / df_copy['AMT_INCOME_TOTAL']
        
    if 'AMT_ANNUITY' in df_copy and 'AMT_CREDIT' in df_copy:
        df_copy['CREDIT_TERM'] = df_copy['AMT_ANNUITY'] / df_copy['AMT_CREDIT']
        
    if 'DAYS_EMPLOYED' in df_copy and 'DAYS_BIRTH' in df_copy:
        df_copy['DAYS_EMPLOYED_PERCENT'] = df_copy['DAYS_EMPLOYED'] / df_copy['DAYS_BIRTH']
        
    return df_copy

def run_feature_engineering(data_dir: str = 'Data', output_dir: str = 'Data'):
    """
    Load preprocessed data, generate features, optimize memory, and save to output_dir.
    """
    print("--- Starting Feature Engineering Phase ---")
    
    train_path = os.path.join(data_dir, 'processed_train.pkl')
    test_path = os.path.join(data_dir, 'processed_test.pkl')
    
    if not os.path.exists(train_path) or not os.path.exists(test_path):
        raise FileNotFoundError(
            f"Preprocessed datasets not found. Please run preprocess.py first."
        )
        
    print(f"Loading preprocessed datasets: {train_path} and {test_path}...")
    app_train = pd.read_pickle(train_path)
    app_test = pd.read_pickle(test_path)
    
    print("Constructing domain features...")
    app_train = create_domain_features(app_train)
    app_test = create_domain_features(app_test)
    
    # Optimize memory of new features
    app_train = reduce_mem_usage(app_train, verbose=False)
    app_test = reduce_mem_usage(app_test, verbose=False)
    
    train_out = os.path.join(output_dir, 'engineered_train.pkl')
    test_out = os.path.join(output_dir, 'engineered_test.pkl')
    
    print(f"Saving engineered datasets to {train_out} and {test_out}...")
    app_train.to_pickle(train_out)
    app_test.to_pickle(test_out)
    
    print("--- Feature Engineering Phase Complete ---")
    return app_train, app_test

if __name__ == '__main__':
    setup_logging()
    run_feature_engineering()
