from sklearn.model_selection import train_test_split
from ml_implemention.src.model_training import MatchPredictor
from ml_implemention.src.data_loading import load_match_data
from ml_implemention.src.data_preparation import prepare_data


def evaluate_predictor(test_size=0.2, random_state=42):

    df = load_match_data()
    X, y, feature_columns = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"Total samples: {len(X)}")
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    predictor = MatchPredictor()
    predictor.train(X_train, y_train, feature_columns)

    print("TEST SET EVALUATION")
    accuracy = predictor.evaluate(X_test, y_test)
    
    return accuracy


if __name__ == "__main__":
    evaluate_predictor()
