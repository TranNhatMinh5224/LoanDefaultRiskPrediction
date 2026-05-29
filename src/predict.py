import os
import sys
import json
import pandas as pd

# Add the backend folder to Python path so we can import services
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.insert(0, backend_dir)

from app.services.ml_service import MLService

def run_prediction():
    """
    CLI interface to run a single prediction using the production MLService.
    If a JSON filepath is provided via command line, it parses and runs prediction,
    otherwise it runs on a mock high-risk client profile.
    """
    print("--- Loan Default Risk Prediction CLI Helper ---")
    
    # Initialize service
    print("Initializing MLService...")
    ml_service = MLService()
    
    if ml_service.model is None or ml_service.preprocessor is None:
        print("Error: Could not load production model or preprocessor artifacts. Make sure retrain.py has been executed.")
        sys.exit(1)
        
    print(f"Active Model Version: {ml_service.active_version} (Threshold: {ml_service.threshold:.2f})")
    
    # Load input sample
    sample_features = None
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
        if os.path.exists(json_path):
            print(f"Loading custom input features from {json_path}...")
            with open(json_path, 'r') as f:
                sample_features = json.load(f)
        else:
            # Check if JSON string directly
            try:
                sample_features = json.loads(json_path)
            except json.JSONDecodeError:
                print(f"Error: Argument '{json_path}' is not a valid JSON string or file path.")
                sys.exit(1)
                
    if sample_features is None:
        print("No input provided. Running prediction on a mock client profile...")
        # Mock high-risk profile: Young client, low credit scores, previous late payments
        sample_features = {
            "EXT_SOURCE_1": 0.05,
            "EXT_SOURCE_2": 0.08,
            "EXT_SOURCE_3": 0.12,
            "DAYS_BIRTH": -9125,       # 25 years old
            "DAYS_EMPLOYED": -365,      # 1 year employed
            "AMT_INCOME_TOTAL": 120000,
            "AMT_CREDIT": 600000,
            "AMT_ANNUITY": 30000,
            "CODE_GENDER": "M",
            "FLAG_OWN_CAR": "N",
            "NAME_EDUCATION_TYPE": "Secondary / secondary special",
            "INSTAL_DPD_max": 45        # Had late payments up to 45 days
        }
        
    print("\nClient Features:")
    print(json.dumps(sample_features, indent=2))
    
    # Predict
    try:
        score, decision, duration_ms = ml_service.predict_default_risk(sample_features)
        print("\n--- Prediction Results ---")
        print(f"Risk Score:  {score:.4f} ({score*100:.2f}%)")
        print(f"Decision:    {decision}")
        print(f"Latency:     {duration_ms} ms")
        print("--------------------------")
    except Exception as e:
        print(f"Prediction failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_prediction()
