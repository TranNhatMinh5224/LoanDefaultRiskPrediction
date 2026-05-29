import os
import gc
import re
import pandas as pd
import numpy as np
from utils import setup_logging, reduce_mem_usage

def preprocess_data(data_dir: str = 'Data', output_dir: str = 'Data'):
    """
    Load raw CSVs, optimize memory, aggregate satellite tables,
    clean anomalies, drop columns with >60% missing values, and save to output_dir.
    """
    print("--- Starting Preprocessing Phase ---")
    
    # 1. Load Main Application Datasets
    train_path = os.path.join(data_dir, 'application_train.csv')
    test_path = os.path.join(data_dir, 'application_test.csv')
    
    print(f"Loading main datasets: {train_path} and {test_path}...")
    app_train = pd.read_csv(train_path)
    app_test = pd.read_csv(test_path)
    
    # Optimize memory of main datasets
    app_train = reduce_mem_usage(app_train, verbose=False)
    app_test = reduce_mem_usage(app_test, verbose=False)
    
    print(f"Initial Train shape: {app_train.shape}")
    print(f"Initial Test shape: {app_test.shape}")
    
    # 2. Basic Cleaning: DAYS_EMPLOYED anomaly
    print("Cleaning DAYS_EMPLOYED anomaly...")
    for df in [app_train, app_test]:
        df['DAYS_EMPLOYED_ANOM'] = (df['DAYS_EMPLOYED'] == 365243).astype(np.int8)
        df['DAYS_EMPLOYED'] = df['DAYS_EMPLOYED'].replace({365243: np.nan})
    
    # 3. Process Satellite Tables one by one (to save RAM)
    
    # --- BENGAL 1: BUREAU ---
    bureau_path = os.path.join(data_dir, 'bureau.csv')
    if os.path.exists(bureau_path):
        print("Processing bureau.csv...")
        bureau = pd.read_csv(bureau_path)
        bureau = reduce_mem_usage(bureau, verbose=False)
        bureau_agg = bureau.groupby('SK_ID_CURR').agg({
            'SK_ID_BUREAU': ['count'],
            'AMT_CREDIT_SUM': ['sum', 'mean'],
            'AMT_CREDIT_SUM_DEBT': ['sum', 'mean']
        })
        bureau_agg.columns = ['BUREAU_' + '_'.join(col).strip() for col in bureau_agg.columns.values]
        
        app_train = app_train.merge(bureau_agg, on='SK_ID_CURR', how='left')
        app_test = app_test.merge(bureau_agg, on='SK_ID_CURR', how='left')
        del bureau, bureau_agg
        gc.collect()
        
    # --- BENGAL 2: PREVIOUS APPLICATION ---
    prev_path = os.path.join(data_dir, 'previous_application.csv')
    if os.path.exists(prev_path):
        print("Processing previous_application.csv...")
        prev = pd.read_csv(prev_path)
        prev = reduce_mem_usage(prev, verbose=False)
        prev_agg = prev.groupby('SK_ID_CURR').agg({
            'SK_ID_PREV': ['count'],
            'AMT_APPLICATION': ['sum', 'mean', 'max'],
            'AMT_CREDIT': ['sum', 'mean']
        })
        prev_agg.columns = ['PREV_' + '_'.join(col).strip() for col in prev_agg.columns.values]
        
        app_train = app_train.merge(prev_agg, on='SK_ID_CURR', how='left')
        app_test = app_test.merge(prev_agg, on='SK_ID_CURR', how='left')
        del prev, prev_agg
        gc.collect()

    # --- BENGAL 3: INSTALLMENTS PAYMENTS ---
    inst_path = os.path.join(data_dir, 'installments_payments.csv')
    if os.path.exists(inst_path):
        print("Processing installments_payments.csv...")
        inst = pd.read_csv(inst_path)
        inst = reduce_mem_usage(inst, verbose=False)
        inst['PAYMENT_PERC'] = inst['AMT_PAYMENT'] / inst['AMT_INSTALMENT']
        inst['PAYMENT_DIFF'] = inst['AMT_INSTALMENT'] - inst['AMT_PAYMENT']
        inst['DPD'] = (inst['DAYS_ENTRY_PAYMENT'] - inst['DAYS_INSTALMENT']).clip(lower=0)
        
        inst_agg = inst.groupby('SK_ID_CURR').agg({
            'NUM_INSTALMENT_VERSION': ['nunique'],
            'PAYMENT_PERC': ['mean'],
            'PAYMENT_DIFF': ['mean', 'sum'],
            'DPD': ['mean', 'max']
        })
        inst_agg.columns = ['INSTAL_' + '_'.join(col).strip() for col in inst_agg.columns.values]
        
        app_train = app_train.merge(inst_agg, on='SK_ID_CURR', how='left')
        app_test = app_test.merge(inst_agg, on='SK_ID_CURR', how='left')
        del inst, inst_agg
        gc.collect()

    # --- BENGAL 4: POS CASH BALANCE ---
    pos_path = os.path.join(data_dir, 'POS_CASH_balance.csv')
    if os.path.exists(pos_path):
        print("Processing POS_CASH_balance.csv...")
        pos = pd.read_csv(pos_path)
        pos = reduce_mem_usage(pos, verbose=False)
        pos_agg = pos.groupby('SK_ID_CURR').agg({
            'MONTHS_BALANCE': ['count', 'max'],
            'SK_DPD': ['max', 'mean']
        })
        pos_agg.columns = ['POS_' + '_'.join(col).strip() for col in pos_agg.columns.values]
        
        app_train = app_train.merge(pos_agg, on='SK_ID_CURR', how='left')
        app_test = app_test.merge(pos_agg, on='SK_ID_CURR', how='left')
        del pos, pos_agg
        gc.collect()

    # --- BENGAL 5: CREDIT CARD BALANCE ---
    cc_path = os.path.join(data_dir, 'credit_card_balance.csv')
    if os.path.exists(cc_path):
        print("Processing credit_card_balance.csv...")
        cc = pd.read_csv(cc_path)
        cc = reduce_mem_usage(cc, verbose=False)
        cc_agg = cc.groupby('SK_ID_CURR').agg({
            'MONTHS_BALANCE': ['count'],
            'AMT_BALANCE': ['mean', 'max'],
            'SK_DPD': ['max', 'sum']
        })
        cc_agg.columns = ['CC_' + '_'.join(col).strip() for col in cc_agg.columns.values]
        
        app_train = app_train.merge(cc_agg, on='SK_ID_CURR', how='left')
        app_test = app_test.merge(cc_agg, on='SK_ID_CURR', how='left')
        del cc, cc_agg
        gc.collect()

    # 4. Remove columns with >60% missing values
    print("Calculating columns to drop based on missing percentage (>60%)...")
    missing_percent = (app_train.isnull().sum() / len(app_train)) * 100
    cols_to_drop = missing_percent[missing_percent > 60].index.tolist()
    # Retain TARGET and SK_ID_CURR just in case they have >60% (highly unlikely, but safe)
    if 'TARGET' in cols_to_drop:
        cols_to_drop.remove('TARGET')
    if 'SK_ID_CURR' in cols_to_drop:
        cols_to_drop.remove('SK_ID_CURR')
        
    print(f"Dropping {len(cols_to_drop)} columns...")
    app_train = app_train.drop(columns=cols_to_drop)
    app_test = app_test.drop(columns=cols_to_drop, errors='ignore')
    
    # Final memory optimization
    app_train = reduce_mem_usage(app_train, verbose=False)
    app_test = reduce_mem_usage(app_test, verbose=False)
    
    print(f"Preprocessed Train shape: {app_train.shape}")
    print(f"Preprocessed Test shape: {app_test.shape}")
    
    # 5. Save output
    os.makedirs(output_dir, exist_ok=True)
    train_out = os.path.join(output_dir, 'processed_train.pkl')
    test_out = os.path.join(output_dir, 'processed_test.pkl')
    
    print(f"Saving preprocessed datasets to {train_out} and {test_out}...")
    app_train.to_pickle(train_out)
    app_test.to_pickle(test_out)
    
    print("--- Preprocessing Phase Complete ---")
    return app_train, app_test

if __name__ == '__main__':
    setup_logging()
    preprocess_data()
