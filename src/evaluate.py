import os
import json
import shutil
import joblib
import pandas as pd
from datetime import datetime
from sklearn.metrics import roc_auc_score
from utils import setup_logging

def evaluate_and_register(model_dir: str = 'Model', backend_model_dir: str = 'src/backend/model'):
    """
    Evaluate candidate model, compare with production model,
    and register both the model and preprocessor if performance exceeds/equals production ROC-AUC.
    """
    print("--- Starting Evaluation & Registry Phase (Pipeline Standardized) ---")
    
    candidate_dir = os.path.join(model_dir, 'candidate')
    model_path = os.path.join(candidate_dir, 'lgbm_model_candidate.joblib')
    preprocessor_path = os.path.join(candidate_dir, 'preprocessor_candidate.joblib')
    val_path = os.path.join(candidate_dir, 'validation_data.pkl')
    test_path = os.path.join(candidate_dir, 'test_data_imputed.pkl')
    
    if not all(os.path.exists(p) for p in [model_path, preprocessor_path, val_path, test_path]):
        raise FileNotFoundError(
            "Candidate model or preprocessor artifacts not found. Please run train.py first."
        )
        
    # 1. Load Candidate Model, Preprocessor, and Validation Data
    print("Loading candidate artifacts...")
    candidate_model = joblib.load(model_path)
    candidate_preprocessor = joblib.load(preprocessor_path)
    x_val, y_val = joblib.load(val_path)
    X_test_processed, test_ids = joblib.load(test_path)
    
    # 2. Evaluate Candidate Model
    print("Evaluating candidate model performance...")
    val_probs = candidate_model.predict_proba(x_val)[:, 1]
    candidate_auc = roc_auc_score(y_val, val_probs)
    print(f"Candidate Model Validation ROC-AUC: {candidate_auc:.4f}")
    
    # 3. Load Active Metadata to Compare
    metadata_path = os.path.join(model_dir, 'model_metadata.json')
    active_auc = 0.0
    active_version = "v0"
    metadata_exists = os.path.exists(metadata_path)
    
    if metadata_exists:
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            active_version = metadata.get("active_version", "v0")
            
            # Find ROC-AUC of active model
            for model_info in metadata.get("models", []):
                if model_info.get("version") == active_version:
                    active_auc = model_info.get("roc_auc", 0.0)
                    break
            print(f"Active Model ({active_version}) ROC-AUC: {active_auc:.4f}")
        except Exception as e:
            print(f"Warning: Failed to load metadata, defaulting active_auc to 0.0. Error: {e}")
            metadata = {"active_version": "v0", "models": []}
    else:
        print("No active metadata file found. Initializing metadata.")
        metadata = {"active_version": "v0", "models": []}

    # 4. Model Registry Promotion Logic
    is_better = candidate_auc >= active_auc
    
    if is_better:
        print(f"SUCCESS: Candidate model ({candidate_auc:.4f}) outperforms or matches active model ({active_auc:.4f}).")
        print("Promoting candidate model and preprocessor to Production...")
        
        # Determine next version code
        try:
            current_ver_num = int(active_version.replace('v', ''))
        except ValueError:
            current_ver_num = 0
        next_version = f"v{current_ver_num + 1}"
        print(f"Target Version Code: {next_version}")
        
        # Build paths
        prod_model_name = "lgbm_model_v1.joblib" # Backend expects v1
        prod_preprocessor_name = "preprocessor_v1.joblib" # Backend expects preprocessor_v1
        
        # Copy to root Model folder
        dest_model_root = os.path.join(model_dir, prod_model_name)
        dest_preprocessor_root = os.path.join(model_dir, prod_preprocessor_name)
        
        shutil.copy2(model_path, dest_model_root)
        shutil.copy2(preprocessor_path, dest_preprocessor_root)
        print(f"Copied artifacts to {model_dir}/")
        
        old_imputer_root = os.path.join(model_dir, "imputer_v1.joblib")
        if os.path.exists(old_imputer_root):
            os.remove(old_imputer_root)
            print("Removed deprecated imputer_v1.joblib from Model/")
            
        # Generate Test Predictions CSV
        print("Generating test predictions on the newly promoted model...")
        test_preds = candidate_model.predict_proba(X_test_processed)[:, 1]
        submit_df = pd.DataFrame({
            'SK_ID_CURR': test_ids,
            'TARGET': test_preds
        })
        submit_path = os.path.join(model_dir, 'submission_retrained.csv')
        submit_df.to_csv(submit_path, index=False)
        print(f"Test submission saved to {submit_path}")
        
        # Load candidate metadata
        candidate_meta_path = os.path.join(candidate_dir, 'candidate_metadata.json')
        candidate_meta = {}
        if os.path.exists(candidate_meta_path):
            try:
                with open(candidate_meta_path, 'r') as f:
                    candidate_meta = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load candidate metadata: {e}")

        # Update metadata record
        new_model_record = {
            "version": next_version,
            "algorithm": "LightGBM",
            "model_file": prod_model_name,
            "preprocessor_file": prod_preprocessor_name,
            "roc_auc": round(float(candidate_auc), 4),
            "threshold": 0.3,
            "n_features": int(len(x_val.columns)),
            "n_estimators_used": int(candidate_model.best_iteration_) if hasattr(candidate_model, 'best_iteration_') and candidate_model.best_iteration_ else 1000,
            "trained_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "training_rows": int(len(y_val) * 4), # Total training set size was validation * 4
            "validation_rows": int(len(y_val)),
            "status": "production",
            "notes": f"Retrained model {next_version} using automated retraining pipeline. Preprocessing aligned with Jupyter notebook using pd.get_dummies and SimpleImputer.",
            "num_cols": candidate_meta.get("num_cols", []),
            "cat_cols": candidate_meta.get("cat_cols", []),
            "feature_names": candidate_meta.get("feature_names", [])
        }
        
        # Mark old production models as archived
        for record in metadata.get("models", []):
            if record.get("status") == "production":
                record["status"] = "archived"
                
        metadata["models"].append(new_model_record)
        metadata["active_version"] = next_version
        
        # Save metadata to registry target
        dest_metadata_root = os.path.join(model_dir, 'model_metadata.json')
        
        with open(dest_metadata_root, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print("Updated model_metadata.json registered in Model/")
    else:
        print(f"WARNING: Candidate model ({candidate_auc:.4f}) failed to outperform active model ({active_auc:.4f}).")
        print("No promotion occurred. Existing production models retained.")
        
    print("--- Evaluation & Registry Phase Complete ---")

if __name__ == '__main__':
    setup_logging()
    evaluate_and_register()
