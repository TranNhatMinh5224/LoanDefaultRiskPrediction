import os
import re
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from utils import setup_logging, reduce_mem_usage

def train_model(data_dir: str = 'Data', model_dir: str = 'Model'):
    """
    Load feature-engineered datasets, construct a unified ColumnTransformer pipeline,
    preprocess features, train LightGBM, and save candidate model and preprocessor artifacts.
    """
    print("--- Starting Training Phase (Pipeline Standardized) ---")
    
    train_path = os.path.join(data_dir, 'engineered_train.pkl')
    test_path = os.path.join(data_dir, 'engineered_test.pkl')
    
    if not os.path.exists(train_path) or not os.path.exists(test_path):
        raise FileNotFoundError(
            f"Engineered datasets not found. Please run feature_engineering.py first."
        )
        
    print(f"Loading engineered datasets: {train_path} and {test_path}...")
    app_train = pd.read_pickle(train_path)
    app_test = pd.read_pickle(test_path)
    
    # Separate Target and Identifiers
    y_train = app_train['TARGET']
    X_train = app_train.drop(columns=['TARGET', 'SK_ID_CURR'])
    X_test = app_test.drop(columns=['SK_ID_CURR'])
    test_ids = app_test['SK_ID_CURR']
    
    # Identify numerical and categorical features
    # Exclude target/id, boolean is treated as categorical for OHE representation
    num_cols = X_train.select_dtypes(exclude=['object', 'category', 'bool']).columns.tolist()
    cat_cols = X_train.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    
    print(f"Features configuration: {len(num_cols)} numerical, {len(cat_cols)} categorical.")
    
    # 2. Build ColumnTransformer Pipeline
    print("Building scikit-learn ColumnTransformer pipeline...")
    num_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median'))
    ])
    
    cat_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_transformer, num_cols),
            ('cat', cat_transformer, cat_cols)
        ]
    )
    
    # 3. Fit and Transform Preprocessing Pipeline
    print("Fitting preprocessing pipeline on training features...")
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # Extract feature names for LightGBM column naming compatibility
    raw_feature_names = preprocessor.get_feature_names_out()
    # Sanitize feature names (replace non-alphanumeric characters with _)
    sanitize_col = lambda x: re.sub(r'[^A-Za-z0-9_]+', '_', x)
    feature_names = [sanitize_col(col) for col in raw_feature_names]
    
    # Reconstruct DataFrames
    X_train_df = pd.DataFrame(X_train_processed, columns=feature_names)
    X_test_df = pd.DataFrame(X_test_processed, columns=feature_names)
    
    # Optimize memory of preprocessed sets
    X_train_df = reduce_mem_usage(X_train_df, verbose=False)
    X_test_df = reduce_mem_usage(X_test_df, verbose=False)
    
    # 4. Train/Validation Split (80/20)
    print("Splitting train/validation sets (80/20)...")
    x_tr, x_val, y_tr, y_val = train_test_split(
        X_train_df, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    # 5. Train LightGBM Model
    print("Training LightGBM Classifier...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=34,
        colsample_bytree=0.9497036,
        subsample=0.8715623,
        max_depth=8,
        reg_alpha=0.041545473,
        reg_lambda=0.0735294,
        min_child_weight=39.32597,
        random_state=42,
        verbosity=-1
    )
    
    lgb_model.fit(
        x_tr, y_tr,
        eval_set=[(x_tr, y_tr), (x_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=True)]
    )
    
    # 6. Save Candidate Artifacts
    candidate_dir = os.path.join(model_dir, 'candidate')
    os.makedirs(candidate_dir, exist_ok=True)
    
    model_out = os.path.join(candidate_dir, 'lgbm_model_candidate.joblib')
    preprocessor_out = os.path.join(candidate_dir, 'preprocessor_candidate.joblib')
    val_out = os.path.join(candidate_dir, 'validation_data.pkl')
    test_out = os.path.join(candidate_dir, 'test_data_imputed.pkl')
    
    print(f"Saving candidate model to {model_out}...")
    joblib.dump(lgb_model, model_out)
    
    print(f"Saving candidate preprocessor to {preprocessor_out}...")
    joblib.dump(preprocessor, preprocessor_out)
    
    print(f"Saving validation data and test predictions inputs...")
    joblib.dump((x_val, y_val), val_out)
    joblib.dump((X_test_df, test_ids), test_out)
    
    print("--- Training Phase Complete ---")

if __name__ == '__main__':
    setup_logging()
    train_model()
