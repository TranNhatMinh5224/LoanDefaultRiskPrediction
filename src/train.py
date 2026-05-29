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
    
    # Replace all infinite values (including float32 inf) with NaN
    X_train = X_train.replace([np.inf, -np.inf, np.float32(np.inf), np.float32(-np.inf)], np.nan)
    X_test = X_test.replace([np.inf, -np.inf, np.float32(np.inf), np.float32(-np.inf)], np.nan)
    
    # Identify numerical and categorical features (before OHE dummies)
    num_cols = X_train.select_dtypes(exclude=['object', 'category', 'bool']).columns.tolist()
    cat_cols = X_train.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    
    print(f"Features configuration before OHE: {len(num_cols)} numerical, {len(cat_cols)} categorical.")
    
    # 2. One-hot Encoding (dummies) and Column Alignment (join='inner', axis=1)
    print("Applying OHE (pd.get_dummies) and aligning train/test columns...")
    X_train_encoded = pd.get_dummies(X_train)
    X_test_encoded = pd.get_dummies(X_test)
    X_train_encoded, X_test_encoded = X_train_encoded.align(X_test_encoded, join='inner', axis=1)
    
    # Clean up column names to sanitize non-alphanumeric characters
    X_train_encoded = X_train_encoded.rename(columns=lambda x: re.sub('[^A-Za-z0-9_]+', '_', x))
    X_test_encoded = X_test_encoded.rename(columns=lambda x: re.sub('[^A-Za-z0-9_]+', '_', x))
    
    feature_names = X_train_encoded.columns.tolist()
    print(f"Total features after OHE and alignment: {len(feature_names)}")
    
    # 3. Fit and Transform Imputer
    print("Fitting SimpleImputer(strategy='median') on all features...")
    imputer = SimpleImputer(strategy='median')
    X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train_encoded), columns=feature_names)
    X_test_imputed = pd.DataFrame(imputer.transform(X_test_encoded), columns=feature_names)
    
    # Optimize memory of preprocessed sets
    X_train_df = reduce_mem_usage(X_train_imputed, verbose=False)
    X_test_df = reduce_mem_usage(X_test_imputed, verbose=False)
    
    # 4. Train/Validation Split (80/20) - matches notebook (no stratification)
    print("Splitting train/validation sets (80/20)...")
    x_tr, x_val, y_tr, y_val = train_test_split(
        X_train_df, y_train, test_size=0.2, random_state=42
    )
    
    # 5. Train LightGBM Model - aligned with the notebook parameters
    print("Training LightGBM Classifier (aligned hyperparameters)...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        random_state=42,
        n_jobs=-1
    )
    
    lgb_model.fit(
        x_tr, y_tr,
        eval_set=[(x_val, y_val)],
        eval_metric='auc',
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=True)]
    )
    
    # 6. Save Candidate Artifacts
    candidate_dir = os.path.join(model_dir, 'candidate')
    os.makedirs(candidate_dir, exist_ok=True)
    
    model_out = os.path.join(candidate_dir, 'lgbm_model_candidate.joblib')
    preprocessor_out = os.path.join(candidate_dir, 'preprocessor_candidate.joblib')
    val_out = os.path.join(candidate_dir, 'validation_data.pkl')
    test_out = os.path.join(candidate_dir, 'test_data_imputed.pkl')
    metadata_out = os.path.join(candidate_dir, 'candidate_metadata.json')
    
    print(f"Saving candidate model to {model_out}...")
    joblib.dump(lgb_model, model_out)
    
    print(f"Saving candidate imputer to {preprocessor_out}...")
    joblib.dump(imputer, preprocessor_out)
    
    print(f"Saving validation data and test predictions inputs...")
    joblib.dump((x_val, y_val), val_out)
    joblib.dump((X_test_df, test_ids), test_out)
    
    print(f"Saving candidate metadata helper to {metadata_out}...")
    import json
    candidate_meta = {
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "feature_names": feature_names
    }
    with open(metadata_out, 'w') as f:
        json.dump(candidate_meta, f, indent=2)
        
    print("--- Training Phase Complete ---")

if __name__ == '__main__':
    setup_logging()
    train_model()
