"""
Complete Pharmacy Management System - FULL WORKING VERSION
Save as pharmacy.py and run
"""

import sys
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from decimal import Decimal
import json

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QFormLayout, QMessageBox, QHeaderView,
    QDialog, QDialogButtonBox, QComboBox, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QSplitter, QFrame, QStackedWidget,
    QScrollArea, QToolBar, QStatusBar, QCheckBox, QRadioButton,
    QButtonGroup, QProgressBar, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, QDate, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

# For charts and reports
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd


class Database:
    """Database handler"""
    
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()
        self.insert_sample_data()
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect('pharmacy.db')
        self.conn.row_factory = sqlite3.Row
    
    def execute(self, query, params=None):
        """Execute query and return cursor"""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
            return cursor.lastrowid if query.strip().upper().startswith("INSERT") else cursor
        except Exception as e:
            print(f"Database error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise e
    
    def fetch_all(self, query, params=None):
        """Fetch all results"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        """Fetch one result"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()
    
    def create_tables(self):
        """Create all tables"""
        # Users table
        self.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Suppliers table
        self.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Medicines table
        self.execute('''
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT NOT NULL,
                category TEXT,
                manufacturer TEXT,
                batch_no TEXT,
                expiry_date DATE,
                supplier_id INTEGER,
                cost_price REAL,
                selling_price REAL,
                quantity INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                location TEXT,
                prescription_required INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        
        # Sales table
        self.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                customer_name TEXT,
                customer_phone TEXT,
                subtotal REAL,
                tax REAL,
                discount REAL,
                total REAL,
                payment_method TEXT,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Sale items table
        self.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                medicine_id INTEGER,
                quantity INTEGER,
                price REAL,
                total REAL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (medicine_id) REFERENCES medicines(id)
            )
        ''')
        
        # Settings table
        self.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Stock movements
        self.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER,
                type TEXT,
                quantity INTEGER,
                reference TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def insert_sample_data(self):
        """Insert sample data"""
        # Check if users exist
        users = self.fetch_all("SELECT * FROM users")
        if not users:
            # Create admin user
            admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
            self.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                ("admin", admin_pass, "System Administrator", "admin")
            )
            
            # Create cashier user
            cashier_pass = hashlib.sha256("cashier123".encode()).hexdigest()
            self.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                ("cashier", cashier_pass, "John Doe", "cashier")
            )
        
        # Check if medicines exist
        medicines = self.fetch_all("SELECT * FROM medicines LIMIT 1")
        if not medicines:
            # Insert sample medicines
            samples = [
                ("123456789", "Paracetamol 500mg", "Pain Relief", "GSK", "B001", "2025-12-31", None, 50.0, 100.0, 100, 20, "A1", 0),
                ("123456788", "Ibuprofen 400mg", "Pain Relief", "Pfizer", "B002", "2025-11-30", None, 80.0, 150.0, 75, 15, "A2", 0),
                ("123456787", "Amoxicillin 250mg", "Antibiotic", "GSK", "B003", "2025-10-31", None, 120.0, 200.0, 50, 10, "B1", 1),
                ("123456786", "Vitamin C 1000mg", "Vitamins", "NatureWay", "B004", "2026-01-31", None, 30.0, 60.0, 200, 30, "C1", 0),
                ("123456785", "Aspirin 75mg", "Blood Thinner", "Bayer", "B005", "2025-09-30", None, 25.0, 50.0, 150, 20, "A3", 1),
                ("123456784", "Omeprazole 20mg", "Stomach Care", "Astra", "B006", "2025-08-31", None, 100.0, 180.0, 80, 15, "B2", 0),
            ]
            
            for med in samples:
                try:
                    self.execute('''
                        INSERT INTO medicines (
                            barcode, name, category, manufacturer, batch_no, expiry_date,
                            supplier_id, cost_price, selling_price, quantity, reorder_level, 
                            location, prescription_required
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', med)
                except Exception as e:
                    print(f"Error inserting medicine: {e}")
        
        # Default settings
        settings = self.fetch_one("SELECT * FROM settings LIMIT 1")
        if not settings:
            default_settings = [
                ("tax_rate", "13"),
                ("currency", "₨"),
                ("company_name", "City Pharmacy"),
                ("invoice_footer", "Thank you for shopping with us!"),
                ("low_stock_alert", "10"),
                ("expiry_alert_days", "30")
            ]
            for key, value in default_settings:
                self.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class LoginDialog(QDialog):
    """Login dialog"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user_data = None
        self.setWindowTitle("Pharmacy Management System - Login")
        self.setFixedSize(400, 500)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 50, 30, 50)
        
        title = QLabel("🏥 PHARMACY SYSTEM")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        subtitle = QLabel("Login to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet("padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px;")
        form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px;")
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        self.login_btn = QPushButton("LOGIN")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)
        
        demo_info = QLabel("Demo Accounts:\nAdmin: admin / admin123\nCashier: cashier / cashier123")
        demo_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        demo_info.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 20px;")
        layout.addWidget(demo_info)
        
        self.setLayout(layout)
        self.username_input.setFocus()
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password!")
            return
        
        hashed = hashlib.sha256(password.encode()).hexdigest()
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND password = ? AND is_active = 1",
            (username, hashed)
        )
        
        if user:
            self.user_data = dict(user)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or password!")


class DashboardWidget(QWidget):
    """Dashboard widget"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        self.welcome_label = QLabel(f"Welcome back, {self.user['full_name']}!")
        self.welcome_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.welcome_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.today_sales_card = self.create_stat_card("Today's Sales", "₨0", "#3498db")
        stats_layout.addWidget(self.today_sales_card)
        
        self.low_stock_card = self.create_stat_card("Low Stock Items", "0", "#e74c3c")
        stats_layout.addWidget(self.low_stock_card)
        
        self.expiring_card = self.create_stat_card("Expiring Soon", "0", "#f39c12")
        stats_layout.addWidget(self.expiring_card)
        
        self.total_meds_card = self.create_stat_card("Total Medicines", "0", "#27ae60")
        stats_layout.addWidget(self.total_meds_card)
        
        layout.addLayout(stats_layout)
        
        charts_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.sales_chart = self.create_chart()
        charts_splitter.addWidget(self.sales_chart)
        
        self.products_frame = QFrame()
        self.products_frame.setStyleSheet("background-color: white; border-radius: 10px;")
        products_layout = QVBoxLayout(self.products_frame)
        products_layout.addWidget(QLabel("Top Selling Products"))
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(2)
        self.products_table.setHorizontalHeaderLabels(["Product", "Sold"])
        products_layout.addWidget(self.products_table)
        charts_splitter.addWidget(self.products_frame)
        
        layout.addWidget(charts_splitter)
        
        alert_label = QLabel("⚠️ Low Stock Alerts")
        alert_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c; margin-top: 10px;")
        layout.addWidget(alert_label)
        
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(4)
        self.alert_table.setHorizontalHeaderLabels(["Medicine", "Current Stock", "Reorder Level", "Status"])
        layout.addWidget(self.alert_table)
        
        self.setLayout(layout)
    
    def create_stat_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border-top: 5px solid {color};
            }}
        """)
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return card
    
    def create_chart(self):
        figure = plt.figure(figsize=(6, 4), facecolor='#f0f0f0')
        canvas = FigureCanvas(figure)
        
        sales_data = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            result = self.db.fetch_one(
                "SELECT COALESCE(SUM(total), 0) FROM sales WHERE DATE(sale_date) = ?",
                (date,)
            )
            sales_data.append(result[0] if result else 0)
        
        ax = figure.add_subplot(111)
        days = [(datetime.now() - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]
        ax.plot(days, sales_data, marker='o', color='#3498db', linewidth=2)
        ax.fill_between(days, sales_data, alpha=0.3, color='#3498db')
        ax.set_title("Last 7 Days Sales", fontsize=12, fontweight='bold')
        ax.set_xlabel("Date")
        ax.set_ylabel("Sales (₨)")
        ax.grid(True, alpha=0.3)
        
        canvas.draw()
        return canvas
    
    def load_data(self):
        today = datetime.now().strftime("%Y-%m-%d")
        result = self.db.fetch_one(
            "SELECT COALESCE(SUM(total), 0) FROM sales WHERE DATE(sale_date) = ?",
            (today,)
        )
        today_total = result[0] if result else 0
        self.today_sales_card.findChild(QLabel, "value").setText(f"₨{today_total:,.0f}")
        
        low_stock = self.db.fetch_all("SELECT COUNT(*) FROM medicines WHERE quantity <= reorder_level")
        self.low_stock_card.findChild(QLabel, "value").setText(str(low_stock[0][0] if low_stock else 0))
        
        expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        expiring = self.db.fetch_all(
            "SELECT COUNT(*) FROM medicines WHERE expiry_date <= ? AND expiry_date >= ?",
            (expiry_date, datetime.now().strftime("%Y-%m-%d"))
        )
        self.expiring_card.findChild(QLabel, "value").setText(str(expiring[0][0] if expiring else 0))
        
        total = self.db.fetch_all("SELECT COUNT(*) FROM medicines")
        self.total_meds_card.findChild(QLabel, "value").setText(str(total[0][0] if total else 0))
        
        self.load_alerts()
        self.load_top_products()
    
    def load_alerts(self):
        medicines = self.db.fetch_all(
            "SELECT name, quantity, reorder_level FROM medicines WHERE quantity <= reorder_level LIMIT 10"
        )
        
        self.alert_table.setRowCount(len(medicines))
        for row, med in enumerate(medicines):
            self.alert_table.setItem(row, 0, QTableWidgetItem(med['name']))
            self.alert_table.setItem(row, 1, QTableWidgetItem(str(med['quantity'])))
            self.alert_table.setItem(row, 2, QTableWidgetItem(str(med['reorder_level'])))
            status = "⚠️ LOW" if med['quantity'] == 0 else "⚠️ Reorder"
            self.alert_table.setItem(row, 3, QTableWidgetItem(status))
        
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def load_top_products(self):
        products = self.db.fetch_all('''
            SELECT m.name, SUM(si.quantity) as total_sold
            FROM sale_items si
            JOIN medicines m ON si.medicine_id = m.id
            GROUP BY m.id
            ORDER BY total_sold DESC
            LIMIT 5
        ''')
        
        self.products_table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product['name']))
            self.products_table.setItem(row, 1, QTableWidgetItem(str(product['total_sold'])))
        
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


class MedicineDialog(QDialog):
    """Medicine add/edit dialog"""
    
    def __init__(self, db, medicine=None):
        super().__init__()
        self.db = db
        self.medicine = medicine
        self.setWindowTitle("Add Medicine" if not medicine else "Edit Medicine")
        self.setFixedSize(500, 600)
        self.setup_ui()
        
        if medicine:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.barcode_input = QLineEdit()
        form_layout.addRow("Barcode:", self.barcode_input)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Medicine name")
        form_layout.addRow("Name:*", self.name_input)
        
        self.category_input = QLineEdit()
        form_layout.addRow("Category:", self.category_input)
        
        self.manufacturer_input = QLineEdit()
        form_layout.addRow("Manufacturer:", self.manufacturer_input)
        
        self.batch_input = QLineEdit()
        form_layout.addRow("Batch No:", self.batch_input)
        
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate().addYears(1))
        form_layout.addRow("Expiry Date:", self.expiry_input)
        
        self.cost_price = QDoubleSpinBox()
        self.cost_price.setMaximum(100000)
        self.cost_price.setPrefix("₨ ")
        form_layout.addRow("Cost Price:", self.cost_price)
        
        self.selling_price = QDoubleSpinBox()
        self.selling_price.setMaximum(100000)
        self.selling_price.setPrefix("₨ ")
        form_layout.addRow("Selling Price:*", self.selling_price)
        
        self.quantity = QSpinBox()
        self.quantity.setMaximum(100000)
        form_layout.addRow("Quantity:*", self.quantity)
        
        self.reorder_level = QSpinBox()
        self.reorder_level.setValue(10)
        form_layout.addRow("Reorder Level:", self.reorder_level)
        
        self.location = QLineEdit()
        form_layout.addRow("Location:", self.location)
        
        self.prescription = QCheckBox("Prescription Required")
        form_layout.addRow("", self.prescription)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_data(self):
        self.barcode_input.setText(self.medicine['barcode'] or "")
        self.name_input.setText(self.medicine['name'])
        self.category_input.setText(self.medicine['category'] or "")
        self.manufacturer_input.setText(self.medicine['manufacturer'] or "")
        self.batch_input.setText(self.medicine['batch_no'] or "")
        
        if self.medicine['expiry_date']:
            date = QDate.fromString(self.medicine['expiry_date'], "yyyy-MM-dd")
            self.expiry_input.setDate(date)
        
        self.cost_price.setValue(self.medicine['cost_price'] or 0)
        self.selling_price.setValue(self.medicine['selling_price'] or 0)
        self.quantity.setValue(self.medicine['quantity'] or 0)
        self.reorder_level.setValue(self.medicine['reorder_level'] or 10)
        self.location.setText(self.medicine['location'] or "")
        self.prescription.setChecked(self.medicine['prescription_required'] == 1)
    
    def save(self):
        if not self.name_input.text():
            QMessageBox.warning(self, "Error", "Medicine name is required!")
            return
        
        if self.selling_price.value() <= 0:
            QMessageBox.warning(self, "Error", "Selling price must be greater than 0!")
            return
        
        data = (
            self.barcode_input.text() or None,
            self.name_input.text(),
            self.category_input.text() or None,
            self.manufacturer_input.text() or None,
            self.batch_input.text() or None,
            self.expiry_input.date().toString("yyyy-MM-dd"),
            None,
            self.cost_price.value(),
            self.selling_price.value(),
            self.quantity.value(),
            self.reorder_level.value(),
            self.location.text() or None,
            1 if self.prescription.isChecked() else 0
        )
        
        if self.medicine:
            query = """
                UPDATE medicines SET
                    barcode=?, name=?, category=?, manufacturer=?, batch_no=?,
                    expiry_date=?, supplier_id=?, cost_price=?, selling_price=?,
                    quantity=?, reorder_level=?, location=?, prescription_required=?
                WHERE id = ?
            """
            self.db.execute(query, data + (self.medicine['id'],))
            QMessageBox.information(self, "Success", "Medicine updated successfully!")
        else:
            query = """
                INSERT INTO medicines (
                    barcode, name, category, manufacturer, batch_no, expiry_date,
                    supplier_id, cost_price, selling_price, quantity, reorder_level,
                    location, prescription_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute(query, data)
            QMessageBox.information(self, "Success", "Medicine added successfully!")
        
        self.accept()


class InventoryWidget(QWidget):
    """Inventory management widget"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setup_ui()
        self.load_medicines()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, barcode, or category...")
        self.search_input.textChanged.connect(self.search_medicines)
        search_layout.addWidget(self.search_input)
        
        self.add_btn = QPushButton("+ Add Medicine")
        self.add_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 15px;")
        self.add_btn.clicked.connect(self.add_medicine)
        search_layout.addWidget(self.add_btn)
        
        layout.addLayout(search_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Barcode", "Name", "Category", "Batch", "Expiry", "Price", "Stock", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_medicines(self, search=""):
        if search:
            query = """
                SELECT * FROM medicines 
                WHERE name LIKE ? OR barcode LIKE ? OR category LIKE ?
                ORDER BY name
            """
            params = (f"%{search}%", f"%{search}%", f"%{search}%")
            medicines = self.db.fetch_all(query, params)
        else:
            medicines = self.db.fetch_all("SELECT * FROM medicines ORDER BY name")
        
        self.table.setRowCount(len(medicines))
        for row, med in enumerate(medicines):
            self.table.setItem(row, 0, QTableWidgetItem(str(med['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(med['barcode'] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(med['name']))
            self.table.setItem(row, 3, QTableWidgetItem(med['category'] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(med['batch_no'] or ""))
            self.table.setItem(row, 5, QTableWidgetItem(med['expiry_date'] or ""))
            self.table.setItem(row, 6, QTableWidgetItem(f"₨{med['selling_price']:.2f}"))
            
            stock_item = QTableWidgetItem(str(med['quantity']))
            if med['quantity'] <= med['reorder_level']:
                stock_item.setBackground(QColor(255, 200, 200))
            self.table.setItem(row, 7, stock_item)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 0, 5, 0)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px;")
            edit_btn.clicked.connect(lambda checked, m=med: self.edit_medicine(m))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
            delete_btn.clicked.connect(lambda checked, m=med: self.delete_medicine(m))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 8, action_widget)
    
    def search_medicines(self):
        self.load_medicines(self.search_input.text())
    
    def add_medicine(self):
        dialog = MedicineDialog(self.db)
        if dialog.exec():
            self.load_medicines()
    
    def edit_medicine(self, medicine):
        dialog = MedicineDialog(self.db, medicine)
        if dialog.exec():
            self.load_medicines()
    
    def delete_medicine(self, medicine):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {medicine['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM medicines WHERE id = ?", (medicine['id'],))
            self.load_medicines()
            QMessageBox.information(self, "Success", "Medicine deleted successfully!")


class POSWidget(QWidget):
    """Point of Sale widget"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.cart = []
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or barcode...")
        self.search_input.returnPressed.connect(self.search_product)
        left_layout.addWidget(self.search_input)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode here...")
        self.barcode_input.returnPressed.connect(self.add_by_barcode)
        left_layout.addWidget(self.barcode_input)
        
        self.products_list = QTableWidget()
        self.products_list.setColumnCount(4)
        self.products_list.setHorizontalHeaderLabels(["ID", "Name", "Price", "Stock"])
        self.products_list.itemDoubleClicked.connect(self.add_to_cart)
        left_layout.addWidget(self.products_list)
        
        layout.addWidget(left_widget, stretch=2)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        cart_title = QLabel("Shopping Cart")
        cart_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(cart_title)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Price", "Qty", "Total", "Actions"])
        right_layout.addWidget(self.cart_table)
        
        totals_frame = QFrame()
        totals_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px;")
        totals_layout = QFormLayout(totals_frame)
        
        self.subtotal_label = QLabel("₨0.00")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_label = QLabel("₨0.00")
        totals_layout.addRow("Tax (13%):", self.tax_label)
        
        self.total_label = QLabel("₨0.00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        totals_layout.addRow("Total:", self.total_label)
        
        right_layout.addWidget(totals_frame)
        
        btn_layout = QHBoxLayout()
        
        self.checkout_btn = QPushButton("Checkout")
        self.checkout_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        self.checkout_btn.clicked.connect(self.checkout)
        btn_layout.addWidget(self.checkout_btn)
        
        self.clear_btn = QPushButton("Clear Cart")
        self.clear_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
        self.clear_btn.clicked.connect(self.clear_cart)
        btn_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(btn_layout)
        
        layout.addWidget(right_widget, stretch=1)
        self.setLayout(layout)
    
    def load_products(self, search=""):
        if search:
            query = "SELECT id, name, selling_price, quantity FROM medicines WHERE name LIKE ? AND quantity > 0 LIMIT 20"
            products = self.db.fetch_all(query, (f"%{search}%",))
        else:
            query = "SELECT id, name, selling_price, quantity FROM medicines WHERE quantity > 0 LIMIT 20"
            products = self.db.fetch_all(query)
        
        self.products_list.setRowCount(len(products))
        for row, prod in enumerate(products):
            self.products_list.setItem(row, 0, QTableWidgetItem(str(prod['id'])))
            self.products_list.setItem(row, 1, QTableWidgetItem(prod['name']))
            self.products_list.setItem(row, 2, QTableWidgetItem(f"₨{prod['selling_price']:.2f}"))
            self.products_list.setItem(row, 3, QTableWidgetItem(str(prod['quantity'])))
        
        self.products_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def search_product(self):
        self.load_products(self.search_input.text())
    
    def add_by_barcode(self):
        barcode = self.barcode_input.text()
        if barcode:
            product = self.db.fetch_one(
                "SELECT id, name, selling_price, quantity FROM medicines WHERE barcode = ? AND quantity > 0",
                (barcode,)
            )
            if product:
                self.add_to_cart_by_id(dict(product))
                self.barcode_input.clear()
            else:
                QMessageBox.warning(self, "Not Found", "Product not found or out of stock!")
    
    def add_to_cart(self, item):
        row = item.row()
        product_id = int(self.products_list.item(row, 0).text())
        product = self.db.fetch_one("SELECT * FROM medicines WHERE id = ?", (product_id,))
        if product:
            self.add_to_cart_by_id(dict(product))
    
    def add_to_cart_by_id(self, product):
        for item in self.cart:
            if item['id'] == product['id']:
                if item['quantity'] < product['quantity']:
                    item['quantity'] += 1
                    item['total'] = item['quantity'] * item['price']
                else:
                    QMessageBox.warning(self, "Out of Stock", "Not enough stock available!")
                self.update_cart_display()
                return
        
        self.cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['selling_price'],
            'quantity': 1,
            'total': product['selling_price'],
            'max_qty': product['quantity']
        })
        self.update_cart_display()
    
    def update_cart_display(self):
        self.cart_table.setRowCount(len(self.cart))
        
        subtotal = 0
        for row, item in enumerate(self.cart):
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"₨{item['price']:.2f}"))
            
            qty_spinner = QSpinBox()
            qty_spinner.setRange(1, item['max_qty'])
            qty_spinner.setValue(item['quantity'])
            qty_spinner.valueChanged.connect(lambda v, r=row: self.update_quantity(r, v))
            self.cart_table.setCellWidget(row, 2, qty_spinner)
            
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"₨{item['total']:.2f}"))
            
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 4, remove_btn)
            
            subtotal += item['total']
        
        tax = subtotal * 0.13
        total = subtotal + tax
        
        self.subtotal_label.setText(f"₨{subtotal:.2f}")
        self.tax_label.setText(f"₨{tax:.2f}")
        self.total_label.setText(f"₨{total:.2f}")
        
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def update_quantity(self, row, quantity):
        self.cart[row]['quantity'] = quantity
        self.cart[row]['total'] = quantity * self.cart[row]['price']
        self.update_cart_display()
    
    def remove_from_cart(self, row):
        self.cart.pop(row)
        self.update_cart_display()
    
    def clear_cart(self):
        self.cart = []
        self.update_cart_display()
    
    def checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty!")
            return
        
        customer_name, ok = QInputDialog.getText(self, "Customer Info", "Customer Name:")
        if not ok or not customer_name:
            customer_name = "Walk-in Customer"
        
        customer_phone, ok = QInputDialog.getText(self, "Customer Info", "Phone Number:")
        if not ok:
            customer_phone = ""
        
        payment_method, ok = QInputDialog.getItem(
            self, "Payment", "Select Payment Method:",
            ["Cash", "Card", "Mobile Payment"], 0, False
        )
        if not ok:
            return
        
        subtotal = sum(item['total'] for item in self.cart)
        tax = subtotal * 0.13
        total = subtotal + tax
        
        invoice_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        sale_id = self.db.execute('''
            INSERT INTO sales (invoice_no, user_id, customer_name, customer_phone,
                             subtotal, tax, total, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (invoice_no, self.user['id'], customer_name, customer_phone,
              subtotal, tax, total, payment_method))
        
        for item in self.cart:
            self.db.execute('''
                INSERT INTO sale_items (sale_id, medicine_id, quantity, price, total)
                VALUES (?, ?, ?, ?, ?)
            ''', (sale_id, item['id'], item['quantity'], item['price'], item['total']))
            
            self.db.execute(
                "UPDATE medicines SET quantity = quantity - ? WHERE id = ?",
                (item['quantity'], item['id'])
            )
        
        receipt = f"""
        {'='*40}
        PHARMACY MANAGEMENT SYSTEM
        {'='*40}
        Invoice: {invoice_no}
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Cashier: {self.user['full_name']}
        Customer: {customer_name}
        {'-'*40}
        Items:
        """
        for item in self.cart:
            receipt += f"\n{item['name']} x{item['quantity']} = ₨{item['total']:.2f}"
        
        receipt += f"""
        {'-'*40}
        Subtotal: ₨{subtotal:.2f}
        Tax (13%): ₨{tax:.2f}
        Total: ₨{total:.2f}
        Payment: {payment_method}
        {'='*40}
        Thank you for shopping!
        """
        
        QMessageBox.information(self, "Sale Complete", receipt)
        
        self.clear_cart()
        self.load_products()


class SalesWidget(QWidget):
    """Sales history widget"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setup_ui()
        self.load_sales()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        
        self.date_filter = QComboBox()
        self.date_filter.addItems(["Today", "This Week", "This Month", "All Time"])
        self.date_filter.currentTextChanged.connect(self.load_sales)
        filter_layout.addWidget(self.date_filter)
        
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self.export_sales)
        filter_layout.addWidget(self.export_btn)
        
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Invoice", "Date", "Customer", "Subtotal", "Tax", "Total", "Payment"
        ])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_sales(self):
        filter_type = self.date_filter.currentText()
        
        if filter_type == "Today":
            date_filter = datetime.now().strftime("%Y-%m-%d")
            query = "SELECT * FROM sales WHERE DATE(sale_date) = ? ORDER BY sale_date DESC"
            sales = self.db.fetch_all(query, (date_filter,))
        elif filter_type == "This Week":
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            query = "SELECT * FROM sales WHERE DATE(sale_date) >= ? ORDER BY sale_date DESC"
            sales = self.db.fetch_all(query, (week_ago,))
        elif filter_type == "This Month":
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            query = "SELECT * FROM sales WHERE DATE(sale_date) >= ? ORDER BY sale_date DESC"
            sales = self.db.fetch_all(query, (month_ago,))
        else:
            query = "SELECT * FROM sales ORDER BY sale_date DESC"
            sales = self.db.fetch_all(query)
        
        self.table.setRowCount(len(sales))
        for row, sale in enumerate(sales):
            self.table.setItem(row, 0, QTableWidgetItem(sale['invoice_no']))
            self.table.setItem(row, 1, QTableWidgetItem(sale['sale_date']))
            self.table.setItem(row, 2, QTableWidgetItem(sale['customer_name'] or "Walk-in"))
            self.table.setItem(row, 3, QTableWidgetItem(f"₨{sale['subtotal']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"₨{sale['tax']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"₨{sale['total']:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(sale['payment_method']))
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def export_sales(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Sales Report", "sales_report.xlsx", "Excel Files (*.xlsx)"
        )
        if filename:
            sales = self.db.fetch_all("SELECT * FROM sales ORDER BY sale_date DESC")
            df = pd.DataFrame([dict(s) for s in sales])
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Success", f"Report saved to {filename}")


class SupplierDialog(QDialog):
    """Supplier add/edit dialog"""
    
    def __init__(self, db, supplier=None):
        super().__init__()
        self.db = db
        self.supplier = supplier
        self.setWindowTitle("Add Supplier" if not supplier else "Edit Supplier")
        self.setFixedSize(400, 400)
        self.setup_ui()
        
        if supplier:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        form_layout.addRow("Name:*", self.name_input)
        
        self.contact_input = QLineEdit()
        form_layout.addRow("Contact Person:", self.contact_input)
        
        self.phone_input = QLineEdit()
        form_layout.addRow("Phone:", self.phone_input)
        
        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)
        
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_data(self):
        self.name_input.setText(self.supplier['name'])
        self.contact_input.setText(self.supplier['contact_person'] or "")
        self.phone_input.setText(self.supplier['phone'] or "")
        self.email_input.setText(self.supplier['email'] or "")
        self.address_input.setText(self.supplier['address'] or "")
    
    def save(self):
        if not self.name_input.text():
            QMessageBox.warning(self, "Error", "Supplier name is required!")
            return
        
        data = (
            self.name_input.text(),
            self.contact_input.text() or None,
            self.phone_input.text() or None,
            self.email_input.text() or None,
            self.address_input.toPlainText() or None
        )
        
        if self.supplier:
            query = "UPDATE suppliers SET name=?, contact_person=?, phone=?, email=?, address=? WHERE id=?"
            self.db.execute(query, data + (self.supplier['id'],))
        else:
            query = "INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES (?, ?, ?, ?, ?)"
            self.db.execute(query, data)
        
        self.accept()


class SuppliersWidget(QWidget):
    """Supplier management widget"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setup_ui()
        self.load_suppliers()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.add_btn = QPushButton("+ Add Supplier")
        self.add_btn.clicked.connect(self.add_supplier)
        layout.addWidget(self.add_btn)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Contact", "Phone", "Email", "Actions"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_suppliers(self):
        suppliers = self.db.fetch_all("SELECT * FROM suppliers ORDER BY name")
        
        self.table.setRowCount(len(suppliers))
        for row, sup in enumerate(suppliers):
            self.table.setItem(row, 0, QTableWidgetItem(str(sup['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(sup['name']))
            self.table.setItem(row, 2, QTableWidgetItem(sup['contact_person'] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(sup['phone'] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(sup['email'] or ""))
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, s=sup: self.edit_supplier(s))
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, s=sup: self.delete_supplier(s))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 5, action_widget)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def add_supplier(self):
        dialog = SupplierDialog(self.db)
        if dialog.exec():
            self.load_suppliers()
    
    def edit_supplier(self, supplier):
        dialog = SupplierDialog(self.db, supplier)
        if dialog.exec():
            self.load_suppliers()
    
    def delete_supplier(self, supplier):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete supplier {supplier['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM suppliers WHERE id = ?", (supplier['id'],))
            self.load_suppliers()


class SettingsWidget(QWidget):
    """Settings widget"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setSuffix("%")
        form_layout.addRow("Tax Rate:", self.tax_rate)
        
        self.currency = QLineEdit()
        form_layout.addRow("Currency Symbol:", self.currency)
        
        self.company_name = QLineEdit()
        form_layout.addRow("Company Name:", self.company_name)
        
        self.invoice_footer = QTextEdit()
        self.invoice_footer.setMaximumHeight(80)
        form_layout.addRow("Invoice Footer:", self.invoice_footer)
        
        self.low_stock_alert = QSpinBox()
        self.low_stock_alert.setRange(1, 100)
        form_layout.addRow("Low Stock Alert Level:", self.low_stock_alert)
        
        self.expiry_alert = QSpinBox()
        self.expiry_alert.setRange(1, 365)
        self.expiry_alert.setSuffix(" days")
        form_layout.addRow("Expiry Alert Days:", self.expiry_alert)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        btn_layout.addWidget(backup_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        settings = self.db.fetch_all("SELECT key, value FROM settings")
        setting_dict = {row['key']: row['value'] for row in settings}
        
        self.tax_rate.setValue(float(setting_dict.get('tax_rate', 13)))
        self.currency.setText(setting_dict.get('currency', '₨'))
        self.company_name.setText(setting_dict.get('company_name', 'City Pharmacy'))
        self.invoice_footer.setText(setting_dict.get('invoice_footer', 'Thank you for shopping with us!'))
        self.low_stock_alert.setValue(int(setting_dict.get('low_stock_alert', 10)))
        self.expiry_alert.setValue(int(setting_dict.get('expiry_alert_days', 30)))
    
    def save_settings(self):
        settings = [
            ('tax_rate', str(self.tax_rate.value())),
            ('currency', self.currency.text()),
            ('company_name', self.company_name.text()),
            ('invoice_footer', self.invoice_footer.toPlainText()),
            ('low_stock_alert', str(self.low_stock_alert.value())),
            ('expiry_alert_days', str(self.expiry_alert.value()))
        ]
        
        for key, value in settings:
            self.db.execute(
                "UPDATE settings SET value = ? WHERE key = ?",
                (value, key)
            )
        
        QMessageBox.information(self, "Success", "Settings saved successfully!")
    
    def backup_database(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Backup Database", f"pharmacy_backup_{datetime.now().strftime('%Y%m%d')}.db",
            "Database Files (*.db)"
        )
        if filename:
            import shutil
            shutil.copy2('pharmacy.db', filename)
            QMessageBox.information(self, "Success", f"Database backed up to {filename}")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setWindowTitle("Pharmacy Management System")
        self.setGeometry(100, 100, 1400, 800)
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                text-align: left;
                padding: 12px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #27ae60;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("🏥 PHARMACY")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo)
        
        self.nav_buttons = []
        nav_items = [
            ("📊", "Dashboard", DashboardWidget),
            ("💊", "Inventory", InventoryWidget),
            ("💰", "Point of Sale", POSWidget),
            ("📈", "Sales", SalesWidget),
            ("🤝", "Suppliers", SuppliersWidget),
            ("⚙️", "Settings", SettingsWidget)
        ]
        
        self.stack = QStackedWidget()
        
        for icon, text, widget_class in nav_items:
            btn = QPushButton(f"{icon} {text}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, w=widget_class: self.switch_to_widget(w))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
            widget = widget_class(self.db, self.user)
            self.stack.addWidget(widget)
        
        sidebar_layout.addStretch()
        
        user_label = QLabel(f"👤 {self.user['full_name']}\n{self.user['role'].upper()}")
        user_label.setStyleSheet("padding: 10px; background-color: #1a252f; border-radius: 5px;")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(user_label)
        
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)
        
        self.nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)
        
        self.statusBar().showMessage("Ready")
    
    def switch_to_widget(self, widget_class):
        for i in range(self.stack.count()):
            if isinstance(self.stack.widget(i), widget_class):
                self.stack.setCurrentIndex(i)
                break
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            self.login_dialog = LoginDialog(self.db)
            if self.login_dialog.exec():
                self.user = self.login_dialog.user_data
                self.setup_ui()
            else:
                sys.exit()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTableWidget {
            alternate-background-color: #f8f9fa;
            selection-background-color: #27ae60;
        }
        QHeaderView::section {
            background-color: #2c3e50;
            color: white;
            padding: 5px;
            border: none;
        }
        QPushButton {
            border-radius: 5px;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
            padding: 5px;
            border: 1px solid #bdc3c7;
            border-radius: 3px;
        }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #27ae60;
        }
    """)
    
    db = Database()
    
    login_dialog = LoginDialog(db)
    if login_dialog.exec():
        user = login_dialog.user_data
        window = MainWindow(db, user)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()


if __name__ == "__main__":
    main()