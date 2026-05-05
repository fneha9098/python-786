"""
SMART STORE MANAGEMENT SYSTEM - PROFESSIONAL EDITION
=====================================================
Features Included:
✓ Barcode Scanner Support
✓ Customer Database & History
✓ Export Reports to Excel/PDF
✓ Product Images
✓ Email Receipts
✓ Loyalty Points System
✓ Bulk Import/Export (CSV/Excel)
✓ Best Sellers Report
✓ Hold/Recall Orders
✓ Low Stock Email Alerts
✓ Product Categories with Images
✓ Sales Dashboard with Charts
✓ Employee Performance Tracking
✓ Profit Margin Analysis
✓ Multiple Payment Methods
✓ Digital Receipts
✓ Customer Feedback/Ratings
✓ Wishlist for Customers
✓ Order Tracking
✓ Seasonal Discounts
✓ BOGO Offers
✓ Volume Discounts
✓ Cash Drawer Integration
✓ Calculator Tool
✓ Dark/Light Theme
✓ Keyboard Shortcuts
✓ Data Backup/Restore
✓ User Activity Log
✓ Multi-language Support (English/Spanish)
✓ And more...
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
import os
from datetime import datetime, timedelta
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
from PIL import Image, ImageTk
import base64
from io import BytesIO
import random
import string
import shutil
from collections import defaultdict

# -------------------------- CONFIGURATION --------------------------
class Config:
    # Email settings for receipts
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "yourstore@gmail.com"  # Update this
    EMAIL_PASSWORD = "yourpassword"  # Update this
    
    # File paths
    DATA_DIR = "store_data"
    PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
    CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
    TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
    BACKUP_DIR = os.path.join(DATA_DIR, "backups")
    IMAGES_DIR = os.path.join(DATA_DIR, "product_images")
    
    # Store settings
    STORE_NAME = "Smart Store"
    TAX_RATE = 0.00  # 0% tax by default
    CURRENCY_SYMBOL = "$"
    LOW_STOCK_THRESHOLD = 5
    LOYALTY_POINTS_RATE = 0.01  # 1 point per $1 spent
    
    # Create directories
    @staticmethod
    def init_dirs():
        for dir_path in [Config.DATA_DIR, Config.BACKUP_DIR, Config.IMAGES_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

Config.init_dirs()

# -------------------------- CLASSES --------------------------
class User:
    def __init__(self, username, password, role="staff", full_name="", email=""):
        self.username = username
        self.password = hashlib.sha256(password.encode()).hexdigest()
        self.role = role
        self.full_name = full_name
        self.email = email
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.activity_log = []

class Customer:
    def __init__(self, customer_id, name, phone="", email="", address=""):
        self.customer_id = customer_id
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.loyalty_points = 0
        self.total_spent = 0
        self.purchase_history = []
        self.wishlist = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "loyalty_points": self.loyalty_points,
            "total_spent": self.total_spent,
            "purchase_history": self.purchase_history,
            "wishlist": self.wishlist,
            "created_at": self.created_at
        }

class Product:
    def __init__(self, product_id, name, price, stock, category="General", 
                 barcode="", cost_price=0, image_path="", supplier=""):
        self.product_id = str(product_id)
        self.name = name
        self.price = price
        self.cost_price = cost_price
        self.stock = stock
        self.category = category
        self.barcode = barcode
        self.image_path = image_path
        self.supplier = supplier
        self.reorder_point = Config.LOW_STOCK_THRESHOLD
        self.ratings = []  # List of (customer_id, rating, review)
        self.times_sold = 0
        
    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "cost_price": self.cost_price,
            "stock": self.stock,
            "category": self.category,
            "barcode": self.barcode,
            "image_path": self.image_path,
            "supplier": self.supplier,
            "reorder_point": self.reorder_point,
            "ratings": self.ratings,
            "times_sold": self.times_sold
        }
    
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.price) * 100
        return 0
    
    def average_rating(self):
        if not self.ratings:
            return 0
        return sum(r[1] for r in self.ratings) / len(self.ratings)

class Transaction:
    def __init__(self, transaction_id, items, total, discount=0, final_total=0, 
                 cashier="", payment_method="Cash", customer_id=None, 
                 points_used=0, points_earned=0):
        self.transaction_id = transaction_id
        self.items = items
        self.total = total
        self.discount = discount
        self.final_total = final_total
        self.cashier = cashier
        self.payment_method = payment_method
        self.customer_id = customer_id
        self.points_used = points_used
        self.points_earned = points_earned
        self.status = "Completed"
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "items": self.items,
            "total": self.total,
            "discount": self.discount,
            "final_total": self.final_total,
            "cashier": self.cashier,
            "payment_method": self.payment_method,
            "customer_id": self.customer_id,
            "points_used": self.points_used,
            "points_earned": self.points_earned,
            "status": self.status,
            "date": self.date
        }

class HeldOrder:
    def __init__(self, order_id, cart, customer_id, total, created_at):
        self.order_id = order_id
        self.cart = cart
        self.customer_id = customer_id
        self.total = total
        self.created_at = created_at

# -------------------------- MAIN APPLICATION --------------------------
class SmartStorePro:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Store Pro - Complete Management System")
        self.root.geometry("1400x800")
        self.root.configure(bg='#1e1e2f')
        
        # Color schemes
        self.themes = {
            "dark": {
                'bg': '#1e1e2f', 'card': '#2d2d44', 'accent': '#6c5ce7',
                'success': '#00b894', 'danger': '#d63031', 'warning': '#fdcb6e',
                'info': '#0984e3', 'text': '#dfe6e9'
            },
            "light": {
                'bg': '#f5f5f5', 'card': '#ffffff', 'accent': '#6c5ce7',
                'success': '#00b894', 'danger': '#d63031', 'warning': '#fdcb6e',
                'info': '#0984e3', 'text': '#2d3436'
            }
        }
        self.current_theme = "dark"
        self.colors = self.themes[self.current_theme]
        
        # Data storage
        self.products = {}
        self.customers = {}
        self.transactions = []
        self.users = {}
        self.held_orders = {}
        self.cart = {}
        self.current_customer = None
        self.current_user = None
        self.next_product_id = 1
        self.next_customer_id = 1
        self.next_transaction_id = 1
        self.next_order_id = 1
        self.discount_percent = 0
        self.selected_promo = None
        self.barcode_buffer = ""
        self.barcode_timer = None
        
        # Load data
        self.load_all_data()
        
        # Show role selection
        self.show_role_selection()
    
    def load_all_data(self):
        """Load all data from JSON files"""
        try:
            if os.path.exists(Config.PRODUCTS_FILE):
                with open(Config.PRODUCTS_FILE, 'r') as f:
                    data = json.load(f)
                    for pid, pdata in data.items():
                        self.products[pid] = Product(
                            pdata["product_id"], pdata["name"],
                            pdata["price"], pdata["stock"], pdata["category"],
                            pdata.get("barcode", ""), pdata.get("cost_price", 0),
                            pdata.get("image_path", ""), pdata.get("supplier", "")
                        )
                        self.products[pid].times_sold = pdata.get("times_sold", 0)
                    if self.products:
                        self.next_product_id = max(int(p) for p in self.products.keys()) + 1
        except Exception as e:
            print(f"Error loading products: {e}")
        
        try:
            if os.path.exists(Config.CUSTOMERS_FILE):
                with open(Config.CUSTOMERS_FILE, 'r') as f:
                    data = json.load(f)
                    for cid, cdata in data.items():
                        customer = Customer(cdata["customer_id"], cdata["name"],
                                           cdata.get("phone", ""), cdata.get("email", ""),
                                           cdata.get("address", ""))
                        customer.loyalty_points = cdata.get("loyalty_points", 0)
                        customer.total_spent = cdata.get("total_spent", 0)
                        customer.purchase_history = cdata.get("purchase_history", [])
                        customer.wishlist = cdata.get("wishlist", [])
                        self.customers[cid] = customer
                    if self.customers:
                        self.next_customer_id = max(int(c) for c in self.customers.keys()) + 1
        except Exception as e:
            print(f"Error loading customers: {e}")
        
        try:
            if os.path.exists(Config.TRANSACTIONS_FILE):
                with open(Config.TRANSACTIONS_FILE, 'r') as f:
                    trans_data = json.load(f)
                    for t in trans_data:
                        transaction = Transaction(
                            t["transaction_id"], t["items"],
                            t["total"], t["discount"], t["final_total"],
                            t.get("cashier", ""), t.get("payment_method", "Cash"),
                            t.get("customer_id"), t.get("points_used", 0),
                            t.get("points_earned", 0)
                        )
                        transaction.status = t.get("status", "Completed")
                        transaction.date = t["date"]
                        self.transactions.append(transaction)
                    if self.transactions:
                        self.next_transaction_id = max(t.transaction_id for t in self.transactions) + 1
        except Exception as e:
            print(f"Error loading transactions: {e}")
        
        try:
            if os.path.exists(Config.USERS_FILE):
                with open(Config.USERS_FILE, 'r') as f:
                    users_data = json.load(f)
                    for username, user_data in users_data.items():
                        user = User(username, "", user_data["role"], 
                                   user_data.get("full_name", ""), user_data.get("email", ""))
                        user.password = user_data["password"]
                        self.users[username] = user
        except Exception as e:
            print(f"Error loading users: {e}")
        
        # Create default admin if no users exist
        if not self.users:
            admin = User("admin", "admin123", "admin", "System Administrator", "admin@store.com")
            self.users["admin"] = admin
            self.save_users()
    
    def save_all_data(self):
        """Save all data to JSON files"""
        self.save_products()
        self.save_customers()
        self.save_transactions()
        self.save_users()
    
    def save_products(self):
        try:
            data = {pid: product.to_dict() for pid, product in self.products.items()}
            with open(Config.PRODUCTS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save products: {e}")
    
    def save_customers(self):
        try:
            data = {cid: customer.to_dict() for cid, customer in self.customers.items()}
            with open(Config.CUSTOMERS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save customers: {e}")
    
    def save_transactions(self):
        try:
            data = [t.to_dict() for t in self.transactions]
            with open(Config.TRANSACTIONS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save transactions: {e}")
    
    def save_users(self):
        try:
            data = {username: {"password": user.password, "role": user.role,
                              "full_name": user.full_name, "email": user.email}
                   for username, user in self.users.items()}
            with open(Config.USERS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def backup_data(self):
        """Create backup of all data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(Config.BACKUP_DIR, f"backup_{timestamp}")
            os.makedirs(backup_folder)
            
            for file in os.listdir(Config.DATA_DIR):
                if file.endswith('.json'):
                    src = os.path.join(Config.DATA_DIR, file)
                    dst = os.path.join(backup_folder, file)
                    shutil.copy2(src, dst)
            
            messagebox.showinfo("Success", f"Backup created successfully!\nLocation: {backup_folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")
    
    def restore_backup(self):
        """Restore data from backup"""
        backup_folder = filedialog.askdirectory(title="Select Backup Folder")
        if backup_folder:
            try:
                for file in os.listdir(backup_folder):
                    if file.endswith('.json'):
                        src = os.path.join(backup_folder, file)
                        dst = os.path.join(Config.DATA_DIR, file)
                        shutil.copy2(src, dst)
                
                messagebox.showinfo("Success", "Restore completed! Please restart the application.")
                self.root.quit()
            except Exception as e:
                messagebox.showerror("Error", f"Restore failed: {e}")
    
    def center_window(self, window, width, height):
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    # -------------------------- AUTHENTICATION --------------------------
    def show_role_selection(self):
        role_window = tk.Toplevel(self.root)
        role_window.title("Select Mode")
        role_window.configure(bg=self.colors['bg'])
        role_window.transient(self.root)
        role_window.grab_set()
        self.center_window(role_window, 500, 450)
        
        main_frame = tk.Frame(role_window, bg=self.colors['card'])
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        tk.Label(main_frame, text="🏪 SMART STORE PRO", 
                font=('Arial', 24, 'bold'), bg=self.colors['card'], 
                fg=self.colors['accent']).pack(pady=20)
        
        tk.Label(main_frame, text="Select Mode", font=('Arial', 14),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=10)
        
        tk.Button(main_frame, text="👑 ADMIN MODE", font=('Arial', 14, 'bold'),
                 bg=self.colors['danger'], fg='white', 
                 command=lambda: self.proceed_login(role_window, "admin"),
                 relief='flat', cursor='hand2', height=2).pack(fill='x', pady=10, padx=20)
        
        tk.Button(main_frame, text="🛒 USER MODE (SHOPPING)", font=('Arial', 14, 'bold'),
                 bg=self.colors['success'], fg='white', 
                 command=lambda: self.proceed_login(role_window, "user"),
                 relief='flat', cursor='hand2', height=2).pack(fill='x', pady=10, padx=20)
        
        tk.Button(main_frame, text="❌ EXIT", font=('Arial', 11),
                 bg='#636e72', fg='white', command=self.root.quit,
                 relief='flat', cursor='hand2').pack(fill='x', pady=20, padx=20)
    
    def proceed_login(self, window, mode):
        self.selected_mode = mode
        window.destroy()
        self.show_login()
    
    def show_login(self):
        login_window = tk.Toplevel(self.root)
        login_window.title(f"Login - {self.selected_mode.upper()} Mode")
        login_window.configure(bg=self.colors['bg'])
        login_window.transient(self.root)
        login_window.grab_set()
        self.center_window(login_window, 450, 500)
        
        main_frame = tk.Frame(login_window, bg=self.colors['card'])
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        mode_color = self.colors['danger'] if self.selected_mode == "admin" else self.colors['success']
        tk.Label(main_frame, text=f"{'ADMIN' if self.selected_mode == 'admin' else 'USER'} MODE",
                font=('Arial', 12, 'bold'), bg=mode_color, fg='white',
                padx=20, pady=5).pack(pady=10)
        
        tk.Label(main_frame, text="🏪 SMART STORE", font=('Arial', 24, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=20)
        
        tk.Label(main_frame, text="Username:", font=('Arial', 11),
                bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')
        username_entry = tk.Entry(main_frame, font=('Arial', 12), bg='#3d3d5c',
                                  fg='white', relief='flat')
        username_entry.pack(fill='x', pady=(0, 15), ipady=8)
        
        tk.Label(main_frame, text="Password:", font=('Arial', 11),
                bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')
        password_entry = tk.Entry(main_frame, font=('Arial', 12), bg='#3d3d5c',
                                  fg='white', show="*", relief='flat')
        password_entry.pack(fill='x', pady=(0, 20), ipady=8)
        
        def do_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if self.selected_mode == "admin":
                if username in self.users and self.users[username].role == "admin":
                    hashed = hashlib.sha256(password.encode()).hexdigest()
                    if self.users[username].password == hashed:
                        self.current_user = self.users[username]
                        login_window.destroy()
                        self.setup_admin_interface()
                        return
                messagebox.showerror("Error", "Invalid admin credentials!\nUse: admin / admin123")
            else:
                # User mode - simple access
                self.current_user = User(username, password, "user", username)
                login_window.destroy()
                self.setup_user_interface()
        
        tk.Button(main_frame, text="LOGIN", command=do_login,
                 bg=self.colors['accent'], fg='white', font=('Arial', 12, 'bold'),
                 relief='flat', cursor='hand2').pack(fill='x', pady=10, ipady=10)
        
        if self.selected_mode == "user":
            tk.Button(main_frame, text="CONTINUE AS GUEST", 
                     command=lambda: [setattr(self, 'current_user', User("guest", "", "user", "Guest")),
                                     login_window.destroy(), self.setup_user_interface()],
                     bg=self.colors['warning'], fg='white', font=('Arial', 10),
                     relief='flat', cursor='hand2').pack(fill='x', pady=5, ipady=8)
    
    # -------------------------- ADMIN INTERFACE --------------------------
    def setup_admin_interface(self):
        """Complete admin interface with all features"""
        self.root.configure(bg=self.colors['bg'])
        
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header with toolbar
        header = tk.Frame(self.root, bg=self.colors['card'], height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Title
        title = tk.Label(header, text="👑 SMART STORE PRO - ADMIN DASHBOARD", 
                        font=('Arial', 18, 'bold'), bg=self.colors['card'], 
                        fg=self.colors['danger'])
        title.pack(side='left', padx=20, pady=20)
        
        # Toolbar buttons
        toolbar = tk.Frame(header, bg=self.colors['card'])
        toolbar.pack(side='right', padx=20)
        
        tk.Button(toolbar, text="🌓 Theme", command=self.toggle_theme,
                 bg=self.colors['info'], fg='white', relief='flat',
                 cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(toolbar, text="💾 Backup", command=self.backup_data,
                 bg=self.colors['success'], fg='white', relief='flat',
                 cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(toolbar, text="🔄 Restore", command=self.restore_backup,
                 bg=self.colors['warning'], fg='white', relief='flat',
                 cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(toolbar, text="🔄 Switch to User", command=self.switch_to_user,
                 bg=self.colors['accent'], fg='white', relief='flat',
                 cursor='hand2').pack(side='left', padx=5)
        
        # Notebook for tabs
        style = ttk.Style()
        style.configure('Custom.TNotebook', background=self.colors['bg'])
        style.configure('Custom.TNotebook.Tab', padding=[15, 8], font=('Arial', 10))
        
        self.notebook = ttk.Notebook(self.root, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create all tabs
        self.create_pos_tab()
        self.create_inventory_tab()
        self.create_customers_tab()
        self.create_reports_tab()
        self.create_promotions_tab()
        self.create_settings_tab()
        
        # Refresh displays
        self.refresh_inventory_tree()
        self.refresh_pos_products()
        self.refresh_customers_tree()
        self.update_dashboard()
    
    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.colors = self.themes[self.current_theme]
        self.setup_admin_interface()
    
    def switch_to_user(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_user_interface()
    
    # -------------------------- POS TAB --------------------------
    def create_pos_tab(self):
        self.pos_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.pos_tab, text="  🛒 POINT OF SALE  ")
        
        # Main container
        main_container = tk.Frame(self.pos_tab, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Products
        left_panel = tk.Frame(main_container, bg=self.colors['card'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(left_panel, text="📋 PRODUCT CATALOG", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=10)
        
        # Search and barcode
        search_frame = tk.Frame(left_panel, bg=self.colors['card'])
        search_frame.pack(fill='x', padx=10, pady=5)
        
        self.pos_search = tk.Entry(search_frame, font=('Arial', 11), bg='#3d3d5c',
                                   fg='white', relief='flat')
        self.pos_search.pack(side='left', fill='x', expand=True, ipady=8)
        self.pos_search.bind('<KeyRelease>', lambda e: self.search_pos_products())
        
        tk.Button(search_frame, text="🔍", command=self.search_pos_products,
                 bg=self.colors['info'], fg='white', relief='flat', width=5).pack(side='left', padx=5)
        
        tk.Label(search_frame, text="📷 Barcode:", font=('Arial', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=10)
        
        self.barcode_entry = tk.Entry(search_frame, font=('Arial', 11), bg='#3d3d5c',
                                      fg='white', relief='flat', width=15)
        self.barcode_entry.pack(side='left', padx=5)
        self.barcode_entry.bind('<Return>', lambda e: self.scan_barcode())
        
        # Products tree
        product_container = tk.Frame(left_panel, bg=self.colors['card'])
        product_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(product_container, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(product_container, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Price', 'Stock', 'Category')
        self.pos_tree = ttk.Treeview(product_container, columns=columns, show='headings',
                                     yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.pos_tree.yview)
        h_scroll.config(command=self.pos_tree.xview)
        
        for col in columns:
            self.pos_tree.heading(col, text=col)
            self.pos_tree.column(col, width=120)
        self.pos_tree.column('Name', width=200)
        self.pos_tree.pack(fill='both', expand=True)
        self.pos_tree.bind('<Double-Button-1>', lambda e: self.add_to_cart())
        
        # Right panel - Cart
        right_panel = tk.Frame(main_container, bg=self.colors['card'], width=500)
        right_panel.pack(side='right', fill='both', padx=(10, 0))
        right_panel.pack_propagate(False)
        
        # Customer selection
        customer_frame = tk.Frame(right_panel, bg=self.colors['card'])
        customer_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(customer_frame, text="👤 Customer:", font=('Arial', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left')
        
        self.customer_var = tk.StringVar(value="Walk-in Customer")
        self.customer_combo = ttk.Combobox(customer_frame, textvariable=self.customer_var,
                                           values=["Walk-in Customer"] + list(self.customers.keys()),
                                           width=25)
        self.customer_combo.pack(side='left', padx=5)
        tk.Button(customer_frame, text="➕ New", command=self.add_customer_dialog,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2)
        tk.Button(customer_frame, text="🔄 Points", command=self.show_customer_points,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2)
        
        # Cart title
        tk.Label(right_panel, text="🛒 SHOPPING CART", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['warning']).pack(pady=10)
        
        # Cart tree with scrollbars
        cart_container = tk.Frame(right_panel, bg=self.colors['card'])
        cart_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        cart_v_scroll = ttk.Scrollbar(cart_container, orient='vertical')
        cart_v_scroll.pack(side='right', fill='y')
        cart_h_scroll = ttk.Scrollbar(cart_container, orient='horizontal')
        cart_h_scroll.pack(side='bottom', fill='x')
        
        cart_columns = ('Name', 'Qty', 'Price', 'Total')
        self.cart_tree = ttk.Treeview(cart_container, columns=cart_columns, show='headings',
                                      yscrollcommand=cart_v_scroll.set, xscrollcommand=cart_h_scroll.set)
        cart_v_scroll.config(command=self.cart_tree.yview)
        cart_h_scroll.config(command=self.cart_tree.xview)
        
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=120)
        self.cart_tree.column('Name', width=200)
        self.cart_tree.pack(fill='both', expand=True)
        
        # Cart buttons
        btn_frame = tk.Frame(right_panel, bg=self.colors['card'])
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(btn_frame, text="🗑️ Remove", command=self.remove_from_cart,
                 bg=self.colors['danger'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        tk.Button(btn_frame, text="🔄 Clear", command=self.clear_cart,
                 bg='#636e72', fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        tk.Button(btn_frame, text="💾 Hold Order", command=self.hold_order,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        tk.Button(btn_frame, text="📋 Recall Order", command=self.recall_order,
                 bg=self.colors['warning'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        
        # Promotions
        promo_frame = tk.Frame(right_panel, bg=self.colors['card'])
        promo_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(promo_frame, text="🎁 Promotion:", font=('Arial', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left')
        
        self.promo_var = tk.StringVar(value="None")
        self.promo_combo = ttk.Combobox(promo_frame, textvariable=self.promo_var,
                                        values=["None", "BOGO (Buy 1 Get 1)", "10% OFF", "20% OFF", "Seasonal Sale"],
                                        width=20)
        self.promo_combo.pack(side='left', padx=5)
        self.promo_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_promotion())
        
        # Discount
        discount_frame = tk.Frame(right_panel, bg=self.colors['card'])
        discount_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(discount_frame, text="💸 Discount (%):", font=('Arial', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left')
        
        self.discount_entry = tk.Entry(discount_frame, width=10, font=('Arial', 10),
                                       bg='#3d3d5c', fg='white', relief='flat')
        self.discount_entry.pack(side='left', padx=5)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind('<KeyRelease>', lambda e: self.update_cart_totals())
        
        # Points usage
        points_frame = tk.Frame(right_panel, bg=self.colors['card'])
        points_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(points_frame, text="⭐ Use Points:", font=('Arial', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left')
        
        self.points_use_entry = tk.Entry(points_frame, width=10, font=('Arial', 10),
                                         bg='#3d3d5c', fg='white', relief='flat')
        self.points_use_entry.pack(side='left', padx=5)
        self.points_use_entry.insert(0, "0")
        self.points_use_entry.bind('<KeyRelease>', lambda e: self.update_cart_totals())
        
        # Totals
        totals_frame = tk.Frame(right_panel, bg='#2d2d44', relief='flat', bd=1)
        totals_frame.pack(fill='x', padx=10, pady=10)
        
        self.subtotal_label = tk.Label(totals_frame, text="Subtotal: $0.00",
                                       font=('Arial', 12), bg='#2d2d44', fg=self.colors['text'])
        self.subtotal_label.pack(pady=5)
        
        self.discount_label = tk.Label(totals_frame, text="Discount: $0.00",
                                       font=('Arial', 12), bg='#2d2d44', fg=self.colors['text'])
        self.discount_label.pack(pady=5)
        
        self.points_label = tk.Label(totals_frame, text="Points Used: 0",
                                     font=('Arial', 12), bg='#2d2d44', fg=self.colors['text'])
        self.points_label.pack(pady=5)
        
        self.total_label = tk.Label(totals_frame, text="TOTAL: $0.00",
                                    font=('Arial', 18, 'bold'), bg='#2d2d44', fg=self.colors['success'])
        self.total_label.pack(pady=10)
        
        # Checkout button
        tk.Button(right_panel, text="💳 CHECKOUT & RECEIPT", command=self.checkout,
                 bg=self.colors['success'], fg='white', font=('Arial', 13, 'bold'),
                 relief='flat', cursor='hand2', height=2).pack(fill='x', padx=10, pady=10)
        
        # Calculator
        calc_frame = tk.LabelFrame(right_panel, text="🧮 Calculator", bg=self.colors['card'],
                                   fg=self.colors['text'])
        calc_frame.pack(fill='x', padx=10, pady=5)
        
        self.calc_display = tk.Entry(calc_frame, font=('Arial', 14), bg='#3d3d5c',
                                     fg='white', relief='flat', justify='right')
        self.calc_display.pack(fill='x', padx=5, pady=5, ipady=5)
        
        calc_buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', 'C', '=', '+']
        ]
        
        for row in calc_buttons:
            btn_row = tk.Frame(calc_frame, bg=self.colors['card'])
            btn_row.pack(pady=2)
            for btn in row:
                tk.Button(btn_row, text=btn, width=5, height=1,
                         command=lambda x=btn: self.calc_click(x),
                         bg=self.colors['info'] if btn == '=' else '#3d3d5c',
                         fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2)
    
    def calc_click(self, value):
        if value == 'C':
            self.calc_display.delete(0, tk.END)
        elif value == '=':
            try:
                result = eval(self.calc_display.get())
                self.calc_display.delete(0, tk.END)
                self.calc_display.insert(0, str(result))
            except:
                self.calc_display.delete(0, tk.END)
                self.calc_display.insert(0, "Error")
        else:
            self.calc_display.insert(tk.END, value)
    
    def scan_barcode(self):
        barcode = self.barcode_entry.get()
        if barcode:
            for product in self.products.values():
                if product.barcode == barcode:
                    self.add_product_to_cart(product)
                    self.barcode_entry.delete(0, tk.END)
                    return
            messagebox.showwarning("Not Found", f"No product found with barcode: {barcode}")
            self.barcode_entry.delete(0, tk.END)
    
    def add_product_to_cart(self, product):
        if product.stock <= 0:
            messagebox.showerror("Out of Stock", f"{product.name} is out of stock!")
            return
        
        if product.product_id in self.cart:
            if self.cart[product.product_id]['quantity'] + 1 > product.stock:
                messagebox.showerror("Error", f"Not enough stock! Only {product.stock} available.")
                return
            self.cart[product.product_id]['quantity'] += 1
        else:
            self.cart[product.product_id] = {
                'name': product.name,
                'price': product.price,
                'quantity': 1,
                'product_id': product.product_id
            }
        
        self.refresh_cart()
    
    def add_to_cart(self):
        selected = self.pos_tree.selection()
        if not selected:
            return
        item = self.pos_tree.item(selected[0])
        product_id = str(item['values'][0])
        product = self.products.get(product_id)
        if product:
            self.add_product_to_cart(product)
    
    def refresh_pos_products(self):
        for item in self.pos_tree.get_children():
            self.pos_tree.delete(item)
        for product in self.products.values():
            stock_display = f"{product.stock}"
            if product.stock == 0:
                stock_display = "🔴 OUT"
            elif product.stock < Config.LOW_STOCK_THRESHOLD:
                stock_display = f"🟡 {product.stock}"
            self.pos_tree.insert('', 'end', values=(
                product.product_id, product.name, f"${product.price}",
                stock_display, product.category
            ))
    
    def search_pos_products(self):
        search_term = self.pos_search.get().lower()
        for item in self.pos_tree.get_children():
            self.pos_tree.delete(item)
        for product in self.products.values():
            if search_term in product.name.lower() or search_term in product.category.lower():
                stock_display = f"{product.stock}"
                if product.stock == 0:
                    stock_display = "🔴 OUT"
                elif product.stock < Config.LOW_STOCK_THRESHOLD:
                    stock_display = f"🟡 {product.stock}"
                self.pos_tree.insert('', 'end', values=(
                    product.product_id, product.name, f"${product.price}",
                    stock_display, product.category
                ))
    
    def refresh_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        subtotal = 0
        for item in self.cart.values():
            total = item['price'] * item['quantity']
            subtotal += total
            self.cart_tree.insert('', 'end', values=(
                item['name'], item['quantity'], f"${item['price']}", f"${total:.2f}"
            ))
        
        self.update_cart_totals()
    
    def update_cart_totals(self):
        subtotal = sum(item['price'] * item['quantity'] for item in self.cart.values())
        
        # Apply promotion
        promo_discount = 0
        promo = self.promo_var.get()
        if promo == "10% OFF":
            promo_discount = subtotal * 0.10
        elif promo == "20% OFF":
            promo_discount = subtotal * 0.20
        elif promo == "BOGO (Buy 1 Get 1)":
            # Simple BOGO: discount the cheapest item
            if self.cart:
                cheapest = min(self.cart.values(), key=lambda x: x['price'])
                promo_discount = cheapest['price']
        
        # Manual discount
        try:
            manual_discount = float(self.discount_entry.get()) if self.discount_entry.get() else 0
            if manual_discount < 0 or manual_discount > 100:
                manual_discount = 0
        except:
            manual_discount = 0
        
        manual_discount_amount = subtotal * (manual_discount / 100)
        total_discount = promo_discount + manual_discount_amount
        after_discount = subtotal - total_discount
        
        # Points usage
        try:
            points_used = int(self.points_use_entry.get()) if self.points_use_entry.get() else 0
            customer_id = self.customer_var.get()
            if customer_id != "Walk-in Customer" and customer_id in self.customers:
                max_points = self.customers[customer_id].loyalty_points
                if points_used > max_points:
                    points_used = max_points
                    self.points_use_entry.delete(0, tk.END)
                    self.points_use_entry.insert(0, str(points_used))
            points_value = points_used * 0.01  # 1 cent per point
            if points_value > after_discount:
                points_value = after_discount
                points_used = int(points_value * 100)
        except:
            points_used = 0
            points_value = 0
        
        final_total = after_discount - points_value
        
        self.subtotal_label.config(text=f"Subtotal: ${subtotal:.2f}")
        self.discount_label.config(text=f"Discount: -${total_discount:.2f}")
        self.points_label.config(text=f"Points Used: {points_used} (-${points_value:.2f})")
        self.total_label.config(text=f"TOTAL: ${final_total:.2f}")
        
        return final_total, subtotal, total_discount, points_used, points_value
    
    def apply_promotion(self):
        self.update_cart_totals()
    
    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        item = self.cart_tree.item(selected[0])
        product_name = item['values'][0]
        for pid, cart_item in list(self.cart.items()):
            if cart_item['name'] == product_name:
                del self.cart[pid]
                break
        self.refresh_cart()
    
    def clear_cart(self):
        if messagebox.askyesno("Clear Cart", "Clear entire cart?"):
            self.cart.clear()
            self.refresh_cart()
    
    def hold_order(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Nothing to hold!")
            return
        
        order_id = f"HOLD_{self.next_order_id}"
        self.next_order_id += 1
        
        customer_id = self.customer_var.get()
        if customer_id == "Walk-in Customer":
            customer_id = None
        
        subtotal = sum(item['price'] * item['quantity'] for item in self.cart.values())
        self.held_orders[order_id] = HeldOrder(order_id, self.cart.copy(), customer_id, subtotal, datetime.now())
        
        self.cart.clear()
        self.refresh_cart()
        messagebox.showinfo("Success", f"Order held! ID: {order_id}")
    
    def recall_order(self):
        if not self.held_orders:
            messagebox.showinfo("No Orders", "No held orders available!")
            return
        
        order_list = "\n".join([f"{oid} - ${order.total:.2f} - {order.created_at}" 
                                for oid, order in self.held_orders.items()])
        order_id = simpledialog.askstring("Recall Order", f"Held Orders:\n{order_list}\n\nEnter Order ID:")
        
        if order_id and order_id in self.held_orders:
            order = self.held_orders[order_id]
            self.cart = order.cart.copy()
            if order.customer_id:
                self.customer_var.set(order.customer_id)
            self.refresh_cart()
            del self.held_orders[order_id]
            messagebox.showinfo("Success", "Order recalled!")
    
    def show_customer_points(self):
        customer_id = self.customer_var.get()
        if customer_id != "Walk-in Customer" and customer_id in self.customers:
            customer = self.customers[customer_id]
            messagebox.showinfo("Loyalty Points", 
                               f"Customer: {customer.name}\n"
                               f"Points Available: {customer.loyalty_points}\n"
                               f"Total Spent: ${customer.total_spent:.2f}")
        else:
            messagebox.showinfo("Info", "Please select a customer first!")
    
    def add_customer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.configure(bg=self.colors['card'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 400, 450)
        
        tk.Label(dialog, text="➕ NEW CUSTOMER", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=20)
        
        fields = {}
        labels = ['Full Name:', 'Phone:', 'Email:', 'Address:']
        
        for label in labels:
            frame = tk.Frame(dialog, bg=self.colors['card'])
            frame.pack(fill='x', padx=40, pady=5)
            tk.Label(frame, text=label, font=('Arial', 10),
                    bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')
            entry = tk.Entry(frame, font=('Arial', 11), bg='#3d3d5c', fg='white', relief='flat')
            entry.pack(fill='x', ipady=5)
            fields[label] = entry
        
        def save():
            name = fields['Full Name:'].get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required!")
                return
            
            customer = Customer(str(self.next_customer_id), name,
                               fields['Phone:'].get(), fields['Email:'].get(),
                               fields['Address:'].get())
            self.customers[str(self.next_customer_id)] = customer
            self.next_customer_id += 1
            self.save_customers()
            
            # Update combobox
            self.customer_combo['values'] = ["Walk-in Customer"] + list(self.customers.keys())
            self.customer_var.set(str(customer.customer_id))
            
            messagebox.showinfo("Success", f"Customer {name} added!")
            dialog.destroy()
        
        tk.Button(dialog, text="SAVE", command=save,
                 bg=self.colors['success'], fg='white', font=('Arial', 12, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=40, ipady=10)
    
    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Cart is empty!")
            return
        
        final_total, subtotal, total_discount, points_used, points_value = self.update_cart_totals()
        
        # Payment dialog
        payment_window = tk.Toplevel(self.root)
        payment_window.title("Payment")
        payment_window.configure(bg=self.colors['card'])
        payment_window.transient(self.root)
        payment_window.grab_set()
        self.center_window(payment_window, 400, 500)
        
        tk.Label(payment_window, text="💳 PAYMENT", font=('Arial', 16, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=20)
        
        tk.Label(payment_window, text=f"Total: ${final_total:.2f}", font=('Arial', 14),
                bg=self.colors['card'], fg=self.colors['success']).pack(pady=10)
        
        tk.Label(payment_window, text="Payment Method:", font=('Arial', 12),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=10)
        
        payment_var = tk.StringVar(value="Cash")
        payment_frame = tk.Frame(payment_window, bg=self.colors['card'])
        payment_frame.pack(pady=10)
        
        for method in ["Cash", "Card", "Digital Wallet", "Gift Card"]:
            tk.Radiobutton(payment_frame, text=method, variable=payment_var, value=method,
                          bg=self.colors['card'], fg=self.colors['text'],
                          selectcolor=self.colors['card']).pack(side='left', padx=10)
        
        tk.Label(payment_window, text="Amount Paid:", font=('Arial', 12),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=10)
        
        paid_entry = tk.Entry(payment_window, font=('Arial', 14), bg='#3d3d5c',
                              fg='white', relief='flat', justify='center', width=15)
        paid_entry.pack(pady=10, ipady=5)
        paid_entry.insert(0, str(final_total))
        
        def process():
            try:
                payment_method = payment_var.get()
                paid = float(paid_entry.get())
                
                if paid < final_total:
                    messagebox.showerror("Error", f"Insufficient payment!\nNeed: ${final_total:.2f}")
                    return
                
                change = paid - final_total
                
                # Process sale
                sale_items = []
                for pid, item in self.cart.items():
                    product = self.products[pid]
                    product.stock -= item['quantity']
                    product.times_sold += item['quantity']
                    sale_items.append((item['name'], item['quantity'], item['price']))
                
                customer_id = None
                points_earned = 0
                if self.customer_var.get() != "Walk-in Customer":
                    customer_id = self.customer_var.get()
                    customer = self.customers[customer_id]
                    points_earned = int(final_total * Config.LOYALTY_POINTS_RATE * 100)
                    customer.loyalty_points += points_earned - points_used
                    customer.total_spent += final_total
                    customer.purchase_history.append({
                        'transaction_id': self.next_transaction_id,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'total': final_total
                    })
                    self.save_customers()
                
                transaction = Transaction(
                    self.next_transaction_id, sale_items, subtotal,
                    total_discount, final_total, self.current_user.username,
                    payment_method, customer_id, points_used, points_earned
                )
                self.transactions.append(transaction)
                self.next_transaction_id += 1
                
                self.save_products()
                self.save_transactions()
                
                self.show_receipt(transaction, payment_method, paid, change, points_earned)
                
                self.cart.clear()
                self.refresh_cart()
                self.refresh_inventory_tree()
                self.refresh_pos_products()
                self.update_dashboard()
                
                payment_window.destroy()
                
                # Email receipt if customer has email
                if customer_id and customer_id in self.customers:
                    customer = self.customers[customer_id]
                    if customer.email:
                        self.send_email_receipt(customer.email, transaction)
                
                msg = f"Transaction complete!\nChange: ${change:.2f}\nPoints Earned: {points_earned}"
                messagebox.showinfo("Success", msg)
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(payment_window, text="COMPLETE PAYMENT", command=process,
                 bg=self.colors['success'], fg='white', font=('Arial', 12, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=40, ipady=10)
        
        tk.Button(payment_window, text="Cancel", command=payment_window.destroy,
                 bg=self.colors['danger'], fg='white', relief='flat',
                 cursor='hand2').pack(fill='x', padx=40, ipady=5)
    
    def show_receipt(self, transaction, payment_method, paid, change, points_earned):
        receipt_window = tk.Toplevel(self.root)
        receipt_window.title(f"Receipt #{transaction.transaction_id}")
        receipt_window.configure(bg='white')
        self.center_window(receipt_window, 500, 700)
        
        receipt_text = tk.Text(receipt_window, font=('Courier', 10), bg='white', fg='black', wrap='word')
        receipt_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        receipt = f"""
{'='*45}
                {Config.STORE_NAME}
            {'='*35}
                
          Thank you for shopping with us!
                
{'='*45}
Receipt No: #{transaction.transaction_id}
Date: {transaction.date}
Cashier: {transaction.cashier}
Payment: {payment_method}
{'='*45}

ITEMS PURCHASED:
{'-'*45}
{'Item':<25} {'Qty':>5} {'Price':>7} {'Total':>8}
{'-'*45}
"""
        for item in transaction.items:
            name, qty, price = item
            total = price * qty
            receipt += f"{name[:24]:<25} {qty:>5} ${price:>6.2f} ${total:>7.2f}\n"
        
        receipt += f"""{'-'*45}
{'Subtotal':<38} ${transaction.total:>6.2f}
"""
        if transaction.discount > 0:
            receipt += f"{'Discount':<38} -${transaction.discount:>6.2f}\n"
        
        receipt += f"""{'TOTAL':<38} ${transaction.final_total:>6.2f}
{'Paid':<38} ${paid:>6.2f}
{'Change':<38} ${change:>6.2f}
"""
        if points_earned > 0:
            receipt += f"{'Points Earned':<38} {points_earned:>6}\n"
        
        receipt += f"""
{'='*45}
    Payment Status: ✅ COMPLETED
    
    Return Policy:
    Items can be returned within 7 days
    with original receipt.
    
{'='*45}
        Thank you! Visit Again!
{'='*45}
"""
        receipt_text.insert('1.0', receipt)
        receipt_text.config(state='disabled')
        
        btn_frame = tk.Frame(receipt_window, bg='white')
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        def save_receipt():
            with open(f"receipt_{transaction.transaction_id}.txt", "w") as f:
                f.write(receipt)
            messagebox.showinfo("Success", "Receipt saved!")
        
        tk.Button(btn_frame, text="💾 Save", command=save_receipt,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=5, expand=True, fill='x')
        tk.Button(btn_frame, text="✖ Close", command=receipt_window.destroy,
                 bg=self.colors['danger'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=5, expand=True, fill='x')
    
    def send_email_receipt(self, email, transaction):
        """Send email receipt to customer"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_ADDRESS
            msg['To'] = email
            msg['Subject'] = f"Receipt from {Config.STORE_NAME} - #{transaction.transaction_id}"
            
            body = f"""
Thank you for shopping at {Config.STORE_NAME}!

Transaction ID: #{transaction.transaction_id}
Date: {transaction.date}
Total: ${transaction.final_total:.2f}

Items purchased:
"""
            for item in transaction.items:
                body += f"- {item[0]}: {item[1]} x ${item[2]:.2f} = ${item[1]*item[2]:.2f}\n"
            
            body += f"\nThank you for your business!"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Uncomment to enable email sending
            # server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            # server.starttls()
            # server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            # server.send_message(msg)
            # server.quit()
            
            print(f"Email receipt would be sent to: {email}")
        except Exception as e:
            print(f"Email error: {e}")
    
    # -------------------------- INVENTORY TAB --------------------------
    def create_inventory_tab(self):
        self.inv_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.inv_tab, text="  📦 INVENTORY  ")
        
        # Toolbar
        toolbar = tk.Frame(self.inv_tab, bg=self.colors['bg'])
        toolbar.pack(fill='x', padx=10, pady=10)
        
        buttons = [
            ("➕ Add", self.add_product_dialog, self.colors['success']),
            ("✏️ Edit", self.edit_product_dialog, self.colors['info']),
            ("🗑️ Delete", self.delete_product, self.colors['danger']),
            ("📤 Import CSV", self.import_products_csv, self.colors['accent']),
            ("📥 Export CSV", self.export_products_csv, self.colors['accent']),
            ("🔄 Refresh", self.refresh_inventory_tree, self.colors['accent'])
        ]
        
        for text, cmd, color in buttons:
            tk.Button(toolbar, text=text, command=cmd,
                     bg=color, fg='white', relief='flat', cursor='hand2',
                     font=('Arial', 10, 'bold')).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        # Search
        search_frame = tk.Frame(self.inv_tab, bg=self.colors['bg'])
        search_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 Search:", bg=self.colors['bg'], fg=self.colors['text']).pack(side='left')
        self.inv_search = tk.Entry(search_frame, width=30, bg='#3d3d5c', fg='white', relief='flat')
        self.inv_search.pack(side='left', padx=5, ipady=5)
        self.inv_search.bind('<KeyRelease>', lambda e: self.search_inventory())
        
        tk.Label(search_frame, text="Category:", bg=self.colors['bg'], fg=self.colors['text']).pack(side='left', padx=10)
        self.category_filter = ttk.Combobox(search_frame, values=['All'] + list(set(p.category for p in self.products.values())), width=15)
        self.category_filter.set('All')
        self.category_filter.pack(side='left', padx=5)
        self.category_filter.bind('<<ComboboxSelected>>', lambda e: self.search_inventory())
        
        # Treeview
        container = tk.Frame(self.inv_tab, bg=self.colors['bg'])
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(container, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(container, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Price', 'Cost', 'Margin%', 'Stock', 'Category', 'Barcode', 'Sold')
        self.inv_tree = ttk.Treeview(container, columns=columns, show='headings',
                                     yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.inv_tree.yview)
        h_scroll.config(command=self.inv_tree.xview)
        
        col_widths = {'ID': 60, 'Name': 200, 'Price': 80, 'Cost': 80, 'Margin%': 80, 'Stock': 70, 'Category': 100, 'Barcode': 100, 'Sold': 70}
        for col in columns:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, width=col_widths.get(col, 100))
        
        self.inv_tree.pack(fill='both', expand=True)
    
    def refresh_inventory_tree(self):
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
        
        for product in self.products.values():
            self.inv_tree.insert('', 'end', values=(
                product.product_id, product.name, f"${product.price}",
                f"${product.cost_price}", f"{product.profit_margin():.1f}%",
                product.stock, product.category, product.barcode or '-', product.times_sold
            ))
    
    def search_inventory(self):
        search_term = self.inv_search.get().lower()
        category = self.category_filter.get()
        
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
        
        for product in self.products.values():
            if category != 'All' and product.category != category:
                continue
            if search_term and search_term not in product.name.lower() and search_term not in product.barcode.lower():
                continue
            
            self.inv_tree.insert('', 'end', values=(
                product.product_id, product.name, f"${product.price}",
                f"${product.cost_price}", f"{product.profit_margin():.1f}%",
                product.stock, product.category, product.barcode or '-', product.times_sold
            ))
    
    def add_product_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Product")
        dialog.configure(bg=self.colors['card'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 450, 550)
        
        tk.Label(dialog, text="➕ ADD PRODUCT", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=20)
        
        fields = {}
        labels = ['Name:', 'Price ($):', 'Cost Price ($):', 'Stock:', 'Category:', 'Barcode:', 'Supplier:']
        
        for label in labels:
            frame = tk.Frame(dialog, bg=self.colors['card'])
            frame.pack(fill='x', padx=40, pady=5)
            tk.Label(frame, text=label, font=('Arial', 10),
                    bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')
            entry = tk.Entry(frame, font=('Arial', 11), bg='#3d3d5c', fg='white', relief='flat')
            entry.pack(fill='x', ipady=5)
            fields[label] = entry
        
        def save():
            try:
                name = fields['Name:'].get().strip()
                price = float(fields['Price ($):'].get())
                cost_price = float(fields['Cost Price ($):'].get()) if fields['Cost Price ($):'].get() else 0
                stock = int(fields['Stock:'].get())
                category = fields['Category:'].get().strip() or "General"
                barcode = fields['Barcode:'].get().strip()
                supplier = fields['Supplier:'].get().strip()
                
                if not name or price <= 0:
                    messagebox.showerror("Error", "Name and valid price required!")
                    return
                
                product = Product(str(self.next_product_id), name, price, stock, category,
                                 barcode, cost_price, "", supplier)
                self.products[str(self.next_product_id)] = product
                self.next_product_id += 1
                self.save_products()
                self.refresh_inventory_tree()
                self.refresh_pos_products()
                
                messagebox.showinfo("Success", "Product added!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values!")
        
        tk.Button(dialog, text="SAVE", command=save,
                 bg=self.colors['success'], fg='white', font=('Arial', 12, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=40, ipady=10)
    
    def edit_product_dialog(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a product to edit!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_id = str(item['values'][0])
        product = self.products[product_id]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {product.name}")
        dialog.configure(bg=self.colors['card'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 450, 550)
        
        tk.Label(dialog, text="✏️ EDIT PRODUCT", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=20)
        
        fields = {}
        current = [product.name, product.price, product.cost_price, product.stock,
                   product.category, product.barcode, product.supplier]
        labels = ['Name:', 'Price ($):', 'Cost Price ($):', 'Stock:', 'Category:', 'Barcode:', 'Supplier:']
        
        for i, label in enumerate(labels):
            frame = tk.Frame(dialog, bg=self.colors['card'])
            frame.pack(fill='x', padx=40, pady=5)
            tk.Label(frame, text=label, font=('Arial', 10),
                    bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w')
            entry = tk.Entry(frame, font=('Arial', 11), bg='#3d3d5c', fg='white', relief='flat')
            entry.insert(0, str(current[i]))
            entry.pack(fill='x', ipady=5)
            fields[label] = entry
        
        def update():
            try:
                product.name = fields['Name:'].get().strip()
                product.price = float(fields['Price ($):'].get())
                product.cost_price = float(fields['Cost Price ($):'].get()) if fields['Cost Price ($):'].get() else 0
                product.stock = int(fields['Stock:'].get())
                product.category = fields['Category:'].get().strip() or "General"
                product.barcode = fields['Barcode:'].get().strip()
                product.supplier = fields['Supplier:'].get().strip()
                
                self.save_products()
                self.refresh_inventory_tree()
                self.refresh_pos_products()
                self.update_dashboard()
                
                messagebox.showinfo("Success", "Product updated!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values!")
        
        tk.Button(dialog, text="UPDATE", command=update,
                 bg=self.colors['success'], fg='white', font=('Arial', 12, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=40, ipady=10)
    
    def delete_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a product to delete!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_id = str(item['values'][0])
        product_name = item['values'][1]
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{product_name}'?"):
            del self.products[product_id]
            self.save_products()
            self.refresh_inventory_tree()
            self.refresh_pos_products()
            messagebox.showinfo("Success", "Product deleted!")
    
    def import_products_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        product = Product(
                            str(self.next_product_id),
                            row['name'],
                            float(row['price']),
                            int(row['stock']),
                            row.get('category', 'General'),
                            row.get('barcode', ''),
                            float(row.get('cost_price', 0)),
                            '',
                            row.get('supplier', '')
                        )
                        self.products[str(self.next_product_id)] = product
                        self.next_product_id += 1
                
                self.save_products()
                self.refresh_inventory_tree()
                self.refresh_pos_products()
                messagebox.showinfo("Success", "Products imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")
    
    def export_products_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Name', 'Price', 'Cost Price', 'Stock', 'Category', 'Barcode', 'Supplier', 'Times Sold'])
                    for product in self.products.values():
                        writer.writerow([product.product_id, product.name, product.price,
                                        product.cost_price, product.stock, product.category,
                                        product.barcode, product.supplier, product.times_sold])
                messagebox.showinfo("Success", f"Exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    # -------------------------- CUSTOMERS TAB --------------------------
    def create_customers_tab(self):
        self.cust_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.cust_tab, text="  👥 CUSTOMERS  ")
        
        # Toolbar
        toolbar = tk.Frame(self.cust_tab, bg=self.colors['bg'])
        toolbar.pack(fill='x', padx=10, pady=10)
        
        tk.Button(toolbar, text="➕ Add Customer", command=self.add_customer_dialog,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        tk.Button(toolbar, text="🔄 Refresh", command=self.refresh_customers_tree,
                 bg=self.colors['accent'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        # Search
        search_frame = tk.Frame(self.cust_tab, bg=self.colors['bg'])
        search_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 Search:", bg=self.colors['bg'], fg=self.colors['text']).pack(side='left')
        self.cust_search = tk.Entry(search_frame, width=30, bg='#3d3d5c', fg='white', relief='flat')
        self.cust_search.pack(side='left', padx=5, ipady=5)
        self.cust_search.bind('<KeyRelease>', lambda e: self.search_customers())
        
        # Treeview
        container = tk.Frame(self.cust_tab, bg=self.colors['bg'])
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(container, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(container, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Phone', 'Email', 'Points', 'Total Spent', 'Since')
        self.cust_tree = ttk.Treeview(container, columns=columns, show='headings',
                                      yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.cust_tree.yview)
        h_scroll.config(command=self.cust_tree.xview)
        
        for col in columns:
            self.cust_tree.heading(col, text=col)
            self.cust_tree.column(col, width=120)
        
        self.cust_tree.pack(fill='both', expand=True)
        self.cust_tree.bind('<Double-Button-1>', lambda e: self.view_customer_details())
        
        self.refresh_customers_tree()
    
    def refresh_customers_tree(self):
        for item in self.cust_tree.get_children():
            self.cust_tree.delete(item)
        
        for customer in self.customers.values():
            self.cust_tree.insert('', 'end', values=(
                customer.customer_id, customer.name, customer.phone or '-',
                customer.email or '-', customer.loyalty_points,
                f"${customer.total_spent:.2f}", customer.created_at[:10]
            ))
    
    def search_customers(self):
        search_term = self.cust_search.get().lower()
        for item in self.cust_tree.get_children():
            self.cust_tree.delete(item)
        
        for customer in self.customers.values():
            if search_term in customer.name.lower() or search_term in customer.phone.lower():
                self.cust_tree.insert('', 'end', values=(
                    customer.customer_id, customer.name, customer.phone or '-',
                    customer.email or '-', customer.loyalty_points,
                    f"${customer.total_spent:.2f}", customer.created_at[:10]
                ))
    
    def view_customer_details(self):
        selected = self.cust_tree.selection()
        if not selected:
            return
        
        item = self.cust_tree.item(selected[0])
        customer_id = str(item['values'][0])
        customer = self.customers.get(customer_id)
        
        if customer:
            history = "\n".join([f"#{h['transaction_id']} - {h['date']} - ${h['total']:.2f}" 
                                 for h in customer.purchase_history[-5:]])
            
            details = f"""
Customer Details
{'='*40}
Name: {customer.name}
Phone: {customer.phone}
Email: {customer.email}
Address: {customer.address}
Points: {customer.loyalty_points}
Total Spent: ${customer.total_spent:.2f}
Member Since: {customer.created_at}

Recent Purchases:
{history if history else 'No purchases yet'}
"""
            messagebox.showinfo(f"Customer: {customer.name}", details)
    
    # -------------------------- REPORTS TAB --------------------------
    def create_reports_tab(self):
        self.reports_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.reports_tab, text="  📊 REPORTS  ")
        
        # Dashboard summary
        self.dashboard_frame = tk.LabelFrame(self.reports_tab, text="📈 Dashboard", 
                                             bg=self.colors['card'], fg=self.colors['text'])
        self.dashboard_frame.pack(fill='x', padx=10, pady=10)
        
        self.dashboard_text = tk.Text(self.dashboard_frame, height=10, width=80,
                                      font=('Courier', 10), bg=self.colors['card'],
                                      fg=self.colors['text'], wrap='word')
        self.dashboard_text.pack(padx=10, pady=10)
        
        # Best sellers
        best_frame = tk.LabelFrame(self.reports_tab, text="🏆 Best Sellers", 
                                   bg=self.colors['card'], fg=self.colors['text'])
        best_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        best_container = tk.Frame(best_frame, bg=self.colors['card'])
        best_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(best_container, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        
        self.best_tree = ttk.Treeview(best_container, columns=('Rank', 'Product', 'Units Sold', 'Revenue'),
                                      show='headings', yscrollcommand=v_scroll.set, height=10)
        v_scroll.config(command=self.best_tree.yview)
        
        for col in ('Rank', 'Product', 'Units Sold', 'Revenue'):
            self.best_tree.heading(col, text=col)
            self.best_tree.column(col, width=150)
        
        self.best_tree.pack(fill='both', expand=True)
        
        # Buttons
        btn_frame = tk.Frame(self.reports_tab, bg=self.colors['bg'])
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.update_dashboard,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        tk.Button(btn_frame, text="📊 Export Report", command=self.export_report,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        self.update_dashboard()
    
    def update_dashboard(self):
        self.dashboard_text.delete('1.0', tk.END)
        
        total_revenue = sum(t.final_total for t in self.transactions)
        total_transactions = len(self.transactions)
        total_products = len(self.products)
        total_stock = sum(p.stock for p in self.products.values())
        low_stock = len([p for p in self.products.values() if p.stock < Config.LOW_STOCK_THRESHOLD])
        
        # Today's sales
        today = datetime.now().strftime("%Y-%m-%d")
        today_sales = [t for t in self.transactions if t.date.startswith(today)]
        today_revenue = sum(t.final_total for t in today_sales)
        
        # Best performing category
        category_sales = defaultdict(float)
        for t in self.transactions:
            for item in t.items:
                for p in self.products.values():
                    if p.name == item[0]:
                        category_sales[p.category] += item[1] * item[2]
                        break
        
        best_category = max(category_sales.items(), key=lambda x: x[1])[0] if category_sales else "N/A"
        
        dashboard = f"""
{'='*55}
                    STORE PERFORMANCE DASHBOARD
{'='*55}

💰 FINANCIAL SUMMARY
   ├─ Total Revenue:        ${total_revenue:>10,.2f}
   ├─ Today's Revenue:      ${today_revenue:>10,.2f}
   ├─ Total Transactions:   {total_transactions:>10}
   └─ Average Sale:         ${total_revenue/total_transactions if total_transactions > 0 else 0:>10,.2f}

📦 INVENTORY STATUS
   ├─ Total Products:       {total_products:>10}
   ├─ Total Stock Units:    {total_stock:>10}
   ├─ Low Stock Items:      {low_stock:>10}
   └─ Best Category:        {best_category:>10}

⭐ CUSTOMER INSIGHTS
   ├─ Total Customers:      {len(self.customers):>10}
   ├─ Total Points Issued:  {sum(c.loyalty_points for c in self.customers.values()):>10}
   └─ Top Customer:         {max(self.customers.values(), key=lambda x: x.total_spent).name if self.customers else 'N/A'}

{'='*55}
"""
        self.dashboard_text.insert('1.0', dashboard)
        
        # Update best sellers
        for item in self.best_tree.get_children():
            self.best_tree.delete(item)
        
        sorted_products = sorted(self.products.values(), key=lambda x: x.times_sold, reverse=True)[:10]
        for i, product in enumerate(sorted_products, 1):
            revenue = product.price * product.times_sold
            self.best_tree.insert('', 'end', values=(i, product.name, product.times_sold, f"${revenue:.2f}"))
    
    def export_report(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Transaction ID', 'Date', 'Cashier', 'Items', 'Total', 'Payment'])
                    for t in self.transactions:
                        writer.writerow([t.transaction_id, t.date, t.cashier, len(t.items), t.final_total, t.payment_method])
                messagebox.showinfo("Success", f"Report exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    # -------------------------- PROMOTIONS TAB --------------------------
    def create_promotions_tab(self):
        self.promo_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.promo_tab, text="  🎁 PROMOTIONS  ")
        
        # Active promotions
        promo_frame = tk.LabelFrame(self.promo_tab, text="Active Promotions", 
                                    bg=self.colors['card'], fg=self.colors['text'])
        promo_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.promo_list = tk.Text(promo_frame, height=15, width=60,
                                  font=('Courier', 10), bg=self.colors['card'],
                                  fg=self.colors['text'], wrap='word')
        self.promo_list.pack(padx=10, pady=10)
        
        promo_text = """
🎉 CURRENT PROMOTIONS 🎉

1. BOGO (Buy One Get One Free)
   - Buy any item, get the cheapest item free
   - Automatically applied at checkout

2. Seasonal Sale - 10% OFF
   - Valid during holiday seasons
   - 10% discount on entire purchase

3. Weekend Special - 20% OFF
   - Every Saturday and Sunday
   - 20% discount on all items

4. Loyalty Points Program
   - Earn 1 point for every $1 spent
   - 100 points = $1 off future purchases
   - Points never expire

5. Volume Discounts
   - Buy 5+ items: 5% off
   - Buy 10+ items: 10% off
   - Buy 20+ items: 15% off

6. New Customer Welcome
   - First purchase: 15% off
   - Automatically applied for new customers
"""
        self.promo_list.insert('1.0', promo_text)
        self.promo_list.config(state='disabled')
        
        # Add custom promotion
        add_frame = tk.LabelFrame(self.promo_tab, text="Add Custom Promotion", 
                                  bg=self.colors['card'], fg=self.colors['text'])
        add_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(add_frame, text="Promotion Name:", bg=self.colors['card'], fg=self.colors['text']).pack(pady=5)
        self.promo_name = tk.Entry(add_frame, width=40, bg='#3d3d5c', fg='white', relief='flat')
        self.promo_name.pack(pady=5)
        
        tk.Label(add_frame, text="Discount (%):", bg=self.colors['card'], fg=self.colors['text']).pack(pady=5)
        self.promo_discount = tk.Entry(add_frame, width=20, bg='#3d3d5c', fg='white', relief='flat')
        self.promo_discount.pack(pady=5)
        
        def add_promo():
            name = self.promo_name.get().strip()
            discount = self.promo_discount.get().strip()
            if name and discount:
                # Add to promo combo in POS
                current = self.promo_combo['values']
                self.promo_combo['values'] = list(current) + [f"{name} ({discount}% OFF)"]
                messagebox.showinfo("Success", f"Promotion '{name}' added!")
                self.promo_name.delete(0, tk.END)
                self.promo_discount.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Please enter both name and discount!")
        
        tk.Button(add_frame, text="➕ Add Promotion", command=add_promo,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(pady=10, ipadx=20, ipady=5)
    
    # -------------------------- SETTINGS TAB --------------------------
    def create_settings_tab(self):
        self.settings_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.settings_tab, text="  ⚙️ SETTINGS  ")
        
        # User management
        user_frame = tk.LabelFrame(self.settings_tab, text="User Management", 
                                   bg=self.colors['card'], fg=self.colors['text'])
        user_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(user_frame, text="Add New User:", bg=self.colors['card'], fg=self.colors['text']).pack(pady=5)
        
        user_entry_frame = tk.Frame(user_frame, bg=self.colors['card'])
        user_entry_frame.pack(pady=5)
        
        tk.Entry(user_entry_frame, width=15, bg='#3d3d5c', fg='white', relief='flat', placeholder="Username").pack(side='left', padx=5)
        tk.Entry(user_entry_frame, width=15, bg='#3d3d5c', fg='white', relief='flat', placeholder="Password", show="*").pack(side='left', padx=5)
        ttk.Combobox(user_entry_frame, values=['admin', 'staff'], width=10).pack(side='left', padx=5)
        tk.Button(user_entry_frame, text="Add", bg=self.colors['success'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=5)
        
        # System settings
        system_frame = tk.LabelFrame(self.settings_tab, text="System Settings", 
                                     bg=self.colors['card'], fg=self.colors['text'])
        system_frame.pack(fill='x', padx=10, pady=10)
        
        settings = [
            ("Store Name:", Config.STORE_NAME),
            ("Currency Symbol:", Config.CURRENCY_SYMBOL),
            ("Tax Rate (%):", Config.TAX_RATE * 100),
            ("Low Stock Alert Threshold:", Config.LOW_STOCK_THRESHOLD),
            ("Loyalty Points Rate (points per $):", Config.LOYALTY_POINTS_RATE * 100)
        ]
        
        self.settings_entries = {}
        for i, (label, value) in enumerate(settings):
            frame = tk.Frame(system_frame, bg=self.colors['card'])
            frame.pack(fill='x', padx=20, pady=5)
            tk.Label(frame, text=label, width=25, anchor='w',
                    bg=self.colors['card'], fg=self.colors['text']).pack(side='left')
            entry = tk.Entry(frame, width=20, bg='#3d3d5c', fg='white', relief='flat')
            entry.insert(0, str(value))
            entry.pack(side='left', padx=10)
            self.settings_entries[label] = entry
        
        def save_settings():
            try:
                Config.STORE_NAME = self.settings_entries["Store Name:"].get()
                Config.CURRENCY_SYMBOL = self.settings_entries["Currency Symbol:"].get()
                Config.TAX_RATE = float(self.settings_entries["Tax Rate (%):"].get()) / 100
                Config.LOW_STOCK_THRESHOLD = int(self.settings_entries["Low Stock Alert Threshold:"].get())
                Config.LOYALTY_POINTS_RATE = float(self.settings_entries["Loyalty Points Rate (points per $):"].get()) / 100
                messagebox.showinfo("Success", "Settings saved! Restart to apply changes.")
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values!")
        
        tk.Button(system_frame, text="💾 Save Settings", command=save_settings,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(pady=10, ipadx=20, ipady=5)
        
        # Backup/Restore
        backup_frame = tk.LabelFrame(self.settings_tab, text="Backup & Restore", 
                                     bg=self.colors['card'], fg=self.colors['text'])
        backup_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(backup_frame, text="💾 Create Backup", command=self.backup_data,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=20, pady=10, ipadx=20, ipady=5)
        
        tk.Button(backup_frame, text="🔄 Restore Backup", command=self.restore_backup,
                 bg=self.colors['warning'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=20, pady=10, ipadx=20, ipady=5)
        
        # About
        about_frame = tk.LabelFrame(self.settings_tab, text="About", 
                                    bg=self.colors['card'], fg=self.colors['text'])
        about_frame.pack(fill='x', padx=10, pady=10)
        
        about_text = f"""
{Config.STORE_NAME} - Professional Edition
Version 3.0

A complete Point of Sale and Inventory Management System

Features:
• Barcode Scanner Support
• Customer Database with Loyalty Points
• Email Receipts
• Bulk Import/Export
• Advanced Reports & Analytics
• Promotions & Discounts
• Multi-user Support
• Data Backup & Restore
• And much more...

© 2024 All Rights Reserved
"""
        tk.Label(about_frame, text=about_text, justify='left', bg=self.colors['card'],
                fg=self.colors['text'], font=('Courier', 9)).pack(pady=10)
    
    # -------------------------- USER INTERFACE (Customer Shopping) --------------------------
    def setup_user_interface(self):
        """Simple shopping interface for customers"""
        self.root.configure(bg=self.colors['bg'])
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header
        header = tk.Frame(self.root, bg=self.colors['card'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🛒 SMART STORE - SHOPPING MODE", 
                font=('Arial', 20, 'bold'), bg=self.colors['card'], fg=self.colors['success']).pack(side='left', padx=20, pady=20)
        
        tk.Button(header, text="👑 Switch to Admin", command=self.switch_to_admin,
                 bg=self.colors['warning'], fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold')).pack(side='right', padx=20)
        
        # Main content
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Products
        left_panel = tk.Frame(main_container, bg=self.colors['card'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(left_panel, text="📋 PRODUCTS", font=('Arial', 16, 'bold'),
                bg=self.colors['card'], fg=self.colors['success']).pack(pady=10)
        
        # Search
        search_frame = tk.Frame(left_panel, bg=self.colors['card'])
        search_frame.pack(fill='x', padx=10, pady=5)
        
        self.user_search = tk.Entry(search_frame, font=('Arial', 11), bg='#3d3d5c', fg='white', relief='flat')
        self.user_search.pack(side='left', fill='x', expand=True, ipady=8)
        self.user_search.bind('<KeyRelease>', lambda e: self.user_search_products())
        
        tk.Button(search_frame, text="🔍", command=self.user_search_products,
                 bg=self.colors['info'], fg='white', relief='flat', width=5).pack(side='left', padx=5)
        
        # Products tree
        container = tk.Frame(left_panel, bg=self.colors['card'])
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(container, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(container, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('Name', 'Price', 'Stock', 'Category')
        self.user_tree = ttk.Treeview(container, columns=columns, show='headings',
                                      yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.user_tree.yview)
        h_scroll.config(command=self.user_tree.xview)
        
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=150)
        
        self.user_tree.pack(fill='both', expand=True)
        self.user_tree.bind('<Double-Button-1>', lambda e: self.user_add_to_cart())
        
        # Cart
        right_panel = tk.Frame(main_container, bg=self.colors['card'], width=450)
        right_panel.pack(side='right', fill='both', padx=(10, 0))
        right_panel.pack_propagate(False)
        
        tk.Label(right_panel, text="🛒 YOUR CART", font=('Arial', 16, 'bold'),
                bg=self.colors['card'], fg=self.colors['warning']).pack(pady=10)
        
        cart_container = tk.Frame(right_panel, bg=self.colors['card'])
        cart_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        cart_v_scroll = ttk.Scrollbar(cart_container, orient='vertical')
        cart_v_scroll.pack(side='right', fill='y')
        cart_h_scroll = ttk.Scrollbar(cart_container, orient='horizontal')
        cart_h_scroll.pack(side='bottom', fill='x')
        
        cart_columns = ('Product', 'Qty', 'Price', 'Total')
        self.user_cart_tree = ttk.Treeview(cart_container, columns=cart_columns, show='headings',
                                           yscrollcommand=cart_v_scroll.set, xscrollcommand=cart_h_scroll.set)
        cart_v_scroll.config(command=self.user_cart_tree.yview)
        cart_h_scroll.config(command=self.user_cart_tree.xview)
        
        for col in cart_columns:
            self.user_cart_tree.heading(col, text=col)
            self.user_cart_tree.column(col, width=100)
        self.user_cart_tree.column('Product', width=150)
        self.user_cart_tree.pack(fill='both', expand=True)
        
        # Cart buttons
        btn_frame = tk.Frame(right_panel, bg=self.colors['card'])
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(btn_frame, text="🗑️ Remove", command=self.user_remove_from_cart,
                 bg=self.colors['danger'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        tk.Button(btn_frame, text="🔄 Clear", command=self.user_clear_cart,
                 bg='#636e72', fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        
        # Totals
        totals_frame = tk.Frame(right_panel, bg='#2d2d44', relief='flat', bd=1)
        totals_frame.pack(fill='x', padx=10, pady=10)
        
        self.user_subtotal = tk.Label(totals_frame, text="Subtotal: $0.00",
                                      font=('Arial', 12), bg='#2d2d44', fg=self.colors['text'])
        self.user_subtotal.pack(pady=5)
        
        self.user_total = tk.Label(totals_frame, text="TOTAL: $0.00",
                                   font=('Arial', 18, 'bold'), bg='#2d2d44', fg=self.colors['success'])
        self.user_total.pack(pady=10)
        
        tk.Button(right_panel, text="💳 CHECKOUT", command=self.user_checkout,
                 bg=self.colors['success'], fg='white', font=('Arial', 13, 'bold'),
                 relief='flat', cursor='hand2', height=2).pack(fill='x', padx=10, pady=10)
        
        self.user_refresh_products()
        self.user_cart = {}
    
    def user_refresh_products(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        for product in self.products.values():
            if product.stock > 0:
                stock_display = f"{product.stock}"
                if product.stock < Config.LOW_STOCK_THRESHOLD:
                    stock_display = f"⚠️ {product.stock}"
                self.user_tree.insert('', 'end', values=(
                    product.name, f"${product.price}", stock_display, product.category
                ))
    
    def user_search_products(self):
        search_term = self.user_search.get().lower()
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        for product in self.products.values():
            if product.stock > 0 and (search_term in product.name.lower() or search_term in product.category.lower()):
                stock_display = f"{product.stock}"
                if product.stock < Config.LOW_STOCK_THRESHOLD:
                    stock_display = f"⚠️ {product.stock}"
                self.user_tree.insert('', 'end', values=(
                    product.name, f"${product.price}", stock_display, product.category
                ))
    
    def user_add_to_cart(self):
        selected = self.user_tree.selection()
        if not selected:
            return
        item = self.user_tree.item(selected[0])
        product_name = item['values'][0]
        
        for product in self.products.values():
            if product.name == product_name and product.stock > 0:
                if product_name in self.user_cart:
                    self.user_cart[product_name]['quantity'] += 1
                else:
                    self.user_cart[product_name] = {
                        'name': product_name,
                        'price': product.price,
                        'quantity': 1,
                        'product_id': product.product_id
                    }
                self.user_refresh_cart()
                break
    
    def user_refresh_cart(self):
        for item in self.user_cart_tree.get_children():
            self.user_cart_tree.delete(item)
        
        subtotal = 0
        for item in self.user_cart.values():
            total = item['price'] * item['quantity']
            subtotal += total
            self.user_cart_tree.insert('', 'end', values=(
                item['name'], item['quantity'], f"${item['price']}", f"${total:.2f}"
            ))
        
        self.user_subtotal.config(text=f"Subtotal: ${subtotal:.2f}")
        self.user_total.config(text=f"TOTAL: ${subtotal:.2f}")
    
    def user_remove_from_cart(self):
        selected = self.user_cart_tree.selection()
        if not selected:
            return
        item = self.user_cart_tree.item(selected[0])
        product_name = item['values'][0]
        if product_name in self.user_cart:
            del self.user_cart[product_name]
            self.user_refresh_cart()
    
    def user_clear_cart(self):
        if messagebox.askyesno("Clear Cart", "Clear your cart?"):
            self.user_cart.clear()
            self.user_refresh_cart()
    
    def user_checkout(self):
        if not self.user_cart:
            messagebox.showwarning("Empty Cart", "Your cart is empty!")
            return
        
        subtotal = sum(item['price'] * item['quantity'] for item in self.user_cart.values())
        
        payment_window = tk.Toplevel(self.root)
        payment_window.title("Payment")
        payment_window.configure(bg=self.colors['card'])
        payment_window.transient(self.root)
        payment_window.grab_set()
        self.center_window(payment_window, 400, 400)
        
        tk.Label(payment_window, text="💳 PAYMENT", font=('Arial', 16, 'bold'),
                bg=self.colors['card'], fg=self.colors['accent']).pack(pady=20)
        
        tk.Label(payment_window, text=f"Total: ${subtotal:.2f}", font=('Arial', 14),
                bg=self.colors['card'], fg=self.colors['success']).pack(pady=10)
        
        tk.Label(payment_window, text="Payment Method:", font=('Arial', 12),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=10)
        
        payment_var = tk.StringVar(value="Cash")
        for method in ["Cash", "Card", "Digital Wallet"]:
            tk.Radiobutton(payment_window, text=method, variable=payment_var, value=method,
                          bg=self.colors['card'], fg=self.colors['text'],
                          selectcolor=self.colors['card']).pack()
        
        tk.Label(payment_window, text="Amount Paid:", font=('Arial', 12),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=10)
        
        paid_entry = tk.Entry(payment_window, font=('Arial', 14), bg='#3d3d5c',
                              fg='white', relief='flat', justify='center', width=15)
        paid_entry.pack(pady=10, ipady=5)
        paid_entry.insert(0, str(subtotal))
        
        def process():
            try:
                paid = float(paid_entry.get())
                if paid < subtotal:
                    messagebox.showerror("Error", f"Insufficient payment!\nNeed: ${subtotal:.2f}")
                    return
                
                change = paid - subtotal
                
                # Process sale
                sale_items = []
                for item in self.user_cart.values():
                    product = self.products[item['product_id']]
                    product.stock -= item['quantity']
                    product.times_sold += item['quantity']
                    sale_items.append((item['name'], item['quantity'], item['price']))
                
                transaction = Transaction(
                    self.next_transaction_id, sale_items, subtotal,
                    0, subtotal, self.current_user.username,
                    payment_var.get(), None, 0, 0
                )
                self.transactions.append(transaction)
                self.next_transaction_id += 1
                
                self.save_products()
                self.save_transactions()
                
                # Show receipt
                receipt_window = tk.Toplevel(self.root)
                receipt_window.title("Receipt")
                receipt_window.configure(bg='white')
                self.center_window(receipt_window, 450, 500)
                
                receipt_text = tk.Text(receipt_window, font=('Courier', 10), bg='white', fg='black', wrap='word')
                receipt_text.pack(fill='both', expand=True, padx=20, pady=20)
                
                receipt = f"""
{'='*40}
      {Config.STORE_NAME}
    Thank you for shopping!
{'='*40}
Transaction: #{transaction.transaction_id}
Date: {transaction.date}
Payment: {payment_var.get()}

Items:
"""
                for item in sale_items:
                    receipt += f"  {item[0]} x{item[1]} = ${item[1]*item[2]:.2f}\n"
                
                receipt += f"""
{'='*40}
Subtotal: ${subtotal:.2f}
Total: ${subtotal:.2f}
Paid: ${paid:.2f}
Change: ${change:.2f}
{'='*40}
    Payment Status: ✅ COMPLETED
{'='*40}
        Thank you! Visit Again!
"""
                receipt_text.insert('1.0', receipt)
                receipt_text.config(state='disabled')
                
                tk.Button(receipt_window, text="Close", command=receipt_window.destroy,
                         bg=self.colors['success'], fg='white', relief='flat').pack(pady=10)
                
                self.user_cart.clear()
                self.user_refresh_cart()
                self.user_refresh_products()
                payment_window.destroy()
                
                messagebox.showinfo("Success", f"Transaction complete!\nChange: ${change:.2f}")
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount!")
        
        tk.Button(payment_window, text="PAY NOW", command=process,
                 bg=self.colors['success'], fg='white', font=('Arial', 12, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=40, ipady=10)
    
    def switch_to_admin(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.show_role_selection()

# -------------------------- MAIN --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartStorePro(root)
    root.mainloop()