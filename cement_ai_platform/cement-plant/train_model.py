import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from data_tools import prepare_training_data
import os

def train_freelime_model():
    # Update paths according to your actual file structure
    quality_path = 'archive/CAX_Train_Quality (1)/CAX_Train_Quality.csv'
    # process_path = None  # No process data available based on EDA
    
    print("Loading and preparing data...")
    (X_train_scaled, X_test_scaled, y_train, y_test, 
     scaler, feature_cols, target_col, df) = prepare_training_data(quality_path)
    
    print(f"Training data shape: {X_train_scaled.shape}")
    print(f"Target column: {target_col}")
    print(f"Feature columns: {feature_cols}")
    
    # Try multiple models
    models = {
        'gradient_boosting': GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        ),
        'random_forest': RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            random_state=42
        )
    }
    
    best_model = None
    best_score = float('inf')
    best_name = None
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        
        # Metrics
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        test_r2 = r2_score(y_test, y_pred_test)
        
        print(f"{name} - Train MAE: {train_mae:.4f}, Test MAE: {test_mae:.4f}")
        print(f"{name} - Test RMSE: {test_rmse:.4f}, Test R²: {test_r2:.4f}")
        
        if test_mae < best_score:
            best_model = model
            best_score = test_mae
            best_name = name
    
    print(f"\nBest model: {best_name} with MAE: {best_score:.4f}")
    
    # Create models directory
    os.makedirs('models', exist_ok=True)
    
    # Save best model and scaler
    joblib.dump(best_model, 'models/freelime_model.pkl')
    joblib.dump(scaler, 'models/freelime_scaler.pkl')
    
    # Save feature information
    model_info = {
        'feature_columns': feature_cols,
        'target_column': target_col,
        'model_type': best_name,
        'test_mae': best_score
    }
    joblib.dump(model_info, 'models/model_info.pkl')
    
    print("Model saved successfully!")
    return best_model, scaler, model_info

if __name__ == "__main__":
    train_freelime_model()
