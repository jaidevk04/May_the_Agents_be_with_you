import os
import sys
import subprocess
import time
from train_model import train_freelime_model
import uvicorn

def main():
    print("🏭 Clinker Quality Prediction Agent (CQPA)")
    print("=" * 50)
    
    # Step 1: Check if model exists, if not train it
    if not os.path.exists('models/freelime_model.pkl'):
        print("No trained model found. Training new model...")
        try:
            train_freelime_model()
            print("✅ Model training completed!")
        except Exception as e:
            print(f"❌ Model training failed: {e}")
            return
    else:
        print("✅ Using existing trained model")
    
    print("\n" + "=" * 50)
    print("Starting API server...")
    print("=" * 50)
    
    # Start the FastAPI server using uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
