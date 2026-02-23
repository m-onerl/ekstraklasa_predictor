from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error

from .data_preparation import prepare_data, prepare_data_stats
from .data_loading import load_match_data 

import joblib
import os
import logging


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MatchPredictor:
    
    STATS_TO_PREDICT = [
        'corner_kicks',
        'fouls',
        'yellow_cards',
        'ball_possession',
        'total_shots',
        'shots_on_target',
    ]
    
    def __init__(self):
        self.result_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.result_scaler = StandardScaler()
        self.result_feature_names = None
        self.stats_models = {}
        self.stats_scalers = {}
        self.stats_feature_names = None
        
    
    
    def train(self, X_train, y_train, feature_names):

        self.result_feature_names = feature_names
        X_scaled = self.result_scaler.fit_transform(X_train)
        self.result_model.fit(X_scaled, y_train)
        logger.info(f'Result model trained on {len(X_train)} matches')

    def predict(self, X):
        X_scaled = self.result_scaler.transform(X)
        return self.result_model.predict(X_scaled)
    
    def predict_proba(self, X):
        X_scaled = self.result_scaler.transform(X)
        return self.result_model.predict_proba(X_scaled)
    
    def evaluate(self, X_test, y_test):
        predictions = self.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        
        logger.info(f"  Accuracy: {accuracy:.2%}")
        logger.info(f"\n{classification_report(y_test, predictions, target_names=['Draw', 'Home Win', 'Away Win'])}")
        
        return accuracy
    

    
    def train_stats(self, X, targets, feature_names):

        self.stats_feature_names = feature_names
        
        for stat in self.STATS_TO_PREDICT:
            logger.info(f"Training model for {stat}...")
            
            y_home, y_away = targets[stat]
            
            self.stats_scalers[stat] = StandardScaler()
            X_scaled = self.stats_scalers[stat].fit_transform(X)
            
            if stat == 'ball_possession':
                self.stats_models[f'home_{stat}'] = RandomForestRegressor(
                    n_estimators = 100, max_depth = 10, random_state = 42
                )
                self.stats_models[f'home_{stat}'].fit(X_scaled, y_home.fillna(50))
            else:
                self.stats_models[f'home_{stat}'] = RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42
                )
                self.stats_models[f'home_{stat}'].fit(X_scaled, y_home.fillna(0))
                
                self.stats_models[f'away_{stat}'] = RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42
                )
                self.stats_models[f'away_{stat}'].fit(X_scaled, y_away.fillna(0))
            
        logger.info("All stats models trained!")
    
    def predict_stats(self, X):

        predictions = {}
        
        for stat in self.STATS_TO_PREDICT:
            X_scaled = self.stats_scalers[stat].transform(X)
            
            if stat == 'ball_possession':
                home_pred = self.stats_models[f'home_{stat}'].predict(X_scaled)[0]
                home_pred = max(30, min(70, home_pred))
                away_pred = 100 - home_pred
            
                predictions[stat] = {
                'home': round(home_pred, 1),
                'away': round(away_pred, 1),
                'total': 100.0
                }
                
            else:    
                home_pred = max(0, self.stats_models[f'home_{stat}'].predict(X_scaled)[0])
                away_pred = max(0, self.stats_models[f'away_{stat}'].predict(X_scaled)[0])
                
                predictions[stat] = {
                    'home': round(home_pred, 1),
                    'away': round(away_pred, 1),
                    'total': round(home_pred + away_pred, 1)
                }
            
        return predictions
    
    def evaluate_stats(self, X, targets):

        results = {}
        
        for stat in self.STATS_TO_PREDICT:
            X_scaled = self.stats_scalers[stat].transform(X)
            y_home, y_away = targets[stat]
            
            home_pred = self.stats_models[f'home_{stat}'].predict(X_scaled)
            away_pred = self.stats_models[f'away_{stat}'].predict(X_scaled)
            
            home_mae = mean_absolute_error(y_home.fillna(0), home_pred)
            away_mae = mean_absolute_error(y_away.fillna(0), away_pred)
            
            results[stat] = {'home_mae': home_mae, 'away_mae': away_mae}
            logger.info(f"{stat.upper()}: Home MAE={home_mae:.2f}, Away MAE={away_mae:.2f}")
        
        return results
    

    def save(self, path='models/match_predictor.pkl'):

        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'result_model': self.result_model,
            'result_scaler': self.result_scaler,
            'result_feature_names': self.result_feature_names,
            'stats_models': self.stats_models,
            'stats_scalers': self.stats_scalers,
            'stats_feature_names': self.stats_feature_names,
        }, path)
        logger.info(f"All models saved to {path}")
        
    def load(self, path='models/match_predictor.pkl'):

        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}")
            return False
            
        data = joblib.load(path)
        self.result_model = data['result_model']
        self.result_scaler = data['result_scaler']
        self.result_feature_names = data['result_feature_names']
        self.stats_models = data.get('stats_models', {})
        self.stats_scalers = data.get('stats_scalers', {})
        self.stats_feature_names = data.get('stats_feature_names')
        logger.info(f"All models loaded from {path}")
        return True
    
    def has_stats_models(self):
        return len(self.stats_models) > 0
    
    def train_models(self):
        
        df = load_match_data()

        X, y, feature_columns = prepare_data(df)
        self.train(X, y, feature_columns)
        
        X_stats, targets, stats_features = prepare_data_stats(df)
        self.train_stats(X_stats, targets, stats_features)
        
        self.save()