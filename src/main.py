from .predictor_gui import PredictorGui
import tkinter as tk


def main():
    root = tk.Tk()
    app = PredictorGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()