
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import *

from ml_implemention.prediction import predict_match, get_all_teams
from ml_implemention.model_training import train_models
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PredictorGui:    
    def __init__(self, root):
        self.root = root
        self.root.title("EKSTRAKLASA MATCH PREDICTOR")
        self.root.geometry("1400x700")
        self.teams = get_all_teams()
        
        self.setup_ui()
        
    def setup_ui(self):

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main_frame, text="EKSTRAKLASA MATCH PREDICTOR", font=('Helvetica', 16, 'bold'))
        title.pack(pady=20)

        team_frame = ttk.LabelFrame(main_frame, text="Select Teams", padding="10")
        team_frame.pack(fill=tk.X, pady=10)
  
        ttk.Label(team_frame, text="Home Team:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.home_var = tk.StringVar()
        self.home_combo = ttk.Combobox(team_frame, textvariable=self.home_var, values=self.teams, width=30)
        self.home_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(team_frame, text="Away Team:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.away_var = tk.StringVar()
        self.away_combo = ttk.Combobox(team_frame, textvariable=self.away_var, values=self.teams, width=30)
        self.away_combo.grid(row=1, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="Predict", command=self.predict).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Train Models", command=self.train).pack(side=tk.LEFT, padx=5)
        

        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.result_var = tk.StringVar(value="Select teams and click Predict")
        ttk.Label(results_frame, textvariable=self.result_var, font=('Helvetica', 12)).pack(pady=10)

        columns = ('Statistic', 'Home', 'Away', 'Total')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=6)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor='center')
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    
    def train(self):
        self.result_var.set("Training models... Please wait")
        self.root.update()
        
        try:
            train_models()
            messagebox.showinfo("Success", "Models trained and saved!")
            self.result_var.set("Models trained successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Training failed: {e}")
            self.result_var.set("Training failed")
    
    def predict(self):
        home = self.home_var.get().strip()
        away = self.away_var.get().strip()
        
        if not home or not away:
            messagebox.showwarning("Warning", "Select both teams")
            return
        
        if home == away:
            messagebox.showwarning("Warning", "Select different teams")
            return
        
        try:
            result = predict_match(home, away)
            
            if result is None:
                messagebox.showerror("Error", "Could not find teams or model not trained")
                return

            self.result_var.set(
                f"Prediction: {result['prediction']}\n"
                f"Home Win: {result['probabilities']['Home Win']} | "
                f"Draw: {result['probabilities']['Draw']} | "
                f"Away Win: {result['probabilities']['Away Win']}"
            )
            
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if 'stats_predictions' in result:
                stat_names = {
                    'corner_kicks': 'Corner Kicks',
                    'fouls': 'Fouls',
                    'yellow_cards': 'Yellow Cards',
                    'ball_possession': 'Ball Possession %',
                    'total_shots': 'Total Shots',
                    'shots_on_target': 'Shots on Target',
                }
                
                for stat, values in result['stats_predictions'].items():
                    self.tree.insert('', tk.END, values=(
                        stat_names.get(stat, stat),
                        values['home'],
                        values['away'],
                        values['total']
                    ))
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed: {e}")
