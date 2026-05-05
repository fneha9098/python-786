import tkinter as tk
from tkinter import messagebox
import random

class ProGuessingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Pro Guessing Game")
        self.root.geometry("520x600")
        self.root.config(bg="#0f172a")

        self.number = 0
        self.attempts = 0
        self.max_range = 100
        self.time_left = 30
        self.timer_running = False

        self.create_ui()
        self.fade_in()
        self.new_game()

    # ---------------- UI ----------------
    def create_ui(self):
        self.title = tk.Label(self.root, text="🎯 Guess The Number",
                              font=("Helvetica", 22, "bold"),
                              bg="#0f172a", fg="#38bdf8")
        self.title.pack(pady=15)

        # Difficulty Selection
        self.difficulty = tk.StringVar(value="Medium")

        diff_frame = tk.Frame(self.root, bg="#0f172a")
        diff_frame.pack()

        tk.Label(diff_frame, text="Difficulty:",
                 bg="#0f172a", fg="white").pack(side="left", padx=5)

        diff_menu = tk.OptionMenu(diff_frame, self.difficulty,
                                 "Easy", "Medium", "Hard")
        diff_menu.config(bg="#1e293b", fg="white")
        diff_menu.pack(side="left")

        # Timer Toggle
        self.timer_var = tk.IntVar()
        tk.Checkbutton(self.root, text="⏱ Timer Mode (30s)",
                       variable=self.timer_var,
                       bg="#0f172a", fg="white",
                       selectcolor="#0f172a").pack(pady=5)

        self.timer_label = tk.Label(self.root, text="Time: 30",
                                    font=("Arial", 12),
                                    bg="#0f172a", fg="#f87171")
        self.timer_label.pack()

        # Entry
        self.entry = tk.Entry(self.root, font=("Arial", 18),
                              justify="center")
        self.entry.pack(pady=15, ipady=5)

        # Buttons
        self.guess_btn = tk.Button(self.root, text="Submit Guess",
                                   command=self.check_guess,
                                   bg="#22c55e", fg="white")
        self.guess_btn.pack(pady=5, ipadx=10, ipady=5)

        self.restart_btn = tk.Button(self.root, text="Restart",
                                     command=self.new_game,
                                     bg="#ef4444", fg="white")
        self.restart_btn.pack(pady=5, ipadx=10, ipady=5)

        self.add_hover(self.guess_btn)
        self.add_hover(self.restart_btn)

        # Result
        self.result = tk.Label(self.root, text="",
                               font=("Arial", 16, "bold"),
                               bg="#0f172a", fg="#facc15")
        self.result.pack(pady=15)

        # Attempts
        self.attempt_label = tk.Label(self.root, text="Attempts: 0",
                                      bg="#0f172a", fg="white")
        self.attempt_label.pack()

        # Progress Bar (Canvas)
        self.canvas = tk.Canvas(self.root, width=300, height=20,
                                bg="#1e293b", highlightthickness=0)
        self.canvas.pack(pady=15)

    # ---------------- Animations ----------------

    def fade_in(self):
        for i in range(0, 11):
            self.root.attributes("-alpha", i * 0.1)
            self.root.update()
            self.root.after(30)

    def shake(self):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        for _ in range(4):
            self.root.geometry(f"+{x+8}+{y}")
            self.root.update()
            self.root.after(20)
            self.root.geometry(f"+{x-8}+{y}")
            self.root.update()
            self.root.after(20)
        self.root.geometry(f"+{x}+{y}")

    def glow(self):
        colors = ["#facc15", "#38bdf8", "#22c55e"]
        current = self.result.cget("fg")
        next_color = colors[(colors.index(current)+1) % len(colors)] if current in colors else colors[0]
        self.result.config(fg=next_color)
        self.root.after(300, self.glow)

    def add_hover(self, btn):
        def enter(e): btn.config(bg="#38bdf8")
        def leave(e):
            if "Restart" in btn.cget("text"):
                btn.config(bg="#ef4444")
            else:
                btn.config(bg="#22c55e")
        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)

    # ---------------- Game Logic ----------------

    def set_difficulty(self):
        level = self.difficulty.get()
        if level == "Easy":
            self.max_range = 50
            self.time_left = 40
        elif level == "Medium":
            self.max_range = 100
            self.time_left = 30
        else:
            self.max_range = 200
            self.time_left = 20

    def new_game(self):
        self.set_difficulty()
        self.number = random.randint(1, self.max_range)
        self.attempts = 0
        self.result.config(text=f"Guess (1 - {self.max_range})")
        self.attempt_label.config(text="Attempts: 0")
        self.entry.delete(0, tk.END)

        self.canvas.delete("all")
        self.update_bar(0)

        self.timer_running = self.timer_var.get() == 1
        if self.timer_running:
            self.countdown()

        self.glow()

    def update_bar(self, guess):
        if guess == 0:
            percent = 0
        else:
            diff = abs(self.number - guess)
            percent = max(0, 100 - int((diff / self.max_range) * 100))

        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, 3*percent, 20, fill="#22c55e")

    def smart_hint(self, guess):
        diff = abs(self.number - guess)
        if diff == 0:
            return "Perfect!"
        elif diff <= 5:
            return "🔥 Very Close!"
        elif diff <= 15:
            return "😊 Close"
        else:
            return "❄️ Far Away"

    def countdown(self):
        if self.timer_running:
            self.timer_label.config(text=f"Time: {self.time_left}")
            if self.time_left <= 0:
                messagebox.showinfo("Time Up!", f"The number was {self.number}")
                self.timer_running = False
                return
            self.time_left -= 1
            self.root.after(1000, self.countdown)

    def check_guess(self):
        try:
            guess = int(self.entry.get())
            self.attempts += 1

            hint = self.smart_hint(guess)

            if guess < self.number:
                self.result.config(text=f"Too Low ⬇️ | {hint}")
                self.shake()

            elif guess > self.number:
                self.result.config(text=f"Too High ⬆️ | {hint}")
                self.shake()

            else:
                self.result.config(text="🎉 Correct!", fg="#22c55e")
                messagebox.showinfo("Winner!", f"Attempts: {self.attempts}")
                self.timer_running = False

            self.update_bar(guess)
            self.attempt_label.config(text=f"Attempts: {self.attempts}")
            self.entry.delete(0, tk.END)

        except ValueError:
            self.shake()
            messagebox.showerror("Error", "Enter a valid number!")

# ---------------- Run ---------------- 
if __name__ == "__main__":
    root = tk.Tk()
    app = ProGuessingGame(root)
    root.mainloop()