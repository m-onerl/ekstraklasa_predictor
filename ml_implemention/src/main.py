from .prediction import predict_match, get_all_teams
from .model_training import MatchPredictor
from .data_loading import load_match_data
from .data_preparation import prepare_data, prepare_data_stats

from tkinter import *
import logging


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

        
def train_models():
    print("\nLoading data...")
    df = load_match_data()
    
    predictor = MatchPredictor()
    
    print("Training result prediction model...")
    X, y, feature_columns = prepare_data(df)
    predictor.train(X, y, feature_columns)
    
    print("Training stats prediction models...")
    X_stats, targets, stats_features = prepare_data_stats(df)
    predictor.train_stats(X_stats, targets, stats_features)
    
    predictor.save()
    print("All models trained and saved!")
    
    
class PredictorGui:    
    def __init__(self, root):
        self.root = root
        self.root.title("EKSTRAKLASA MATCH PREDICTOR")
        self.root.geometry("1400x700")


    def show_menu():
        print("\n" + "="*50)
        print("   EKSTRAKLASA MATCH PREDICTOR")
        print("="*50)
        print("\n  1. Predict match")
        print("  2. Train models")
        print("  3. Exit")
        return input("\nChoose option (1-3): ").strip()


    def predict():
        home_team = input("\nEnter HOME team name: ").strip()
        away_team = input("Enter AWAY team name: ").strip()
        
        print(f"\nPredicting: {home_team} vs {away_team}...")
        
        result = predict_match(home_team, away_team)
        
        if result is None:
            print("Error: Could not find one or both teams or model not trained!")
            return

        # Match result 
        print("\n" + "="*50)
        print("   MATCH RESULT PREDICTION")
        print("="*50)
        print(f"\n  Prediction: {result['prediction']}")
        print(f"\n  Probabilities:")
        print(f"     Home Win ({home_team}): {result['probabilities']['Home Win']}")
        print(f"     Draw:                   {result['probabilities']['Draw']}")
        print(f"     Away Win ({away_team}): {result['probabilities']['Away Win']}")

        # Stats predictions
        if 'stats_predictions' in result:
            print("\n" + "="*50)
            print("   STATISTICS PREDICTIONS")
            print("="*50)
            
            stats = result['stats_predictions']
            
            stat_names = {
                'corner_kicks': 'Corner Kicks',
                'fouls': 'Fouls',
                'yellow_cards': 'Yellow Cards',
                'red_cards': 'Red Cards',
                'free_kicks': 'Free Kicks'
            }
            
            print(f"\n  {'Statistic':<20} {'Home':>8} {'Away':>8} {'Total':>8}")
            print("  " + "-"*46)
            
            for stat, values in stats.items():
                name = stat_names.get(stat, stat)
                print(f"  {name:<20} {values['home']:>8} {values['away']:>8} {values['total']:>8}")
        else:
            print("\nStats models not trained. You have to try enter 2 and make a traning.")
        
        print("\n" + "="*50)


def main():
    root = Tk()
    app = PredictorGui(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()