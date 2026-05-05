"""
SMART STORE MANAGEMENT SYSTEM - ENTERPRISE EDITION
==================================================
Professional POS & Inventory System with:
- Modern Professional GUI (Clean, Minimal, Enterprise-ready)
- Return/Refund Product Feature
- Three Roles: Admin, Staff, Cashier
- Complete Inventory Management
- Customer Loyalty Program
- Advanced Reporting
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
from datetime import datetime, timedelta
import hashlib
import csv
from collections import defaultdict
import shutil

# -------------------------- CONFIGURATION --------------------------
class Config:
    APP_NAME = "SMART STORE ENTERPRISE"
    VERSION = "3.0"
    
    # File paths
    DATA_DIR = "store_data"
    PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
    CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
    TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
    RETURNS_FILE = os.path.join(DATA_DIR, "returns.json")
    BACKUP_DIR = os.path.join(DATA_DIR, "backups")
    
    # Business settings
    TAX_RATE = 0.00
    CURRENCY = "$"
    LOW_STOCK_THRESHOLD = 5
    LOYALTY_POINTS_RATE = 0.01
    RETURN_DAYS_LIMIT = 7
    
    @staticmethod
    def init_dirs():
        for dir_path in [Config.DATA_DIR, Config.BACKUP_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

Config.init_dirs()

# -------------------------- CLASSES --------------------------
class User:
    def __init__(self, username, password, role, full_name="", email=""):
        self.username = username
        self.password = hashlib.sha256(password.encode()).hexdigest()
        self.role = role  # admin, staff, cashier
        self.full_name = full_name
        self.email = email
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Product:
    def __init__(self, product_id, name, price, stock, category="General", 
                 barcode="", cost_price=0, supplier=""):
        self.product_id = str(product_id)
        self.name = name
        self.price = price
        self.cost_price = cost_price
        self.stock = stock
        self.category = category
        self.barcode = barcode
        self.supplier = supplier
        self.times_sold = 0
        
    def to_dict(self):
        return {
            "product_id": self.product_id, "name": self.name, "price": self.price,
            "cost_price": self.cost_price, "stock": self.stock, "category": self.category,
            "barcode": self.barcode, "supplier": self.supplier, "times_sold": self.times_sold
        }

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
        self.returned = False
        self.return_date = None

class ReturnTransaction:
    def __init__(self, return_id, original_transaction_id, items, refund_amount, 
                 reason, cashier, customer_id=None):
        self.return_id = return_id
        self.original_transaction_id = original_transaction_id
        self.items = items
        self.refund_amount = refund_amount
        self.reason = reason
        self.cashier = cashier
        self.customer_id = customer_id
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# -------------------------- MAIN APPLICATION --------------------------
class SmartStoreEnterprise:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{Config.APP_NAME} v{Config.VERSION}")
        self.root.geometry("1400x850")
        self.root.configure(bg='#f5f5f5')
        
        # Professional color scheme - Minimal Enterprise
        self.colors = {
            'bg': '#f5f5f5',
            'card': '#ffffff',
            'border': '#e0e0e0',
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#3498db',
            'text': '#2c3e50',
            'text_light': '#7f8c8d',
            'header_bg': '#2c3e50'
        }
        
        # Data storage
        self.products = {}
        self.customers = {}
        self.transactions = []
        self.returns = []
        self.users = {}
        self.cart = {}
        self.current_user = None
        self.current_customer = None
        self.next_product_id = 1
        self.next_customer_id = 1
        self.next_transaction_id = 1
        self.next_return_id = 1
        
        # Load data
        self.load_all_data()
        
        # Show login
        self.show_login()
    
    def load_all_data(self):
        """Load all data from JSON files"""
        try:
            if os.path.exists(Config.PRODUCTS_FILE):
                with open(Config.PRODUCTS_FILE, 'r') as f:
                    data = json.load(f)
                    for pid, pdata in data.items():
                        self.products[pid] = Product(
                            pdata["product_id"], pdata["name"], pdata["price"],
                            pdata["stock"], pdata["category"], pdata.get("barcode", ""),
                            pdata.get("cost_price", 0), pdata.get("supplier", "")
                        )
                        self.products[pid].times_sold = pdata.get("times_sold", 0)
                    if self.products:
                        self.next_product_id = max(int(p) for p in self.products.keys()) + 1
        except: pass
        
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
                        self.customers[cid] = customer
                    if self.customers:
                        self.next_customer_id = max(int(c) for c in self.customers.keys()) + 1
        except: pass
        
        try:
            if os.path.exists(Config.TRANSACTIONS_FILE):
                with open(Config.TRANSACTIONS_FILE, 'r') as f:
                    trans_data = json.load(f)
                    for t in trans_data:
                        transaction = Transaction(
                            t["transaction_id"], t["items"], t["total"],
                            t["discount"], t["final_total"], t.get("cashier", ""),
                            t.get("payment_method", "Cash"), t.get("customer_id"),
                            t.get("points_used", 0), t.get("points_earned", 0)
                        )
                        transaction.date = t["date"]
                        transaction.status = t.get("status", "Completed")
                        transaction.returned = t.get("returned", False)
                        self.transactions.append(transaction)
                    if self.transactions:
                        self.next_transaction_id = max(t.transaction_id for t in self.transactions) + 1
        except: pass
        
        try:
            if os.path.exists(Config.RETURNS_FILE):
                with open(Config.RETURNS_FILE, 'r') as f:
                    returns_data = json.load(f)
                    for r in returns_data:
                        ret = ReturnTransaction(
                            r["return_id"], r["original_transaction_id"], r["items"],
                            r["refund_amount"], r["reason"], r["cashier"], r.get("customer_id")
                        )
                        ret.date = r["date"]
                        self.returns.append(ret)
                    if self.returns:
                        self.next_return_id = max(r.return_id for r in self.returns) + 1
        except: pass
        
        try:
            if os.path.exists(Config.USERS_FILE):
                with open(Config.USERS_FILE, 'r') as f:
                    users_data = json.load(f)
                    for username, user_data in users_data.items():
                        user = User(username, "", user_data["role"],
                                   user_data.get("full_name", ""), user_data.get("email", ""))
                        user.password = user_data["password"]
                        self.users[username] = user
        except: pass
        
        # Create default users if none exist
        if not self.users:
            self.users = {
                "admin": User("admin", "admin123", "admin", "System Administrator", "admin@store.com"),
                "staff1": User("staff1", "staff123", "staff", "John Staff", "staff@store.com"),
                "cashier1": User("cashier1", "cash123", "cashier", "Mary Cashier", "cashier@store.com")
            }
            self.save_users()
    
    def save_all_data(self):
        self.save_products()
        self.save_customers()
        self.save_transactions()
        self.save_users()
        self.save_returns()
    
    def save_products(self):
        try:
            with open(Config.PRODUCTS_FILE, 'w') as f:
                json.dump({pid: p.to_dict() for pid, p in self.products.items()}, f, indent=2)
        except: pass
    
    def save_customers(self):
        try:
            data = {cid: {"customer_id": c.customer_id, "name": c.name, "phone": c.phone,
                         "email": c.email, "address": c.address, "loyalty_points": c.loyalty_points,
                         "total_spent": c.total_spent, "purchase_history": c.purchase_history,
                         "created_at": c.created_at} for cid, c in self.customers.items()}
            with open(Config.CUSTOMERS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except: pass
    
    def save_transactions(self):
        try:
            data = [{"transaction_id": t.transaction_id, "items": t.items, "total": t.total,
                    "discount": t.discount, "final_total": t.final_total, "cashier": t.cashier,
                    "payment_method": t.payment_method, "customer_id": t.customer_id,
                    "points_used": t.points_used, "points_earned": t.points_earned,
                    "status": t.status, "date": t.date, "returned": t.returned} 
                   for t in self.transactions]
            with open(Config.TRANSACTIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except: pass
    
    def save_users(self):
        try:
            data = {u: {"password": user.password, "role": user.role,
                       "full_name": user.full_name, "email": user.email}
                   for u, user in self.users.items()}
            with open(Config.USERS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except: pass
    
    def save_returns(self):
        try:
            data = [{"return_id": r.return_id, "original_transaction_id": r.original_transaction_id,
                    "items": r.items, "refund_amount": r.refund_amount, "reason": r.reason,
                    "cashier": r.cashier, "customer_id": r.customer_id, "date": r.date}
                   for r in self.returns]
            with open(Config.RETURNS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except: pass
    
    def center_window(self, window, width, height):
        window.update_idletasks()
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    # -------------------------- LOGIN SYSTEM --------------------------
    def show_login(self):
        login_window = tk.Toplevel(self.root)
        login_window.title(f"{Config.APP_NAME} - Login")
        login_window.configure(bg=self.colors['bg'])
        login_window.transient(self.root)
        login_window.grab_set()
        self.center_window(login_window, 450, 500)
        
        # Main card
        card = tk.Frame(login_window, bg=self.colors['card'], relief='flat', bd=1)
        card.pack(expand=True, fill='both', padx=30, pady=30)
        
        # Header
        tk.Label(card, text=Config.APP_NAME, font=('Segoe UI', 20, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=(30, 10))
        tk.Label(card, text="Enterprise Management System", font=('Segoe UI', 11),
                bg=self.colors['card'], fg=self.colors['text_light']).pack(pady=(0, 30))
        
        # Username
        tk.Label(card, text="Username", font=('Segoe UI', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w', padx=30)
        username_entry = tk.Entry(card, font=('Segoe UI', 11), bg='#f8f9fa',
                                  fg=self.colors['text'], relief='solid', bd=1)
        username_entry.pack(fill='x', padx=30, pady=(5, 15), ipady=8)
        
        # Password
        tk.Label(card, text="Password", font=('Segoe UI', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w', padx=30)
        password_entry = tk.Entry(card, font=('Segoe UI', 11), bg='#f8f9fa',
                                  fg=self.colors['text'], show="*", relief='solid', bd=1)
        password_entry.pack(fill='x', padx=30, pady=(5, 20), ipady=8)
        
        def do_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if username in self.users:
                hashed = hashlib.sha256(password.encode()).hexdigest()
                if self.users[username].password == hashed:
                    self.current_user = self.users[username]
                    login_window.destroy()
                    self.setup_dashboard()
                    return
            
            messagebox.showerror("Login Failed", "Invalid username or password!\n\nDemo Accounts:\nadmin / admin123\nstaff1 / staff123\ncashier1 / cash123")
        
        tk.Button(card, text="LOGIN", command=do_login,
                 bg=self.colors['primary'], fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2').pack(fill='x', padx=30, pady=10, ipady=10)
        
        # Role info
        info_frame = tk.Frame(card, bg=self.colors['card'])
        info_frame.pack(pady=20)
        
        roles = [
            ("👑 Admin", "Full System Access", self.colors['danger']),
            ("👔 Staff", "Inventory + POS", self.colors['info']),
            ("💰 Cashier", "POS Only", self.colors['success'])
        ]
        
        for role, desc, color in roles:
            frame = tk.Frame(info_frame, bg=self.colors['card'])
            frame.pack(side='left', padx=15)
            tk.Label(frame, text=role, font=('Segoe UI', 10, 'bold'),
                    bg=self.colors['card'], fg=color).pack()
            tk.Label(frame, text=desc, font=('Segoe UI', 8),
                    bg=self.colors['card'], fg=self.colors['text_light']).pack()
        
        password_entry.bind('<Return>', lambda e: do_login())
    
    # -------------------------- MAIN DASHBOARD --------------------------
    def setup_dashboard(self):
        self.root.configure(bg=self.colors['bg'])
        
        # Clear existing
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header
        header = tk.Frame(self.root, bg=self.colors['header_bg'], height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Logo
        tk.Label(header, text=Config.APP_NAME, font=('Segoe UI', 16, 'bold'),
                bg=self.colors['header_bg'], fg='white').pack(side='left', padx=30)
        
        tk.Label(header, text=f"v{Config.VERSION}", font=('Segoe UI', 10),
                bg=self.colors['header_bg'], fg='#95a5a6').pack(side='left')
        
        # User info
        user_frame = tk.Frame(header, bg=self.colors['header_bg'])
        user_frame.pack(side='right', padx=30)
        
        role_colors = {'admin': '#e74c3c', 'staff': '#3498db', 'cashier': '#27ae60'}
        role_color = role_colors.get(self.current_user.role, '#95a5a6')
        
        tk.Label(user_frame, text=f"{self.current_user.full_name}", font=('Segoe UI', 11),
                bg=self.colors['header_bg'], fg='white').pack(side='left')
        
        tk.Label(user_frame, text=f" [{self.current_user.role.upper()}]", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['header_bg'], fg=role_color).pack(side='left', padx=(5, 15))
        
        tk.Button(user_frame, text="LOGOUT", command=self.logout,
                 bg='#e74c3c', fg='white', font=('Segoe UI', 9),
                 relief='flat', cursor='hand2').pack(side='left')
        
        # Navigation Bar
        nav = tk.Frame(self.root, bg=self.colors['card'], height=50)
        nav.pack(fill='x')
        nav.pack_propagate(False)
        
        # Navigation buttons based on role
        nav_buttons = [("🛒 POS", self.show_pos)]
        
        if self.current_user.role in ['admin', 'staff']:
            nav_buttons.append(("📦 Inventory", self.show_inventory))
            nav_buttons.append(("👥 Customers", self.show_customers))
        
        if self.current_user.role == 'admin':
            nav_buttons.append(("📊 Reports", self.show_reports))
            nav_buttons.append(("🔄 Returns", self.show_returns))
            nav_buttons.append(("⚙️ Settings", self.show_settings))
        
        for text, command in nav_buttons:
            tk.Button(nav, text=text, command=command,
                     bg=self.colors['card'], fg=self.colors['primary'],
                     font=('Segoe UI', 10), relief='flat', cursor='hand2',
                     padx=20).pack(side='left', padx=5, pady=10)
        
        # Main content area
        self.main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Show default view
        self.show_pos()
    
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            for widget in self.root.winfo_children():
                widget.destroy()
            self.show_login()
    
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    # -------------------------- POS SYSTEM --------------------------
    def show_pos(self):
        self.clear_main_frame()
        self.cart = {}
        self.current_customer = None
        
        # Two-column layout
        left_panel = tk.Frame(self.main_frame, bg=self.colors['card'], relief='solid', bd=1)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_panel = tk.Frame(self.main_frame, bg=self.colors['card'], relief='solid', bd=1, width=450)
        right_panel.pack(side='right', fill='both', padx=(10, 0))
        right_panel.pack_propagate(False)
        
        # ========== LEFT PANEL - Products ==========
        tk.Label(left_panel, text="PRODUCT CATALOG", font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=15)
        
        # Search
        search_frame = tk.Frame(left_panel, bg=self.colors['card'])
        search_frame.pack(fill='x', padx=15, pady=5)
        
        self.pos_search = tk.Entry(search_frame, font=('Segoe UI', 10),
                                   bg='#f8f9fa', relief='solid', bd=1)
        self.pos_search.pack(side='left', fill='x', expand=True, ipady=6)
        self.pos_search.bind('<KeyRelease>', lambda e: self.search_products())
        
        tk.Button(search_frame, text="🔍", command=self.search_products,
                 bg=self.colors['info'], fg='white', relief='flat', width=5).pack(side='left', padx=5)
        
        # Products tree
        tree_frame = tk.Frame(left_panel, bg=self.colors['card'])
        tree_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Price', 'Stock', 'Category')
        self.pos_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                      yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.pos_tree.yview)
        h_scroll.config(command=self.pos_tree.xview)
        
        for col in columns:
            self.pos_tree.heading(col, text=col)
            self.pos_tree.column(col, width=120)
        self.pos_tree.column('Name', width=200)
        self.pos_tree.pack(fill='both', expand=True)
        self.pos_tree.bind('<Double-Button-1>', lambda e: self.add_to_cart())
        
        # ========== RIGHT PANEL - Cart ==========
        tk.Label(right_panel, text="SHOPPING CART", font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=15)
        
        # Customer selection
        cust_frame = tk.Frame(right_panel, bg=self.colors['card'])
        cust_frame.pack(fill='x', padx=15, pady=5)
        
        tk.Label(cust_frame, text="Customer:", font=('Segoe UI', 10),
                bg=self.colors['card']).pack(side='left')
        
        self.customer_var = tk.StringVar(value="Walk-in Customer")
        self.customer_combo = ttk.Combobox(cust_frame, textvariable=self.customer_var,
                                           values=["Walk-in Customer"] + list(self.customers.keys()),
                                           width=25)
        self.customer_combo.pack(side='left', padx=5)
        
        tk.Button(cust_frame, text="+ New", command=self.add_customer_dialog,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2)
        
        # Cart tree
        cart_frame = tk.Frame(right_panel, bg=self.colors['card'])
        cart_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        cart_v_scroll = ttk.Scrollbar(cart_frame, orient='vertical')
        cart_v_scroll.pack(side='right', fill='y')
        cart_h_scroll = ttk.Scrollbar(cart_frame, orient='horizontal')
        cart_h_scroll.pack(side='bottom', fill='x')
        
        cart_columns = ('Product', 'Qty', 'Price', 'Total')
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show='headings',
                                       yscrollcommand=cart_v_scroll.set, xscrollcommand=cart_h_scroll.set)
        cart_v_scroll.config(command=self.cart_tree.yview)
        cart_h_scroll.config(command=self.cart_tree.xview)
        
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=100)
        self.cart_tree.column('Product', width=150)
        self.cart_tree.pack(fill='both', expand=True)
        
        # Cart buttons
        btn_frame = tk.Frame(right_panel, bg=self.colors['card'])
        btn_frame.pack(fill='x', padx=15, pady=5)
        
        tk.Button(btn_frame, text="Remove", command=self.remove_from_cart,
                 bg=self.colors['danger'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        tk.Button(btn_frame, text="Clear", command=self.clear_cart,
                 bg='#95a5a6', fg='white', relief='flat', cursor='hand2').pack(side='left', padx=2, expand=True, fill='x')
        
        # Discount
        disc_frame = tk.Frame(right_panel, bg=self.colors['card'])
        disc_frame.pack(fill='x', padx=15, pady=5)
        
        tk.Label(disc_frame, text="Discount (%):", font=('Segoe UI', 10),
                bg=self.colors['card']).pack(side='left')
        
        self.discount_entry = tk.Entry(disc_frame, width=10, font=('Segoe UI', 10),
                                       bg='#f8f9fa', relief='solid', bd=1)
        self.discount_entry.pack(side='left', padx=5)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind('<KeyRelease>', lambda e: self.update_totals())
        
        # Totals
        totals_frame = tk.Frame(right_panel, bg='#f8f9fa', relief='solid', bd=1)
        totals_frame.pack(fill='x', padx=15, pady=10)
        
        self.subtotal_label = tk.Label(totals_frame, text="Subtotal: $0.00",
                                       font=('Segoe UI', 11), bg='#f8f9fa', fg=self.colors['text'])
        self.subtotal_label.pack(pady=5)
        
        self.discount_label = tk.Label(totals_frame, text="Discount: $0.00",
                                       font=('Segoe UI', 11), bg='#f8f9fa', fg=self.colors['text'])
        self.discount_label.pack(pady=5)
        
        self.total_label = tk.Label(totals_frame, text="TOTAL: $0.00",
                                    font=('Segoe UI', 16, 'bold'), bg='#f8f9fa', fg=self.colors['success'])
        self.total_label.pack(pady=10)
        
        # Checkout button
        tk.Button(right_panel, text="CHECKOUT", command=self.checkout,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 12, 'bold'),
                 relief='flat', cursor='hand2', height=2).pack(fill='x', padx=15, pady=15)
        
        self.refresh_product_list()
    
    def refresh_product_list(self):
        for item in self.pos_tree.get_children():
            self.pos_tree.delete(item)
        for product in self.products.values():
            if product.stock > 0:
                self.pos_tree.insert('', 'end', values=(
                    product.product_id, product.name, f"{Config.CURRENCY}{product.price}",
                    product.stock, product.category
                ))
    
    def search_products(self):
        search_term = self.pos_search.get().lower()
        for item in self.pos_tree.get_children():
            self.pos_tree.delete(item)
        for product in self.products.values():
            if product.stock > 0 and (search_term in product.name.lower() or search_term in product.category.lower()):
                self.pos_tree.insert('', 'end', values=(
                    product.product_id, product.name, f"{Config.CURRENCY}{product.price}",
                    product.stock, product.category
                ))
    
    def add_to_cart(self):
        selected = self.pos_tree.selection()
        if not selected:
            return
        item = self.pos_tree.item(selected[0])
        product_id = str(item['values'][0])
        product = self.products.get(product_id)
        
        if product and product.stock > 0:
            if product_id in self.cart:
                if self.cart[product_id]['quantity'] + 1 <= product.stock:
                    self.cart[product_id]['quantity'] += 1
                else:
                    messagebox.showwarning("Stock Limit", f"Only {product.stock} available!")
                    return
            else:
                self.cart[product_id] = {
                    'name': product.name,
                    'price': product.price,
                    'quantity': 1,
                    'product_id': product_id
                }
            self.refresh_cart()
    
    def refresh_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        for item in self.cart.values():
            total = item['price'] * item['quantity']
            self.cart_tree.insert('', 'end', values=(
                item['name'], item['quantity'], f"{Config.CURRENCY}{item['price']}",
                f"{Config.CURRENCY}{total:.2f}"
            ))
        
        self.update_totals()
    
    def update_totals(self):
        subtotal = sum(item['price'] * item['quantity'] for item in self.cart.values())
        
        try:
            discount_percent = float(self.discount_entry.get()) if self.discount_entry.get() else 0
            if discount_percent < 0 or discount_percent > 100:
                discount_percent = 0
        except:
            discount_percent = 0
        
        discount_amount = subtotal * (discount_percent / 100)
        final_total = subtotal - discount_amount
        
        self.subtotal_label.config(text=f"Subtotal: {Config.CURRENCY}{subtotal:.2f}")
        self.discount_label.config(text=f"Discount: -{Config.CURRENCY}{discount_amount:.2f}")
        self.total_label.config(text=f"TOTAL: {Config.CURRENCY}{final_total:.2f}")
        
        return final_total, subtotal, discount_amount
    
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
    
    def add_customer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Customer")
        dialog.configure(bg=self.colors['card'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 400, 450)
        
        tk.Label(dialog, text="Add New Customer", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=20)
        
        fields = {}
        labels = ['Full Name:', 'Phone:', 'Email:', 'Address:']
        
        for label in labels:
            frame = tk.Frame(dialog, bg=self.colors['card'])
            frame.pack(fill='x', padx=30, pady=5)
            tk.Label(frame, text=label, font=('Segoe UI', 10),
                    bg=self.colors['card']).pack(anchor='w')
            entry = tk.Entry(frame, font=('Segoe UI', 10), bg='#f8f9fa', relief='solid', bd=1)
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
            
            self.customer_combo['values'] = ["Walk-in Customer"] + list(self.customers.keys())
            self.customer_var.set(str(customer.customer_id))
            
            messagebox.showinfo("Success", f"Customer {name} added!")
            dialog.destroy()
        
        tk.Button(dialog, text="SAVE", command=save,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 11),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=30, ipady=8)
    
    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Cart is empty!")
            return
        
        final_total, subtotal, discount_amount = self.update_totals()
        
        # Payment dialog
        payment_window = tk.Toplevel(self.root)
        payment_window.title("Payment")
        payment_window.configure(bg=self.colors['card'])
        payment_window.transient(self.root)
        payment_window.grab_set()
        self.center_window(payment_window, 400, 450)
        
        tk.Label(payment_window, text="Payment", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=20)
        
        tk.Label(payment_window, text=f"Total Amount: {Config.CURRENCY}{final_total:.2f}",
                font=('Segoe UI', 12), bg=self.colors['card'], fg=self.colors['success']).pack(pady=10)
        
        tk.Label(payment_window, text="Payment Method:", font=('Segoe UI', 11),
                bg=self.colors['card']).pack(pady=10)
        
        payment_var = tk.StringVar(value="Cash")
        payment_frame = tk.Frame(payment_window, bg=self.colors['card'])
        payment_frame.pack(pady=5)
        
        for method in ["Cash", "Card", "Digital Wallet"]:
            tk.Radiobutton(payment_frame, text=method, variable=payment_var, value=method,
                          bg=self.colors['card']).pack(side='left', padx=15)
        
        tk.Label(payment_window, text="Amount Paid:", font=('Segoe UI', 11),
                bg=self.colors['card']).pack(pady=10)
        
        paid_entry = tk.Entry(payment_window, font=('Segoe UI', 12), bg='#f8f9fa',
                              relief='solid', bd=1, justify='center', width=15)
        paid_entry.pack(pady=5, ipady=5)
        paid_entry.insert(0, str(final_total))
        
        def process():
            try:
                paid = float(paid_entry.get())
                if paid < final_total:
                    messagebox.showerror("Error", f"Insufficient payment!\nNeed: {Config.CURRENCY}{final_total:.2f}")
                    return
                
                change = paid - final_total
                
                # Process sale
                sale_items = []
                for item in self.cart.values():
                    product = self.products[item['product_id']]
                    product.stock -= item['quantity']
                    product.times_sold += item['quantity']
                    sale_items.append((item['name'], item['quantity'], item['price']))
                
                customer_id = None
                points_earned = 0
                if self.customer_var.get() != "Walk-in Customer":
                    customer_id = self.customer_var.get()
                    customer = self.customers[customer_id]
                    points_earned = int(final_total * Config.LOYALTY_POINTS_RATE * 100)
                    customer.loyalty_points += points_earned
                    customer.total_spent += final_total
                    self.save_customers()
                
                transaction = Transaction(
                    self.next_transaction_id, sale_items, subtotal,
                    discount_amount, final_total, self.current_user.username,
                    payment_var.get(), customer_id, 0, points_earned
                )
                self.transactions.append(transaction)
                self.next_transaction_id += 1
                
                self.save_products()
                self.save_transactions()
                
                self.show_receipt(transaction, paid, change, points_earned)
                
                self.cart.clear()
                self.refresh_cart()
                self.refresh_product_list()
                
                payment_window.destroy()
                
                msg = f"Transaction Complete!\nChange: {Config.CURRENCY}{change:.2f}"
                if points_earned > 0:
                    msg += f"\nPoints Earned: {points_earned}"
                messagebox.showinfo("Success", msg)
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount!")
        
        tk.Button(payment_window, text="COMPLETE PAYMENT", command=process,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=30, ipady=10)
        
        tk.Button(payment_window, text="Cancel", command=payment_window.destroy,
                 bg=self.colors['danger'], fg='white', relief='flat',
                 cursor='hand2').pack(fill='x', padx=30, ipady=8)
    
    def show_receipt(self, transaction, paid, change, points_earned):
        receipt_window = tk.Toplevel(self.root)
        receipt_window.title(f"Receipt #{transaction.transaction_id}")
        receipt_window.configure(bg='white')
        self.center_window(receipt_window, 450, 600)
        
        receipt_text = tk.Text(receipt_window, font=('Courier', 10), bg='white', fg='black', wrap='word')
        receipt_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        receipt = f"""
{'='*45}
{Config.APP_NAME}
{'='*45}
Receipt No: #{transaction.transaction_id}
Date: {transaction.date}
Cashier: {transaction.cashier}
Payment: {transaction.payment_method}
{'-'*45}

