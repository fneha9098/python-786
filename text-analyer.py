import tkinter as tk

# -------- Functions --------
def characters():
    text = box.get("1.0", tk.END)
    result.config(text="Characters: " + str(len(text)-1))

def words():
    text = box.get("1.0", tk.END)
    result.config(text="Words: " + str(len(text.split())))

def upper():
    text = box.get("1.0", tk.END)
    result.config(text="Uppercase: " + text.upper())

def lower():
    text = box.get("1.0", tk.END)
    result.config(text="Lowercase: " + text.lower())

def replace():
    text = box.get("1.0", tk.END)
    old = old_entry.get()
    new = new_entry.get()
    result.config(text="Updated: " + text.replace(old, new))

def letter():
    text = box.get("1.0", tk.END)
    l = letter_entry.get()
    result.config(text="Letter Count: " + str(text.count(l)))

# -------- Window --------
root = tk.Tk()
root.title("Text Analyzer Tool")
root.geometry("420x650")
root.configure(bg="#e6f2ff")

# -------- Title --------
title = tk.Label(root, text="Text Analyzer Tool",
                 font=("Arial", 16, "bold"),
                 bg="#e6f2ff")
title.pack(pady=10)

# -------- Text Input --------
tk.Label(root, text="Enter Sentence:", bg="#e6f2ff").pack()
box = tk.Text(root, height=4, width=35)
box.pack(pady=5)

# -------- Buttons --------
btn1 = tk.Button(root, text="Count Characters", width=20, command=characters)
btn1.pack(pady=3)

btn2 = tk.Button(root, text="Count Words", width=20, command=words)
btn2.pack(pady=3)

btn3 = tk.Button(root, text="Uppercase", width=20, command=upper)
btn3.pack(pady=3)

btn4 = tk.Button(root, text="Lowercase", width=20, command=lower)
btn4.pack(pady=3)

# -------- Replace Word --------
tk.Label(root, text="Word to Replace:", bg="#e6f2ff").pack(pady=5)
old_entry = tk.Entry(root)
old_entry.pack()

tk.Label(root, text="New Word:", bg="#e6f2ff").pack()
new_entry = tk.Entry(root)
new_entry.pack()

tk.Button(root, text="Replace Word", width=20, command=replace).pack(pady=5)

# -------- Letter Count --------
tk.Label(root, text="Enter Letter:", bg="#e6f2ff").pack(pady=5)
letter_entry = tk.Entry(root)
letter_entry.pack()

tk.Button(root, text="Count Letter", width=20, command=letter).pack(pady=5)

# -------- Result --------
result = tk.Label(root,
                  text="Result will appear here",
                  font=("Arial", 11),
                  bg="white",
                  width=35,
                  height=3,
                  relief="sunken")
result.pack(pady=15)

root.mainloop()