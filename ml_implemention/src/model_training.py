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
    
    def evaluate(self, X_test, y_test):

        predictions = self.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        

        logger.info(f"  Accuracy: {accuracy:.2%}")
        logger.info(f"\n{classification_report(y_test, predictions, target_names=['Draw', 'Home Win', 'Away Win'])}")
        
        return accuracy
    
    def save(self, path='models/match_predictor.pkl'):

        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, path)
        logger.info(f"Model saved to {path}")
        
    def load(self, path='models/match_predictor.pkl'):

        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        logger.info(f"Model loaded from {path}")


def main():

    logger.info("Loading data...")
    df = load_match_data()
    
    logger.info("Preparing features...")
    X, y, features = prepare_data(df)
    
    logger.info("Splitting data...")
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    logger.info("Training model...")
    predictor = MatchPredictor()
    predictor.train(X_train, y_train, features)

    predictor.evaluate(X_test, y_test)
    predictor.save('models/match_predictor.pkl')


if __name__ == "__main__":
    main()