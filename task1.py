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

    # Check if roll number already exists
    for student in students:
        if student['roll'] == roll:
            messagebox.showwarning("Warning", "Roll Number already exists!")
            return

    student = {
        "name": name,
        "roll": roll,
        "marks": marks
    }

    students.append(student)
    messagebox.showinfo("Success", "Student Added Successfully")
    clear_entries()

# Function to View Students
def view_students():
    text_area.delete("1.0", tk.END)

    if not students:
        text_area.insert(tk.END, "No Records Found\n")
        return

    for student in students:
        record = f"Name: {student['name']} | Roll: {student['roll']} | Marks: {student['marks']}\n"
        text_area.insert(tk.END, record)

# Function to Search Student
def search_student():
    roll = entry_roll.get()
    text_area.delete("1.0", tk.END)

    if roll == "":
        messagebox.showwarning("Warning", "Enter Roll Number to search")
        return

    found = False
    for student in students:
        if student['roll'] == roll:
            record = f"Name: {student['name']} | Roll: {student['roll']} | Marks: {student['marks']}\n"
            text_area.insert(tk.END, record)
            found = True
            break

    if not found:
        text_area.insert(tk.END, "No Record Found\n")

# Function to Update Student
def update_student():
    name = entry_name.get()
    roll = entry_roll.get()
    marks = entry_marks.get()

    if roll == "":
        messagebox.showwarning("Warning", "Enter Roll Number to update")
        return

    for student in students:
        if student['roll'] == roll:
            if name != "":
                student['name'] = name
            if marks != "":
                student['marks'] = marks
            messagebox.showinfo("Success", "Student Record Updated Successfully")
            clear_entries()
            return

    messagebox.showwarning("Warning", "No Record Found to Update")

# Function to Remove Student
def remove_student():
    roll = entry_roll.get()

    if roll == "":
        messagebox.showwarning("Warning", "Enter Roll Number to remove")
        return

    for student in students:
        if student['roll'] == roll:
            students.remove(student)
            messagebox.showinfo("Success", "Student Record Removed Successfully")
            clear_entries()
            return

    messagebox.showwarning("Warning", "No Record Found to Remove")

# Function to clear entries
def clear_entries():
    entry_name.delete(0, tk.END)
    entry_roll.delete(0, tk.END)
    entry_marks.delete(0, tk.END)

# Main Window
root = tk.Tk()
root.title("Student Record System")
root.geometry("550x600")

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
tk.Button(root, text="Add Student", command=add_student).pack(pady=5)
tk.Button(root, text="View Students", command=view_students).pack(pady=5)
tk.Button(root, text="Search Student", command=search_student).pack(pady=5)
tk.Button(root, text="Update Student", command=update_student).pack(pady=5)
tk.Button(root, text="Remove Student", command=remove_student).pack(pady=5)

# Text Area
text_area = tk.Text(root, height=15, width=60)
text_area.pack(pady=10)

root.mainloop()