ITEMS:
{'-'*45}
{'Item':<25} {'Qty':>5} {'Price':>7} {'Total':>8}
{'-'*45}
"""
        for item in transaction.items:
            name, qty, price = item
            total = price * qty
            receipt += f"{name[:24]:<25} {qty:>5} {Config.CURRENCY}{price:>6.2f} {Config.CURRENCY}{total:>7.2f}\n"
        
        receipt += f"""{'-'*45}
{'Subtotal':<38} {Config.CURRENCY}{transaction.total:>6.2f}
"""
        if transaction.discount > 0:
            receipt += f"{'Discount':<38} -{Config.CURRENCY}{transaction.discount:>5.2f}\n"
        
        receipt += f"""{'TOTAL':<38} {Config.CURRENCY}{transaction.final_total:>6.2f}
{'Paid':<38} {Config.CURRENCY}{paid:>6.2f}
{'Change':<38} {Config.CURRENCY}{change:>6.2f}
"""
        if points_earned > 0:
            receipt += f"{'Points Earned':<38} {points_earned:>6}\n"
        
        receipt += f"""
{'='*45}
    Thank you for shopping!
    Visit Again!
{'='*45}
"""
        receipt_text.insert('1.0', receipt)
        receipt_text.config(state='disabled')
        
        tk.Button(receipt_window, text="Close", command=receipt_window.destroy,
                 bg=self.colors['primary'], fg='white', relief='flat').pack(pady=10, ipadx=20)
    
    # -------------------------- INVENTORY MANAGEMENT --------------------------
    def show_inventory(self):
        self.clear_main_frame()
        
        # Toolbar
        toolbar = tk.Frame(self.main_frame, bg=self.colors['bg'])
        toolbar.pack(fill='x', pady=(0, 10))
        
        buttons = [
            ("➕ Add Product", self.add_product_dialog),
            ("✏️ Edit Product", self.edit_product_dialog),
            ("🗑️ Delete Product", self.delete_product),
            ("📤 Export CSV", self.export_products),
            ("🔄 Refresh", self.refresh_inventory)
        ]
        
        for text, cmd in buttons:
            tk.Button(toolbar, text=text, command=cmd,
                     bg=self.colors['primary'], fg='white', relief='flat', cursor='hand2',
                     font=('Segoe UI', 9)).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        # Search
        search_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        search_frame.pack(fill='x', pady=10)
        
        tk.Label(search_frame, text="Search:", bg=self.colors['bg']).pack(side='left')
        self.inv_search = tk.Entry(search_frame, width=30, bg='white', relief='solid', bd=1)
        self.inv_search.pack(side='left', padx=5, ipady=5)
        self.inv_search.bind('<KeyRelease>', lambda e: self.search_inventory())
        
        tk.Label(search_frame, text="Category:", bg=self.colors['bg']).pack(side='left', padx=10)
        categories = ['All'] + list(set(p.category for p in self.products.values()))
        self.category_filter = ttk.Combobox(search_frame, values=categories, width=15)
        self.category_filter.set('All')
        self.category_filter.pack(side='left', padx=5)
        self.category_filter.bind('<<ComboboxSelected>>', lambda e: self.search_inventory())
        
        # Treeview
        tree_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        tree_frame.pack(fill='both', expand=True)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Price', 'Cost', 'Stock', 'Category', 'Sold')
        self.inv_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                      yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.inv_tree.yview)
        h_scroll.config(command=self.inv_tree.xview)
        
        for col in columns:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, width=100)
        self.inv_tree.column('Name', width=200)
        self.inv_tree.pack(fill='both', expand=True)
        
        self.refresh_inventory()
    
    def refresh_inventory(self):
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
        for product in self.products.values():
            self.inv_tree.insert('', 'end', values=(
                product.product_id, product.name, f"{Config.CURRENCY}{product.price}",
                f"{Config.CURRENCY}{product.cost_price}", product.stock,
                product.category, product.times_sold
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
                product.product_id, product.name, f"{Config.CURRENCY}{product.price}",
                f"{Config.CURRENCY}{product.cost_price}", product.stock,
                product.category, product.times_sold
            ))
    
    def add_product_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Product")
        dialog.configure(bg=self.colors['card'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 450, 550)
        
        tk.Label(dialog, text="Add New Product", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=20)
        
        fields = {}
        labels = ['Name:', 'Price:', 'Cost Price:', 'Stock:', 'Category:', 'Barcode:', 'Supplier:']
        
        for label in labels:
            frame = tk.Frame(dialog, bg=self.colors['card'])
            frame.pack(fill='x', padx=30, pady=5)
            tk.Label(frame, text=label, font=('Segoe UI', 10),
                    bg=self.colors['card']).pack(anchor='w')
            entry = tk.Entry(frame, font=('Segoe UI', 10), bg='#f8f9fa', relief='solid', bd=1)
            entry.pack(fill='x', ipady=5)
            fields[label] = entry
        
        def save():
            try:
                name = fields['Name:'].get().strip()
                price = float(fields['Price:'].get())
                cost_price = float(fields['Cost Price:'].get()) if fields['Cost Price:'].get() else 0
                stock = int(fields['Stock:'].get())
                category = fields['Category:'].get().strip() or "General"
                barcode = fields['Barcode:'].get().strip()
                supplier = fields['Supplier:'].get().strip()
                
                if not name or price <= 0:
                    messagebox.showerror("Error", "Name and valid price required!")
                    return
                
                product = Product(str(self.next_product_id), name, price, stock, category,
                                 barcode, cost_price, supplier)
                self.products[str(self.next_product_id)] = product
                self.next_product_id += 1
                self.save_products()
                self.refresh_inventory()
                self.refresh_product_list()
                
                messagebox.showinfo("Success", "Product added!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values!")
        
        tk.Button(dialog, text="SAVE", command=save,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 11),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=30, ipady=8)
    
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
        
        tk.Label(dialog, text="Edit Product", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['primary']).pack(pady=20)
        
        fields = {}
        current = [product.name, product.price, product.cost_price, product.stock,
                   product.category, product.barcode, product.supplier]
        labels = ['Name:', 'Price:', 'Cost Price:', 'Stock:', 'Category:', 'Barcode:', 'Supplier:']
        
        for i, label in enumerate(labels):
            frame = tk.Frame(dialog, bg=self.colors['card'])
            frame.pack(fill='x', padx=30, pady=5)
            tk.Label(frame, text=label, font=('Segoe UI', 10),
                    bg=self.colors['card']).pack(anchor='w')
            entry = tk.Entry(frame, font=('Segoe UI', 10), bg='#f8f9fa', relief='solid', bd=1)
            entry.insert(0, str(current[i]))
            entry.pack(fill='x', ipady=5)
            fields[label] = entry
        
        def update():
            try:
                product.name = fields['Name:'].get().strip()
                product.price = float(fields['Price:'].get())
                product.cost_price = float(fields['Cost Price:'].get()) if fields['Cost Price:'].get() else 0
                product.stock = int(fields['Stock:'].get())
                product.category = fields['Category:'].get().strip() or "General"
                product.barcode = fields['Barcode:'].get().strip()
                product.supplier = fields['Supplier:'].get().strip()
                
                self.save_products()
                self.refresh_inventory()
                self.refresh_product_list()
                
                messagebox.showinfo("Success", "Product updated!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values!")
        
        tk.Button(dialog, text="UPDATE", command=update,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 11),
                 relief='flat', cursor='hand2').pack(pady=20, fill='x', padx=30, ipady=8)
    
    def delete_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a product to delete!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_name = item['values'][1]
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{product_name}'?"):
            product_id = str(item['values'][0])
            del self.products[product_id]
            self.save_products()
            self.refresh_inventory()
            self.refresh_product_list()
            messagebox.showinfo("Success", "Product deleted!")
    
    def export_products(self):
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
    
    # -------------------------- CUSTOMERS --------------------------
    def show_customers(self):
        self.clear_main_frame()
        
        # Toolbar
        toolbar = tk.Frame(self.main_frame, bg=self.colors['bg'])
        toolbar.pack(fill='x', pady=(0, 10))
        
        tk.Button(toolbar, text="➕ Add Customer", command=self.add_customer_dialog,
                 bg=self.colors['primary'], fg='white', relief='flat', cursor='hand2',
                 font=('Segoe UI', 9)).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        tk.Button(toolbar, text="🔄 Refresh", command=self.refresh_customers,
                 bg=self.colors['primary'], fg='white', relief='flat', cursor='hand2',
                 font=('Segoe UI', 9)).pack(side='left', padx=5, ipadx=10, ipady=5)
        
        # Search
        search_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        search_frame.pack(fill='x', pady=10)
        
        tk.Label(search_frame, text="Search:", bg=self.colors['bg']).pack(side='left')
        self.cust_search = tk.Entry(search_frame, width=30, bg='white', relief='solid', bd=1)
        self.cust_search.pack(side='left', padx=5, ipady=5)
        self.cust_search.bind('<KeyRelease>', lambda e: self.search_customers())
        
        # Treeview
        tree_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        tree_frame.pack(fill='both', expand=True)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Phone', 'Email', 'Points', 'Total Spent', 'Since')
        self.cust_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                       yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.config(command=self.cust_tree.yview)
        h_scroll.config(command=self.cust_tree.xview)
        
        for col in columns:
            self.cust_tree.heading(col, text=col)
            self.cust_tree.column(col, width=120)
        self.cust_tree.pack(fill='both', expand=True)
        self.cust_tree.bind('<Double-Button-1>', lambda e: self.view_customer_details())
        
        self.refresh_customers()
    
    def refresh_customers(self):
        for item in self.cust_tree.get_children():
            self.cust_tree.delete(item)
        for customer in self.customers.values():
            self.cust_tree.insert('', 'end', values=(
                customer.customer_id, customer.name, customer.phone or '-',
                customer.email or '-', customer.loyalty_points,
                f"{Config.CURRENCY}{customer.total_spent:.2f}", customer.created_at[:10]
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
                    f"{Config.CURRENCY}{customer.total_spent:.2f}", customer.created_at[:10]
                ))
    
    def view_customer_details(self):
        selected = self.cust_tree.selection()
        if not selected:
            return
        item = self.cust_tree.item(selected[0])
        customer_id = str(item['values'][0])
        customer = self.customers.get(customer_id)
        
        if customer:
            history = "\n".join([f"#{h['transaction_id']} - {h['date']} - {Config.CURRENCY}{h['total']:.2f}" 
                                 for h in customer.purchase_history[-5:]])
            
            details = f"""
