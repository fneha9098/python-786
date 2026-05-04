import tkinter as tk
from tkinter import messagebox

# List to store student records
students = []

# Function to Add Student
def add_student():
    name = entry_name.get()
    roll = entry_roll.get()
    marks = entry_marks.get()

    if name == "" or roll == "" or marks == "":
        messagebox.showwarning("Warning", "Please fill all fields")
        return

    student = {
        "name": name,
        "roll": roll,
        "marks": marks
    }

    students.append(student)
    messagebox.showinfo("Success", "Student Added Successfully")

    entry_name.delete(0, tk.END)
    entry_roll.delete(0, tk.END)
    entry_marks.delete(0, tk.END)

# Function to View Students
def view_students():
    text_area.delete("1.0", tk.END)

    if not students:
        text_area.insert(tk.END, "No Records Found\n")
        return

    for student in students:
        record = f"Name: {student['name']} | Roll: {student['roll']} | Marks: {student['marks']}\n"
        text_area.insert(tk.END, record)

# Main Window
root = tk.Tk()
root.title("Student Record System")
root.geometry("500x500")

# Labels
tk.Label(root, text="Student Record System", font=("Arial", 16)).pack(pady=10)

tk.Label(root, text="Name").pack()
entry_name = tk.Entry(root)
entry_name.pack()

tk.Label(root, text="Roll Number").pack()
entry_roll = tk.Entry(root)
entry_roll.pack()

tk.Label(root, text="Marks").pack()
entry_marks = tk.Entry(root)
entry_marks.pack()

# Buttons
tk.Button(root, text="Add Student", command=add_student).pack(pady=10)
tk.Button(root, text="View Students", command=view_students).pack()

# Text Area
text_area = tk.Text(root, height=10, width=50)
text_area.pack(pady=10)

root.mainloop()