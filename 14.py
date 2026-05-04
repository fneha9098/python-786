"""
Professional Grocery Store Management System
Sleek Two-Color Design (Dark Blue & Silver) — Full Fixed & Enhanced Version
"""

import sqlite3
import os
import shutil
import csv
from datetime import datetime
from typing import List, Dict, Optional
from tkinter import messagebox, filedialog, simpledialog, END
import json

import customtkinter as ctk
from PIL import Image, ImageDraw

# ==================== CONSTANTS ====================

DATABASE_NAME = "grocery_store.db"
APP_TITLE = "Grocery Store Management System Pro"
APP_WIDTH = 1440
APP_HEIGHT = 860

# Professional Two-Color Scheme
COLOR_PRIMARY     = "#1a2a3a"   # Dark Navy Blue
COLOR_SECONDARY   = "#2c3e50"   # Steel Blue (slightly darker for contrast)
COLOR_ACCENT      = "#5d7a8c"   # Silver Gray
COLOR_BACKGROUND  = "#0f1a24"   # Deep Navy
COLOR_TEXT        = "#e8ecf0"   # Light Gray
COLOR_SUCCESS     = "#27ae60"   # Clean Green
COLOR_WARNING     = "#f39c12"   # Amber
COLOR_ERROR       = "#c0392b"   # Red
COLOR_HIGHLIGHT   = "#2980b9"   # Blue highlight
COLOR_CARD_BORDER = "#34495e"   # Card border

TAX_RATE              = 0.10
LOW_STOCK_THRESHOLD   = 10
DISCOUNT_RATES        = {"None": 0.0, "Staff": 0.10, "Senior": 0.15, "Bulk (10+)": 0.20}

# Paths
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR        = os.path.join(BASE_DIR, "assets", "images", "products")
DEFAULT_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "images", "default_image.png")
RECEIPTS_DIR      = os.path.join(BASE_DIR, "receipts")
BACKUP_DIR        = os.path.join(BASE_DIR, "backups")

