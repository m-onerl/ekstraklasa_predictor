from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import logging

from ml_implemention.src.data_loading import load_match_data
from ml_implemention.src.data_preparation import prepare_data
from ml_implemention.src.train_test_split import split_data

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MatchPredictor:
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators = 100,
            max_depth = 10,
            random_state = 42,
            class_weight = 'balanced'
        )
        self.scaler = StandardScaler()
        self.feature_names = None
        
    def train(self, X_train, y_train, feature_names):
        self.feature_names = feature_names
        
        X_scaled = self.scaler.fit_transform(X_train)
        
        self.model.fit(X_scaled, y_train)
        logger.info(f'Model trained on {len(X_train)}')

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)