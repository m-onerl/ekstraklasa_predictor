from .prediction import predict_match
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
def main():

    logger.info("  EKSTRAKLASA MATCH PREDICTOR")

    
    home_team = input("\nEnter HOME team name: ").strip()
    away_team = input("Enter AWAY team name: ").strip()
    
    logger.info(f"\nPredicting: {home_team} vs {away_team}...")
    
    result = predict_match(home_team, away_team)
    
    if result is None:
        logger.info("Error: Could not find one or both teams!")
        return

    logger.info(f"\n  PREDICTION: {result['prediction']}")
    logger.info(f"\n  PROBABILITIES:")
    logger.info(f"    Home Win ({home_team}): {result['probabilities']['Home Win']}")
    logger.info(f"    Draw:                   {result['probabilities']['Draw']}")
    logger.info(f"    Away Win ({away_team}): {result['probabilities']['Away Win']}")


if __name__ == "__main__":
    main()