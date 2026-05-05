import tkinter as tk
from tkinter import messagebox

# -------------------- Car Class --------------------
class Car:
    def __init__(self, brand, model, speed=0):
        self.brand = brand
        self.model = model
        self.speed = speed
        self.max_speed = 200  # Max speed limit
        self.min_speed = 0    # Min speed limit

    def accelerate(self, increment=10):
        if self.speed + increment > self.max_speed:
            self.speed = self.max_speed
            return f"{self.brand} {self.model} reached max speed!"
        else:
            self.speed += increment
            return f"{self.brand} {self.model} accelerated to {self.speed} km/h"

    def brake(self, decrement=10):
        if self.speed - decrement < self.min_speed:
            self.speed = self.min_speed
            return f"{self.brand} {self.model} stopped!"
        else:
            self.speed -= decrement
            return f"{self.brand} {self.model} slowed down to {self.speed} km/h"

    def display(self):
        return f"Brand: {self.brand}\nModel: {self.model}\nSpeed: {self.speed} km/h"

# -------------------- GUI --------------------
class CarManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Car Management System")
        self.root.geometry("600x500")
        self.root.config(bg="#1e1e2f")

        self.cars = []
        self.current_car = None

        self.create_ui()

    # ---------------- UI ----------------
    def create_ui(self):
        # Title
        self.title = tk.Label(self.root, text="Car Management System", font=("Helvetica", 20, "bold"), fg="#38bdf8", bg="#1e1e2f")
        self.title.pack(pady=15)

        # Car Inputs
        input_frame = tk.Frame(self.root, bg="#1e1e2f")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Brand:", bg="#1e1e2f", fg="white").grid(row=0, column=0, padx=5, pady=5)
        self.brand_entry = tk.Entry(input_frame)
        self.brand_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Model:", bg="#1e1e2f", fg="white").grid(row=1, column=0, padx=5, pady=5)
        self.model_entry = tk.Entry(input_frame)
        self.model_entry.grid(row=1, column=1, padx=5, pady=5)

        # Buttons
        button_frame = tk.Frame(self.root, bg="#1e1e2f")
        button_frame.pack(pady=10)

        self.add_car_btn = tk.Button(button_frame, text="Add Car", bg="#22c55e", fg="white", command=self.add_car)
        self.add_car_btn.grid(row=0, column=0, padx=5, pady=5)

        self.select_car_btn = tk.Button(button_frame, text="Select Car", bg="#38bdf8", fg="white", command=self.select_car)
        self.select_car_btn.grid(row=0, column=1, padx=5, pady=5)

        self.accelerate_btn = tk.Button(button_frame, text="Accelerate", bg="#facc15", fg="white", command=self.accelerate_car)
        self.accelerate_btn.grid(row=0, column=2, padx=5, pady=5)

        self.brake_btn = tk.Button(button_frame, text="Brake", bg="#ef4444", fg="white", command=self.brake_car)
        self.brake_btn.grid(row=0, column=3, padx=5, pady=5)

        self.display_btn = tk.Button(button_frame, text="Display Info", bg="#8b5cf6", fg="white", command=self.display_car)
        self.display_btn.grid(row=0, column=4, padx=5, pady=5)

        # Result Label
        self.result_label = tk.Label(self.root, text="", font=("Arial", 14), fg="#f87171", bg="#1e1e2f")
        self.result_label.pack(pady=20)

        # Car List
        self.car_listbox = tk.Listbox(self.root, width=40)
        self.car_listbox.pack(pady=10)

    # ---------------- Methods ----------------
    def add_car(self):
        brand = self.brand_entry.get().strip()
        model = self.model_entry.get().strip()
        if brand == "" or model == "":
            messagebox.showerror("Error", "Brand and Model cannot be empty!")
            return
        car = Car(brand, model)
        self.cars.append(car)
        self.car_listbox.insert(tk.END, f"{brand} {model}")
        self.brand_entry.delete(0, tk.END)
        self.model_entry.delete(0, tk.END)
        self.result_label.config(text=f"Added Car: {brand} {model}")

    def select_car(self):
        try:
            index = self.car_listbox.curselection()[0]
            self.current_car = self.cars[index]
            self.result_label.config(text=f"Selected Car: {self.current_car.brand} {self.current_car.model}")
        except IndexError:
            messagebox.showerror("Error", "Select a car from the list!")

    def accelerate_car(self):
        if self.current_car:
            msg = self.current_car.accelerate()
            self.result_label.config(text=msg)
        else:
            messagebox.showerror("Error", "No car selected!")

    def brake_car(self):
        if self.current_car:
            msg = self.current_car.brake()
            self.result_label.config(text=msg)
        else:
            messagebox.showerror("Error", "No car selected!")

    def display_car(self):
        if self.current_car:
            info = self.current_car.display()
            self.result_label.config(text=info)
        else:
            messagebox.showerror("Error", "No car selected!")

# ---------------- Run ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CarManagementGUI(root)
    root.mainloop()