"""
Professional Grocery Store Management System
FULLY WORKING – Fixed cart visibility & database schema
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from tkinter import messagebox, filedialog, simpledialog, END
import json

import customtkinter as ctk
from PIL import Image, ImageDraw

# ==================== CONSTANTS ====================

DATABASE_NAME = "grocery_store.db"
APP_TITLE = "Grocery Store Management System Pro"
APP_WIDTH = 1400
APP_HEIGHT = 800

# Professional Two-Color Scheme
COLOR_PRIMARY = "#1a2a3a"      # Dark Navy Blue
COLOR_SECONDARY = "#4a5c6c"    # Steel Blue
COLOR_ACCENT = "#6c7a89"       # Silver Gray
COLOR_BACKGROUND = "#0f1a24"   # Deep Navy
COLOR_TEXT = "#e0e0e0"         # Light Gray
COLOR_SUCCESS = "#2e7d64"      # Muted Teal
COLOR_WARNING = "#c9a03d"      # Muted Gold
COLOR_ERROR = "#b5654b"        # Muted Copper

TAX_RATE = 0.10
LOW_STOCK_THRESHOLD = 10
DISCOUNT_RATES = {"None": 0, "Staff": 0.10, "Senior": 0.15, "Bulk (10+)": 0.20}

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images", "products")
DEFAULT_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "images", "default_image.png")
RECEIPTS_DIR = os.path.join(BASE_DIR, "receipts")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(RECEIPTS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

CATEGORIES = [
    "All", "Fruits & Vegetables", "Dairy & Eggs", "Meat & Seafood",
    "Bakery", "Beverages", "Snacks", "Frozen Foods", "Household",
    "Personal Care", "Electronics", "Other"
]

UNITS = ["pcs", "kg", "g", "liter", "ml", "pack", "box", "dozen"]

# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        try:
            self.connection = sqlite3.connect(DATABASE_NAME)
            self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect: {e}")
            raise
    
    def create_tables(self):
        cursor = self.connection.cursor()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                cost_price REAL,
                stock_quantity INTEGER DEFAULT 0,
                unit TEXT DEFAULT 'pcs',
                image_path TEXT,
                min_stock INTEGER DEFAULT 5,
                location TEXT,
                supplier TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add missing columns in products (safe)
        cursor.execute("PRAGMA table_info(products)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        for col, typ in [('min_stock','INTEGER DEFAULT 5'),('location','TEXT'),('supplier','TEXT'),
                         ('barcode','TEXT'),('cost_price','REAL'),('unit',"TEXT DEFAULT 'pcs'")]:
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {typ}")
                except: pass
        
        # Transactions table – ensure all columns exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                subtotal REAL NOT NULL,
                tax_amount REAL NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                cashier_name TEXT DEFAULT 'Default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add missing columns one by one
        cursor.execute("PRAGMA table_info(transactions)")
        txn_cols = [col[1] for col in cursor.fetchall()]
        required_columns = [
            ('discount_amount', 'REAL', '0'),
            ('discount_type', 'TEXT', "'None'"),
            ('cash_received', 'REAL', 'NULL'),
            ('change_amount', 'REAL', 'NULL'),
            ('customer_name', 'TEXT', "''"),
            ('cashier_name', 'TEXT', "'Default'")
        ]
        for col, col_type, default in required_columns:
            if col not in txn_cols:
                try:
                    cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col} {col_type}")
                except Exception:
                    pass
        
        # Transaction items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL
            )
        ''')
        
        # Returns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id TEXT UNIQUE NOT NULL,
                original_transaction_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                refund_amount REAL NOT NULL,
                reason TEXT,
                processed_by TEXT DEFAULT 'Default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Daily summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_sales REAL DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                total_items_sold INTEGER DEFAULT 0,
                total_returns REAL DEFAULT 0,
                total_expenses REAL DEFAULT 0,
                net_profit REAL DEFAULT 0
            )
        ''')
        
        self.connection.commit()
    
    def backup_database(self):
        try:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            shutil.copy2(DATABASE_NAME, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
    
    # Product Operations
    def add_product(self, name: str, category: str, price: float, stock: int, 
                    unit: str, barcode: str = None, cost_price: float = None,
                    min_stock: int = 5, location: str = "", supplier: str = "",
                    image_path: str = None):
        cursor = self.connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO products (name, category, price, stock_quantity, unit, barcode,
                                    cost_price, min_stock, location, supplier, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, category, price, stock, unit, barcode, cost_price, 
                  min_stock, location, supplier, image_path))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
    
    def get_all_products(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_product_by_id(self, product_id: int):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_product_by_barcode(self, barcode: str):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products WHERE barcode = ?', (barcode,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_product(self, product_id: int, **kwargs):
        allowed_fields = ['name', 'category', 'price', 'stock_quantity', 'unit', 
                         'barcode', 'cost_price', 'min_stock', 'location', 'supplier', 'image_path']
        updates = [f"{field} = ?" for field in kwargs if field in allowed_fields]
        values = [kwargs[field] for field in kwargs if field in allowed_fields]
        
        if updates:
            cursor = self.connection.cursor()
            values.append(product_id)
            cursor.execute(f"UPDATE products SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
            self.connection.commit()
            return True
        return False
    
    def update_stock(self, product_id: int, quantity_change: int):
        cursor = self.connection.cursor()
        cursor.execute('''
            UPDATE products SET stock_quantity = stock_quantity + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND stock_quantity + ? >= 0
        ''', (quantity_change, product_id, quantity_change))
        self.connection.commit()
        return cursor.rowcount > 0
    
    def search_products(self, search_term: str, category: str = "All", min_price: float = 0, max_price: float = 999999):
        cursor = self.connection.cursor()
        query = "SELECT * FROM products WHERE name LIKE ? AND price BETWEEN ? AND ?"
        params = [f"%{search_term}%", min_price, max_price]
        
        if category != "All":
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY name"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_low_stock_products(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products WHERE stock_quantity <= min_stock ORDER BY stock_quantity ASC')
        return [dict(row) for row in cursor.fetchall()]
    
    # Transaction Operations
    def create_transaction(self, items: List[Dict], subtotal: float, tax: float, 
                          discount_type: str, discount_amount: float, total: float,
                          payment_method: str, cash_received: float = None, 
                          customer_name: str = "", cashier: str = "Default"):
        
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        change_amount = cash_received - total if cash_received and cash_received > total else 0
        
        cursor = self.connection.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            cursor.execute('''
                INSERT INTO transactions 
                (transaction_id, subtotal, tax_amount, discount_type, discount_amount, 
                 total_amount, payment_method, cash_received, change_amount, 
                 customer_name, cashier_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, subtotal, tax, discount_type, discount_amount, 
                  total, payment_method, cash_received, change_amount, 
                  customer_name, cashier))
            
            for item in items:
                cursor.execute('''
                    INSERT INTO transaction_items (transaction_id, product_id, product_name,
                                                   quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (transaction_id, item['id'], item['name'], 
                      item['quantity'], item['price'], item['total']))
                
                cursor.execute('''
                    UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND stock_quantity >= ?
                ''', (item['quantity'], item['id'], item['quantity']))
            
            # Update daily summary
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO daily_summary (date, total_sales, total_transactions, total_items_sold)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                total_sales = total_sales + ?,
                total_transactions = total_transactions + 1,
                total_items_sold = total_items_sold + ?
            ''', (today, total, 1, sum(item['quantity'] for item in items), total, sum(item['quantity'] for item in items)))
            
            self.connection.commit()
            return transaction_id
        except Exception as e:
            self.connection.rollback()
            print(f"Transaction error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_transaction(self, transaction_id: str):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM transactions WHERE transaction_id = ?', (transaction_id,))
        transaction = cursor.fetchone()
        
        if transaction:
            cursor.execute('SELECT * FROM transaction_items WHERE transaction_id = ?', (transaction_id,))
            items = [dict(row) for row in cursor.fetchall()]
            result = dict(transaction)
            result['items'] = items
            return result
        return None
    
    def get_todays_transactions(self):
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM transactions WHERE DATE(created_at) = ? ORDER BY created_at DESC', (today,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_transactions_by_date_range(self, start_date: str, end_date: str):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE DATE(created_at) BETWEEN ? AND ? 
            ORDER BY created_at DESC
        ''', (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    # Return Operations
    def process_return(self, transaction_id: str, product_id: int, quantity: int, reason: str, processed_by: str = "Default"):
        return_id = f"RET{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        cursor = self.connection.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            cursor.execute('''
                SELECT * FROM transaction_items 
                WHERE transaction_id = ? AND product_id = ?
            ''', (transaction_id, product_id))
            original_item = cursor.fetchone()
            
            if not original_item:
                return None
            
            refund_amount = original_item['unit_price'] * quantity
            
            cursor.execute('''
                INSERT INTO returns (return_id, original_transaction_id, product_id, 
                                   quantity, refund_amount, reason, processed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (return_id, transaction_id, product_id, quantity, refund_amount, reason, processed_by))
            
            cursor.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?', (quantity, product_id))
            cursor.execute('UPDATE transactions SET total_amount = total_amount - ? WHERE transaction_id = ?', (refund_amount, transaction_id))
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE daily_summary 
                SET total_returns = total_returns + ?, net_profit = total_sales - total_returns - total_expenses
                WHERE date = ?
            ''', (refund_amount, today))
            
            self.connection.commit()
            return return_id
        except Exception as e:
            self.connection.rollback()
            print(f"Return error: {e}")
            return None
    
    def get_all_returns(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT r.*, p.name as product_name 
            FROM returns r
            JOIN products p ON r.product_id = p.id
            ORDER BY r.created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    # Analytics
    def get_total_revenue(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT COALESCE(SUM(total_amount), 0) as total FROM transactions')
        return cursor.fetchone()['total']
    
    def get_total_items_sold(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT COALESCE(SUM(quantity), 0) as total FROM transaction_items')
        return cursor.fetchone()['total']
    
    def get_out_of_stock_items(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products WHERE stock_quantity = 0 ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_summary(self, date: str = None):
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM daily_summary WHERE date = ?', (date,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def add_expense(self, category: str, description: str, amount: float):
        expense_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO expenses (expense_id, category, description, amount)
            VALUES (?, ?, ?, ?)
        ''', (expense_id, category, description, amount))
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            UPDATE daily_summary 
            SET total_expenses = total_expenses + ?, net_profit = total_sales - total_returns - total_expenses
            WHERE date = ?
        ''', (amount, today))
        
        self.connection.commit()
        return expense_id
    
    def get_top_selling_products(self, limit: int = 10):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.category, SUM(ti.quantity) as total_sold, SUM(ti.total_price) as total_revenue
            FROM products p
            JOIN transaction_items ti ON p.id = ti.product_id
            GROUP BY p.id
            ORDER BY total_sold DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_product(self, product_id: int):
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        self.connection.commit()
        return cursor.rowcount > 0
    
    def close(self):
        if self.connection:
            self.connection.close()


# ==================== CUSTOM WIDGETS ====================

class ModernButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
            corner_radius=8,
            height=35
        )


class ModernCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLOR_PRIMARY,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_ACCENT
        )


# ==================== MAIN APPLICATION ====================

class GroceryStoreApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.minsize(1200, 600)
        self.root.configure(fg_color=COLOR_BACKGROUND)
        
        self.db = DatabaseManager()
        self.cart_items = []
        self.tax_enabled = True
        self.discount_type = "None"
        self.current_cashier = "Admin"
        
        self.create_default_placeholder()
        self.setup_ui()
        self.refresh_inventory()
        self.update_analytics()
        self.update_daily_summary()
    
    def create_default_placeholder(self):
        if not os.path.exists(DEFAULT_IMAGE_PATH):
            try:
                os.makedirs(os.path.dirname(DEFAULT_IMAGE_PATH), exist_ok=True)
                img = Image.new('RGB', (200, 200), color=COLOR_SECONDARY)
                draw = ImageDraw.Draw(img)
                draw.text((65, 90), 'No Image', fill=COLOR_TEXT)
                img.save(DEFAULT_IMAGE_PATH)
            except:
                pass
    
    def setup_ui(self):
        """Setup professional UI with two colors"""
        self.main_container = ctk.CTkFrame(self.root, fg_color=COLOR_BACKGROUND)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header = ctk.CTkFrame(self.main_container, height=60, fg_color=COLOR_PRIMARY, corner_radius=10)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(header, text="🛒 GROCERY STORE MANAGEMENT SYSTEM PRO", 
                            font=("Arial", 20, "bold"), text_color=COLOR_TEXT)
        title.pack(side="left", padx=20, pady=10)
        
        # Stats bar
        self.stats_frame = ctk.CTkFrame(header, fg_color=COLOR_SECONDARY, corner_radius=8)
        self.stats_frame.pack(side="right", padx=10, pady=5)
        
        self.today_sales_label = ctk.CTkLabel(self.stats_frame, text="Today: $0", font=("Arial", 12))
        self.today_sales_label.pack(side="left", padx=10)
        
        self.cashier_label = ctk.CTkLabel(self.stats_frame, text=f"👤 {self.current_cashier}", font=("Arial", 12))
        self.cashier_label.pack(side="left", padx=10)
        
        # Notebook
        self.notebook = ctk.CTkTabview(self.main_container, fg_color=COLOR_PRIMARY, segmented_button_fg_color=COLOR_SECONDARY)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.pos_tab = self.notebook.add("💳 POS Terminal")
        self.inventory_tab = self.notebook.add("📦 Inventory")
        self.returns_tab = self.notebook.add("🔄 Returns")
        self.analytics_tab = self.notebook.add("📊 Analytics")
        self.expenses_tab = self.notebook.add("💰 Expenses")
        
        self.setup_pos_tab()
        self.setup_inventory_tab()
        self.setup_returns_tab()
        self.setup_analytics_tab()
        self.setup_expenses_tab()
    
    def setup_pos_tab(self):
        """Professional POS Tab – FIXED CART LAYOUT"""
        # Left panel - Products
        left_panel = ModernCard(self.pos_tab)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Search and filters
        filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="🔍 Search:", text_color=COLOR_TEXT).pack(side="left", padx=5)
        self.pos_search_var = ctk.StringVar()
        self.pos_search_var.trace("w", lambda *args: self.filter_products())
        search_entry = ctk.CTkEntry(filter_frame, textvariable=self.pos_search_var, width=200, 
                                    fg_color=COLOR_SECONDARY, border_color=COLOR_ACCENT)
        search_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(filter_frame, text="📁 Category:", text_color=COLOR_TEXT).pack(side="left", padx=5)
        self.pos_category_var = ctk.StringVar(value="All")
        category_menu = ctk.CTkOptionMenu(filter_frame, values=CATEGORIES, variable=self.pos_category_var,
                                          fg_color=COLOR_SECONDARY, button_color=COLOR_ACCENT,
                                          command=lambda x: self.filter_products())
        category_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(filter_frame, text="💰 Price:", text_color=COLOR_TEXT).pack(side="left", padx=(20,5))
        self.min_price_var = ctk.StringVar(value="0")
        ctk.CTkEntry(filter_frame, textvariable=self.min_price_var, width=80, 
                    fg_color=COLOR_SECONDARY).pack(side="left", padx=2)
        ctk.CTkLabel(filter_frame, text="to", text_color=COLOR_TEXT).pack(side="left")
        self.max_price_var = ctk.StringVar(value="999999")
        ctk.CTkEntry(filter_frame, textvariable=self.max_price_var, width=80,
                    fg_color=COLOR_SECONDARY).pack(side="left", padx=2)
        
        ctk.CTkButton(filter_frame, text="Apply", width=60, command=self.filter_products,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_SECONDARY).pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="🔄 Reset", width=60, command=self.reset_filters,
                      fg_color=COLOR_SECONDARY, hover_color=COLOR_ACCENT).pack(side="left", padx=5)
        
        # Product grid
        self.product_grid_frame = ctk.CTkScrollableFrame(left_panel, fg_color=COLOR_PRIMARY)
        self.product_grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ---------- RIGHT PANEL (CART) – FIXED LAYOUT ----------
        right_panel = ModernCard(self.pos_tab)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # --- Top fixed area (header & barcode) ---
        top_area = ctk.CTkFrame(right_panel, fg_color="transparent")
        top_area.pack(fill="x")
        
        cart_header = ctk.CTkFrame(top_area, fg_color="transparent")
        cart_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(cart_header, text="🛒 SHOPPING CART", font=("Arial", 18, "bold"), 
                    text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(cart_header, text="Clear All", width=80, command=self.clear_cart,
                     fg_color=COLOR_ERROR, hover_color=COLOR_SECONDARY).pack(side="right")
        
        barcode_frame = ctk.CTkFrame(top_area, fg_color="transparent")
        barcode_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(barcode_frame, text="📷 Scan Barcode:", text_color=COLOR_TEXT).pack(side="left", padx=5)
        self.barcode_var = ctk.StringVar()
        self.barcode_var.trace("w", self.barcode_scanned)
        barcode_entry = ctk.CTkEntry(barcode_frame, textvariable=self.barcode_var, width=150,
                                    fg_color=COLOR_SECONDARY)
        barcode_entry.pack(side="left", padx=5)
        barcode_entry.bind('<Return>', lambda e: self.add_by_barcode())
        
        # --- Scrollable cart area (takes all remaining vertical space) ---
        self.cart_frame = ctk.CTkScrollableFrame(right_panel, fg_color=COLOR_PRIMARY)
        self.cart_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- Bottom fixed area (customer, discount, totals, payment, buttons) ---
        bottom_area = ctk.CTkFrame(right_panel, fg_color="transparent")
        bottom_area.pack(fill="x", side="bottom")
        
        # Customer info
        customer_frame = ctk.CTkFrame(bottom_area, fg_color="transparent")
        customer_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(customer_frame, text="👤 Customer Name:", text_color=COLOR_TEXT).pack(side="left")
        self.customer_name_var = ctk.StringVar()
        ctk.CTkEntry(customer_frame, textvariable=self.customer_name_var, width=150,
                    fg_color=COLOR_SECONDARY).pack(side="left", padx=5)
        
        # Discount and Tax
        discount_frame = ctk.CTkFrame(bottom_area, fg_color="transparent")
        discount_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(discount_frame, text="🎫 Discount:", text_color=COLOR_TEXT).pack(side="left")
        self.discount_var = ctk.StringVar(value="None")
        discount_menu = ctk.CTkOptionMenu(discount_frame, values=list(DISCOUNT_RATES.keys()),
                                         variable=self.discount_var, command=self.update_discount,
                                         fg_color=COLOR_SECONDARY, button_color=COLOR_ACCENT)
        discount_menu.pack(side="left", padx=5)
        self.tax_var = ctk.BooleanVar(value=True)
        tax_check = ctk.CTkCheckBox(discount_frame, text="Tax (10%)", variable=self.tax_var,
                                   command=self.update_cart_totals,
                                   fg_color=COLOR_ACCENT, hover_color=COLOR_SECONDARY)
        tax_check.pack(side="left", padx=20)
        
        # Totals
        totals_frame = ModernCard(bottom_area)
        totals_frame.pack(fill="x", padx=10, pady=5)
        self.subtotal_label = ctk.CTkLabel(totals_frame, text="Subtotal: $0.00", font=("Arial", 14))
        self.subtotal_label.pack(pady=2)
        self.discount_label = ctk.CTkLabel(totals_frame, text="Discount: $0.00", font=("Arial", 14))
        self.discount_label.pack(pady=2)
        self.tax_label = ctk.CTkLabel(totals_frame, text="Tax: $0.00", font=("Arial", 14))
        self.tax_label.pack(pady=2)
        self.total_label = ctk.CTkLabel(totals_frame, text="TOTAL: $0.00", font=("Arial", 18, "bold"),
                                        text_color=COLOR_WARNING)
        self.total_label.pack(pady=5)
        
        # Payment
        payment_frame = ctk.CTkFrame(bottom_area, fg_color="transparent")
        payment_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(payment_frame, text="💵 Payment:", text_color=COLOR_TEXT).pack(side="left")
        self.payment_method_var = ctk.StringVar(value="cash")
        payment_menu = ctk.CTkOptionMenu(payment_frame, values=["cash", "card", "mobile"],
                                        variable=self.payment_method_var,
                                        fg_color=COLOR_SECONDARY, button_color=COLOR_ACCENT)
        payment_menu.pack(side="left", padx=5)
        ctk.CTkLabel(payment_frame, text="Amount Received:", text_color=COLOR_TEXT).pack(side="left", padx=10)
        self.cash_received_var = ctk.StringVar()
        cash_entry = ctk.CTkEntry(payment_frame, textvariable=self.cash_received_var, width=100,
                                 fg_color=COLOR_SECONDARY)
        cash_entry.pack(side="left", padx=5)
        
        # Action buttons
        button_frame = ctk.CTkFrame(bottom_area, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        checkout_btn = ModernButton(button_frame, text="✅ CHECKOUT", command=self.checkout, height=45)
        checkout_btn.pack(fill="x", pady=5)
        hold_btn = ModernButton(button_frame, text="⏸️ Hold Order", command=self.hold_order, height=35)
        hold_btn.pack(fill="x", pady=5)
    
    def setup_inventory_tab(self):
        """Professional Inventory Tab"""
        control_panel = ctk.CTkFrame(self.inventory_tab, fg_color="transparent")
        control_panel.pack(fill="x", padx=10, pady=10)
        
        buttons = [
            ("➕ Add Product", self.add_product_dialog, COLOR_SUCCESS),
            ("✏️ Edit Selected", self.edit_selected_product, COLOR_ACCENT),
            ("🗑️ Delete Selected", self.delete_selected_product, COLOR_ERROR),
            ("📊 Bulk Import", self.bulk_import, COLOR_SECONDARY),
            ("📤 Export CSV", self.export_inventory, COLOR_SECONDARY),
            ("💾 Backup DB", self.backup_database, COLOR_ACCENT),
            ("🔄 Refresh", self.refresh_inventory, COLOR_ACCENT)
        ]
        
        for text, command, color in buttons:
            btn = ctk.CTkButton(control_panel, text=text, command=command,
                               fg_color=color, hover_color=COLOR_SECONDARY,
                               corner_radius=8, height=35)
            btn.pack(side="left", padx=5)
        
        search_frame = ctk.CTkFrame(control_panel, fg_color="transparent")
        search_frame.pack(side="right", padx=5)
        ctk.CTkLabel(search_frame, text="🔍 Search:", text_color=COLOR_TEXT).pack(side="left")
        self.inv_search_var = ctk.StringVar()
        self.inv_search_var.trace("w", lambda *args: self.refresh_inventory())
        ctk.CTkEntry(search_frame, textvariable=self.inv_search_var, width=200,
                    fg_color=COLOR_SECONDARY).pack(side="left", padx=5)
        
        # Inventory table
        self.inventory_table_frame = ctk.CTkScrollableFrame(self.inventory_tab, fg_color=COLOR_PRIMARY)
        self.inventory_table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Headers
        headers = ["Select", "ID", "Name", "Category", "Price", "Stock", "Unit", "Min Stock", "Location", "Actions"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(self.inventory_table_frame, text=header, font=("Arial", 12, "bold"),
                        text_color=COLOR_TEXT, width=100).grid(row=0, column=i, padx=5, pady=5)
        
        self.selected_products = {}
    
    def setup_returns_tab(self):
        """Professional Returns Tab"""
        # Lookup section
        lookup_card = ModernCard(self.returns_tab)
        lookup_card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(lookup_card, text="🔍 FIND TRANSACTION", font=("Arial", 14, "bold")).pack(pady=5)
        
        txn_frame = ctk.CTkFrame(lookup_card, fg_color="transparent")
        txn_frame.pack(pady=5)
        ctk.CTkLabel(txn_frame, text="Transaction ID:").pack(side="left", padx=5)
        self.return_txn_var = ctk.StringVar()
        ctk.CTkEntry(txn_frame, textvariable=self.return_txn_var, width=250,
                    fg_color=COLOR_SECONDARY).pack(side="left", padx=5)
        ctk.CTkButton(txn_frame, text="Search", command=self.lookup_transaction,
                     fg_color=COLOR_ACCENT).pack(side="left", padx=5)
        
        # Also search by date
        date_frame = ctk.CTkFrame(lookup_card, fg_color="transparent")
        date_frame.pack(pady=5)
        ctk.CTkLabel(date_frame, text="Or search by date:").pack(side="left", padx=5)
        self.return_date_var = ctk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ctk.CTkEntry(date_frame, textvariable=self.return_date_var, width=120,
                    fg_color=COLOR_SECONDARY).pack(side="left", padx=5)
        ctk.CTkButton(date_frame, text="Show Today's Transactions", command=self.show_daily_transactions,
                     fg_color=COLOR_SUCCESS).pack(side="left", padx=5)
        
        # Transaction details
        self.transaction_details_frame = ctk.CTkScrollableFrame(self.returns_tab, fg_color=COLOR_PRIMARY, height=250)
        self.transaction_details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Returns history
        history_card = ModernCard(self.returns_tab)
        history_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(history_card, text="📜 RETURNS HISTORY", font=("Arial", 14, "bold")).pack(pady=5)
        self.returns_history_frame = ctk.CTkScrollableFrame(history_card, fg_color=COLOR_PRIMARY, height=150)
        self.returns_history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_returns_history()
    
    def setup_analytics_tab(self):
        """Professional Analytics Tab with charts"""
        # Summary cards
        summary_frame = ctk.CTkFrame(self.analytics_tab, fg_color="transparent")
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        cards = [
            ("💰 TOTAL REVENUE", "revenue_label", "$0"),
            ("📦 ITEMS SOLD", "items_label", "0"),
            ("📊 TODAY'S SALES", "today_label", "$0"),
            ("🔄 TOTAL RETURNS", "returns_label", "$0")
        ]
        
        for title, attr, default in cards:
            card = ModernCard(summary_frame)
            card.pack(side="left", expand=True, fill="both", padx=5, pady=5)
            ctk.CTkLabel(card, text=title, font=("Arial", 12), text_color=COLOR_ACCENT).pack(pady=(10,0))
            setattr(self, attr, ctk.CTkLabel(card, text=default, font=("Arial", 24, "bold")))
            getattr(self, attr).pack(pady=10)
        
        # Top products
        top_products_frame = ModernCard(self.analytics_tab)
        top_products_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(top_products_frame, text="🏆 TOP SELLING PRODUCTS", font=("Arial", 14, "bold")).pack(pady=5)
        self.top_products_frame = ctk.CTkScrollableFrame(top_products_frame, fg_color=COLOR_PRIMARY, height=200)
        self.top_products_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Low stock alert
        low_stock_frame = ModernCard(self.analytics_tab)
        low_stock_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(low_stock_frame, text="⚠️ LOW STOCK ALERT", font=("Arial", 14, "bold"), 
                    text_color=COLOR_WARNING).pack(pady=5)
        self.low_stock_frame = ctk.CTkScrollableFrame(low_stock_frame, fg_color=COLOR_PRIMARY, height=150)
        self.low_stock_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def setup_expenses_tab(self):
        """Expenses Tracking Tab"""
        add_card = ModernCard(self.expenses_tab)
        add_card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(add_card, text="➕ ADD EXPENSE", font=("Arial", 14, "bold")).pack(pady=5)
        
        form_frame = ctk.CTkFrame(add_card, fg_color="transparent")
        form_frame.pack(pady=10)
        
        ctk.CTkLabel(form_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        self.exp_category_var = ctk.CTkOptionMenu(form_frame, values=["Rent", "Utilities", "Salary", "Maintenance", "Supplies", "Other"],
                                                  fg_color=COLOR_SECONDARY)
        self.exp_category_var.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Description:").grid(row=0, column=2, padx=5, pady=5)
        self.exp_desc_entry = ctk.CTkEntry(form_frame, width=200, fg_color=COLOR_SECONDARY)
        self.exp_desc_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Amount ($):").grid(row=0, column=4, padx=5, pady=5)
        self.exp_amount_entry = ctk.CTkEntry(form_frame, width=100, fg_color=COLOR_SECONDARY)
        self.exp_amount_entry.grid(row=0, column=5, padx=5, pady=5)
        
        ctk.CTkButton(form_frame, text="Add Expense", command=self.add_expense,
                     fg_color=COLOR_SUCCESS).grid(row=0, column=6, padx=10, pady=5)
        
        expenses_card = ModernCard(self.expenses_tab)
        expenses_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(expenses_card, text="📋 EXPENSES HISTORY", font=("Arial", 14, "bold")).pack(pady=5)
        self.expenses_list_frame = ctk.CTkScrollableFrame(expenses_card, fg_color=COLOR_PRIMARY, height=300)
        self.expenses_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_expenses()
    
    # ==================== POS FUNCTIONS ====================
    
    def filter_products(self):
        search_term = self.pos_search_var.get().strip()
        category = self.pos_category_var.get()
        
        try:
            min_price = float(self.min_price_var.get() or 0)
            max_price = float(self.max_price_var.get() or 999999)
        except:
            min_price, max_price = 0, 999999
        
        products = self.db.search_products(search_term, category, min_price, max_price)
        self.display_product_grid(products)
    
    def reset_filters(self):
        self.pos_search_var.set("")
        self.pos_category_var.set("All")
        self.min_price_var.set("0")
        self.max_price_var.set("999999")
        self.filter_products()
    
    def display_product_grid(self, products: List[Dict]):
        for widget in self.product_grid_frame.winfo_children():
            widget.destroy()
        
        row, col = 0, 0
        max_cols = 4
        
        for product in products:
            card = ModernCard(self.product_grid_frame)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Image
            self.display_product_image(card, product)
            
            # Info
            ctk.CTkLabel(card, text=product['name'][:25], font=("Arial", 12, "bold")).pack(pady=(5,0))
            ctk.CTkLabel(card, text=f"${product['price']:.2f}", font=("Arial", 14), 
                        text_color=COLOR_SUCCESS).pack()
            
            stock_color = COLOR_WARNING if product['stock_quantity'] < product.get('min_stock', 5) else COLOR_TEXT
            ctk.CTkLabel(card, text=f"Stock: {product['stock_quantity']} {product['unit']}",
                        font=("Arial", 10), text_color=stock_color).pack()
            
            # Quantity selector
            qty_frame = ctk.CTkFrame(card, fg_color="transparent")
            qty_frame.pack(pady=5)
            qty_var = ctk.StringVar(value="1")
            ctk.CTkEntry(qty_frame, textvariable=qty_var, width=50,
                        fg_color=COLOR_SECONDARY).pack(side="left", padx=2)
            ctk.CTkButton(qty_frame, text="Add", width=60,
                         command=lambda p=product, q=qty_var: self.add_to_cart(p, int(q.get())),
                         fg_color=COLOR_ACCENT).pack(side="left", padx=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        for i in range(max_cols):
            self.product_grid_frame.grid_columnconfigure(i, weight=1)
    
    def display_product_image(self, parent, product: Dict):
        image_path = product.get('image_path')
        
        if image_path and os.path.exists(image_path):
            try:
                pil_image = Image.open(image_path)
                pil_image = pil_image.resize((100, 100), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
                img_label = ctk.CTkLabel(parent, image=photo, text="")
                img_label.image = photo
                img_label.pack(pady=5)
                return
            except:
                pass
        
        # Placeholder
        if os.path.exists(DEFAULT_IMAGE_PATH):
            try:
                pil_image = Image.open(DEFAULT_IMAGE_PATH)
                pil_image = pil_image.resize((100, 100), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
                img_label = ctk.CTkLabel(parent, image=photo, text="")
                img_label.image = photo
                img_label.pack(pady=5)
            except:
                ctk.CTkLabel(parent, text="📷", width=100, height=100,
                            fg_color=COLOR_SECONDARY, font=("Arial", 30)).pack(pady=5)
        else:
            ctk.CTkLabel(parent, text="📷", width=100, height=100,
                        fg_color=COLOR_SECONDARY, font=("Arial", 30)).pack(pady=5)
    
    def add_to_cart(self, product: Dict, quantity: int = 1):
        if product['stock_quantity'] < quantity:
            messagebox.showerror("Error", f"Only {product['stock_quantity']} {product['unit']} available!")
            return
        
        for item in self.cart_items:
            if item['id'] == product['id']:
                if item['quantity'] + quantity > product['stock_quantity']:
                    messagebox.showerror("Error", "Not enough stock!")
                    return
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['price']
                self.update_cart_display()
                return
        
        self.cart_items.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'total': product['price'] * quantity
        })
        self.update_cart_display()
    
    def add_by_barcode(self):
        barcode = self.barcode_var.get().strip()
        if barcode:
            product = self.db.get_product_by_barcode(barcode)
            if product:
                self.add_to_cart(product, 1)
                self.barcode_var.set("")
            else:
                messagebox.showerror("Error", "Product not found!")
    
    def barcode_scanned(self, *args):
        if len(self.barcode_var.get()) > 5:
            self.add_by_barcode()
    
    def update_cart_display(self):
        for widget in self.cart_frame.winfo_children():
            widget.destroy()
        
        if not self.cart_items:
            ctk.CTkLabel(self.cart_frame, text="Cart is empty", text_color=COLOR_ACCENT).pack(pady=20)
            self.update_cart_totals()
            return
        
        for i, item in enumerate(self.cart_items):
            item_frame = ctk.CTkFrame(self.cart_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            item_frame.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(item_frame, text=item['name'][:20], width=120, anchor="w").pack(side="left", padx=5)
            
            qty_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            qty_frame.pack(side="left", padx=10)
            
            ctk.CTkButton(qty_frame, text="-", width=25, command=lambda idx=i: self.update_quantity(idx, -1),
                         fg_color=COLOR_ERROR).pack(side="left")
            ctk.CTkLabel(qty_frame, text=str(item['quantity']), width=30).pack(side="left")
            ctk.CTkButton(qty_frame, text="+", width=25, command=lambda idx=i: self.update_quantity(idx, 1),
                         fg_color=COLOR_SUCCESS).pack(side="left")
            
            ctk.CTkLabel(item_frame, text=f"${item['total']:.2f}", width=80).pack(side="left", padx=5)
            ctk.CTkButton(item_frame, text="✕", width=30, command=lambda idx=i: self.remove_from_cart(idx),
                         fg_color=COLOR_ERROR).pack(side="right", padx=5)
        
        self.update_cart_totals()
    
    def update_quantity(self, index: int, delta: int):
        new_qty = self.cart_items[index]['quantity'] + delta
        
        if new_qty <= 0:
            self.remove_from_cart(index)
        else:
            product = self.db.get_product_by_id(self.cart_items[index]['id'])
            if product and new_qty > product['stock_quantity']:
                messagebox.showerror("Error", "Not enough stock!")
                return
            
            self.cart_items[index]['quantity'] = new_qty
            self.cart_items[index]['total'] = new_qty * self.cart_items[index]['price']
            self.update_cart_display()
    
    def remove_from_cart(self, index: int):
        self.cart_items.pop(index)
        self.update_cart_display()
    
    def update_discount(self, *args):
        self.discount_type = self.discount_var.get()
        self.update_cart_totals()
    
    def update_cart_totals(self):
        subtotal = sum(item['total'] for item in self.cart_items)
        
        discount_rate = DISCOUNT_RATES.get(self.discount_type, 0)
        discount_amount = subtotal * discount_rate
        after_discount = subtotal - discount_amount
        
        tax = after_discount * TAX_RATE if self.tax_var.get() else 0
        total = after_discount + tax
        
        self.subtotal_label.configure(text=f"Subtotal: ${subtotal:.2f}")
        self.discount_label.configure(text=f"Discount: -${discount_amount:.2f}")
        self.tax_label.configure(text=f"Tax: ${tax:.2f}")
        self.total_label.configure(text=f"TOTAL: ${total:.2f}")
    
    def checkout(self):
        if not self.cart_items:
            messagebox.showwarning("Warning", "Cart is empty!")
            return
        
        subtotal = sum(item['total'] for item in self.cart_items)
        discount_amount = subtotal * DISCOUNT_RATES.get(self.discount_type, 0)
        after_discount = subtotal - discount_amount
        tax = after_discount * TAX_RATE if self.tax_var.get() else 0
        total = after_discount + tax
        
        payment_method = self.payment_method_var.get()
        cash_received = None
        change = 0
        
        if payment_method == "cash":
            try:
                cash_received = float(self.cash_received_var.get() or 0)
                if cash_received < total:
                    messagebox.showerror("Error", f"Insufficient cash! Need ${total:.2f}")
                    return
                change = cash_received - total
                if change > 0:
                    messagebox.showinfo("Change", f"Change: ${change:.2f}")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid cash amount")
                return
        
        if not messagebox.askyesno("Confirm Checkout", 
                                  f"Subtotal: ${subtotal:.2f}\nDiscount: -${discount_amount:.2f}\nTax: ${tax:.2f}\nTotal: ${total:.2f}\n\nProceed?"):
            return
        
        transaction_id = self.db.create_transaction(
            self.cart_items, subtotal, tax, self.discount_type, discount_amount, total,
            payment_method, cash_received, self.customer_name_var.get(),
            self.current_cashier
        )
        
        if transaction_id:
            self.generate_receipt(transaction_id)
            msg = f"Transaction Complete!\nID: {transaction_id}"
            if change > 0:
                msg += f"\nChange: ${change:.2f}"
            messagebox.showinfo("Success", msg)
            self.clear_cart()
            self.refresh_inventory()
            self.update_analytics()
            self.filter_products()
            self.update_daily_summary()
        else:
            messagebox.showerror("Error", "Transaction failed!\nSee console for details.")
    
    def hold_order(self):
        if self.cart_items:
            hold_data = {
                'items': self.cart_items,
                'customer': self.customer_name_var.get(),
                'timestamp': datetime.now().isoformat()
            }
            hold_file = os.path.join(BACKUP_DIR, f"hold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(hold_file, 'w') as f:
                json.dump(hold_data, f)
            messagebox.showinfo("Success", "Order held successfully!")
            self.clear_cart()
    
    def generate_receipt(self, transaction_id: str):
        receipt_path = os.path.join(RECEIPTS_DIR, f"{transaction_id}.txt")
        
        with open(receipt_path, 'w') as f:
            f.write("="*50 + "\n")
            f.write("GROCERY STORE\n")
            f.write("="*50 + "\n")
            f.write(f"Transaction: {transaction_id}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Cashier: {self.current_cashier}\n")
            if self.customer_name_var.get():
                f.write(f"Customer: {self.customer_name_var.get()}\n")
            f.write("-"*50 + "\n")
            f.write(f"{'Item':<20} {'Qty':<5} {'Price':<8} {'Total':<10}\n")
            f.write("-"*50 + "\n")
            
            for item in self.cart_items:
                f.write(f"{item['name'][:20]:<20} {item['quantity']:<5} ${item['price']:<7.2f} ${item['total']:<9.2f}\n")
            
            subtotal = sum(item['total'] for item in self.cart_items)
            discount_amount = subtotal * DISCOUNT_RATES.get(self.discount_type, 0)
            after_discount = subtotal - discount_amount
            tax = after_discount * TAX_RATE if self.tax_var.get() else 0
            total = after_discount + tax
            
            f.write("-"*50 + "\n")
            f.write(f"{'Subtotal:':>30} ${subtotal:>8.2f}\n")
            if discount_amount > 0:
                f.write(f"{'Discount:':>30} -${discount_amount:>7.2f}\n")
            if tax > 0:
                f.write(f"{'Tax:':>30} ${tax:>8.2f}\n")
            f.write(f"{'TOTAL:':>30} ${total:>8.2f}\n")
            f.write("="*50 + "\n")
            f.write("Thank you for shopping with us!\n")
    
    def clear_cart(self):
        self.cart_items = []
        self.customer_name_var.set("")
        self.cash_received_var.set("")
        self.discount_var.set("None")
        self.update_cart_display()
    
    # ==================== INVENTORY FUNCTIONS ====================
    
    def refresh_inventory(self):
        search_term = self.inv_search_var.get().strip()
        products = self.db.search_products(search_term) if search_term else self.db.get_all_products()
        
        for widget in self.inventory_table_frame.winfo_children():
            if int(widget.grid_info().get('row', 0)) > 0:
                widget.destroy()
        
        for i, product in enumerate(products, start=1):
            var = ctk.BooleanVar()
            self.selected_products[product['id']] = var
            cb = ctk.CTkCheckBox(self.inventory_table_frame, variable=var, width=20,
                                 fg_color=COLOR_ACCENT)
            cb.grid(row=i, column=0, padx=5, pady=2)
            
            ctk.CTkLabel(self.inventory_table_frame, text=str(product['id']), width=50).grid(row=i, column=1, padx=5, pady=2)
            ctk.CTkLabel(self.inventory_table_frame, text=product['name'][:25], width=120, anchor="w").grid(row=i, column=2, padx=5, pady=2)
            ctk.CTkLabel(self.inventory_table_frame, text=product['category'], width=100).grid(row=i, column=3, padx=5, pady=2)
            ctk.CTkLabel(self.inventory_table_frame, text=f"${product['price']:.2f}", width=70).grid(row=i, column=4, padx=5, pady=2)
            
            stock_color = COLOR_WARNING if product['stock_quantity'] < product.get('min_stock', 5) else COLOR_TEXT
            ctk.CTkLabel(self.inventory_table_frame, text=str(product['stock_quantity']), width=60, text_color=stock_color).grid(row=i, column=5, padx=5, pady=2)
            ctk.CTkLabel(self.inventory_table_frame, text=product['unit'], width=60).grid(row=i, column=6, padx=5, pady=2)
            ctk.CTkLabel(self.inventory_table_frame, text=str(product.get('min_stock', 5)), width=60).grid(row=i, column=7, padx=5, pady=2)
            location_text = product.get('location') or ''
            ctk.CTkLabel(self.inventory_table_frame, text=location_text[:15], width=80).grid(row=i, column=8, padx=5, pady=2)
            
            actions = ctk.CTkFrame(self.inventory_table_frame, fg_color="transparent")
            actions.grid(row=i, column=9, padx=5, pady=2)
            ctk.CTkButton(actions, text="Edit", width=50, command=lambda p=product: self.edit_product_dialog(p),
                         fg_color=COLOR_ACCENT).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="Delete", width=50, command=lambda pid=product['id']: self.delete_product(pid),
                         fg_color=COLOR_ERROR).pack(side="left", padx=2)
    
    def edit_selected_product(self):
        selected = [pid for pid, var in self.selected_products.items() if var.get()]
        if len(selected) != 1:
            messagebox.showwarning("Warning", "Please select exactly one product to edit!")
            return
        product = self.db.get_product_by_id(selected[0])
        if product:
            self.edit_product_dialog(product)
    
    def delete_selected_product(self):
        selected = [pid for pid, var in self.selected_products.items() if var.get()]
        if not selected:
            messagebox.showwarning("Warning", "Please select products to delete!")
            return
        if messagebox.askyesno("Confirm", f"Delete {len(selected)} product(s)?"):
            for pid in selected:
                self.db.delete_product(pid)
            self.refresh_inventory()
            self.filter_products()
    
    def add_product_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Product")
        dialog.geometry("600x700")
        dialog.grab_set()
        dialog.configure(fg_color=COLOR_BACKGROUND)
        
        fields = {}
        labels = ["Product Name:*", "Barcode:", "Category:*", "Price:*", "Cost Price:", 
                  "Stock:*", "Unit:*", "Min Stock:", "Location:", "Supplier:"]
        
        for i, label in enumerate(labels):
            ctk.CTkLabel(dialog, text=label, text_color=COLOR_TEXT).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            if label in ["Category:*", "Unit:*"]:
                entry = None
            else:
                entry = ctk.CTkEntry(dialog, width=250, fg_color=COLOR_SECONDARY)
                entry.grid(row=i, column=1, padx=10, pady=5)
            fields[label] = entry
        
        category_menu = ctk.CTkOptionMenu(dialog, values=CATEGORIES[1:], fg_color=COLOR_SECONDARY)
        category_menu.grid(row=2, column=1, padx=10, pady=5)
        fields["Category:*"] = category_menu
        
        unit_menu = ctk.CTkOptionMenu(dialog, values=UNITS, fg_color=COLOR_SECONDARY)
        unit_menu.grid(row=6, column=1, padx=10, pady=5)
        fields["Unit:*"] = unit_menu
        
        image_path_var = ctk.StringVar()
        ctk.CTkButton(dialog, text="Select Image", command=lambda: self.select_image(image_path_var, dialog),
                     fg_color=COLOR_ACCENT).grid(row=10, column=0, columnspan=2, pady=10)
        
        def save():
            try:
                name = fields["Product Name:*"].get().strip()
                if not name:
                    messagebox.showerror("Error", "Product name required!")
                    return
                product_id = self.db.add_product(
                    name=name,
                    barcode=fields["Barcode:"].get().strip() or None,
                    category=fields["Category:*"].get(),
                    price=float(fields["Price:*"].get()),
                    stock=int(fields["Stock:*"].get()),
                    unit=fields["Unit:*"].get(),
                    cost_price=float(fields["Cost Price:"].get()) if fields["Cost Price:"].get() else None,
                    min_stock=int(fields["Min Stock:"].get()) if fields["Min Stock:"].get() else 5,
                    location=fields["Location:"].get(),
                    supplier=fields["Supplier:"].get(),
                    image_path=image_path_var.get() or None
                )
                if product_id:
                    messagebox.showinfo("Success", "Product added!")
                    dialog.destroy()
                    self.refresh_inventory()
                    self.filter_products()
                else:
                    messagebox.showerror("Error", "Failed to add product!")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        ctk.CTkButton(dialog, text="Save Product", command=save, fg_color=COLOR_SUCCESS, height=40).grid(row=11, column=0, columnspan=2, pady=20)
    
    def edit_product_dialog(self, product: Dict):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Edit Product - {product['name']}")
        dialog.geometry("600x700")
        dialog.grab_set()
        
        fields = {}
        labels = ["Product Name:", "Barcode:", "Category:", "Price:", "Cost Price:", 
                  "Stock:", "Unit:", "Min Stock:", "Location:", "Supplier:"]
        
        current_values = [
            product['name'], product.get('barcode', ''), product['category'],
            str(product['price']), str(product.get('cost_price', '')),
            str(product['stock_quantity']), product['unit'], str(product.get('min_stock', 5)),
            product.get('location', ''), product.get('supplier', '')
        ]
        
        for i, (label, value) in enumerate(zip(labels, current_values)):
            ctk.CTkLabel(dialog, text=label, text_color=COLOR_TEXT).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            if label in ["Category:", "Unit:"]:
                widget = None
            else:
                widget = ctk.CTkEntry(dialog, width=250, fg_color=COLOR_SECONDARY)
                widget.grid(row=i, column=1, padx=10, pady=5)
                widget.insert(0, value)
            fields[label] = widget
        
        category_menu = ctk.CTkOptionMenu(dialog, values=CATEGORIES[1:], fg_color=COLOR_SECONDARY)
        category_menu.set(product['category'])
        category_menu.grid(row=2, column=1, padx=10, pady=5)
        fields["Category:"] = category_menu
        
        unit_menu = ctk.CTkOptionMenu(dialog, values=UNITS, fg_color=COLOR_SECONDARY)
        unit_menu.set(product['unit'])
        unit_menu.grid(row=6, column=1, padx=10, pady=5)
        fields["Unit:"] = unit_menu
        
        def save():
            try:
                updates = {
                    'name': fields["Product Name:"].get().strip(),
                    'barcode': fields["Barcode:"].get().strip() or None,
                    'category': fields["Category:"].get(),
                    'price': float(fields["Price:"].get()),
                    'stock_quantity': int(fields["Stock:"].get()),
                    'unit': fields["Unit:"].get(),
                    'cost_price': float(fields["Cost Price:"].get()) if fields["Cost Price:"].get() else None,
                    'min_stock': int(fields["Min Stock:"].get()) if fields["Min Stock:"].get() else 5,
                    'location': fields["Location:"].get(),
                    'supplier': fields["Supplier:"].get()
                }
                if self.db.update_product(product['id'], **updates):
                    messagebox.showinfo("Success", "Product updated!")
                    dialog.destroy()
                    self.refresh_inventory()
                    self.filter_products()
                else:
                    messagebox.showerror("Error", "Failed to update!")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        ctk.CTkButton(dialog, text="Save Changes", command=save, fg_color=COLOR_SUCCESS, height=40).grid(row=10, column=0, columnspan=2, pady=20)
    
    def delete_product(self, product_id: int):
        if messagebox.askyesno("Confirm", "Delete this product?"):
            if self.db.delete_product(product_id):
                self.refresh_inventory()
                self.filter_products()
    
    def bulk_import(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            messagebox.showinfo("Info", "CSV import feature - Add your CSV parsing logic here")
    
    def export_inventory(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            products = self.db.get_all_products()
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if products:
                    writer = csv.DictWriter(f, fieldnames=products[0].keys())
                    writer.writeheader()
                    writer.writerows(products)
            messagebox.showinfo("Success", f"Exported {len(products)} products!")
    
    def backup_database(self):
        backup_path = self.db.backup_database()
        if backup_path:
            messagebox.showinfo("Success", f"Backup created:\n{backup_path}")
    
    def select_image(self, path_var, parent):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(IMAGES_DIR, filename)
            shutil.copy(file_path, dest_path)
            path_var.set(dest_path)
            messagebox.showinfo("Success", "Image selected!")
    
    # ==================== RETURNS FUNCTIONS ====================
    
    def lookup_transaction(self):
        transaction_id = self.return_txn_var.get().strip()
        if not transaction_id:
            messagebox.showwarning("Warning", "Enter Transaction ID!")
            return
        transaction = self.db.get_transaction(transaction_id)
        if not transaction:
            messagebox.showerror("Error", "Transaction not found!")
            return
        self.display_transaction_for_return(transaction)
    
    def show_daily_transactions(self):
        date = self.return_date_var.get()
        transactions = self.db.get_transactions_by_date_range(date, date)
        for widget in self.transaction_details_frame.winfo_children():
            widget.destroy()
        if not transactions:
            ctk.CTkLabel(self.transaction_details_frame, text="No transactions found for this date.",
                        text_color=COLOR_WARNING).pack(pady=20)
            return
        for txn in transactions:
            txn_card = ModernCard(self.transaction_details_frame)
            txn_card.pack(fill="x", pady=5)
            ctk.CTkLabel(txn_card, text=f"📄 {txn['transaction_id']}", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(txn_card, text=f"Amount: ${txn['total_amount']:.2f} | Date: {txn['created_at']}",
                        text_color=COLOR_ACCENT).pack(anchor="w", padx=10)
            ctk.CTkButton(txn_card, text="View & Return", command=lambda tid=txn['transaction_id']: self.view_transaction_for_return(tid),
                         fg_color=COLOR_ACCENT).pack(anchor="e", padx=10, pady=5)
    
    def view_transaction_for_return(self, transaction_id: str):
        transaction = self.db.get_transaction(transaction_id)
        if transaction:
            self.display_transaction_for_return(transaction)
    
    def display_transaction_for_return(self, transaction):
        for widget in self.transaction_details_frame.winfo_children():
            widget.destroy()
        header = ModernCard(self.transaction_details_frame)
        header.pack(fill="x", pady=5)
        ctk.CTkLabel(header, text=f"Transaction: {transaction['transaction_id']}", 
                    font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(header, text=f"Date: {transaction['created_at']} | Total: ${transaction['total_amount']:.2f}",
                    text_color=COLOR_ACCENT).pack(anchor="w", padx=10)
        items_card = ModernCard(self.transaction_details_frame)
        items_card.pack(fill="x", pady=5)
        ctk.CTkLabel(items_card, text="Items:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        for item in transaction['items']:
            item_frame = ctk.CTkFrame(items_card, fg_color=COLOR_SECONDARY, corner_radius=8)
            item_frame.pack(fill="x", pady=2, padx=10)
            ctk.CTkLabel(item_frame, text=f"{item['product_name']} - Qty: {item['quantity']} - ${item['unit_price']:.2f}",
                        width=300, anchor="w").pack(side="left", padx=5)
            qty_var = ctk.StringVar(value="1")
            qty_entry = ctk.CTkEntry(item_frame, textvariable=qty_var, width=50, fg_color=COLOR_PRIMARY)
            qty_entry.pack(side="left", padx=5)
            reason_entry = ctk.CTkEntry(item_frame, placeholder_text="Reason", width=150, fg_color=COLOR_PRIMARY)
            reason_entry.pack(side="left", padx=5)
            ctk.CTkButton(item_frame, text="Return", command=lambda pid=item['product_id'], qty_var=qty_var,
                         reason=reason_entry, tid=transaction['transaction_id'], max_qty=item['quantity']:
                         self.process_return(tid, pid, qty_var.get(), reason.get(), max_qty),
                         fg_color=COLOR_WARNING).pack(side="right", padx=5)
    
    def process_return(self, transaction_id: str, product_id: int, quantity_str: str, reason: str, max_qty: int):
        try:
            quantity = int(quantity_str)
            if quantity <= 0 or quantity > max_qty:
                messagebox.showerror("Error", f"Invalid quantity! Max: {max_qty}")
                return
            product = self.db.get_product_by_id(product_id)
            refund = product['price'] * quantity
            if messagebox.askyesno("Confirm Return", f"Return {quantity} x {product['name']}?\nRefund: ${refund:.2f}"):
                return_id = self.db.process_return(transaction_id, product_id, quantity, reason, self.current_cashier)
                if return_id:
                    messagebox.showinfo("Success", f"Return processed!\nID: {return_id}")
                    self.load_returns_history()
                    self.refresh_inventory()
                    self.update_analytics()
                    self.filter_products()
                    self.return_txn_var.set("")
                    for widget in self.transaction_details_frame.winfo_children():
                        widget.destroy()
                else:
                    messagebox.showerror("Error", "Return failed!")
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity!")
    
    def load_returns_history(self):
        for widget in self.returns_history_frame.winfo_children():
            widget.destroy()
        returns = self.db.get_all_returns()
        if not returns:
            ctk.CTkLabel(self.returns_history_frame, text="No returns recorded.",
                        text_color=COLOR_ACCENT).pack(pady=20)
            return
        for ret in returns:
            frame = ctk.CTkFrame(self.returns_history_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=f"{ret['return_id'][:20]} | {ret['product_name'][:20]} | Qty: {ret['quantity']} | Refund: ${ret['refund_amount']:.2f} | {ret.get('reason', '-')[:20]}",
                        font=("Arial", 10)).pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=ret['created_at'][:10], text_color=COLOR_ACCENT).pack(side="right", padx=5)
    
    # ==================== ANALYTICS FUNCTIONS ====================
    
    def update_analytics(self):
        revenue = self.db.get_total_revenue()
        items_sold = self.db.get_total_items_sold()
        self.revenue_label.configure(text=f"${revenue:,.2f}")
        self.items_label.configure(text=f"{items_sold:,}")
        
        for widget in self.top_products_frame.winfo_children():
            widget.destroy()
        top_products = self.db.get_top_selling_products(10)
        for i, product in enumerate(top_products, 1):
            frame = ctk.CTkFrame(self.top_products_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=f"{i}. {product['name'][:25]}", width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=f"Qty: {product['total_sold']}", width=80).pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=f"${product['total_revenue']:,.2f}", text_color=COLOR_SUCCESS).pack(side="right", padx=5)
        
        for widget in self.low_stock_frame.winfo_children():
            widget.destroy()
        low_stock = self.db.get_low_stock_products()
        if not low_stock:
            ctk.CTkLabel(self.low_stock_frame, text="✓ All products have sufficient stock!",
                        text_color=COLOR_SUCCESS).pack(pady=10)
        else:
            for product in low_stock:
                frame = ctk.CTkFrame(self.low_stock_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"⚠️ {product['name'][:25]}", width=200, anchor="w",
                            text_color=COLOR_WARNING).pack(side="left", padx=5)
                ctk.CTkLabel(frame, text=f"Stock: {product['stock_quantity']}/{product.get('min_stock', 5)}",
                            width=100).pack(side="left", padx=5)
                ctk.CTkButton(frame, text="Restock", command=lambda pid=product['id']: self.quick_restock(pid),
                             width=70, fg_color=COLOR_ACCENT).pack(side="right", padx=5)
    
    def update_daily_summary(self):
        summary = self.db.get_daily_summary()
        if summary:
            self.today_sales_label.configure(text=f"Today: ${summary.get('total_sales', 0):.2f}")
    
    def quick_restock(self, product_id: int):
        qty = simpledialog.askinteger("Restock", "Enter quantity to add:", minvalue=1)
        if qty:
            if self.db.update_stock(product_id, qty):
                messagebox.showinfo("Success", f"Added {qty} items!")
                self.refresh_inventory()
                self.update_analytics()
                self.filter_products()
    
    # ==================== EXPENSES FUNCTIONS ====================
    
    def add_expense(self):
        try:
            category = self.exp_category_var.get()
            description = self.exp_desc_entry.get()
            amount = float(self.exp_amount_entry.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive!")
                return
            expense_id = self.db.add_expense(category, description, amount)
            if expense_id:
                messagebox.showinfo("Success", "Expense added!")
                self.exp_desc_entry.delete(0, END)
                self.exp_amount_entry.delete(0, END)
                self.load_expenses()
                self.update_analytics()
            else:
                messagebox.showerror("Error", "Failed to add expense!")
        except ValueError:
            messagebox.showerror("Error", "Invalid amount!")
    
    def load_expenses(self):
        for widget in self.expenses_list_frame.winfo_children():
            widget.destroy()
        cursor = self.db.connection.cursor()
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC LIMIT 50')
        expenses = cursor.fetchall()
        if not expenses:
            ctk.CTkLabel(self.expenses_list_frame, text="No expenses recorded yet.",
                        text_color=COLOR_ACCENT).pack(pady=20)
            return
        for exp in expenses:
            frame = ctk.CTkFrame(self.expenses_list_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=f"📌 {exp['category']}", width=120, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=exp['description'][:30], width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=f"${exp['amount']:.2f}", width=80, text_color=COLOR_WARNING).pack(side="left", padx=5)
            ctk.CTkLabel(frame, text=exp['date'][:10], width=100, text_color=COLOR_ACCENT).pack(side="right", padx=5)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if messagebox.askyesno("Exit", "Exit the application?"):
            self.db.close()
            self.root.destroy()


if __name__ == "__main__":
    app = GroceryStoreApp()
    app.run()