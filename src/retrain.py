import os
import sys
from utils import setup_logging
from preprocess import preprocess_data
from feature_engineering import run_feature_engineering
from train import train_model
from evaluate import evaluate_and_register

def run_pipeline():
    """
    Run the entire retraining pipeline end-to-end:
    Preprocessing -> Feature Engineering -> Training -> Evaluation & Promotion.
    """
    setup_logging()
    print("==================================================")
    print("🤖 STARTING AUTOMATED END-TO-END ML RETRAINING PIPELINE")
    print("==================================================")
    
    # 1. Preprocess raw data and aggregate satellite tables
    preprocess_data()
    
    # 2. Run feature engineering and domain ratios
    run_feature_engineering()
    
    # 3. Train candidate LightGBM model
    train_model()
    
    # 4. Evaluate candidate and register to production if improved
    evaluate_and_register()
    
    print("==================================================")
    print("✅ RETRAINING PIPELINE EXECUTION COMPLETED")
    print("==================================================")

if __name__ == '__main__':
    # Ensure src directory is in Python path for module resolution
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        
    run_pipeline()
