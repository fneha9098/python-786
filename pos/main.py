"""Main Grocery Store Management System Application"""

import customtkinter as ctk
from PIL import Image, ImageDraw
import os
from datetime import datetime
from typing import List, Dict, Optional
from tkinter import messagebox, filedialog
import shutil

from constants import *
from database_manager import DatabaseManager


class GroceryStoreApp:
    """Main application class"""
    
    def __init__(self):
        # Configure CustomTkinter
        ctk.set_appearance_mode(THEME)
        ctk.set_default_color_theme("blue")
        
        # Main window
        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.minsize(1200, 600)
        
        # Database manager
        self.db = DatabaseManager()
        
        # Cart data
        self.cart_items = []
        self.tax_enabled = ctk.BooleanVar(value=True)
        
        # Create default placeholder image if it doesn't exist
        self.create_default_placeholder()
        
        # UI Components
        self.setup_ui()
        
        # Load initial data
        self.refresh_inventory()
        self.update_analytics()
        
    def create_default_placeholder(self):
        """Create a default placeholder image if it doesn't exist"""
        if not os.path.exists(DEFAULT_IMAGE_PATH):
            try:
                os.makedirs(os.path.dirname(DEFAULT_IMAGE_PATH), exist_ok=True)
                img = Image.new('RGB', (200, 200), color='gray')
                draw = ImageDraw.Draw(img)
                draw.text((70, 90), 'No Image', fill='white')
                img.save(DEFAULT_IMAGE_PATH)
                print(f"Created placeholder image at {DEFAULT_IMAGE_PATH}")
            except Exception as e:
                print(f"Could not create placeholder image: {e}")
        
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Notebook (Tab View)
        self.notebook = ctk.CTkTabview(self.main_container)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.pos_tab = self.notebook.add("POS Terminal")
        self.inventory_tab = self.notebook.add("Inventory Management")
        self.returns_tab = self.notebook.add("Returns Manager")
        self.analytics_tab = self.notebook.add("Analytics Dashboard")
        
        # Setup each tab
        self.setup_pos_tab()
        self.setup_inventory_tab()
        self.setup_returns_tab()
        self.setup_analytics_tab()
        
    def setup_pos_tab(self):
        """Setup Point of Sale tab"""
        # Left Panel - Product Grid
        left_panel = ctk.CTkFrame(self.pos_tab)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Search and filter
        filter_frame = ctk.CTkFrame(left_panel)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Search:", font=("Arial", 14)).pack(side="left", padx=5)
        self.pos_search_var = ctk.StringVar()
        self.pos_search_var.trace("w", lambda *args: self.filter_products())
        search_entry = ctk.CTkEntry(filter_frame, textvariable=self.pos_search_var, width=200)
        search_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(filter_frame, text="Category:", font=("Arial", 14)).pack(side="left", padx=5)
        self.pos_category_var = ctk.StringVar(value="All")
        category_menu = ctk.CTkOptionMenu(filter_frame, values=CATEGORIES, 
                                          variable=self.pos_category_var,
                                          command=lambda x: self.filter_products())
        category_menu.pack(side="left", padx=5)
        
        # Product Grid (Scrollable)
        self.product_grid_frame = ctk.CTkScrollableFrame(left_panel)
        self.product_grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Right Panel - Shopping Cart
        right_panel = ctk.CTkFrame(self.pos_tab, width=400)
        right_panel.pack(side="right", fill="both", padx=(5, 0))
        
        ctk.CTkLabel(right_panel, text="Shopping Cart", font=("Arial", 18, "bold")).pack(pady=10)
        
        # Cart items list
        self.cart_frame = ctk.CTkScrollableFrame(right_panel, height=400)
        self.cart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cart summary
        summary_frame = ctk.CTkFrame(right_panel)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        self.subtotal_label = ctk.CTkLabel(summary_frame, text="Subtotal: $0.00", 
                                           font=("Arial", 14))
        self.subtotal_label.pack(pady=5)
        
        tax_frame = ctk.CTkFrame(summary_frame)
        tax_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(tax_frame, text="Tax (10%):", font=("Arial", 14)).pack(side="left")
        self.tax_checkbox = ctk.CTkCheckBox(tax_frame, text="Enable", 
                                            variable=self.tax_enabled,
                                            command=self.update_cart_totals)
        self.tax_checkbox.pack(side="right")
        
        self.total_label = ctk.CTkLabel(summary_frame, text="Total: $0.00", 
                                        font=("Arial", 16, "bold"))
        self.total_label.pack(pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(right_panel)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.checkout_btn = ctk.CTkButton(button_frame, text="Checkout", 
                                          command=self.checkout, height=40,
                                          fg_color="green", hover_color="dark green")
        self.checkout_btn.pack(fill="x", pady=5)
        
        self.clear_cart_btn = ctk.CTkButton(button_frame, text="Clear Cart", 
                                            command=self.clear_cart, height=40,
                                            fg_color="orange")
        self.clear_cart_btn.pack(fill="x", pady=5)
        
    def setup_inventory_tab(self):
        """Setup Inventory Management tab"""
        # Top control panel
        control_panel = ctk.CTkFrame(self.inventory_tab)
        control_panel.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(control_panel, text="Add New Product", 
                      command=self.add_product_dialog, height=35,
                      fg_color="green").pack(side="left", padx=5)
        
        ctk.CTkButton(control_panel, text="Bulk Edit", 
                      command=self.bulk_edit_dialog, height=35).pack(side="left", padx=5)
        
        ctk.CTkButton(control_panel, text="Refresh", 
                      command=self.refresh_inventory, height=35).pack(side="left", padx=5)
        
        # Search
        search_frame = ctk.CTkFrame(control_panel)
        search_frame.pack(side="right", padx=5)
        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
        self.inv_search_var = ctk.StringVar()
        self.inv_search_var.trace("w", lambda *args: self.refresh_inventory())
        ctk.CTkEntry(search_frame, textvariable=self.inv_search_var, width=200).pack(side="left")
        
        # Inventory Table - Using CTkScrollableFrame with grid layout
        self.inventory_table_frame = ctk.CTkScrollableFrame(self.inventory_tab)
        self.inventory_table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Table headers
        headers = ["ID", "Name", "Category", "Price", "Stock", "Unit", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(self.inventory_table_frame, text=header, 
                                font=("Arial", 12, "bold"), width=120)
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Store product rows for updating
        self.product_rows = {}
        
    def setup_returns_tab(self):
        """Setup Returns Management tab"""
        # Transaction lookup
        lookup_frame = ctk.CTkFrame(self.returns_tab)
        lookup_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(lookup_frame, text="Transaction ID:", font=("Arial", 14)).pack(side="left", padx=5)
        self.return_txn_var = ctk.StringVar()
        ctk.CTkEntry(lookup_frame, textvariable=self.return_txn_var, width=200).pack(side="left", padx=5)
        ctk.CTkButton(lookup_frame, text="Lookup Transaction", 
                      command=self.lookup_transaction).pack(side="left", padx=5)
        
        # Transaction details display
        self.transaction_details_frame = ctk.CTkScrollableFrame(self.returns_tab, height=300)
        self.transaction_details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Returns history
        ctk.CTkLabel(self.returns_tab, text="Returns History", 
                     font=("Arial", 16, "bold")).pack(pady=10)
        
        self.returns_history_frame = ctk.CTkScrollableFrame(self.returns_tab, height=200)
        self.returns_history_frame.pack(fill="x", padx=10, pady=10)
        
        self.load_returns_history()
        
    def setup_analytics_tab(self):
        """Setup Analytics Dashboard tab"""
        # Summary cards
        summary_frame = ctk.CTkFrame(self.analytics_tab)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        # Total Revenue Card
        revenue_card = ctk.CTkFrame(summary_frame, fg_color="green", corner_radius=10)
        revenue_card.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        ctk.CTkLabel(revenue_card, text="Total Revenue", font=("Arial", 14)).pack(pady=10)
        self.revenue_label = ctk.CTkLabel(revenue_card, text="$0.00", 
                                          font=("Arial", 24, "bold"))
        self.revenue_label.pack(pady=10)
        
        # Items Sold Card
        items_card = ctk.CTkFrame(summary_frame, fg_color="blue", corner_radius=10)
        items_card.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        ctk.CTkLabel(items_card, text="Items Sold", font=("Arial", 14)).pack(pady=10)
        self.items_sold_label = ctk.CTkLabel(items_card, text="0", 
                                             font=("Arial", 24, "bold"))
        self.items_sold_label.pack(pady=10)
        
        # Out of Stock Items
        outofstock_frame = ctk.CTkFrame(self.analytics_tab)
        outofstock_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(outofstock_frame, text="Out of Stock Items", 
                     font=("Arial", 16, "bold")).pack(pady=10)
        
        self.outofstock_list = ctk.CTkScrollableFrame(outofstock_frame)
        self.outofstock_list.pack(fill="both", expand=True)
        
    # POS Functions
    def filter_products(self):
        """Filter products based on search and category"""
        search_term = self.pos_search_var.get().strip()
        category = self.pos_category_var.get()
        
        if search_term:
            products = self.db.search_products(search_term, category)
        else:
            all_products = self.db.get_all_products()
            if category != "All":
                products = [p for p in all_products if p['category'] == category]
            else:
                products = all_products
        
        self.display_product_grid(products)
    
    def display_product_grid(self, products: List[Dict]):
        """Display products in a grid with images"""
        # Clear existing widgets
        for widget in self.product_grid_frame.winfo_children():
            widget.destroy()
        
        # Display in rows of 4
        row = 0
        col = 0
        max_cols = 4
        
        for product in products:
            # Product card frame
            card = ctk.CTkFrame(self.product_grid_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Load and display image
            self.display_product_image(card, product)
            
            # Product info
            ctk.CTkLabel(card, text=product['name'], font=("Arial", 12, "bold")).pack(pady=2)
            ctk.CTkLabel(card, text=f"${product['price']:.2f}", 
                        font=("Arial", 11), text_color="green").pack(pady=2)
            
            stock_color = "red" if product['stock_quantity'] < LOW_STOCK_THRESHOLD else "white"
            ctk.CTkLabel(card, text=f"Stock: {product['stock_quantity']}", 
                        font=("Arial", 10), text_color=stock_color).pack(pady=2)
            
            ctk.CTkLabel(card, text=f"Unit: {product['unit']}", 
                        font=("Arial", 10)).pack(pady=2)
            
            # Add to cart button
            add_btn = ctk.CTkButton(card, text="Add to Cart", 
                                   command=lambda p=product: self.add_to_cart(p),
                                   height=30, width=100)
            add_btn.pack(pady=5)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(max_cols):
            self.product_grid_frame.grid_columnconfigure(i, weight=1)
    
    def display_product_image(self, parent, product: Dict):
        """Display product image in the card"""
        image_path = product.get('image_path')
        
        if image_path and os.path.exists(image_path):
            try:
                pil_image = Image.open(image_path)
                pil_image = pil_image.resize((120, 120), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(120, 120))
                img_label = ctk.CTkLabel(parent, image=photo, text="")
                img_label.image = photo  # Keep a reference
                img_label.pack(pady=5)
                return
            except Exception as e:
                print(f"Error loading image: {e}")
        
        # Show placeholder
        self.display_placeholder_image(parent)
    
    def display_placeholder_image(self, parent):
        """Display placeholder image when product image is not available"""
        try:
            if os.path.exists(DEFAULT_IMAGE_PATH):
                pil_image = Image.open(DEFAULT_IMAGE_PATH)
                pil_image = pil_image.resize((120, 120), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(120, 120))
                img_label = ctk.CTkLabel(parent, image=photo, text="")
                img_label.image = photo
                img_label.pack(pady=5)
            else:
                placeholder = ctk.CTkLabel(parent, text="No Image", width=120, height=120, 
                                          fg_color="gray", corner_radius=5)
                placeholder.pack(pady=5)
        except Exception as e:
            placeholder = ctk.CTkLabel(parent, text="No Image", width=120, height=120, 
                                      fg_color="gray", corner_radius=5)
            placeholder.pack(pady=5)
    
    def add_to_cart(self, product: Dict):
        """Add product to shopping cart"""
        # Check stock availability
        if product['stock_quantity'] <= 0:
            messagebox.showerror("Error", f"{product['name']} is out of stock!")
            return
        
        # Check if product already in cart
        for item in self.cart_items:
            if item['id'] == product['id']:
                if item['quantity'] + 1 > product['stock_quantity']:
                    messagebox.showerror("Error", f"Not enough stock for {product['name']}")
                    return
                item['quantity'] += 1
                item['total'] = item['quantity'] * item['price']
                self.update_cart_display()
                return
        
        # Add new item
        cart_item = {
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'total': product['price']
        }
        self.cart_items.append(cart_item)
        self.update_cart_display()
    
    def update_cart_display(self):
        """Update the cart display"""
        # Clear cart frame
        for widget in self.cart_frame.winfo_children():
            widget.destroy()
        
        if not self.cart_items:
            ctk.CTkLabel(self.cart_frame, text="Cart is empty", 
                        font=("Arial", 12)).pack(pady=20)
            self.update_cart_totals()
            return
        
        # Display each cart item
        for i, item in enumerate(self.cart_items):
            item_frame = ctk.CTkFrame(self.cart_frame)
            item_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(item_frame, text=item['name'], width=150, 
                        anchor="w").pack(side="left", padx=5)
            
            # Quantity controls
            qty_frame = ctk.CTkFrame(item_frame)
            qty_frame.pack(side="left", padx=10)
            
            ctk.CTkButton(qty_frame, text="-", width=30, 
                         command=lambda idx=i: self.update_quantity(idx, -1)).pack(side="left")
            
            ctk.CTkLabel(qty_frame, text=str(item['quantity']), width=30).pack(side="left")
            
            ctk.CTkButton(qty_frame, text="+", width=30,
                         command=lambda idx=i: self.update_quantity(idx, 1)).pack(side="left")
            
            ctk.CTkLabel(item_frame, text=f"${item['total']:.2f}", 
                        width=80).pack(side="left", padx=5)
            
            ctk.CTkButton(item_frame, text="X", width=30, fg_color="red",
                         command=lambda idx=i: self.remove_from_cart(idx)).pack(side="right", padx=5)
        
        self.update_cart_totals()
    
    def update_quantity(self, index: int, delta: int):
        """Update quantity of cart item"""
        new_qty = self.cart_items[index]['quantity'] + delta
        
        if new_qty <= 0:
            self.remove_from_cart(index)
        else:
            # Check stock availability
            product = self.db.get_product_by_id(self.cart_items[index]['id'])
            if product and new_qty > product['stock_quantity']:
                messagebox.showerror("Error", "Not enough stock available!")
                return
            
            self.cart_items[index]['quantity'] = new_qty
            self.cart_items[index]['total'] = new_qty * self.cart_items[index]['price']
            self.update_cart_display()
    
    def remove_from_cart(self, index: int):
        """Remove item from cart"""
        self.cart_items.pop(index)
        self.update_cart_display()
    
    def update_cart_totals(self):
        """Update subtotal, tax, and total labels"""
        subtotal = sum(item['total'] for item in self.cart_items)
        self.subtotal_label.configure(text=f"Subtotal: ${subtotal:.2f}")
        
        if self.tax_enabled.get():
            tax = subtotal * TAX_RATE
            total = subtotal + tax
            self.total_label.configure(text=f"Total: ${total:.2f}")
        else:
            self.total_label.configure(text=f"Total: ${subtotal:.2f}")
    
    def checkout(self):
        """Process checkout and generate receipt"""
        if not self.cart_items:
            messagebox.showwarning("Warning", "Cart is empty!")
            return
        
        subtotal = sum(item['total'] for item in self.cart_items)
        tax = subtotal * TAX_RATE if self.tax_enabled.get() else 0
        total = subtotal + tax
        
        # Confirm checkout
        if not messagebox.askyesno("Confirm Checkout", 
                                   f"Total Amount: ${total:.2f}\nProceed with checkout?"):
            return
        
        try:
            # Create transaction
            transaction_id = self.db.create_transaction(self.cart_items, subtotal, tax, total)
            
            if transaction_id:
                # Generate receipt
                self.generate_receipt(transaction_id, self.cart_items, subtotal, tax, total)
                
                messagebox.showinfo("Success", 
                                   f"Checkout complete!\nTransaction ID: {transaction_id}\nReceipt saved to receipts folder")
                
                # Clear cart and refresh
                self.clear_cart()
                self.refresh_inventory()
                self.update_analytics()
                self.filter_products()  # Refresh product grid
            else:
                messagebox.showerror("Error", "Transaction failed!")
        except Exception as e:
            messagebox.showerror("Error", f"Checkout error: {str(e)}")
    
    def generate_receipt(self, transaction_id: str, items: List[Dict], 
                         subtotal: float, tax: float, total: float):
        """Generate text-based receipt"""
        receipt_path = os.path.join(RECEIPTS_DIR, f"{transaction_id}.txt")
        
        try:
            with open(receipt_path, 'w') as f:
                f.write("="*50 + "\n")
                f.write("GROCERY STORE\n")
                f.write("="*50 + "\n")
                f.write(f"Transaction ID: {transaction_id}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-"*50 + "\n")
                f.write(f"{'Item':<20} {'Qty':<5} {'Price':<8} {'Total':<10}\n")
                f.write("-"*50 + "\n")
                
                for item in items:
                    f.write(f"{item['name'][:20]:<20} {item['quantity']:<5} "
                           f"${item['price']:<7.2f} ${item['total']:<9.2f}\n")
                
                f.write("-"*50 + "\n")
                f.write(f"{'Subtotal:':>30} ${subtotal:>8.2f}\n")
                if tax > 0:
                    f.write(f"{'Tax (10%):':>30} ${tax:>8.2f}\n")
                f.write(f"{'Total:':>30} ${total:>8.2f}\n")
                f.write("="*50 + "\n")
                f.write("Thank you for shopping with us!\n")
            
        except Exception as e:
            print(f"Error generating receipt: {e}")
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.cart_items = []
        self.update_cart_display()
    
    # Inventory Functions
    def refresh_inventory(self):
        """Refresh inventory display"""
        search_term = self.inv_search_var.get().strip()
        
        if search_term:
            products = self.db.search_products(search_term)
        else:
            products = self.db.get_all_products()
        
        # Clear existing rows (keep header row at index 0)
        for widget in self.inventory_table_frame.winfo_children():
            if int(widget.grid_info().get('row', 0)) > 0:
                widget.destroy()
        
        # Display products starting from row 1
        for i, product in enumerate(products, start=1):
            # ID
            id_label = ctk.CTkLabel(self.inventory_table_frame, text=str(product['id']), width=50)
            id_label.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            
            # Name
            name_label = ctk.CTkLabel(self.inventory_table_frame, text=product['name'], width=150, anchor="w")
            name_label.grid(row=i, column=1, padx=5, pady=2, sticky="w")
            
            # Category
            cat_label = ctk.CTkLabel(self.inventory_table_frame, text=product['category'], width=120)
            cat_label.grid(row=i, column=2, padx=5, pady=2, sticky="w")
            
            # Price
            price_label = ctk.CTkLabel(self.inventory_table_frame, text=f"${product['price']:.2f}", width=80)
            price_label.grid(row=i, column=3, padx=5, pady=2, sticky="w")
            
            # Stock (with color coding)
            stock_color = "red" if product['stock_quantity'] < LOW_STOCK_THRESHOLD else "white"
            stock_label = ctk.CTkLabel(self.inventory_table_frame, text=str(product['stock_quantity']), 
                                      width=60, text_color=stock_color)
            stock_label.grid(row=i, column=4, padx=5, pady=2, sticky="w")
            
            # Unit
            unit_label = ctk.CTkLabel(self.inventory_table_frame, text=product['unit'], width=80)
            unit_label.grid(row=i, column=5, padx=5, pady=2, sticky="w")
            
            # Actions frame
            actions_frame = ctk.CTkFrame(self.inventory_table_frame)
            actions_frame.grid(row=i, column=6, padx=5, pady=2)
            
            edit_btn = ctk.CTkButton(actions_frame, text="Edit", width=60,
                                     command=lambda p=product: self.edit_product_dialog(p))
            edit_btn.pack(side="left", padx=2)
            
            del_btn = ctk.CTkButton(actions_frame, text="Delete", width=60,
                                   fg_color="red", hover_color="dark red",
                                   command=lambda pid=product['id']: self.delete_product(pid))
            del_btn.pack(side="left", padx=2)
    
    def add_product_dialog(self):
        """Dialog for adding new product"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Product")
        dialog.geometry("500x650")
        dialog.grab_set()  # Make it modal
        
        # Form fields
        fields = {}
        
        ctk.CTkLabel(dialog, text="Product Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack()
        
        ctk.CTkLabel(dialog, text="Category:", font=("Arial", 12)).pack(pady=5)
        category_menu = ctk.CTkOptionMenu(dialog, values=CATEGORIES[1:])
        category_menu.pack()
        
        ctk.CTkLabel(dialog, text="Price ($):", font=("Arial", 12)).pack(pady=5)
        price_entry = ctk.CTkEntry(dialog, width=300)
        price_entry.pack()
        
        ctk.CTkLabel(dialog, text="Stock Quantity:", font=("Arial", 12)).pack(pady=5)
        stock_entry = ctk.CTkEntry(dialog, width=300)
        stock_entry.pack()
        
        ctk.CTkLabel(dialog, text="Unit (kg, pcs, pack, etc.):", font=("Arial", 12)).pack(pady=5)
        unit_entry = ctk.CTkEntry(dialog, width=300)
        unit_entry.pack()
        
        # Image selection
        image_path_var = ctk.StringVar()
        ctk.CTkButton(dialog, text="Select Product Image", 
                     command=lambda: self.select_image(image_path_var, dialog)).pack(pady=10)
        image_label = ctk.CTkLabel(dialog, text="No image selected", text_color="gray")
        image_label.pack()
        
        def save_product():
            try:
                name = name_entry.get().strip()
                category = category_menu.get()
                price = float(price_entry.get())
                stock = int(stock_entry.get())
                unit = unit_entry.get().strip()
                image_path = image_path_var.get() if image_path_var.get() else None
                
                if not all([name, category, unit]):
                    messagebox.showerror("Error", "Please fill all required fields!")
                    return
                
                if price <= 0:
                    messagebox.showerror("Error", "Price must be greater than 0!")
                    return
                
                if stock < 0:
                    messagebox.showerror("Error", "Stock cannot be negative!")
                    return
                
                product_id = self.db.add_product(name, category, price, stock, unit, image_path)
                if product_id:
                    messagebox.showinfo("Success", "Product added successfully!")
                    dialog.destroy()
                    self.refresh_inventory()
                    self.filter_products()  # Refresh POS grid
                else:
                    messagebox.showerror("Error", "Failed to add product!")
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for price and stock!")
        
        ctk.CTkButton(dialog, text="Save Product", command=save_product, 
                     fg_color="green", height=35).pack(pady=20)
    
    def edit_product_dialog(self, product: Dict):
        """Dialog for editing existing product"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Edit Product - {product['name']}")
        dialog.geometry("500x650")
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Product Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.insert(0, product['name'])
        name_entry.pack()
        
        ctk.CTkLabel(dialog, text="Category:", font=("Arial", 12)).pack(pady=5)
        category_menu = ctk.CTkOptionMenu(dialog, values=CATEGORIES[1:])
        category_menu.set(product['category'])
        category_menu.pack()
        
        ctk.CTkLabel(dialog, text="Price ($):", font=("Arial", 12)).pack(pady=5)
        price_entry = ctk.CTkEntry(dialog, width=300)
        price_entry.insert(0, str(product['price']))
        price_entry.pack()
        
        ctk.CTkLabel(dialog, text="Stock Quantity:", font=("Arial", 12)).pack(pady=5)
        stock_entry = ctk.CTkEntry(dialog, width=300)
        stock_entry.insert(0, str(product['stock_quantity']))
        stock_entry.pack()
        
        ctk.CTkLabel(dialog, text="Unit (kg, pcs, pack, etc.):", font=("Arial", 12)).pack(pady=5)
        unit_entry = ctk.CTkEntry(dialog, width=300)
        unit_entry.insert(0, product['unit'])
        unit_entry.pack()
        
        def save_changes():
            try:
                updates = {
                    'name': name_entry.get().strip(),
                    'category': category_menu.get(),
                    'price': float(price_entry.get()),
                    'stock_quantity': int(stock_entry.get()),
                    'unit': unit_entry.get().strip()
                }
                
                if updates['price'] <= 0:
                    messagebox.showerror("Error", "Price must be greater than 0!")
                    return
                
                if updates['stock_quantity'] < 0:
                    messagebox.showerror("Error", "Stock cannot be negative!")
                    return
                
                if self.db.update_product(product['id'], **updates):
                    messagebox.showinfo("Success", "Product updated successfully!")
                    dialog.destroy()
                    self.refresh_inventory()
                    self.filter_products()  # Refresh POS grid
                else:
                    messagebox.showerror("Error", "Failed to update product!")
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for price and stock!")
        
        ctk.CTkButton(dialog, text="Save Changes", command=save_changes, 
                     fg_color="green", height=35).pack(pady=20)
    
    def bulk_edit_dialog(self):
        """Dialog for bulk editing products"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Bulk Edit - Adjust Stock")
        dialog.geometry("400x300")
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Bulk Stock Adjustment", 
                    font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(dialog, text="Add to current stock for ALL products:", 
                    font=("Arial", 12)).pack(pady=5)
        ctk.CTkLabel(dialog, text="(Use negative numbers to reduce stock)", 
                    font=("Arial", 10), text_color="gray").pack()
        
        adjustment_entry = ctk.CTkEntry(dialog, width=200)
        adjustment_entry.pack(pady=10)
        
        def apply_adjustment():
            try:
                adjustment = int(adjustment_entry.get())
                products = self.db.get_all_products()
                
                success_count = 0
                for product in products:
                    new_stock = product['stock_quantity'] + adjustment
                    if new_stock >= 0:
                        if self.db.update_stock(product['id'], adjustment):
                            success_count += 1
                
                messagebox.showinfo("Success", f"Stock adjusted for {success_count} out of {len(products)} products!")
                dialog.destroy()
                self.refresh_inventory()
                self.filter_products()  # Refresh POS grid
                self.update_analytics()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid integer!")
        
        ctk.CTkButton(dialog, text="Apply Bulk Adjustment", 
                     command=apply_adjustment, fg_color="green", height=35).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy, height=35).pack()
    
    def delete_product(self, product_id: int):
        """Delete product from inventory"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?\nThis action cannot be undone!"):
            if self.db.delete_product(product_id):
                messagebox.showinfo("Success", "Product deleted successfully!")
                self.refresh_inventory()
                self.filter_products()  # Refresh POS grid
                self.update_analytics()
            else:
                messagebox.showerror("Error", "Failed to delete product!")
    
    def select_image(self, path_var, parent_dialog):
        """Open file dialog to select product image"""
        file_path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]
        )
        if file_path:
            # Copy image to product images folder
            filename = os.path.basename(file_path)
            dest_path = os.path.join(IMAGES_DIR, filename)
            
            # Handle duplicate filenames
            counter = 1
            name, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                dest_path = os.path.join(IMAGES_DIR, f"{name}_{counter}{ext}")
                counter += 1
            
            shutil.copy(file_path, dest_path)
            path_var.set(dest_path)
            
            # Update label
            for child in parent_dialog.winfo_children():
                if isinstance(child, ctk.CTkLabel) and child.cget("text") == "No image selected":
                    child.configure(text="Image selected!", text_color="green")
                    break
    
    # Returns Functions
    def lookup_transaction(self):
        """Look up transaction for return"""
        transaction_id = self.return_txn_var.get().strip()
        if not transaction_id:
            messagebox.showwarning("Warning", "Please enter a Transaction ID!")
            return
        
        transaction = self.db.get_transaction(transaction_id)
        
        if not transaction:
            messagebox.showerror("Error", "Transaction not found!")
            return
        
        # Clear previous display
        for widget in self.transaction_details_frame.winfo_children():
            widget.destroy()
        
        # Display transaction details
        header_frame = ctk.CTkFrame(self.transaction_details_frame)
        header_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(header_frame, 
                    text=f"Transaction: {transaction['transaction_id']}",
                    font=("Arial", 14, "bold")).pack(side="left", padx=10)
        
        ctk.CTkLabel(header_frame, 
                    text=f"Date: {transaction['created_at']}",
                    font=("Arial", 12)).pack(side="right", padx=10)
        
        ctk.CTkLabel(self.transaction_details_frame, 
                    text=f"Total Amount: ${transaction['total_amount']:.2f}",
                    font=("Arial", 12, "bold")).pack(pady=5)
        
        # Items for return
        ctk.CTkLabel(self.transaction_details_frame, 
                    text="Items Available for Return:", 
                    font=("Arial", 12, "bold")).pack(pady=10)
        
        for item in transaction['items']:
            item_frame = ctk.CTkFrame(self.transaction_details_frame)
            item_frame.pack(fill="x", pady=2, padx=10)
            
            ctk.CTkLabel(item_frame, 
                        text=f"{item['product_name']} - Qty purchased: {item['quantity']} - Price: ${item['unit_price']:.2f}",
                        width=400, anchor="w").pack(side="left", padx=5)
            
            # Return quantity input
            qty_frame = ctk.CTkFrame(item_frame)
            qty_frame.pack(side="left", padx=10)
            
            ctk.CTkLabel(qty_frame, text="Return Qty:").pack(side="left")
            qty_var = ctk.StringVar(value="1")
            qty_entry = ctk.CTkEntry(qty_frame, textvariable=qty_var, width=50)
            qty_entry.pack(side="left", padx=5)
            
            reason_entry = ctk.CTkEntry(item_frame, placeholder_text="Reason (optional)", width=200)
            reason_entry.pack(side="left", padx=5)
            
            ctk.CTkButton(item_frame, text="Process Return", 
                         command=lambda pid=item['product_id'], 
                                        qty_var=qty_var,
                                        reason=reason_entry,
                                        tid=transaction_id,
                                        max_qty=item['quantity']: 
                         self.process_return(tid, pid, qty_var.get(), reason.get(), max_qty),
                         fg_color="orange", width=120).pack(side="right", padx=5)
    
    def process_return(self, transaction_id: str, product_id: int, 
                       quantity_str: str, reason: str, max_qty: int):
        """Process the return"""
        try:
            quantity = int(quantity_str)
            
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity must be greater than 0!")
                return
            
            if quantity > max_qty:
                messagebox.showerror("Error", f"Cannot return more than purchased! (Max: {max_qty})")
                return
            
            product = self.db.get_product_by_id(product_id)
            if not product:
                messagebox.showerror("Error", "Product not found!")
                return
            
            refund_amount = product['price'] * quantity
            
            if messagebox.askyesno("Confirm Return", 
                                  f"Return {quantity} x {product['name']}?\nRefund amount: ${refund_amount:.2f}"):
                return_id = self.db.process_return(transaction_id, product_id, quantity, reason)
                
                if return_id:
                    messagebox.showinfo("Success", 
                                      f"Return processed successfully!\nReturn ID: {return_id}\nStock has been updated.")
                    self.load_returns_history()
                    self.refresh_inventory()
                    self.update_analytics()
                    self.filter_products()  # Refresh POS grid
                    
                    # Clear transaction lookup
                    self.return_txn_var.set("")
                    for widget in self.transaction_details_frame.winfo_children():
                        widget.destroy()
                else:
                    messagebox.showerror("Error", "Failed to process return!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity!")
    
    def load_returns_history(self):
        """Load and display returns history"""
        for widget in self.returns_history_frame.winfo_children():
            widget.destroy()
        
        returns = self.db.get_all_returns()
        
        if not returns:
            ctk.CTkLabel(self.returns_history_frame, text="No returns recorded yet.", 
                        font=("Arial", 12)).pack(pady=20)
            return
        
        # Header
        header_frame = ctk.CTkFrame(self.returns_history_frame)
        header_frame.pack(fill="x", pady=5)
        headers = ["Return ID", "Product", "Quantity", "Refund Amount", "Reason", "Date"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(header_frame, text=header, font=("Arial", 11, "bold"), 
                        width=120).grid(row=0, column=i, padx=5)
        
        for i, ret in enumerate(returns, start=1):
            ret_frame = ctk.CTkFrame(self.returns_history_frame)
            ret_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(ret_frame, text=ret['return_id'], width=120, anchor="w").grid(row=0, column=0, padx=5)
            ctk.CTkLabel(ret_frame, text=ret['product_name'], width=120, anchor="w").grid(row=0, column=1, padx=5)
            ctk.CTkLabel(ret_frame, text=str(ret['quantity']), width=80, anchor="w").grid(row=0, column=2, padx=5)
            ctk.CTkLabel(ret_frame, text=f"${ret['refund_amount']:.2f}", width=100, anchor="w").grid(row=0, column=3, padx=5)
            ctk.CTkLabel(ret_frame, text=ret['reason'] or "N/A", width=150, anchor="w").grid(row=0, column=4, padx=5)
            ctk.CTkLabel(ret_frame, text=ret['created_at'][:10], width=100, anchor="w").grid(row=0, column=5, padx=5)
    
    # Analytics Functions
    def update_analytics(self):
        """Update analytics dashboard"""
        # Update summary cards
        revenue = self.db.get_total_revenue()
        items_sold = self.db.get_total_items_sold()
        
        self.revenue_label.configure(text=f"${revenue:,.2f}")
        self.items_sold_label.configure(text=f"{items_sold:,}")
        
        # Update out of stock items
        for widget in self.outofstock_list.winfo_children():
            widget.destroy()
        
        outofstock_items = self.db.get_out_of_stock_items()
        
        if not outofstock_items:
            ctk.CTkLabel(self.outofstock_list, text="✓ No out of stock items!", 
                        font=("Arial", 14, "bold"), text_color="green").pack(pady=20)
        else:
            ctk.CTkLabel(self.outofstock_list, text=f"Items needing restock: {len(outofstock_items)}",
                        font=("Arial", 12, "bold"), text_color="red").pack(pady=5)
            
            for item in outofstock_items:
                item_frame = ctk.CTkFrame(self.outofstock_list)
                item_frame.pack(fill="x", pady=2, padx=10)
                
                ctk.CTkLabel(item_frame, text=item['name'], width=200, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(item_frame, text=f"Category: {item['category']}").pack(side="left", padx=5)
                ctk.CTkButton(item_frame, text="Restock", 
                             command=lambda pid=item['id']: self.restock_dialog(pid),
                             width=80).pack(side="right", padx=5)
    
    def restock_dialog(self, product_id: int):
        """Dialog to restock an item"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Restock Item")
        dialog.geometry("350x200")
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Enter quantity to add to stock:", 
                    font=("Arial", 12)).pack(pady=20)
        qty_entry = ctk.CTkEntry(dialog, width=200)
        qty_entry.pack(pady=10)
        
        def restock():
            try:
                qty = int(qty_entry.get())
                if qty > 0:
                    if self.db.update_stock(product_id, qty):
                        messagebox.showinfo("Success", f"Added {qty} items to stock!")
                        dialog.destroy()
                        self.refresh_inventory()
                        self.filter_products()  # Refresh POS grid
                        self.update_analytics()
                    else:
                        messagebox.showerror("Error", "Failed to update stock!")
                else:
                    messagebox.showerror("Error", "Please enter a positive number!")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number!")
        
        ctk.CTkButton(dialog, text="Restock", command=restock, 
                     fg_color="green", height=35).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy, 
                     height=35).pack()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.db.close()
            self.root.destroy()


if __name__ == "__main__":
    app = GroceryStoreApp()
    app.run()