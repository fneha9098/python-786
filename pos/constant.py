"""Application constants and configuration"""

import os

# Database
DATABASE_NAME = "grocery_store.db"

# Application Settings
APP_TITLE = "Grocery Store Management System"
APP_WIDTH = 1400
APP_HEIGHT = 800
THEME = "dark"  # "dark" or "light"

# Tax Settings
TAX_RATE = 0.10  # 10%

# Stock Alerts
LOW_STOCK_THRESHOLD = 10

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images", "products")
DEFAULT_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "images", "default_image.png")
RECEIPTS_DIR = os.path.join(BASE_DIR, "receipts")

# Create directories if they don't exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(RECEIPTS_DIR, exist_ok=True)

# Product Categories
CATEGORIES = [
    "All",
    "Fruits & Vegetables",
    "Dairy & Eggs",
    "Meat & Seafood",
    "Bakery",
    "Beverages",
    "Snacks & Sweets",
    "Frozen Foods",
    "Household Supplies",
    "Personal Care",
    "Other"
]