"""Database management for grocery store system"""

import sqlite3
from typing import List, Tuple, Dict, Optional, Any
from datetime import datetime
from constants import DATABASE_NAME


class DatabaseManager:
    """Handles all database operations with proper error handling"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(DATABASE_NAME)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
    
    def create_tables(self):
        """Create all necessary tables"""
        try:
            # Products table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL CHECK (price >= 0),
                    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
                    unit TEXT NOT NULL,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sales/Transactions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    total_amount REAL NOT NULL,
                    tax_amount REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    payment_method TEXT DEFAULT 'cash',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Transaction items table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaction_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            # Returns table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id TEXT UNIQUE NOT NULL,
                    original_transaction_id TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    refund_amount REAL NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_transaction_id) REFERENCES transactions(transaction_id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            print(f"Table creation error: {e}")
            raise
    
    # Product Operations
    def add_product(self, name: str, category: str, price: float, 
                    stock: int, unit: str, image_path: str = None) -> Optional[int]:
        """Add a new product to inventory"""
        try:
            self.cursor.execute('''
                INSERT INTO products (name, category, price, stock_quantity, unit, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, category, price, stock, unit, image_path))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error adding product: {e}")
            return None
    
    def get_all_products(self) -> List[Dict]:
        """Get all products with proper formatting"""
        try:
            self.cursor.execute('SELECT * FROM products ORDER BY name')
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error fetching products: {e}")
            return []
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get single product by ID"""
        try:
            self.cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error fetching product: {e}")
            return None
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product fields dynamically"""
        try:
            allowed_fields = ['name', 'category', 'price', 'stock_quantity', 'unit', 'image_path']
            updates = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if updates:
                values.append(product_id)
                query = f"UPDATE products SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                self.cursor.execute(query, values)
                self.connection.commit()
                return True
            return False
        except sqlite3.Error as e:
            print(f"Error updating product: {e}")
            return False
    
    def update_stock(self, product_id: int, quantity_change: int) -> bool:
        """Update stock quantity (positive for add, negative for subtract)"""
        try:
            self.cursor.execute('''
                UPDATE products 
                SET stock_quantity = stock_quantity + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND stock_quantity + ? >= 0
            ''', (quantity_change, product_id, quantity_change))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating stock: {e}")
            return False
    
    def search_products(self, search_term: str, category: str = "All") -> List[Dict]:
        """Search products with filters"""
        try:
            query = "SELECT * FROM products WHERE name LIKE ?"
            params = [f"%{search_term}%"]
            
            if category != "All":
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY name"
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error searching products: {e}")
            return []
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        """Get products with stock below threshold"""
        try:
            self.cursor.execute('''
                SELECT * FROM products 
                WHERE stock_quantity <= ? 
                ORDER BY stock_quantity ASC
            ''', (threshold,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching low stock products: {e}")
            return []
    
    # Transaction Operations
    def create_transaction(self, items: List[Dict], subtotal: float, 
                           tax: float, total: float) -> Optional[str]:
        """Create a new transaction with items"""
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{id(items)}"
        
        try:
            self.connection.execute("BEGIN TRANSACTION")
            
            # Insert transaction
            self.cursor.execute('''
                INSERT INTO transactions (transaction_id, total_amount, tax_amount, subtotal)
                VALUES (?, ?, ?, ?)
            ''', (transaction_id, total, tax, subtotal))
            
            # Insert items and update stock
            for item in items:
                self.cursor.execute('''
                    INSERT INTO transaction_items (transaction_id, product_id, product_name, 
                                                   quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (transaction_id, item['id'], item['name'], 
                      item['quantity'], item['price'], item['total']))
                
                # Update stock
                self.cursor.execute('''
                    UPDATE products 
                    SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND stock_quantity >= ?
                ''', (item['quantity'], item['id'], item['quantity']))
            
            self.connection.commit()
            return transaction_id
            
        except sqlite3.Error as e:
            self.connection.rollback()
            print(f"Error creating transaction: {e}")
            return None
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get transaction details by ID"""
        try:
            self.cursor.execute('''
                SELECT * FROM transactions WHERE transaction_id = ?
            ''', (transaction_id,))
            transaction = self.cursor.fetchone()
            
            if transaction:
                self.cursor.execute('''
                    SELECT * FROM transaction_items WHERE transaction_id = ?
                ''', (transaction_id,))
                items = [dict(row) for row in self.cursor.fetchall()]
                
                result = dict(transaction)
                result['items'] = items
                return result
            
            return None
        except sqlite3.Error as e:
            print(f"Error fetching transaction: {e}")
            return None
    
    # Return Operations
    def process_return(self, transaction_id: str, product_id: int, 
                       quantity: int, reason: str = "") -> Optional[str]:
        """Process a product return and refund"""
        return_id = f"RET{datetime.now().strftime('%Y%m%d%H%M%S')}{product_id}"
        
        try:
            self.connection.execute("BEGIN TRANSACTION")
            
            # Get product details
            product = self.get_product_by_id(product_id)
            if not product:
                return None
            
            # Get original transaction item
            self.cursor.execute('''
                SELECT * FROM transaction_items 
                WHERE transaction_id = ? AND product_id = ?
            ''', (transaction_id, product_id))
            original_item = self.cursor.fetchone()
            
            if not original_item:
                return None
            
            refund_amount = original_item['unit_price'] * quantity
            
            # Record return
            self.cursor.execute('''
                INSERT INTO returns (return_id, original_transaction_id, product_id, 
                                   quantity, refund_amount, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (return_id, transaction_id, product_id, quantity, refund_amount, reason))
            
            # Add back to stock
            self.cursor.execute('''
                UPDATE products 
                SET stock_quantity = stock_quantity + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (quantity, product_id))
            
            # Update transaction total (optional: adjust sales metrics)
            self.cursor.execute('''
                UPDATE transactions 
                SET total_amount = total_amount - ?
                WHERE transaction_id = ?
            ''', (refund_amount, transaction_id))
            
            self.connection.commit()
            return return_id
            
        except sqlite3.Error as e:
            self.connection.rollback()
            print(f"Error processing return: {e}")
            return None
    
    def get_all_returns(self) -> List[Dict]:
        """Get all return transactions"""
        try:
            self.cursor.execute('''
                SELECT r.*, p.name as product_name 
                FROM returns r
                JOIN products p ON r.product_id = p.id
                ORDER BY r.created_at DESC
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching returns: {e}")
            return []
    
    # Analytics Operations
    def get_total_revenue(self) -> float:
        """Calculate total revenue from all transactions"""
        try:
            self.cursor.execute('SELECT SUM(total_amount) as total FROM transactions')
            result = self.cursor.fetchone()
            return result['total'] if result['total'] else 0.0
        except sqlite3.Error as e:
            print(f"Error calculating revenue: {e}")
            return 0.0
    
    def get_total_items_sold(self) -> int:
        """Calculate total quantity of items sold"""
        try:
            self.cursor.execute('SELECT SUM(quantity) as total FROM transaction_items')
            result = self.cursor.fetchone()
            return result['total'] if result['total'] else 0
        except sqlite3.Error as e:
            print(f"Error calculating items sold: {e}")
            return 0
    
    def get_out_of_stock_items(self) -> List[Dict]:
        """Get all products with zero stock"""
        try:
            self.cursor.execute('SELECT * FROM products WHERE stock_quantity = 0 ORDER BY name')
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching out of stock items: {e}")
            return []
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product from inventory"""
        try:
            self.cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting product: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()