for _d in (IMAGES_DIR, RECEIPTS_DIR, BACKUP_DIR):
    os.makedirs(_d, exist_ok=True)

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
            # isolation_level=None = autocommit / manual transaction mode.
            # This MUST be set so our explicit BEGIN TRANSACTION / COMMIT / ROLLBACK
            # calls don't clash with Python's own implicit transaction management.
            self.connection.isolation_level = None
            self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect: {e}")
            raise

    def create_tables(self):
        c = self.connection.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode         TEXT,
            name            TEXT    NOT NULL,
            category        TEXT    NOT NULL,
            price           REAL    NOT NULL,
            cost_price      REAL,
            stock_quantity  INTEGER DEFAULT 0,
            unit            TEXT    DEFAULT 'pcs',
            image_path      TEXT,
            min_stock       INTEGER DEFAULT 5,
            location        TEXT,
            supplier        TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute("PRAGMA table_info(products)")
        existing = [r[1] for r in c.fetchall()]
        for col, typ in {
            'min_stock': 'INTEGER DEFAULT 5', 'location': 'TEXT', 'supplier': 'TEXT',
            'barcode': 'TEXT', 'cost_price': 'REAL', 'unit': "TEXT DEFAULT 'pcs'"
        }.items():
            if col not in existing:
                try: c.execute(f"ALTER TABLE products ADD COLUMN {col} {typ}")
                except: pass

        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id    TEXT    UNIQUE NOT NULL,
            subtotal          REAL    NOT NULL,
            tax_amount        REAL    NOT NULL,
            discount_amount   REAL    DEFAULT 0,
            discount_type     TEXT    DEFAULT 'None',
            total_amount      REAL    NOT NULL,
            payment_method    TEXT    DEFAULT 'cash',
            cash_received     REAL,
            change_amount     REAL,
            customer_name     TEXT,
            cashier_name      TEXT    DEFAULT 'Default',
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute("PRAGMA table_info(transactions)")
        existing_txn = [r[1] for r in c.fetchall()]
        for col, typ in {
            'discount_amount': 'REAL DEFAULT 0', 'discount_type': "TEXT DEFAULT 'None'",
            'cash_received': 'REAL', 'change_amount': 'REAL', 'customer_name': 'TEXT'
        }.items():
            if col not in existing_txn:
                try: c.execute(f"ALTER TABLE transactions ADD COLUMN {col} {typ}")
                except: pass

        c.execute('''CREATE TABLE IF NOT EXISTS transaction_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id  TEXT    NOT NULL,
            product_id      INTEGER NOT NULL,
            product_name    TEXT    NOT NULL,
            quantity        INTEGER NOT NULL,
            unit_price      REAL    NOT NULL,
            total_price     REAL    NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS returns (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            return_id               TEXT    UNIQUE NOT NULL,
            original_transaction_id TEXT    NOT NULL,
            product_id              INTEGER NOT NULL,
            quantity                INTEGER NOT NULL,
            refund_amount           REAL    NOT NULL,
            reason                  TEXT,
            processed_by            TEXT    DEFAULT 'Default',
            created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id  TEXT    UNIQUE NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT,
            amount      REAL    NOT NULL,
            date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS daily_summary (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            date                TEXT    UNIQUE NOT NULL,
            total_sales         REAL    DEFAULT 0,
            total_transactions  INTEGER DEFAULT 0,
            total_items_sold    INTEGER DEFAULT 0,
            total_returns       REAL    DEFAULT 0,
            total_expenses      REAL    DEFAULT 0,
            net_profit          REAL    DEFAULT 0
        )''')

        self.connection.commit()

    # -------- Products --------
    def add_product(self, name, category, price, stock, unit, barcode=None,
                    cost_price=None, min_stock=5, location="", supplier="", image_path=None):
        c = self.connection.cursor()
        try:
            c.execute('''INSERT INTO products
                (name,category,price,stock_quantity,unit,barcode,cost_price,min_stock,location,supplier,image_path)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (name,category,price,stock,unit,barcode,cost_price,min_stock,location,supplier,image_path))
            self.connection.commit()
            return c.lastrowid
        except sqlite3.Error as e:
            print(f"add_product error: {e}")
            return None

    def get_all_products(self):
        c = self.connection.cursor()
        c.execute('SELECT * FROM products ORDER BY name')
        return [dict(r) for r in c.fetchall()]

    def get_product_by_id(self, product_id):
        c = self.connection.cursor()
        c.execute('SELECT * FROM products WHERE id=?', (product_id,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_product_by_barcode(self, barcode):
        c = self.connection.cursor()
        c.execute('SELECT * FROM products WHERE barcode=?', (barcode,))
        r = c.fetchone()
        return dict(r) if r else None

    def update_product(self, product_id, **kwargs):
        allowed = ['name','category','price','stock_quantity','unit','barcode',
                   'cost_price','min_stock','location','supplier','image_path']
        updates = [f"{k}=?" for k in kwargs if k in allowed]
        values  = [kwargs[k] for k in kwargs if k in allowed]
        if updates:
            c = self.connection.cursor()
            values.append(product_id)
            c.execute(f"UPDATE products SET {', '.join(updates)}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
            self.connection.commit()
            return True
        return False

    def update_stock(self, product_id, qty_change):
        c = self.connection.cursor()
        c.execute('''UPDATE products SET stock_quantity=stock_quantity+?, updated_at=CURRENT_TIMESTAMP
                     WHERE id=? AND stock_quantity+?>=0''', (qty_change, product_id, qty_change))
        self.connection.commit()
        return c.rowcount > 0

    def search_products(self, search_term="", category="All", min_price=0, max_price=999999):
        c = self.connection.cursor()
        q = "SELECT * FROM products WHERE name LIKE ? AND price BETWEEN ? AND ?"
        p = [f"%{search_term}%", min_price, max_price]
        if category != "All":
            q += " AND category=?"
            p.append(category)
        q += " ORDER BY name"
        c.execute(q, p)
        return [dict(r) for r in c.fetchall()]

    def get_low_stock_products(self):
        c = self.connection.cursor()
        c.execute('SELECT * FROM products WHERE stock_quantity<=min_stock ORDER BY stock_quantity ASC')
        return [dict(r) for r in c.fetchall()]

    def delete_product(self, product_id):
        c = self.connection.cursor()
        c.execute('DELETE FROM products WHERE id=?', (product_id,))
        self.connection.commit()
        return c.rowcount > 0

    # -------- Transactions --------
    def create_transaction(self, items, subtotal, tax, discount_type, discount_amount,
                           total, payment_method, cash_received=None, customer_name="", cashier="Default"):
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        change_amount  = (cash_received - total) if cash_received and cash_received > total else 0.0
        c = self.connection.cursor()
        try:
            c.execute("BEGIN TRANSACTION")
            c.execute('''INSERT INTO transactions
                (transaction_id,subtotal,tax_amount,discount_type,discount_amount,total_amount,
                 payment_method,cash_received,change_amount,customer_name,cashier_name)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (transaction_id, subtotal, tax, discount_type, discount_amount, total,
                 payment_method, cash_received, change_amount, customer_name, cashier))

            total_items_qty = 0
            for item in items:
                c.execute('''INSERT INTO transaction_items
                    (transaction_id,product_id,product_name,quantity,unit_price,total_price)
                    VALUES (?,?,?,?,?,?)''',
                    (transaction_id, item['id'], item['name'], item['quantity'], item['price'], item['total']))
                c.execute('''UPDATE products SET stock_quantity=stock_quantity-?, updated_at=CURRENT_TIMESTAMP
                             WHERE id=? AND stock_quantity>=?''',
                          (item['quantity'], item['id'], item['quantity']))
                total_items_qty += item['quantity']

            today = datetime.now().strftime('%Y-%m-%d')
            c.execute('''INSERT INTO daily_summary (date,total_sales,total_transactions,total_items_sold)
                         VALUES (?,?,1,?)
                         ON CONFLICT(date) DO UPDATE SET
                             total_sales=total_sales+?,
                             total_transactions=total_transactions+1,
                             total_items_sold=total_items_sold+?,
                             net_profit=total_sales+?-total_returns-total_expenses''',
                      (today, total, total_items_qty, total, total_items_qty, total))

            self.connection.commit()
            return transaction_id
        except Exception as e:
            self.connection.rollback()
            import traceback; traceback.print_exc()
            print(f"Transaction error: {e}")
            return None

    def get_transaction(self, transaction_id):
        c = self.connection.cursor()
        c.execute('SELECT * FROM transactions WHERE transaction_id=?', (transaction_id,))
        txn = c.fetchone()
        if txn:
            c.execute('SELECT * FROM transaction_items WHERE transaction_id=?', (transaction_id,))
            items = [dict(r) for r in c.fetchall()]
            result = dict(txn)
            result['items'] = items
            return result
        return None

    def get_todays_transactions(self):
        today = datetime.now().strftime('%Y-%m-%d')
        c = self.connection.cursor()
        c.execute("SELECT * FROM transactions WHERE DATE(created_at)=? ORDER BY created_at DESC", (today,))
        return [dict(r) for r in c.fetchall()]

    def get_transactions_by_date_range(self, start_date, end_date):
        c = self.connection.cursor()
        c.execute("SELECT * FROM transactions WHERE DATE(created_at) BETWEEN ? AND ? ORDER BY created_at DESC",
                  (start_date, end_date))
        return [dict(r) for r in c.fetchall()]

    # -------- Returns --------
    def process_return(self, transaction_id, product_id, quantity, reason, processed_by="Default"):
        return_id = f"RET{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        c = self.connection.cursor()
        try:
            c.execute("BEGIN TRANSACTION")
            c.execute("SELECT * FROM transaction_items WHERE transaction_id=? AND product_id=?",
                      (transaction_id, product_id))
            original = c.fetchone()
            if not original:
                self.connection.rollback()
                return None

            refund = original['unit_price'] * quantity
            c.execute('''INSERT INTO returns
                (return_id,original_transaction_id,product_id,quantity,refund_amount,reason,processed_by)
                VALUES (?,?,?,?,?,?,?)''',
                (return_id, transaction_id, product_id, quantity, refund, reason, processed_by))
            c.execute("UPDATE products SET stock_quantity=stock_quantity+? WHERE id=?", (quantity, product_id))
            c.execute("UPDATE transactions SET total_amount=total_amount-? WHERE transaction_id=?",
                      (refund, transaction_id))

            today = datetime.now().strftime('%Y-%m-%d')
            c.execute('''UPDATE daily_summary
                         SET total_returns=total_returns+?,
                             net_profit=total_sales-total_returns-?-total_expenses
                         WHERE date=?''', (refund, refund, today))

            self.connection.commit()
            return return_id
        except Exception as e:
            self.connection.rollback()
            import traceback; traceback.print_exc()
            print(f"Return error: {e}")
            return None

    def get_all_returns(self):
        c = self.connection.cursor()
        c.execute('''SELECT r.*, p.name as product_name FROM returns r
                     JOIN products p ON r.product_id=p.id
                     ORDER BY r.created_at DESC''')
        return [dict(r) for r in c.fetchall()]

    # -------- Analytics --------
    def get_total_revenue(self):
        c = self.connection.cursor()
        c.execute("SELECT COALESCE(SUM(total_amount),0) as t FROM transactions")
        return c.fetchone()['t']

    def get_total_items_sold(self):
        c = self.connection.cursor()
        c.execute("SELECT COALESCE(SUM(quantity),0) as t FROM transaction_items")
        return c.fetchone()['t']

    def get_total_returns_amount(self):
        c = self.connection.cursor()
        c.execute("SELECT COALESCE(SUM(refund_amount),0) as t FROM returns")
        return c.fetchone()['t']

    def get_todays_sales(self):
        today = datetime.now().strftime('%Y-%m-%d')
        c = self.connection.cursor()
        c.execute("SELECT COALESCE(SUM(total_amount),0) as t FROM transactions WHERE DATE(created_at)=?", (today,))
        return c.fetchone()['t']

    def get_top_selling_products(self, limit=10):
        c = self.connection.cursor()
        c.execute('''SELECT p.id,p.name,p.category,SUM(ti.quantity) as total_sold,SUM(ti.total_price) as total_revenue
                     FROM products p JOIN transaction_items ti ON p.id=ti.product_id
                     GROUP BY p.id ORDER BY total_sold DESC LIMIT ?''', (limit,))
        return [dict(r) for r in c.fetchall()]

    def get_daily_summary(self, date=None):
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        c = self.connection.cursor()
        c.execute('SELECT * FROM daily_summary WHERE date=?', (date,))
        r = c.fetchone()
        return dict(r) if r else None

    def add_expense(self, category, description, amount):
        expense_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        c = self.connection.cursor()
        c.execute("INSERT INTO expenses (expense_id,category,description,amount) VALUES (?,?,?,?)",
                  (expense_id, category, description, amount))
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''UPDATE daily_summary
                     SET total_expenses=total_expenses+?,
                         net_profit=total_sales-total_returns-total_expenses-?
                     WHERE date=?''', (amount, amount, today))
        self.connection.commit()
        return expense_id

    def backup_database(self):
        try:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            path = os.path.join(BACKUP_DIR, name)
            shutil.copy2(DATABASE_NAME, path)
            return path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    def close(self):
        if self.connection:
            self.connection.close()


# ==================== CUSTOM WIDGETS ====================

class ModernButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=COLOR_SECONDARY, hover_color=COLOR_ACCENT,
                       text_color=COLOR_TEXT, corner_radius=8, height=35)

class ModernCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=COLOR_PRIMARY, corner_radius=12,
                       border_width=1, border_color=COLOR_CARD_BORDER)


# ==================== MAIN APPLICATION ====================

class GroceryStoreApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.minsize(1200, 700)
        self.root.configure(fg_color=COLOR_BACKGROUND)

        self.db             = DatabaseManager()
        self.cart_items     = []
        self.current_cashier = "Admin"

        self._create_default_placeholder()
        self._setup_ui()

        # ─── Initial data load ───
        self.filter_products()          # BUG FIX: populate POS grid on startup
        self.refresh_inventory()
        self.update_analytics()
        self.update_daily_summary()

    # ─────────────────────────────────────────────────────────────
    #  UI SETUP
    # ─────────────────────────────────────────────────────────────

    def _create_default_placeholder(self):
        if not os.path.exists(DEFAULT_IMAGE_PATH):
            try:
                os.makedirs(os.path.dirname(DEFAULT_IMAGE_PATH), exist_ok=True)
                img  = Image.new('RGB', (200, 200), color=COLOR_SECONDARY)
                draw = ImageDraw.Draw(img)
                draw.rectangle([10,10,190,190], outline=COLOR_ACCENT, width=3)
                draw.text((55, 90), 'No Image', fill=COLOR_TEXT)
                img.save(DEFAULT_IMAGE_PATH)
            except Exception:
                pass

    def _setup_ui(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color=COLOR_BACKGROUND)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Header ──
        header = ctk.CTkFrame(self.main_container, height=65, fg_color=COLOR_PRIMARY, corner_radius=12)
        header.pack(fill="x", pady=(0, 8))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🛒  GROCERY STORE MANAGEMENT SYSTEM PRO",
                     font=("Arial", 19, "bold"), text_color=COLOR_TEXT).pack(side="left", padx=20, pady=12)

        # Stats bar (right side of header)
        stats = ctk.CTkFrame(header, fg_color=COLOR_SECONDARY, corner_radius=10)
        stats.pack(side="right", padx=12, pady=8)

        self.today_sales_header_label = ctk.CTkLabel(stats, text="Today: $0.00",
                                                     font=("Arial", 13, "bold"), text_color=COLOR_SUCCESS)
        self.today_sales_header_label.pack(side="left", padx=12)

        ctk.CTkLabel(stats, text="|", text_color=COLOR_ACCENT).pack(side="left")

        self.cashier_label = ctk.CTkLabel(stats, text=f"👤  {self.current_cashier}",
                                          font=("Arial", 12), text_color=COLOR_TEXT)
        self.cashier_label.pack(side="left", padx=12)

        ctk.CTkButton(stats, text="⚙ Change Cashier", width=130, height=28,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_HIGHLIGHT,
                      command=self._change_cashier).pack(side="left", padx=8)

        # ── Tab view ──
        self.notebook = ctk.CTkTabview(self.main_container,
                                       fg_color=COLOR_PRIMARY,
                                       segmented_button_fg_color=COLOR_SECONDARY,
                                       segmented_button_selected_color=COLOR_HIGHLIGHT,
                                       segmented_button_selected_hover_color=COLOR_ACCENT)
        self.notebook.pack(fill="both", expand=True)

        self.pos_tab       = self.notebook.add("💳  POS Terminal")
        self.inventory_tab = self.notebook.add("📦  Inventory")
        self.returns_tab   = self.notebook.add("🔄  Returns")
        self.analytics_tab = self.notebook.add("📊  Analytics")
        self.expenses_tab  = self.notebook.add("💰  Expenses")

        self._setup_pos_tab()
        self._setup_inventory_tab()
        self._setup_returns_tab()
        self._setup_analytics_tab()
        self._setup_expenses_tab()

    def _change_cashier(self):
        name = simpledialog.askstring("Cashier", "Enter cashier name:", initialvalue=self.current_cashier)
        if name and name.strip():
            self.current_cashier = name.strip()
            self.cashier_label.configure(text=f"👤  {self.current_cashier}")

    # ─────────────────────────────────────────────────────────────
    #  POS TAB
    # ─────────────────────────────────────────────────────────────

    def _setup_pos_tab(self):
        # ── Left: product browser ──
        left = ModernCard(self.pos_tab)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))

        # Filter bar
        fbar = ctk.CTkFrame(left, fg_color="transparent")
        fbar.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(fbar, text="🔍", text_color=COLOR_TEXT).pack(side="left")
        self.pos_search_var = ctk.StringVar()
        self.pos_search_var.trace("w", lambda *_: self.filter_products())
        ctk.CTkEntry(fbar, textvariable=self.pos_search_var, placeholder_text="Search products…",
                     width=180, fg_color=COLOR_SECONDARY, border_color=COLOR_ACCENT).pack(side="left", padx=4)

        ctk.CTkLabel(fbar, text="Category:", text_color=COLOR_TEXT).pack(side="left", padx=(12,4))
        self.pos_category_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(fbar, values=CATEGORIES, variable=self.pos_category_var,
                          fg_color=COLOR_SECONDARY, button_color=COLOR_ACCENT, width=160,
                          command=lambda _: self.filter_products()).pack(side="left", padx=4)

        ctk.CTkLabel(fbar, text="Price $", text_color=COLOR_TEXT).pack(side="left", padx=(14,4))
        self.min_price_var = ctk.StringVar(value="0")
        ctk.CTkEntry(fbar, textvariable=self.min_price_var, width=70,
                     fg_color=COLOR_SECONDARY).pack(side="left", padx=2)
        ctk.CTkLabel(fbar, text="–", text_color=COLOR_TEXT).pack(side="left")
        self.max_price_var = ctk.StringVar(value="999999")
        ctk.CTkEntry(fbar, textvariable=self.max_price_var, width=70,
                     fg_color=COLOR_SECONDARY).pack(side="left", padx=2)

        ctk.CTkButton(fbar, text="Apply", width=55, fg_color=COLOR_HIGHLIGHT, hover_color=COLOR_ACCENT,
                      command=self.filter_products).pack(side="left", padx=4)
        ctk.CTkButton(fbar, text="↺ Reset", width=65, fg_color=COLOR_SECONDARY, hover_color=COLOR_ACCENT,
                      command=self._reset_pos_filters).pack(side="left", padx=4)

        # Product grid
        self.product_grid_frame = ctk.CTkScrollableFrame(left, fg_color=COLOR_BACKGROUND)
        self.product_grid_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # ── Right: cart ──
        right = ModernCard(self.pos_tab)
        right.pack(side="right", fill="both", ipadx=4)
        right.configure(width=400)

        # Cart header
        ch = ctk.CTkFrame(right, fg_color="transparent")
        ch.pack(fill="x", padx=12, pady=(10,4))
        ctk.CTkLabel(ch, text="🛒  SHOPPING CART", font=("Arial", 16, "bold"), text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(ch, text="🗑 Clear", width=75, fg_color=COLOR_ERROR, hover_color="#96281b",
                      command=self.clear_cart).pack(side="right")

        # Barcode
        bc_frame = ctk.CTkFrame(right, fg_color=COLOR_SECONDARY, corner_radius=8)
        bc_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(bc_frame, text="📷 Barcode:", text_color=COLOR_TEXT).pack(side="left", padx=8, pady=6)
        self.barcode_var = ctk.StringVar()
        bc_entry = ctk.CTkEntry(bc_frame, textvariable=self.barcode_var, width=160,
                                fg_color=COLOR_PRIMARY, placeholder_text="Scan or type…")
        bc_entry.pack(side="left", padx=4, pady=6)
        bc_entry.bind('<Return>', lambda _: self._add_by_barcode())
        ctk.CTkButton(bc_frame, text="Add", width=50, fg_color=COLOR_HIGHLIGHT,
                      command=self._add_by_barcode).pack(side="left", padx=4)

        # Cart list
        self.cart_frame = ctk.CTkScrollableFrame(right, fg_color=COLOR_BACKGROUND, height=280)
        self.cart_frame.pack(fill="both", expand=True, padx=12, pady=6)

        # ── Customer ──
        cust_frame = ctk.CTkFrame(right, fg_color="transparent")
        cust_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(cust_frame, text="👤 Customer:", text_color=COLOR_TEXT, width=90).pack(side="left")
        self.customer_name_var = ctk.StringVar()
        ctk.CTkEntry(cust_frame, textvariable=self.customer_name_var, width=180,
                     fg_color=COLOR_SECONDARY, placeholder_text="Optional").pack(side="left", padx=4)

        # ── Discount & Tax ──
        dt_frame = ctk.CTkFrame(right, fg_color="transparent")
        dt_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(dt_frame, text="🎫 Discount:", text_color=COLOR_TEXT, width=90).pack(side="left")
        self.discount_var = ctk.StringVar(value="None")
        ctk.CTkOptionMenu(dt_frame, values=list(DISCOUNT_RATES.keys()),
                          variable=self.discount_var, width=140,
                          fg_color=COLOR_SECONDARY, button_color=COLOR_ACCENT,
                          command=lambda _: self._update_cart_totals()).pack(side="left", padx=4)
        self.tax_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(dt_frame, text="Tax 10%", variable=self.tax_var,
                        fg_color=COLOR_HIGHLIGHT, hover_color=COLOR_ACCENT,
                        command=self._update_cart_totals).pack(side="left", padx=16)

        # ── Totals card ──
        tot = ModernCard(right)
        tot.pack(fill="x", padx=12, pady=6)
        self.subtotal_label  = ctk.CTkLabel(tot, text="Subtotal:    $0.00", font=("Arial", 13), text_color=COLOR_TEXT)
        self.subtotal_label.pack(anchor="e", padx=16, pady=(8,2))
        self.discount_label  = ctk.CTkLabel(tot, text="Discount:   -$0.00", font=("Arial", 13), text_color=COLOR_WARNING)
        self.discount_label.pack(anchor="e", padx=16, pady=2)
        self.tax_label       = ctk.CTkLabel(tot, text="Tax:          $0.00", font=("Arial", 13), text_color=COLOR_ACCENT)
        self.tax_label.pack(anchor="e", padx=16, pady=2)
        sep = ctk.CTkFrame(tot, height=1, fg_color=COLOR_CARD_BORDER)
        sep.pack(fill="x", padx=12, pady=4)
        self.total_label     = ctk.CTkLabel(tot, text="TOTAL:       $0.00", font=("Arial", 20, "bold"), text_color=COLOR_SUCCESS)
        self.total_label.pack(anchor="e", padx=16, pady=(2,10))

        # ── Payment ──
        pay_frame = ctk.CTkFrame(right, fg_color=COLOR_SECONDARY, corner_radius=8)
        pay_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(pay_frame, text="💵 Method:", text_color=COLOR_TEXT).pack(side="left", padx=8, pady=6)
        self.payment_method_var = ctk.StringVar(value="cash")
        ctk.CTkOptionMenu(pay_frame, values=["cash","card","mobile"],
                          variable=self.payment_method_var, width=100,
                          fg_color=COLOR_PRIMARY, button_color=COLOR_ACCENT,
                          command=self._on_payment_method_change).pack(side="left", padx=4)
        self.cash_label = ctk.CTkLabel(pay_frame, text="Received $:", text_color=COLOR_TEXT)
        self.cash_label.pack(side="left", padx=(12,4))
        self.cash_received_var = ctk.StringVar()
        self.cash_entry_widget = ctk.CTkEntry(pay_frame, textvariable=self.cash_received_var,
                                              width=90, fg_color=COLOR_PRIMARY, placeholder_text="0.00")
        self.cash_entry_widget.pack(side="left", padx=4)

        # ── Action buttons ──
        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=8)

        ctk.CTkButton(btn_frame, text="✅  CHECKOUT", font=("Arial", 15, "bold"), height=48,
                      fg_color=COLOR_SUCCESS, hover_color="#1e8449",
                      command=self.checkout).pack(fill="x", pady=4)
        ctk.CTkButton(btn_frame, text="⏸  Hold Order", height=34,
                      fg_color=COLOR_SECONDARY, hover_color=COLOR_ACCENT,
                      command=self._hold_order).pack(fill="x", pady=2)

    def _on_payment_method_change(self, method):
        if method == "cash":
            self.cash_label.configure(text_color=COLOR_TEXT)
            self.cash_entry_widget.configure(state="normal")
        else:
            self.cash_label.configure(text_color=COLOR_ACCENT)
            self.cash_entry_widget.configure(state="disabled")

    # ─────────────────────────────────────────────────────────────
    #  INVENTORY TAB
    # ─────────────────────────────────────────────────────────────

    def _setup_inventory_tab(self):
        ctrl = ctk.CTkFrame(self.inventory_tab, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=8)

        btn_specs = [
            ("➕ Add Product",    self.add_product_dialog,       COLOR_SUCCESS),
            ("✏️ Edit Selected",  self._edit_selected_product,   COLOR_HIGHLIGHT),
            ("🗑️ Delete Selected",self._delete_selected_product, COLOR_ERROR),
            ("📤 Export CSV",     self._export_inventory,        COLOR_SECONDARY),
            ("💾 Backup DB",      self._backup_database,         COLOR_ACCENT),
            ("🔄 Refresh",        self.refresh_inventory,        COLOR_SECONDARY),
        ]
        for txt, cmd, col in btn_specs:
            ctk.CTkButton(ctrl, text=txt, command=cmd, fg_color=col,
                          hover_color=COLOR_SECONDARY, corner_radius=8, height=34).pack(side="left", padx=4)

        # search right side
        sf = ctk.CTkFrame(ctrl, fg_color="transparent")
        sf.pack(side="right")
        ctk.CTkLabel(sf, text="🔍", text_color=COLOR_TEXT).pack(side="left")
        self.inv_search_var = ctk.StringVar()
        self.inv_search_var.trace("w", lambda *_: self.refresh_inventory())
        ctk.CTkEntry(sf, textvariable=self.inv_search_var, width=200,
                     fg_color=COLOR_SECONDARY, placeholder_text="Search inventory…").pack(side="left", padx=4)

        # Table
        self.inventory_table_frame = ctk.CTkScrollableFrame(self.inventory_tab, fg_color=COLOR_BACKGROUND)
        self.inventory_table_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        headers = ["☑", "ID", "Name", "Category", "Price", "Stock", "Unit", "Min Stock", "Location", "Supplier", "Actions"]
        col_widths = [30, 50, 150, 130, 70, 60, 55, 70, 90, 100, 120]
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            ctk.CTkLabel(self.inventory_table_frame, text=h,
                         font=("Arial", 11, "bold"), text_color=COLOR_ACCENT, width=w,
                         fg_color=COLOR_PRIMARY).grid(row=0, column=i, padx=3, pady=6, sticky="w")

        self.selected_products = {}

    # ─────────────────────────────────────────────────────────────
    #  RETURNS TAB
    # ─────────────────────────────────────────────────────────────

    def _setup_returns_tab(self):
        lookup = ModernCard(self.returns_tab)
        lookup.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(lookup, text="🔍  FIND TRANSACTION", font=("Arial", 14, "bold"),
                     text_color=COLOR_TEXT).pack(pady=(10,4))

        row1 = ctk.CTkFrame(lookup, fg_color="transparent")
        row1.pack(pady=4)
        ctk.CTkLabel(row1, text="Transaction ID:", text_color=COLOR_TEXT).pack(side="left", padx=6)
        self.return_txn_var = ctk.StringVar()
        ctk.CTkEntry(row1, textvariable=self.return_txn_var, width=260,
                     fg_color=COLOR_SECONDARY, placeholder_text="e.g. TXN20250101120000000").pack(side="left", padx=6)
        ctk.CTkButton(row1, text="🔎 Search", fg_color=COLOR_HIGHLIGHT,
                      command=self._lookup_transaction).pack(side="left", padx=6)

        row2 = ctk.CTkFrame(lookup, fg_color="transparent")
        row2.pack(pady=(4,10))
        ctk.CTkLabel(row2, text="Or by date (YYYY-MM-DD):", text_color=COLOR_TEXT).pack(side="left", padx=6)
        self.return_date_var = ctk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ctk.CTkEntry(row2, textvariable=self.return_date_var, width=130,
                     fg_color=COLOR_SECONDARY).pack(side="left", padx=6)
        ctk.CTkButton(row2, text="📋 Show Transactions", fg_color=COLOR_SUCCESS,
                      command=self._show_daily_transactions).pack(side="left", padx=6)

        self.transaction_details_frame = ctk.CTkScrollableFrame(
            self.returns_tab, fg_color=COLOR_BACKGROUND, height=260)
        self.transaction_details_frame.pack(fill="both", expand=True, padx=10, pady=6)

        hist = ModernCard(self.returns_tab)
        hist.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(hist, text="📜  RETURNS HISTORY", font=("Arial", 13, "bold"),
                     text_color=COLOR_TEXT).pack(pady=(8,4))
        self.returns_history_frame = ctk.CTkScrollableFrame(hist, fg_color=COLOR_BACKGROUND, height=140)
        self.returns_history_frame.pack(fill="both", expand=True, padx=10, pady=(0,8))
        self._load_returns_history()

    # ─────────────────────────────────────────────────────────────
    #  ANALYTICS TAB
    # ─────────────────────────────────────────────────────────────

    def _setup_analytics_tab(self):
        # Refresh button
        top_bar = ctk.CTkFrame(self.analytics_tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(8,0))
        ctk.CTkButton(top_bar, text="🔄 Refresh Analytics", width=160,
                      fg_color=COLOR_HIGHLIGHT, command=self.update_analytics).pack(side="right")

        # ── Summary cards ──
        cards_frame = ctk.CTkFrame(self.analytics_tab, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=8)

        card_data = [
            ("💰 TOTAL REVENUE",  "revenue_label",  "$0.00",  COLOR_SUCCESS),
            ("📦 ITEMS SOLD",     "items_label",    "0",      COLOR_HIGHLIGHT),
            ("📅 TODAY'S SALES",  "today_label",    "$0.00",  COLOR_WARNING),
            ("🔄 TOTAL RETURNS",  "returns_label",  "$0.00",  COLOR_ERROR),
        ]
        for title, attr, default, color in card_data:
            card = ModernCard(cards_frame)
            card.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(card, text=title, font=("Arial", 11), text_color=COLOR_ACCENT).pack(pady=(12,2))
            lbl = ctk.CTkLabel(card, text=default, font=("Arial", 26, "bold"), text_color=color)
            lbl.pack(pady=(0,12))
            setattr(self, attr, lbl)

        # ── Top products ──
        tp_card = ModernCard(self.analytics_tab)
        tp_card.pack(fill="both", expand=True, padx=10, pady=6)
        ctk.CTkLabel(tp_card, text="🏆  TOP SELLING PRODUCTS",
                     font=("Arial", 13, "bold"), text_color=COLOR_TEXT).pack(pady=(10,4))
        self.top_products_frame = ctk.CTkScrollableFrame(tp_card, fg_color=COLOR_BACKGROUND, height=200)
        self.top_products_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # ── Low stock ──
        ls_card = ModernCard(self.analytics_tab)
        ls_card.pack(fill="both", expand=True, padx=10, pady=(0,10))
        ctk.CTkLabel(ls_card, text="⚠️  LOW STOCK ALERT",
                     font=("Arial", 13, "bold"), text_color=COLOR_WARNING).pack(pady=(10,4))
        self.low_stock_frame = ctk.CTkScrollableFrame(ls_card, fg_color=COLOR_BACKGROUND, height=140)
        self.low_stock_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

    # ─────────────────────────────────────────────────────────────
    #  EXPENSES TAB
    # ─────────────────────────────────────────────────────────────

    def _setup_expenses_tab(self):
        add_card = ModernCard(self.expenses_tab)
        add_card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(add_card, text="➕  ADD EXPENSE",
                     font=("Arial", 13, "bold"), text_color=COLOR_TEXT).pack(pady=(10,6))

        form = ctk.CTkFrame(add_card, fg_color="transparent")
        form.pack(pady=(0,10))

        ctk.CTkLabel(form, text="Category:", text_color=COLOR_TEXT).grid(row=0, column=0, padx=8, pady=6)
        self.exp_category_var = ctk.CTkOptionMenu(
            form, values=["Rent","Utilities","Salary","Maintenance","Supplies","Other"],
            fg_color=COLOR_SECONDARY, width=130)
        self.exp_category_var.grid(row=0, column=1, padx=6, pady=6)

        ctk.CTkLabel(form, text="Description:", text_color=COLOR_TEXT).grid(row=0, column=2, padx=8)
        self.exp_desc_entry = ctk.CTkEntry(form, width=220, fg_color=COLOR_SECONDARY,
                                           placeholder_text="e.g. Monthly electricity bill")
        self.exp_desc_entry.grid(row=0, column=3, padx=6, pady=6)

        ctk.CTkLabel(form, text="Amount ($):", text_color=COLOR_TEXT).grid(row=0, column=4, padx=8)
        self.exp_amount_entry = ctk.CTkEntry(form, width=100, fg_color=COLOR_SECONDARY, placeholder_text="0.00")
        self.exp_amount_entry.grid(row=0, column=5, padx=6, pady=6)

        ctk.CTkButton(form, text="✅ Add", fg_color=COLOR_SUCCESS, hover_color="#1e8449",
                      command=self._add_expense).grid(row=0, column=6, padx=10)

        hist = ModernCard(self.expenses_tab)
        hist.pack(fill="both", expand=True, padx=10, pady=(0,10))
        ctk.CTkLabel(hist, text="📋  EXPENSES HISTORY",
                     font=("Arial", 13, "bold"), text_color=COLOR_TEXT).pack(pady=(10,4))
        self.expenses_list_frame = ctk.CTkScrollableFrame(hist, fg_color=COLOR_BACKGROUND, height=350)
        self.expenses_list_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self._load_expenses()

    # ─────────────────────────────────────────────────────────────
    #  POS LOGIC
    # ─────────────────────────────────────────────────────────────

    def filter_products(self):
        search = self.pos_search_var.get().strip()
        cat    = self.pos_category_var.get()
        try:
            mn = float(self.min_price_var.get() or 0)
            mx = float(self.max_price_var.get() or 999999)
        except ValueError:
            mn, mx = 0, 999999
        products = self.db.search_products(search, cat, mn, mx)
        self._display_product_grid(products)

    def _reset_pos_filters(self):
        self.pos_search_var.set("")
        self.pos_category_var.set("All")
        self.min_price_var.set("0")
        self.max_price_var.set("999999")
        self.filter_products()

    def _display_product_grid(self, products):
        for w in self.product_grid_frame.winfo_children():
            w.destroy()

        if not products:
            ctk.CTkLabel(self.product_grid_frame, text="No products found.",
                         text_color=COLOR_ACCENT, font=("Arial", 13)).grid(row=0, column=0, padx=20, pady=40)
            return

        MAX_COLS = 4
        for idx, product in enumerate(products):
            row, col = divmod(idx, MAX_COLS)
            card = ModernCard(self.product_grid_frame)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            self._display_product_image(card, product)

            ctk.CTkLabel(card, text=product['name'][:22], font=("Arial", 11, "bold"),
                         text_color=COLOR_TEXT, wraplength=140).pack(pady=(4,0), padx=6)
            ctk.CTkLabel(card, text=f"${product['price']:.2f}",
                         font=("Arial", 14, "bold"), text_color=COLOR_SUCCESS).pack()

            stk = product['stock_quantity']
            min_s = product.get('min_stock', 5) or 5
            stock_color = COLOR_ERROR if stk == 0 else (COLOR_WARNING if stk <= min_s else COLOR_ACCENT)
            ctk.CTkLabel(card, text=f"Stock: {stk} {product['unit']}",
                         font=("Arial", 9), text_color=stock_color).pack()

            qty_frame = ctk.CTkFrame(card, fg_color="transparent")
            qty_frame.pack(pady=6)
            qty_var = ctk.StringVar(value="1")
            ctk.CTkEntry(qty_frame, textvariable=qty_var, width=48,
                         fg_color=COLOR_SECONDARY, justify="center").pack(side="left", padx=2)

            p_copy = dict(product)  # capture
            ctk.CTkButton(qty_frame, text="Add 🛒", width=68,
                          fg_color=COLOR_HIGHLIGHT if stk > 0 else COLOR_ACCENT,
                          state="normal" if stk > 0 else "disabled",
                          command=lambda p=p_copy, q=qty_var: self._safe_add_to_cart(p, q)
                          ).pack(side="left", padx=2)

        for i in range(MAX_COLS):
            self.product_grid_frame.grid_columnconfigure(i, weight=1)

    def _safe_add_to_cart(self, product, qty_var):
        try:
            qty = int(qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Qty", "Enter a valid positive quantity!")
            return
        self.add_to_cart(product, qty)

    def _display_product_image(self, parent, product):
        img_path = product.get('image_path')
        use_path = img_path if (img_path and os.path.exists(img_path)) else (
            DEFAULT_IMAGE_PATH if os.path.exists(DEFAULT_IMAGE_PATH) else None)
        if use_path:
            try:
                pil = Image.open(use_path).resize((100, 100), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=pil, dark_image=pil, size=(100, 100))
                lbl = ctk.CTkLabel(parent, image=photo, text="")
                lbl.image = photo
                lbl.pack(pady=(8,0))
                return
            except Exception:
                pass
        ctk.CTkLabel(parent, text="📷", font=("Arial", 32),
                     fg_color=COLOR_SECONDARY, width=100, height=100, corner_radius=8).pack(pady=(8,0))

    def add_to_cart(self, product, quantity=1):
        if product['stock_quantity'] == 0:
            messagebox.showerror("Out of Stock", f"'{product['name']}' is out of stock!")
            return
        if product['stock_quantity'] < quantity:
            messagebox.showerror("Insufficient Stock",
                                 f"Only {product['stock_quantity']} {product['unit']} of '{product['name']}' available.")
            return
        for item in self.cart_items:
            if item['id'] == product['id']:
                new_qty = item['quantity'] + quantity
                if new_qty > product['stock_quantity']:
                    messagebox.showerror("Insufficient Stock",
                                         f"Cannot add {quantity} more. Available: {product['stock_quantity']}, in cart: {item['quantity']}")
                    return
                item['quantity'] = new_qty
                item['total']    = round(new_qty * item['price'], 2)
                self._update_cart_display()
                return
        self.cart_items.append({
            'id':       product['id'],
            'name':     product['name'],
            'price':    product['price'],
            'unit':     product['unit'],
            'quantity': quantity,
            'total':    round(product['price'] * quantity, 2)
        })
        self._update_cart_display()

    def _add_by_barcode(self):
        barcode = self.barcode_var.get().strip()
        if not barcode:
            return
        product = self.db.get_product_by_barcode(barcode)
        if product:
            self.add_to_cart(product, 1)
            self.barcode_var.set("")
        else:
            messagebox.showerror("Not Found", f"No product found with barcode: {barcode}")
            self.barcode_var.set("")

    def _update_cart_display(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()

        if not self.cart_items:
            ctk.CTkLabel(self.cart_frame, text="Cart is empty",
                         text_color=COLOR_ACCENT, font=("Arial", 13)).pack(pady=30)
            self._update_cart_totals()
            return

        # Column headers
        hdr = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0,4))
        for txt, w in [("Item", 140), ("Qty", 90), ("Total", 70), ("", 30)]:
            ctk.CTkLabel(hdr, text=txt, font=("Arial", 10, "bold"),
                         text_color=COLOR_ACCENT, width=w).pack(side="left", padx=2)

        for i, item in enumerate(self.cart_items):
            row = ctk.CTkFrame(self.cart_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=item['name'][:18], width=140, anchor="w",
                         text_color=COLOR_TEXT).pack(side="left", padx=6, pady=6)

            qf = ctk.CTkFrame(row, fg_color="transparent")
            qf.pack(side="left", padx=4)
            ctk.CTkButton(qf, text="−", width=26, height=26, fg_color=COLOR_ERROR,
                          command=lambda idx=i: self._update_quantity(idx, -1)).pack(side="left")
            ctk.CTkLabel(qf, text=str(item['quantity']), width=34,
                         font=("Arial", 12, "bold"), text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkButton(qf, text="+", width=26, height=26, fg_color=COLOR_SUCCESS,
                          command=lambda idx=i: self._update_quantity(idx, 1)).pack(side="left")

            ctk.CTkLabel(row, text=f"${item['total']:.2f}", width=70,
                         text_color=COLOR_SUCCESS, font=("Arial", 12, "bold")).pack(side="left", padx=4)
            ctk.CTkButton(row, text="✕", width=28, height=28, fg_color=COLOR_ERROR,
                          command=lambda idx=i: self._remove_from_cart(idx)).pack(side="right", padx=4)

        self._update_cart_totals()

    def _update_quantity(self, index, delta):
        new_qty = self.cart_items[index]['quantity'] + delta
        if new_qty <= 0:
            self._remove_from_cart(index)
            return
        product = self.db.get_product_by_id(self.cart_items[index]['id'])
        if product and new_qty > product['stock_quantity']:
            messagebox.showerror("Stock Limit", f"Only {product['stock_quantity']} available!")
            return
        self.cart_items[index]['quantity'] = new_qty
        self.cart_items[index]['total']    = round(new_qty * self.cart_items[index]['price'], 2)
        self._update_cart_display()

    def _remove_from_cart(self, index):
        self.cart_items.pop(index)
        self._update_cart_display()

    def _update_cart_totals(self):
        subtotal        = round(sum(i['total'] for i in self.cart_items), 2)
        discount_rate   = DISCOUNT_RATES.get(self.discount_var.get(), 0.0)
        discount_amount = round(subtotal * discount_rate, 2)
        after_discount  = subtotal - discount_amount
        tax             = round(after_discount * TAX_RATE, 2) if self.tax_var.get() else 0.0
        total           = round(after_discount + tax, 2)

        self.subtotal_label.configure(text=f"Subtotal:     ${subtotal:>8.2f}")
        self.discount_label.configure(text=f"Discount:    -${discount_amount:>8.2f}")
        self.tax_label.configure(     text=f"Tax:           ${tax:>8.2f}")
        self.total_label.configure(   text=f"TOTAL:        ${total:>8.2f}")

    def _calc_totals(self):
        """Returns (subtotal, discount_amount, tax, total) for current cart state."""
        subtotal        = round(sum(i['total'] for i in self.cart_items), 2)
        discount_rate   = DISCOUNT_RATES.get(self.discount_var.get(), 0.0)
        discount_amount = round(subtotal * discount_rate, 2)
        after_discount  = subtotal - discount_amount
        tax             = round(after_discount * TAX_RATE, 2) if self.tax_var.get() else 0.0
        total           = round(after_discount + tax, 2)
        return subtotal, discount_amount, tax, total

    # ─────────────────────────────────────────────────────────────
    #  CHECKOUT  (Fixed)
    # ─────────────────────────────────────────────────────────────

    def checkout(self):
        if not self.cart_items:
            messagebox.showwarning("Empty Cart", "Please add items to the cart first!")
            return

        subtotal, discount_amount, tax, total = self._calc_totals()
        discount_type  = self.discount_var.get()
        payment_method = self.payment_method_var.get()

        # ── Cash validation ──
        cash_received = None
        change        = 0.0

        if payment_method == "cash":
            raw = self.cash_received_var.get().strip()
            if not raw:
                messagebox.showerror("Cash Required", "Please enter the cash amount received from the customer.")
                return
            try:
                cash_received = round(float(raw), 2)
            except ValueError:
                messagebox.showerror("Invalid Amount", f"'{raw}' is not a valid cash amount.")
                return
            if cash_received < total:
                shortage = round(total - cash_received, 2)
                messagebox.showerror("Insufficient Cash",
                                     f"Customer gave ${cash_received:.2f} but total is ${total:.2f}.\n"
                                     f"Short by: ${shortage:.2f}")
                return
            change = round(cash_received - total, 2)

        # ── Confirmation dialog ──
        lines = [
            f"{'Items in cart:':<22} {len(self.cart_items)}",
            f"{'Subtotal:':<22} ${subtotal:.2f}",
        ]
        if discount_amount > 0:
            lines.append(f"{'Discount (' + discount_type + '):':<22} -${discount_amount:.2f}")
        if tax > 0:
            lines.append(f"{'Tax (10%):':<22} ${tax:.2f}")
        lines.append(f"{'─'*35}")
        lines.append(f"{'TOTAL:':<22} ${total:.2f}")
        lines.append(f"{'Payment method:':<22} {payment_method.upper()}")
        if payment_method == "cash":
            lines.append(f"{'Cash received:':<22} ${cash_received:.2f}")
            lines.append(f"{'Change to give:':<22} ${change:.2f}")

        if not messagebox.askyesno("Confirm Checkout", "\n".join(lines)):
            return

        # ── Process transaction ──
        transaction_id = self.db.create_transaction(
            items          = self.cart_items,
            subtotal       = subtotal,
            tax            = tax,
            discount_type  = discount_type,
            discount_amount= discount_amount,
            total          = total,
            payment_method = payment_method,
            cash_received  = cash_received,
            customer_name  = self.customer_name_var.get().strip(),
            cashier        = self.current_cashier
        )

        if not transaction_id:
            messagebox.showerror("Transaction Failed",
                                 "Could not complete the transaction. Check stock levels and try again.")
            return

        # ── Generate & show receipt ──
        receipt_text = self._build_receipt(transaction_id, subtotal, discount_amount,
                                           tax, total, payment_method, cash_received, change)
        self._save_receipt_file(transaction_id, receipt_text)
        self._show_receipt_dialog(transaction_id, receipt_text, change)

        # ── Reset ──
        self.clear_cart()
        self.filter_products()
        self.refresh_inventory()
        self.update_analytics()
        self.update_daily_summary()

    def _build_receipt(self, txn_id, subtotal, discount_amount, tax, total,
                       payment_method, cash_received, change):
        w = 50
        lines = [
            "=" * w,
            "        GROCERY STORE PRO",
            f"   {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}",
            "=" * w,
            f"Transaction : {txn_id}",
            f"Cashier     : {self.current_cashier}",
        ]
        cust = self.customer_name_var.get().strip()
        if cust:
            lines.append(f"Customer    : {cust}")
        lines += ["-" * w, f"{'Item':<22} {'Qty':>4} {'Price':>7} {'Total':>8}", "-" * w]
        for item in self.cart_items:
            name = item['name'][:22]
            lines.append(f"{name:<22} {item['quantity']:>4} ${item['price']:>6.2f} ${item['total']:>7.2f}")
        lines += ["-" * w]
        lines.append(f"{'Subtotal:':>36} ${subtotal:>8.2f}")
        if discount_amount > 0:
            lines.append(f"{'Discount (' + self.discount_var.get() + '):':>36} -${discount_amount:>7.2f}")
        if tax > 0:
            lines.append(f"{'Tax (10%):':>36} ${tax:>8.2f}")
        lines += ["=" * w, f"{'TOTAL:':>36} ${total:>8.2f}", "=" * w]
        lines.append(f"{'Payment:':>36} {payment_method.upper()}")
        if payment_method == "cash" and cash_received is not None:
            lines.append(f"{'Cash received:':>36} ${cash_received:>8.2f}")
            lines.append(f"{'Change:':>36} ${change:>8.2f}")
        lines += ["=" * w, "   Thank you for shopping with us!", "=" * w]
        return "\n".join(lines)

    def _save_receipt_file(self, txn_id, text):
        path = os.path.join(RECEIPTS_DIR, f"{txn_id}.txt")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"Could not save receipt: {e}")

    def _show_receipt_dialog(self, txn_id, receipt_text, change):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("Receipt")
        dlg.geometry("520x600")
        dlg.grab_set()
        dlg.configure(fg_color=COLOR_BACKGROUND)

        ctk.CTkLabel(dlg, text="✅  Transaction Successful!",
                     font=("Arial", 15, "bold"), text_color=COLOR_SUCCESS).pack(pady=(16,4))
        if change > 0:
            ctk.CTkLabel(dlg, text=f"💵  Change to return: ${change:.2f}",
                         font=("Arial", 14, "bold"), text_color=COLOR_WARNING).pack(pady=4)

        txt = ctk.CTkTextbox(dlg, font=("Courier", 11), fg_color=COLOR_PRIMARY,
                             text_color=COLOR_TEXT, corner_radius=8)
        txt.pack(fill="both", expand=True, padx=16, pady=10)
        txt.insert("1.0", receipt_text)
        txt.configure(state="disabled")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="📋 Copy Receipt", fg_color=COLOR_HIGHLIGHT,
                      command=lambda: self._copy_to_clipboard(dlg, receipt_text)).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="✅ Close", fg_color=COLOR_SUCCESS,
                      command=dlg.destroy).pack(side="left", padx=8)

    def _copy_to_clipboard(self, parent, text):
        parent.clipboard_clear()
        parent.clipboard_append(text)
        messagebox.showinfo("Copied", "Receipt copied to clipboard!", parent=parent)

    def clear_cart(self):
        self.cart_items = []
        self.customer_name_var.set("")
        self.cash_received_var.set("")
        self.discount_var.set("None")
        self._update_cart_display()

    def _hold_order(self):
        if not self.cart_items:
            messagebox.showinfo("Empty Cart", "Nothing in cart to hold.")
            return
        data = {
            'items':     self.cart_items,
            'customer':  self.customer_name_var.get(),
            'timestamp': datetime.now().isoformat()
        }
        path = os.path.join(BACKUP_DIR, f"hold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Held", f"Order saved.\n{path}")
        self.clear_cart()

    # ─────────────────────────────────────────────────────────────
    #  INVENTORY LOGIC
    # ─────────────────────────────────────────────────────────────

    def refresh_inventory(self):
        term     = self.inv_search_var.get().strip()
        products = self.db.search_products(term) if term else self.db.get_all_products()

        # Remove all rows except header (row 0)
        for w in self.inventory_table_frame.winfo_children():
            info = w.grid_info()
            if info and int(info.get('row', 0)) > 0:
                w.destroy()

        self.selected_products = {}
        col_widths = [30, 50, 150, 130, 70, 60, 55, 70, 90, 100, 120]

        for i, p in enumerate(products, start=1):
            bg = COLOR_PRIMARY if i % 2 == 0 else COLOR_SECONDARY

            var = ctk.BooleanVar()
            self.selected_products[p['id']] = var
            ctk.CTkCheckBox(self.inventory_table_frame, variable=var, text="",
                            fg_color=COLOR_HIGHLIGHT, width=30
                            ).grid(row=i, column=0, padx=3, pady=2)

            vals = [str(p['id']), p['name'][:22], p['category'], f"${p['price']:.2f}",
                    str(p['stock_quantity']), p['unit'], str(p.get('min_stock',5) or 5),
                    (p.get('location') or '')[:14], (p.get('supplier') or '')[:14]]

            for col_idx, (val, cw) in enumerate(zip(vals, col_widths[1:]), start=1):
                tc = COLOR_TEXT
                if col_idx == 5:  # stock
                    min_s = p.get('min_stock', 5) or 5
                    tc = COLOR_ERROR if p['stock_quantity'] == 0 else (
                         COLOR_WARNING if p['stock_quantity'] <= min_s else COLOR_TEXT)
                ctk.CTkLabel(self.inventory_table_frame, text=val, width=cw,
                             text_color=tc, anchor="w").grid(row=i, column=col_idx, padx=3, pady=2)

            # Actions
            act = ctk.CTkFrame(self.inventory_table_frame, fg_color="transparent")
            act.grid(row=i, column=10, padx=3, pady=2)
            ctk.CTkButton(act, text="Edit", width=50, height=26, fg_color=COLOR_HIGHLIGHT,
                          command=lambda prod=dict(p): self.edit_product_dialog(prod)).pack(side="left", padx=2)
            ctk.CTkButton(act, text="Del", width=45, height=26, fg_color=COLOR_ERROR,
                          command=lambda pid=p['id']: self._delete_product(pid)).pack(side="left", padx=2)

    def _edit_selected_product(self):
        selected = [pid for pid, v in self.selected_products.items() if v.get()]
        if len(selected) != 1:
            messagebox.showwarning("Selection", "Select exactly one product to edit.")
            return
        p = self.db.get_product_by_id(selected[0])
        if p:
            self.edit_product_dialog(p)

    def _delete_selected_product(self):
        selected = [pid for pid, v in self.selected_products.items() if v.get()]
        if not selected:
            messagebox.showwarning("Selection", "Select at least one product to delete.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} product(s)?"):
            for pid in selected:
                self.db.delete_product(pid)
            self.refresh_inventory()
            self.filter_products()

    def _product_form_dialog(self, title, product=None):
        """Shared dialog for add & edit product."""
        dlg = ctk.CTkToplevel(self.root)
        dlg.title(title)
        dlg.geometry("560x640")
        dlg.grab_set()
        dlg.configure(fg_color=COLOR_BACKGROUND)

        ctk.CTkLabel(dlg, text=title, font=("Arial", 15, "bold"), text_color=COLOR_TEXT).pack(pady=(16,8))

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(padx=30, pady=4, fill="x")

        def field(row, label, default="", widget_type="entry", options=None):
            ctk.CTkLabel(form, text=label, text_color=COLOR_ACCENT, anchor="e",
                         width=110).grid(row=row, column=0, padx=8, pady=6, sticky="e")
            if widget_type == "entry":
                w = ctk.CTkEntry(form, width=280, fg_color=COLOR_SECONDARY)
                if default:
                    w.insert(0, str(default))
                w.grid(row=row, column=1, padx=8, pady=6, sticky="w")
            elif widget_type == "option":
                w = ctk.CTkOptionMenu(form, values=options, fg_color=COLOR_SECONDARY,
                                      button_color=COLOR_ACCENT, width=280)
                if default and default in options:
                    w.set(default)
                elif options:
                    w.set(options[0])
                w.grid(row=row, column=1, padx=8, pady=6, sticky="w")
            return w

        p = product or {}
        name_e     = field(0, "Name *",        p.get('name',''))
        barcode_e  = field(1, "Barcode",        p.get('barcode','') or '')
        cat_e      = field(2, "Category *",     p.get('category', CATEGORIES[1]), "option", CATEGORIES[1:])
        price_e    = field(3, "Price * ($)",    p.get('price',''))
        cost_e     = field(4, "Cost Price ($)", p.get('cost_price','') or '')
        stock_e    = field(5, "Stock *",        p.get('stock_quantity',''))
        unit_e     = field(6, "Unit *",         p.get('unit','pcs'), "option", UNITS)
        min_e      = field(7, "Min Stock",      p.get('min_stock', 5) or 5)
        loc_e      = field(8, "Location",       p.get('location','') or '')
        sup_e      = field(9, "Supplier",       p.get('supplier','') or '')

        img_var = ctk.StringVar(value=p.get('image_path','') or '')
        img_row = ctk.CTkFrame(form, fg_color="transparent")
        img_row.grid(row=10, column=0, columnspan=2, pady=6)
        ctk.CTkLabel(img_row, text="Image:", text_color=COLOR_ACCENT, width=110).pack(side="left")
        ctk.CTkLabel(img_row, textvariable=img_var, text_color=COLOR_ACCENT,
                     wraplength=200, font=("Arial", 9)).pack(side="left", padx=4)
        ctk.CTkButton(img_row, text="📷 Browse", width=90, fg_color=COLOR_ACCENT,
                      command=lambda: self._select_image(img_var, dlg)).pack(side="left", padx=4)

        err_lbl = ctk.CTkLabel(dlg, text="", text_color=COLOR_ERROR)
        err_lbl.pack(pady=2)

        def save():
            name = name_e.get().strip()
            if not name:
                err_lbl.configure(text="Product name is required.")
                return
            try:
                price = float(price_e.get())
                stock = int(stock_e.get())
            except ValueError:
                err_lbl.configure(text="Price and Stock must be valid numbers.")
                return
            cost_raw = cost_e.get().strip()
            cost  = float(cost_raw) if cost_raw else None
            min_s_raw = min_e.get().strip()
            min_s = int(min_s_raw) if min_s_raw else 5

            kwargs = dict(name=name, barcode=barcode_e.get().strip() or None,
                          category=cat_e.get(), price=price, stock=stock,
                          unit=unit_e.get(), cost_price=cost, min_stock=min_s,
                          location=loc_e.get().strip(), supplier=sup_e.get().strip(),
                          image_path=img_var.get() or None)
            if product:
                ok = self.db.update_product(product['id'],
                     name=kwargs['name'], barcode=kwargs['barcode'],
                     category=kwargs['category'], price=kwargs['price'],
                     stock_quantity=kwargs['stock'], unit=kwargs['unit'],
                     cost_price=kwargs['cost_price'], min_stock=kwargs['min_stock'],
                     location=kwargs['location'], supplier=kwargs['supplier'],
                     image_path=kwargs['image_path'])
                if ok:
                    messagebox.showinfo("Updated", "Product updated successfully!")
                    dlg.destroy(); self.refresh_inventory(); self.filter_products()
                else:
                    err_lbl.configure(text="Update failed.")
            else:
                pid = self.db.add_product(**kwargs)
                if pid:
                    messagebox.showinfo("Added", "Product added successfully!")
                    dlg.destroy(); self.refresh_inventory(); self.filter_products()
                else:
                    err_lbl.configure(text="Failed to add product.")

        ctk.CTkButton(dlg, text="💾  Save", fg_color=COLOR_SUCCESS, hover_color="#1e8449",
                      height=42, font=("Arial", 13, "bold"), command=save).pack(pady=16)

    def add_product_dialog(self):
        self._product_form_dialog("➕  Add New Product")

    def edit_product_dialog(self, product):
        self._product_form_dialog(f"✏️  Edit Product — {product['name']}", product)

    def _delete_product(self, product_id):
        if messagebox.askyesno("Confirm", "Delete this product permanently?"):
            if self.db.delete_product(product_id):
                self.refresh_inventory()
                self.filter_products()

    def _export_inventory(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files","*.csv")],
                                            initialfile="inventory_export.csv")
        if not path:
            return
        products = self.db.get_all_products()
        if not products:
            messagebox.showinfo("Empty", "No products to export.")
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=products[0].keys())
            writer.writeheader()
            writer.writerows(products)
        messagebox.showinfo("Exported", f"Exported {len(products)} products to:\n{path}")

    def _backup_database(self):
        path = self.db.backup_database()
        if path:
            messagebox.showinfo("Backup Created", f"Backup saved to:\n{path}")
        else:
            messagebox.showerror("Backup Failed", "Could not create backup.")

    def _select_image(self, path_var, parent):
        fp = filedialog.askopenfilename(parent=parent,
                                        filetypes=[("Image files","*.png *.jpg *.jpeg *.webp")])
        if fp:
            dest = os.path.join(IMAGES_DIR, os.path.basename(fp))
            shutil.copy(fp, dest)
            path_var.set(dest)

    # ─────────────────────────────────────────────────────────────
    #  RETURNS LOGIC
    # ─────────────────────────────────────────────────────────────

    def _lookup_transaction(self):
        tid = self.return_txn_var.get().strip()
        if not tid:
            messagebox.showwarning("Input Required", "Enter a Transaction ID.")
            return
        txn = self.db.get_transaction(tid)
        if txn:
            self._display_transaction_for_return(txn)
        else:
            messagebox.showerror("Not Found", f"Transaction '{tid}' not found.")

    def _show_daily_transactions(self):
        date = self.return_date_var.get().strip()
        txns = self.db.get_transactions_by_date_range(date, date)
        for w in self.transaction_details_frame.winfo_children():
            w.destroy()
        if not txns:
            ctk.CTkLabel(self.transaction_details_frame,
                         text=f"No transactions found for {date}.",
                         text_color=COLOR_WARNING).pack(pady=20)
            return
        for txn in txns:
            card = ModernCard(self.transaction_details_frame)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text=f"🧾 {txn['transaction_id']}",
                         font=("Arial", 12, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=10, pady=(6,0))
            ctk.CTkLabel(card, text=f"Total: ${txn['total_amount']:.2f}  |  {txn['created_at'][:19]}",
                         text_color=COLOR_ACCENT).pack(anchor="w", padx=10)
            ctk.CTkButton(card, text="View & Process Return", fg_color=COLOR_HIGHLIGHT,
                          command=lambda tid=txn['transaction_id']: self._view_txn_for_return(tid)
                          ).pack(anchor="e", padx=10, pady=6)

    def _view_txn_for_return(self, txn_id):
        txn = self.db.get_transaction(txn_id)
        if txn:
            self._display_transaction_for_return(txn)

    def _display_transaction_for_return(self, txn):
        for w in self.transaction_details_frame.winfo_children():
            w.destroy()

        hdr = ModernCard(self.transaction_details_frame)
        hdr.pack(fill="x", pady=4)
        ctk.CTkLabel(hdr, text=f"🧾  {txn['transaction_id']}",
                     font=("Arial", 13, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=12, pady=(8,2))
        ctk.CTkLabel(hdr, text=f"Date: {txn['created_at'][:19]}  |  Total: ${txn['total_amount']:.2f}  |  Cashier: {txn.get('cashier_name','-')}",
                     text_color=COLOR_ACCENT).pack(anchor="w", padx=12, pady=(0,8))

        for item in txn['items']:
            row = ctk.CTkFrame(self.transaction_details_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f"{item['product_name']}",
                         width=180, anchor="w", text_color=COLOR_TEXT).pack(side="left", padx=8, pady=8)
            ctk.CTkLabel(row, text=f"Qty sold: {item['quantity']}  @  ${item['unit_price']:.2f}",
                         text_color=COLOR_ACCENT).pack(side="left", padx=6)

            ctk.CTkLabel(row, text="Return qty:", text_color=COLOR_TEXT).pack(side="left", padx=(16,4))
            qty_var = ctk.StringVar(value="1")
            ctk.CTkEntry(row, textvariable=qty_var, width=50, fg_color=COLOR_PRIMARY).pack(side="left", padx=4)

            reason_var = ctk.StringVar()
            ctk.CTkEntry(row, textvariable=reason_var, placeholder_text="Reason…",
                         width=140, fg_color=COLOR_PRIMARY).pack(side="left", padx=4)

            ctk.CTkButton(row, text="↩ Return", fg_color=COLOR_WARNING, hover_color="#d68910", width=80,
                          command=lambda pid=item['product_id'], qv=qty_var, rv=reason_var,
                                         tid=txn['transaction_id'], maxq=item['quantity']:
                          self._process_return(tid, pid, qv.get(), rv.get(), maxq)
                          ).pack(side="right", padx=8)

    def _process_return(self, txn_id, product_id, qty_str, reason, max_qty):
        try:
            qty = int(qty_str)
            if qty <= 0 or qty > max_qty:
                messagebox.showerror("Invalid Qty", f"Return quantity must be between 1 and {max_qty}.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter a valid integer quantity.")
            return

        product = self.db.get_product_by_id(product_id)
        if not product:
            messagebox.showerror("Error", "Product not found.")
            return

        refund = round(product['price'] * qty, 2)
        if not messagebox.askyesno("Confirm Return",
                                   f"Return {qty} × {product['name']}\nRefund: ${refund:.2f}\nReason: {reason or '—'}"):
            return

        ret_id = self.db.process_return(txn_id, product_id, qty, reason, self.current_cashier)
        if ret_id:
            messagebox.showinfo("Return Processed", f"Return ID: {ret_id}\nRefund: ${refund:.2f}")
            self._load_returns_history()
            self.refresh_inventory()
            self.update_analytics()
            self.filter_products()
            for w in self.transaction_details_frame.winfo_children():
                w.destroy()
        else:
            messagebox.showerror("Failed", "Return processing failed. Check logs.")

    def _load_returns_history(self):
        for w in self.returns_history_frame.winfo_children():
            w.destroy()
        returns = self.db.get_all_returns()
        if not returns:
            ctk.CTkLabel(self.returns_history_frame, text="No returns recorded.",
                         text_color=COLOR_ACCENT).pack(pady=20)
            return
        for r in returns:
            row = ctk.CTkFrame(self.returns_history_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=r['return_id'][:22], width=180, anchor="w",
                         font=("Arial", 10), text_color=COLOR_ACCENT).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=r['product_name'][:20], width=140, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"Qty: {r['quantity']}", width=60).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"${r['refund_amount']:.2f}", text_color=COLOR_WARNING, width=70).pack(side="left")
            ctk.CTkLabel(row, text=(r.get('reason') or '—')[:20], text_color=COLOR_ACCENT, width=120).pack(side="left")
            ctk.CTkLabel(row, text=r['created_at'][:10], text_color=COLOR_ACCENT).pack(side="right", padx=8)

    # ─────────────────────────────────────────────────────────────
    #  ANALYTICS LOGIC  (Fixed — all 4 cards updated)
    # ─────────────────────────────────────────────────────────────

    def update_analytics(self):
        revenue     = self.db.get_total_revenue()
        items_sold  = self.db.get_total_items_sold()
        today_sales = self.db.get_todays_sales()
        returns_amt = self.db.get_total_returns_amount()

        self.revenue_label.configure(text=f"${revenue:,.2f}")
        self.items_label.configure(  text=f"{items_sold:,}")
        self.today_label.configure(  text=f"${today_sales:,.2f}")
        self.returns_label.configure(text=f"${returns_amt:,.2f}")

        # Top products
        for w in self.top_products_frame.winfo_children():
            w.destroy()
        top = self.db.get_top_selling_products(10)
        if not top:
            ctk.CTkLabel(self.top_products_frame, text="No sales data yet.",
                         text_color=COLOR_ACCENT).pack(pady=20)
        for i, p in enumerate(top, 1):
            row = ctk.CTkFrame(self.top_products_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"#{i}", width=30, text_color=COLOR_WARNING,
                         font=("Arial", 11, "bold")).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=p['name'][:28], width=200, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=p['category'], width=130, anchor="w",
                         text_color=COLOR_ACCENT).pack(side="left")
            ctk.CTkLabel(row, text=f"Qty: {p['total_sold']}", width=80).pack(side="left")
            ctk.CTkLabel(row, text=f"${p['total_revenue']:,.2f}",
                         text_color=COLOR_SUCCESS, width=90).pack(side="right", padx=8)

        # Low stock
        for w in self.low_stock_frame.winfo_children():
            w.destroy()
        low = self.db.get_low_stock_products()
        if not low:
            ctk.CTkLabel(self.low_stock_frame, text="✅  All products have sufficient stock!",
                         text_color=COLOR_SUCCESS, font=("Arial", 12)).pack(pady=16)
        for p in low:
            row = ctk.CTkFrame(self.low_stock_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            row.pack(fill="x", pady=2)
            icon = "🔴" if p['stock_quantity'] == 0 else "⚠️"
            ctk.CTkLabel(row, text=f"{icon} {p['name'][:28]}", width=220, anchor="w",
                         text_color=COLOR_WARNING).pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=f"Stock: {p['stock_quantity']} / Min: {p.get('min_stock',5)}",
                         width=150, text_color=COLOR_ERROR if p['stock_quantity']==0 else COLOR_WARNING
                         ).pack(side="left")
            ctk.CTkButton(row, text="+ Restock", width=80, height=26, fg_color=COLOR_HIGHLIGHT,
                          command=lambda pid=p['id']: self._quick_restock(pid)).pack(side="right", padx=8)

    def update_daily_summary(self):
        today_sales = self.db.get_todays_sales()
        self.today_sales_header_label.configure(text=f"Today: ${today_sales:.2f}")
        # also refresh analytics today card if visible
        try:
            self.today_label.configure(text=f"${today_sales:,.2f}")
        except Exception:
            pass

    def _quick_restock(self, product_id):
        qty = simpledialog.askinteger("Restock", "Quantity to add:", minvalue=1, maxvalue=10000)
        if qty:
            if self.db.update_stock(product_id, qty):
                messagebox.showinfo("Restocked", f"Added {qty} units!")
                self.refresh_inventory()
                self.update_analytics()
                self.filter_products()

    # ─────────────────────────────────────────────────────────────
    #  EXPENSES LOGIC
    # ─────────────────────────────────────────────────────────────

    def _add_expense(self):
        cat  = self.exp_category_var.get()
        desc = self.exp_desc_entry.get().strip()
        raw  = self.exp_amount_entry.get().strip()
        if not raw:
            messagebox.showerror("Error", "Enter an amount.")
            return
        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return

        eid = self.db.add_expense(cat, desc, amount)
        if eid:
            messagebox.showinfo("Added", f"Expense recorded (ID: {eid})")
            self.exp_desc_entry.delete(0, END)
            self.exp_amount_entry.delete(0, END)
            self._load_expenses()
            self.update_daily_summary()
        else:
            messagebox.showerror("Error", "Failed to save expense.")

    def _load_expenses(self):
        for w in self.expenses_list_frame.winfo_children():
            w.destroy()
        c = self.db.connection.cursor()
        c.execute('SELECT * FROM expenses ORDER BY date DESC LIMIT 100')
        exps = c.fetchall()
        if not exps:
            ctk.CTkLabel(self.expenses_list_frame, text="No expenses recorded.",
                         text_color=COLOR_ACCENT).pack(pady=20)
            return

        # Header
        hdr = ctk.CTkFrame(self.expenses_list_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0,4))
        for txt, w in [("Category",100),("Description",200),("Amount",80),("Date",100)]:
            ctk.CTkLabel(hdr, text=txt, font=("Arial",10,"bold"),
                         text_color=COLOR_ACCENT, width=w).pack(side="left", padx=4)

        total = 0.0
        for exp in exps:
            row = ctk.CTkFrame(self.expenses_list_frame, fg_color=COLOR_SECONDARY, corner_radius=8)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=exp['category'], width=100, anchor="w").pack(side="left", padx=6, pady=6)
            ctk.CTkLabel(row, text=(exp['description'] or '—')[:30], width=200, anchor="w",
                         text_color=COLOR_ACCENT).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"${exp['amount']:.2f}", width=80,
                         text_color=COLOR_WARNING, font=("Arial",11,"bold")).pack(side="left")
            ctk.CTkLabel(row, text=exp['date'][:10], text_color=COLOR_ACCENT).pack(side="right", padx=8)
            total += exp['amount']

        # Total footer
        ftr = ctk.CTkFrame(self.expenses_list_frame, fg_color=COLOR_PRIMARY, corner_radius=8)
        ftr.pack(fill="x", pady=6)
        ctk.CTkLabel(ftr, text=f"Total Expenses Shown: ${total:.2f}",
                     font=("Arial", 13, "bold"), text_color=COLOR_ERROR).pack(pady=8)

    # ─────────────────────────────────────────────────────────────
    #  RUN
    # ─────────────────────────────────────────────────────────────

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.db.close()
            self.root.destroy()


if __name__ == "__main__":
    app = GroceryStoreApp()
    app.run()