Customer Details
{'='*40}
Name: {customer.name}
Phone: {customer.phone}
Email: {customer.email}
Address: {customer.address}
Points: {customer.loyalty_points}
Total Spent: {Config.CURRENCY}{customer.total_spent:.2f}
Member Since: {customer.created_at}

Recent Purchases:
{history if history else 'No purchases yet'}
"""
            messagebox.showinfo(f"Customer: {customer.name}", details)
    
    # -------------------------- RETURNS MANAGEMENT --------------------------
    def show_returns(self):
        self.clear_main_frame()
        
        # Header
        tk.Label(self.main_frame, text="RETURNS & REFUNDS", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Search for transaction
        search_frame = tk.Frame(self.main_frame, bg=self.colors['card'], relief='solid', bd=1)
        search_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(search_frame, text="Enter Transaction ID:", font=('Segoe UI', 11),
                bg=self.colors['card']).pack(side='left', padx=15, pady=10)
        
        self.return_trans_id = tk.Entry(search_frame, width=20, font=('Segoe UI', 11),
                                        bg='#f8f9fa', relief='solid', bd=1)
        self.return_trans_id.pack(side='left', padx=10, ipady=5)
        
        tk.Button(search_frame, text="Search", command=self.search_transaction_for_return,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2',
                 font=('Segoe UI', 10)).pack(side='left', padx=5, ipadx=15, ipady=5)
        
        # Results frame
        self.return_result_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.return_result_frame.pack(fill='both', expand=True, pady=10)
    
    def search_transaction_for_return(self):
        trans_id_str = self.return_trans_id.get().strip()
        if not trans_id_str:
            messagebox.showwarning("Input Required", "Please enter a transaction ID!")
            return
        
        try:
            trans_id = int(trans_id_str.replace('#', ''))
        except:
            messagebox.showerror("Error", "Invalid transaction ID!")
            return
        
        # Find transaction
        transaction = None
        for t in self.transactions:
            if t.transaction_id == trans_id:
                transaction = t
                break
        
        if not transaction:
            messagebox.showerror("Not Found", f"Transaction #{trans_id} not found!")
            return
        
        if transaction.returned:
            messagebox.showwarning("Already Returned", "This transaction has already been returned!")
            return
        
        # Check if within return period
        trans_date = datetime.strptime(transaction.date, "%Y-%m-%d %H:%M:%S")
        days_diff = (datetime.now() - trans_date).days
        if days_diff > Config.RETURN_DAYS_LIMIT:
            messagebox.showerror("Return Period Expired", 
                                f"Cannot return items after {Config.RETURN_DAYS_LIMIT} days!\n"
                                f"Transaction date: {transaction.date[:10]}")
            return
        
        self.show_return_items(transaction)
    
    def show_return_items(self, transaction):
        # Clear previous
        for widget in self.return_result_frame.winfo_children():
            widget.destroy()
        
        # Transaction info
        info_frame = tk.Frame(self.return_result_frame, bg=self.colors['card'], relief='solid', bd=1)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        info_text = f"Transaction #{transaction.transaction_id} | Date: {transaction.date} | Cashier: {transaction.cashier} | Total: {Config.CURRENCY}{transaction.final_total:.2f}"
        tk.Label(info_frame, text=info_text, font=('Segoe UI', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=10)
        
        # Items selection
        items_frame = tk.LabelFrame(self.return_result_frame, text="Select Items to Return",
                                    bg=self.colors['card'], fg=self.colors['primary'],
                                    font=('Segoe UI', 10, 'bold'))
        items_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Treeview for items
        tree_frame = tk.Frame(items_frame, bg=self.colors['card'])
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        
        columns = ('Select', 'Product', 'Quantity', 'Price', 'Total')
        self.return_items_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                               yscrollcommand=v_scroll.set, height=8)
        v_scroll.config(command=self.return_items_tree.yview)
        
        self.return_items_tree.heading('Select', text='Select')
        self.return_items_tree.heading('Product', text='Product')
        self.return_items_tree.heading('Quantity', text='Quantity')
        self.return_items_tree.heading('Price', text='Price')
        self.return_items_tree.heading('Total', text='Total')
        
        self.return_items_tree.column('Select', width=60, anchor='center')
        self.return_items_tree.column('Product', width=250)
        self.return_items_tree.column('Quantity', width=80, anchor='center')
        self.return_items_tree.column('Price', width=100, anchor='center')
        self.return_items_tree.column('Total', width=100, anchor='center')
        
        self.return_items_tree.pack(fill='both', expand=True)
        
        self.return_selections = {}
        for item in transaction.items:
            name, qty, price = item
            item_id = f"{name}_{price}"
            self.return_selections[item_id] = tk.BooleanVar(value=False)
            self.return_items_tree.insert('', 'end', values=('□', name, qty, f"{Config.CURRENCY}{price}", f"{Config.CURRENCY}{price*qty:.2f}"), tags=(item_id,))
        
        # Bind click event
        self.return_items_tree.bind('<ButtonRelease-1>', self.on_item_click_return)
        
        # Reason
        reason_frame = tk.Frame(self.return_result_frame, bg=self.colors['bg'])
        reason_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(reason_frame, text="Return Reason:", font=('Segoe UI', 10),
                bg=self.colors['bg']).pack(anchor='w')
        
        self.return_reason = tk.Text(reason_frame, height=3, width=60,
                                     bg='white', relief='solid', bd=1, font=('Segoe UI', 10))
        self.return_reason.pack(fill='x', pady=5)
        
        # Refund amount display
        self.refund_label = tk.Label(self.return_result_frame, text="Refund Amount: $0.00",
                                     font=('Segoe UI', 12, 'bold'), bg=self.colors['bg'],
                                     fg=self.colors['success'])
        self.refund_label.pack(pady=10)
        
        # Process button
        tk.Button(self.return_result_frame, text="PROCESS RETURN", command=lambda: self.process_return(transaction),
                 bg=self.colors['warning'], fg='white', font=('Segoe UI', 11, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=10, ipadx=30, ipady=8)
    
    def on_item_click_return(self, event):
        region = self.return_items_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.return_items_tree.identify_column(event.x)
            if column == '#1':  # Select column
                item = self.return_items_tree.identify_row(event.y)
                values = self.return_items_tree.item(item, 'values')
                item_id = self.return_items_tree.item(item, 'tags')[0]
                
                current = self.return_selections[item_id].get()
                self.return_selections[item_id].set(not current)
                
                new_value = '☑' if not current else '□'
                self.return_items_tree.item(item, values=(new_value, values[1], values[2], values[3], values[4]))
                
                self.update_refund_amount()
    
    def update_refund_amount(self):
        total_refund = 0
        for item_id, var in self.return_selections.items():
            if var.get():
                # Find the item in the tree
                for child in self.return_items_tree.get_children():
                    tags = self.return_items_tree.item(child, 'tags')
                    if tags and tags[0] == item_id:
                        values = self.return_items_tree.item(child, 'values')
                        total_str = values[4].replace(Config.CURRENCY, '')
                        try:
                            total_refund += float(total_str)
                        except:
                            pass
                        break
        
        self.refund_label.config(text=f"Refund Amount: {Config.CURRENCY}{total_refund:.2f}")
        return total_refund
    
    def process_return(self, transaction):
        # Calculate refund amount
        refund_amount = 0
        items_to_return = []
        
        for child in self.return_items_tree.get_children():
            tags = self.return_items_tree.item(child, 'tags')
            if tags:
                item_id = tags[0]
                if self.return_selections[item_id].get():
                    values = self.return_items_tree.item(child, 'values')
                    product_name = values[1]
                    qty = int(values[2])
                    price = float(values[3].replace(Config.CURRENCY, ''))
                    total = price * qty
                    refund_amount += total
                    items_to_return.append((product_name, qty, price))
        
        if refund_amount <= 0:
            messagebox.showwarning("No Items", "Please select items to return!")
            return
        
        reason = self.return_reason.get("1.0", tk.END).strip()
        if not reason:
            reason = "Customer request"
        
        # Confirm
        if not messagebox.askyesno("Confirm Return", 
                                   f"Return {len(items_to_return)} item(s)\n"
                                   f"Refund Amount: {Config.CURRENCY}{refund_amount:.2f}\n\n"
                                   f"Proceed?"):
            return
        
        # Process return - restore stock
        for item_name, qty, price in items_to_return:
            for product in self.products.values():
                if product.name == item_name:
                    product.stock += qty
                    break
        
        # Create return record
        return_trans = ReturnTransaction(
            self.next_return_id, transaction.transaction_id, items_to_return,
            refund_amount, reason, self.current_user.username, transaction.customer_id
        )
        self.returns.append(return_trans)
        self.next_return_id += 1
        
        # Mark original transaction as returned
        transaction.returned = True
        transaction.status = "Returned"
        transaction.return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update customer points if applicable
        if transaction.customer_id and transaction.customer_id in self.customers:
            customer = self.customers[transaction.customer_id]
            points_to_deduct = int(refund_amount * Config.LOYALTY_POINTS_RATE * 100)
            customer.loyalty_points = max(0, customer.loyalty_points - points_to_deduct)
            self.save_customers()
        
        # Save all changes
        self.save_products()
        self.save_transactions()
        self.save_returns()
        
        # Show receipt
        self.show_return_receipt(return_trans, refund_amount)
        
        # Clear and reset
        self.return_trans_id.delete(0, tk.END)
        for widget in self.return_result_frame.winfo_children():
            widget.destroy()
        
        messagebox.showinfo("Success", f"Return processed!\nRefund Amount: {Config.CURRENCY}{refund_amount:.2f}")
    
    def show_return_receipt(self, return_trans, refund_amount):
        receipt_window = tk.Toplevel(self.root)
        receipt_window.title(f"Return Receipt #{return_trans.return_id}")
        receipt_window.configure(bg='white')
        self.center_window(receipt_window, 450, 550)
        
        receipt_text = tk.Text(receipt_window, font=('Courier', 10), bg='white', fg='black', wrap='word')
        receipt_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        receipt = f"""
{'='*45}
{Config.APP_NAME} - RETURN RECEIPT
{'='*45}
Return ID: #{return_trans.return_id}
Original Transaction: #{return_trans.original_transaction_id}
Date: {return_trans.date}
Cashier: {return_trans.cashier}
Reason: {return_trans.reason}
{'-'*45}

