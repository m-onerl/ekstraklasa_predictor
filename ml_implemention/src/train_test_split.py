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
