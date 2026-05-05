import tkinter as tk
from tkinter import messagebox
import random

# -----------------------------
# Main Game Class
# -----------------------------
class GuessingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Number Guessing Game")
        self.root.geometry("450x500")
        self.root.config(bg="#1e1e2f")

        self.number = 0
        self.attempts = 0
        self.max_range = 100

        self.create_widgets()
        self.new_game()

    # -----------------------------
    # UI Design
    # -----------------------------
    def create_widgets(self):
        title = tk.Label(self.root, text="Guess The Number 🎯",
                         font=("Helvetica", 20, "bold"),
                         bg="#1e1e2f", fg="#ffffff")
        title.pack(pady=20)

        # Difficulty Selection
        self.difficulty = tk.StringVar(value="Easy")

        diff_frame = tk.Frame(self.root, bg="#1e1e2f")
        diff_frame.pack()

        tk.Label(diff_frame, text="Select Difficulty:",
                 bg="#1e1e2f", fg="white").pack()

        tk.OptionMenu(diff_frame, self.difficulty,
                      "Easy", "Medium", "Hard").pack(pady=5)

        # Entry Box
        self.entry = tk.Entry(self.root, font=("Arial", 16), justify="center")
        self.entry.pack(pady=20)

        # Guess Button
        guess_btn = tk.Button(self.root, text="Submit Guess",
                              command=self.check_guess,
                              bg="#4CAF50", fg="white",
                              font=("Arial", 12), width=15)
        guess_btn.pack(pady=10)

        # Result Label
        self.result_label = tk.Label(self.root, text="",
                                     font=("Arial", 14),
                                     bg="#1e1e2f", fg="#00ffcc")
        self.result_label.pack(pady=10)

        # Attempts Label
        self.attempt_label = tk.Label(self.root, text="Attempts: 0",
                                      font=("Arial", 12),
                                      bg="#1e1e2f", fg="white")
        self.attempt_label.pack()

        # Restart Button
        restart_btn = tk.Button(self.root, text="Restart Game",
                                command=self.new_game,
                                bg="#ff4757", fg="white",
                                font=("Arial", 12), width=15)
        restart_btn.pack(pady=20)

    # -----------------------------
    # Game Logic
    # -----------------------------
    def set_difficulty(self):
        level = self.difficulty.get()
        if level == "Easy":
            self.max_range = 50
        elif level == "Medium":
            self.max_range = 100
        else:
            self.max_range = 200

    def new_game(self):
        self.set_difficulty()
        self.number = random.randint(1, self.max_range)
        self.attempts = 0
        self.result_label.config(text=f"Guess a number (1 - {self.max_range})")
        self.attempt_label.config(text="Attempts: 0")
        self.entry.delete(0, tk.END)

    def check_guess(self):
        try:
            guess = int(self.entry.get())
            self.attempts += 1

            if guess < self.number:
                self.result_label.config(text="Too Low ⬇️", fg="orange")
            elif guess > self.number:
                self.result_label.config(text="Too High ⬆️", fg="orange")
            else:
                self.result_label.config(text="Correct! 🎉", fg="lightgreen")
                messagebox.showinfo("🎉 Winner!",
                                    f"You guessed it in {self.attempts} attempts!")
            
            self.attempt_label.config(text=f"Attempts: {self.attempts}")
            self.entry.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number!")

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = GuessingGame(root)
    root.mainloop()