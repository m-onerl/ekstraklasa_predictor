from sklearn.model_selection import train_test_split
from ml_implemention.src.data_loading import load_match_data
from ml_implemention.src.data_preparation import prepare_data
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def split_data(X, y, test_size=0.2, random_state=42):

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size,
        random_state=random_state,
        stratify=y  # keep same % of results in both sets
    )
    return X_train, X_test, y_train, y_test


def main():
    #  raw match data
    df = load_match_data()
    
    #  features and target
    X, y, features = prepare_data(df)
    
    # into train/test sets
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # split information
    logger.info("\n")
    logger.info(f"DATA SPLIT:")
    logger.info(f"  Training set: {len(X_train)} matches ({len(X_train)/len(X)*100:.1f}%)")
    logger.info(f"  Test set:     {len(X_test)} matches ({len(X_test)/len(X)*100:.1f}%)")
    
    logger.info("\n")
    logger.info(f"TARGET DISTRIBUTION (y):")
    logger.info(f"  Train: {y_train.value_counts().to_dict()}")
    logger.info(f"  Test:  {y_test.value_counts().to_dict()}")
    
    logger.info("\n")
    logger.info("FEATURES ({len(features)}):")
    for i, f in enumerate(features, 1):
        logger.info(f"  {i:2}. {f}")
    
    return X_train, X_test, y_train, y_test, features

    
if __name__ == "__main__":
    main()