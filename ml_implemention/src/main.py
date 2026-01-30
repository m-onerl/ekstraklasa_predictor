from .prediction import predict_match

def main():

    print("  EKSTRAKLASA MATCH PREDICTOR")

    
    home_team = input("\nEnter HOME team name: ").strip()
    away_team = input("Enter AWAY team name: ").strip()
    
    print(f"\nPredicting: {home_team} vs {away_team}...")
    
    result = predict_match(home_team, away_team)
    
    if result is None:
        print("Error: Could not find one or both teams!")
        return

    print(f"\n  PREDICTION: {result['prediction']}")
    print(f"\n  PROBABILITIES:")
    print(f"    Home Win ({home_team}): {result['probabilities']['Home Win']}")
    print(f"    Draw:                   {result['probabilities']['Draw']}")
    print(f"    Away Win ({away_team}): {result['probabilities']['Away Win']}")


if __name__ == "__main__":
    main()