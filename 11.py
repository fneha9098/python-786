# Professional Car Management System (Tkinter + SQLite)
# Ready-to-run desktop application

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = "cars.db"


class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER,
                color TEXT,
                price REAL,
                status TEXT,
                created_at TEXT
            )
        ''')
        self.conn.commit()

    def add_car(self, data):
        self.cursor.execute('''
            INSERT INTO cars (brand, model, year, color, price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
        self.conn.commit()

    def get_all_cars(self):
        self.cursor.execute("SELECT * FROM cars ORDER BY id DESC")
        return self.cursor.fetchall()

    def update_car(self, car_id, data):
        self.cursor.execute('''
            UPDATE cars
            SET brand=?, model=?, year=?, color=?, price=?, status=?
            WHERE id=?
        ''', (*data, car_id))
        self.conn.commit()

    def delete_car(self, car_id):
        self.cursor.execute("DELETE FROM cars WHERE id=?", (car_id,))
        self.conn.commit()

    def search_cars(self, keyword):
        self.cursor.execute('''
            SELECT * FROM cars
            WHERE brand LIKE ? OR model LIKE ? OR color LIKE ?
        ''', (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        return self.cursor.fetchall()


class CarManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Car Management System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1f2937")

        self.db = DatabaseManager()
        self.selected_car_id = None

        self.build_ui()
        self.load_data()

    def build_ui(self):
        title = tk.Label(self.root, text="🚗 Professional Car Management System",
                         font=("Arial", 24, "bold"), bg="#1f2937", fg="white")
        title.pack(pady=15)

        top_frame = tk.Frame(self.root, bg="#1f2937")
        top_frame.pack(fill="x", padx=20)

        form = tk.LabelFrame(top_frame, text="Car Details", font=("Arial", 14, "bold"),
                             bg="#374151", fg="white", padx=10, pady=10)
        form.pack(side="left" , fill="both" , expand="true")

        labels = ["Brand", "Model", "Year", "Color", "Price", "Status"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(form, text=label, font=("Arial", 12), bg="#374151", fg="white").grid(row=i, column=0, sticky="w", pady=8)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=i, column=1, pady=8, padx=10)
            self.entries[label.lower()] = entry

        button_frame = tk.Frame(form, bg="#374151")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Add Car", command=self.add_car).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Update", command=self.update_car).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_car).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_form).grid(row=0, column=3, padx=5)

        right = tk.Frame(top_frame, bg="#1f2937")
        right.pack(side="right", fill="both", expand=True, padx=20)

        search_frame = tk.Frame(right, bg="#1f2937")
        search_frame.pack(fill="x", pady=10)

        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", padx=10)
        ttk.Button(search_frame, text="Search", command=self.search_car).pack(side="left")
        ttk.Button(search_frame, text="Refresh", command=self.load_data).pack(side="left", padx=10)

        columns = ("ID", "Brand", "Model", "Year", "Color", "Price", "Status", "Created")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=20)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=40)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select_car)

    def validate(self):
        brand = self.entries["brand"].get().strip()
        model = self.entries["model"].get().strip()
        if not brand or not model:
            messagebox.showerror("Error", "Brand and Model are required")
            return None
        try:
            year = int(self.entries["year"].get() or 0)
            price = float(self.entries["price"].get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Year and Price must be numeric")
            return None
        return (
            brand,
            model,
            year,
            self.entries["color"].get(),
            price,
            self.entries["status"].get()
        )

    def add_car(self):
        data = self.validate()
        if data:
            self.db.add_car((*data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.load_data()
            self.clear_form()

    def update_car(self):
        if not self.selected_car_id:
            messagebox.showwarning("Warning", "Select a car first")
            return
        data = self.validate()
        if data:
            self.db.update_car(self.selected_car_id, data)
            self.load_data()
            self.clear_form()

    def delete_car(self):
        if not self.selected_car_id:
            messagebox.showwarning("Warning", "Select a car first")
            return
        self.db.delete_car(self.selected_car_id)
        self.load_data()
        self.clear_form()

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.db.get_all_cars():
            self.tree.insert("", "end", values=row)

    def search_car(self):
        keyword = self.search_entry.get().strip()
        self.tree.delete(*self.tree.get_children())
        for row in self.db.search_cars(keyword):
            self.tree.insert("", "end", values=row)

    def select_car(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        self.selected_car_id = values[0]
        keys = ["brand", "model", "year", "color", "price", "status"]
        for i, key in enumerate(keys, start=1):
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, values[i])

    def clear_form(self):
        self.selected_car_id = None
        for entry in self.entries.values():
            entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = CarManagementSystem(root)
    root.mainloop()