RETURNED ITEMS:
{'-'*45}
{'Item':<25} {'Qty':>5} {'Price':>7} {'Total':>8}
{'-'*45}
"""
        for item in return_trans.items:
            name, qty, price = item
            total = price * qty
            receipt += f"{name[:24]:<25} {qty:>5} {Config.CURRENCY}{price:>6.2f} {Config.CURRENCY}{total:>7.2f}\n"
        
        receipt += f"""
{'-'*45}
{'REFUND AMOUNT':<38} {Config.CURRENCY}{refund_amount:>6.2f}
{'='*45}

Refund will be processed to original
payment method within 3-5 business days.

{'='*45}
    Thank you for your understanding!
{'='*45}
"""
        receipt_text.insert('1.0', receipt)
        receipt_text.config(state='disabled')
        
        tk.Button(receipt_window, text="Close", command=receipt_window.destroy,
                 bg=self.colors['primary'], fg='white', relief='flat').pack(pady=10, ipadx=20)
    
    # -------------------------- REPORTS --------------------------
    def show_reports(self):
        self.clear_main_frame()
        
        # Summary cards
        cards_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        cards_frame.pack(fill='x', pady=10)
        
        total_revenue = sum(t.final_total for t in self.transactions if not t.returned)
        total_returns = sum(r.refund_amount for r in self.returns)
        net_revenue = total_revenue - total_returns
        total_transactions = len([t for t in self.transactions if not t.returned])
        
        cards = [
            ("Total Revenue", f"{Config.CURRENCY}{total_revenue:,.2f}", self.colors['success']),
            ("Returns", f"{Config.CURRENCY}{total_returns:,.2f}", self.colors['danger']),
            ("Net Revenue", f"{Config.CURRENCY}{net_revenue:,.2f}", self.colors['info']),
            ("Transactions", str(total_transactions), self.colors['primary'])
        ]
        
        for title, value, color in cards:
            card = tk.Frame(cards_frame, bg=self.colors['card'], relief='solid', bd=1, width=200, height=100)
            card.pack(side='left', padx=10, pady=10)
            card.pack_propagate(False)
            
            tk.Label(card, text=title, font=('Segoe UI', 10),
                    bg=self.colors['card'], fg=self.colors['text_light']).pack(pady=(15, 5))
            tk.Label(card, text=value, font=('Segoe UI', 18, 'bold'),
                    bg=self.colors['card'], fg=color).pack()
        
        # Best sellers
        best_frame = tk.LabelFrame(self.main_frame, text="Best Selling Products",
                                   bg=self.colors['card'], fg=self.colors['primary'],
                                   font=('Segoe UI', 11, 'bold'))
        best_frame.pack(fill='both', expand=True, pady=10)
        
        tree_frame = tk.Frame(best_frame, bg=self.colors['card'])
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        v_scroll.pack(side='right', fill='y')
        
        columns = ('Rank', 'Product', 'Units Sold', 'Revenue')
        self.best_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                       yscrollcommand=v_scroll.set, height=10)
        v_scroll.config(command=self.best_tree.yview)
        
        for col in columns:
            self.best_tree.heading(col, text=col)
            self.best_tree.column(col, width=150)
        self.best_tree.pack(fill='both', expand=True)
        
        # Populate best sellers
        sorted_products = sorted(self.products.values(), key=lambda x: x.times_sold, reverse=True)[:10]
        for i, product in enumerate(sorted_products, 1):
            revenue = product.price * product.times_sold
            self.best_tree.insert('', 'end', values=(i, product.name, product.times_sold, f"{Config.CURRENCY}{revenue:.2f}"))
        
        # Export button
        tk.Button(self.main_frame, text="📊 Export Full Report", command=self.export_full_report,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 10),
                 relief='flat', cursor='hand2').pack(pady=10, ipadx=20, ipady=5)
    
    def export_full_report(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Transaction ID', 'Date', 'Cashier', 'Items', 'Total', 'Payment', 'Status'])
                    for t in self.transactions:
                        writer.writerow([t.transaction_id, t.date, t.cashier, len(t.items), t.final_total, t.payment_method, t.status])
                    
                    writer.writerow([])
                    writer.writerow(['Return ID', 'Original Transaction', 'Date', 'Refund Amount', 'Reason'])
                    for r in self.returns:
                        writer.writerow([r.return_id, r.original_transaction_id, r.date, r.refund_amount, r.reason])
                
                messagebox.showinfo("Success", f"Report exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    # -------------------------- SETTINGS --------------------------
    def show_settings(self):
        self.clear_main_frame()
        
        # User Management
        user_frame = tk.LabelFrame(self.main_frame, text="User Management",
                                   bg=self.colors['card'], fg=self.colors['primary'],
                                   font=('Segoe UI', 11, 'bold'))
        user_frame.pack(fill='x', padx=20, pady=10)
        
        # User list
        tree_frame = tk.Frame(user_frame, bg=self.colors['card'])
        tree_frame.pack(fill='x', padx=10, pady=10)
        
        columns = ('Username', 'Full Name', 'Role', 'Email')
        self.user_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=5)
        
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=150)
        self.user_tree.pack(fill='x')
        
        for username, user in self.users.items():
            self.user_tree.insert('', 'end', values=(username, user.full_name, user.role, user.email))
        
        # Add user form
        add_frame = tk.Frame(user_frame, bg=self.colors['card'])
        add_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(add_frame, text="Add New User:", font=('Segoe UI', 10),
                bg=self.colors['card']).pack(anchor='w')
        
        entry_frame = tk.Frame(add_frame, bg=self.colors['card'])
        entry_frame.pack(fill='x', pady=5)
        
        self.new_username = tk.Entry(entry_frame, width=15, bg='#f8f9fa', relief='solid', bd=1)
        self.new_username.pack(side='left', padx=5, ipady=5)
        self.new_username.insert(0, "Username")
        
        self.new_password = tk.Entry(entry_frame, width=15, bg='#f8f9fa', relief='solid', bd=1, show="*")
        self.new_password.pack(side='left', padx=5, ipady=5)
        self.new_password.insert(0, "password")
        
        self.new_fullname = tk.Entry(entry_frame, width=20, bg='#f8f9fa', relief='solid', bd=1)
        self.new_fullname.pack(side='left', padx=5, ipady=5)
        self.new_fullname.insert(0, "Full Name")
        
        self.new_role = ttk.Combobox(entry_frame, values=['admin', 'staff', 'cashier'], width=10)
        self.new_role.set('cashier')
        self.new_role.pack(side='left', padx=5)
        
        tk.Button(entry_frame, text="Add User", command=self.add_user,
                 bg=self.colors['success'], fg='white', relief='flat', cursor='hand2').pack(side='left', padx=5, ipadx=10, ipady=5)
        
        # System Settings
        system_frame = tk.LabelFrame(self.main_frame, text="System Settings",
                                     bg=self.colors['card'], fg=self.colors['primary'],
                                     font=('Segoe UI', 11, 'bold'))
        system_frame.pack(fill='x', padx=20, pady=10)
        
        settings_frame = tk.Frame(system_frame, bg=self.colors['card'])
        settings_frame.pack(padx=20, pady=10)
        
        # Return days setting
        row1 = tk.Frame(settings_frame, bg=self.colors['card'])
        row1.pack(fill='x', pady=5)
        tk.Label(row1, text="Return Period (days):", width=20, anchor='w',
                bg=self.colors['card']).pack(side='left')
        self.return_days_entry = tk.Entry(row1, width=10, bg='#f8f9fa', relief='solid', bd=1)
        self.return_days_entry.insert(0, str(Config.RETURN_DAYS_LIMIT))
        self.return_days_entry.pack(side='left', padx=10)
        
        # Low stock threshold
        row2 = tk.Frame(settings_frame, bg=self.colors['card'])
        row2.pack(fill='x', pady=5)
        tk.Label(row2, text="Low Stock Threshold:", width=20, anchor='w',
                bg=self.colors['card']).pack(side='left')
        self.low_stock_entry = tk.Entry(row2, width=10, bg='#f8f9fa', relief='solid', bd=1)
        self.low_stock_entry.insert(0, str(Config.LOW_STOCK_THRESHOLD))
        self.low_stock_entry.pack(side='left', padx=10)
        
        # Points rate
        row3 = tk.Frame(settings_frame, bg=self.colors['card'])
        row3.pack(fill='x', pady=5)
        tk.Label(row3, text="Points Rate (per $):", width=20, anchor='w',
                bg=self.colors['card']).pack(side='left')
        self.points_rate_entry = tk.Entry(row3, width=10, bg='#f8f9fa', relief='solid', bd=1)
        self.points_rate_entry.insert(0, str(Config.LOYALTY_POINTS_RATE * 100))
        self.points_rate_entry.pack(side='left', padx=10)
        
        def save_settings():
            try:
                Config.RETURN_DAYS_LIMIT = int(self.return_days_entry.get())
                Config.LOW_STOCK_THRESHOLD = int(self.low_stock_entry.get())
                Config.LOYALTY_POINTS_RATE = float(self.points_rate_entry.get()) / 100
                messagebox.showinfo("Success", "Settings saved!")
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric values!")
        
        tk.Button(system_frame, text="💾 Save Settings", command=save_settings,
                 bg=self.colors['success'], fg='white', font=('Segoe UI', 10),
                 relief='flat', cursor='hand2').pack(pady=10, ipadx=20, ipady=5)
        
        # Backup section
        backup_frame = tk.LabelFrame(self.main_frame, text="Backup & Restore",
                                     bg=self.colors['card'], fg=self.colors['primary'],
                                     font=('Segoe UI', 11, 'bold'))
        backup_frame.pack(fill='x', padx=20, pady=10)
        
        btn_frame = tk.Frame(backup_frame, bg=self.colors['card'])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 Create Backup", command=self.backup_data,
                 bg=self.colors['info'], fg='white', relief='flat', cursor='hand2',
                 font=('Segoe UI', 10)).pack(side='left', padx=10, ipadx=20, ipady=5)
        
        tk.Button(btn_frame, text="🔄 Restore Backup", command=self.restore_data,
                 bg=self.colors['warning'], fg='white', relief='flat', cursor='hand2',
                 font=('Segoe UI', 10)).pack(side='left', padx=10, ipadx=20, ipady=5)
    
    def add_user(self):
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()
        fullname = self.new_fullname.get().strip()
        role = self.new_role.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password required!")
            return
        
        if username in self.users:
            messagebox.showerror("Error", "Username already exists!")
            return
        
        self.users[username] = User(username, password, role, fullname)
        self.save_users()
        
        # Refresh user list
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        for uname, user in self.users.items():
            self.user_tree.insert('', 'end', values=(uname, user.full_name, user.role, user.email))
        
        # Clear entries
        self.new_username.delete(0, tk.END)
        self.new_password.delete(0, tk.END)
        self.new_fullname.delete(0, tk.END)
        
        messagebox.showinfo("Success", f"User {username} added!")
    
    def backup_data(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(Config.BACKUP_DIR, f"backup_{timestamp}")
            os.makedirs(backup_folder)
            
            for file in os.listdir(Config.DATA_DIR):
                if file.endswith('.json'):
                    src = os.path.join(Config.DATA_DIR, file)
                    dst = os.path.join(backup_folder, file)
                    shutil.copy2(src, dst)
            
            messagebox.showinfo("Success", f"Backup created!\nLocation: {backup_folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")
    
    def restore_data(self):
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

# -------------------------- MAIN --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartStoreEnterprise(root)
    root.mainloop()