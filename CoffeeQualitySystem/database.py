# database.py
"""
Database for storing predictions and user data
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
import hashlib
import logging

import bcrypt

from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Create all tables"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE,
                    full_name TEXT,
                    role TEXT DEFAULT 'user',
                    organization TEXT,
                    country TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Predictions table - matches your model's output
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    prediction_id TEXT UNIQUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Input features (matches your model)
                    aroma REAL,
                    flavor REAL,
                    aftertaste REAL,
                    acidity REAL,
                    body REAL,
                    balance REAL,
                    uniformity REAL,
                    clean_cup REAL,
                    sweetness REAL,
                    cupper_points REAL,
                    altitude REAL,
                    processing_method TEXT,
                    variety TEXT,
                    country TEXT,
                    region TEXT,
                    
                    -- Prediction results
                    predicted_class TEXT,
                    confidence REAL,
                    overall_score REAL,
                    
                    -- Model info
                    model_version TEXT,
                    
                    -- Metadata
                    notes TEXT,
                    is_favorite BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Models table (track your Colab model versions)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE,
                    name TEXT,
                    description TEXT,
                    accuracy REAL,
                    precision REAL,
                    recall REAL,
                    f1_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 0,
                    file_path TEXT
                )
            ''')
            
            # Datasets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    original_filename TEXT,
                    file_path TEXT,
                    row_count INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            conn.commit()

            # Add security-related columns if they don't exist
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                # Column probably already exists
                pass
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN locked_until TIMESTAMP')
            except sqlite3.OperationalError:
                pass

            # Create helpful indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_predictions_user_timestamp "
                "ON predictions(user_id, timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_predictions_user_class "
                "ON predictions(user_id, predicted_class)"
            )

            conn.commit()

            # Create default admin if not exists
            self.create_default_admin()
    
    def create_default_admin(self):
        """Create default admin user."""
        # Hash with bcrypt for new admins; legacy accounts may still use SHA-256
        password_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = "admin"')
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, full_name, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', password_hash, 'admin@coffee.com', 'Administrator', 'admin'))
                conn.commit()
    
    # User management
    def _hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password supporting both bcrypt and legacy SHA-256 hashes."""
        if stored_hash.startswith("$2"):  # bcrypt hash prefix
            try:
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            except ValueError:
                return False

        # Legacy SHA-256 fallback
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return legacy_hash == stored_hash

    def create_user(self, username, password, email=None, full_name=None, 
                   role='user', organization=None, country=None, is_active=True):
        password_hash = self._hash_password(password)
        with self.get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, email, full_name, role, organization, country, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, password_hash, email, full_name, role, organization, country, int(is_active)))
                conn.commit()
                return cursor.lastrowid
            except:
                return None

    def get_user_by_id(self, user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None

    def get_all_users(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, full_name, role, organization, country,
                       created_at, last_login, is_active
                FROM users
                ORDER BY username
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def update_user_profile(self, user_id, email=None, full_name=None, organization=None, country=None):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET email = ?, full_name = ?, organization = ?, country = ?
                WHERE id = ?
            ''', (email, full_name, organization, country, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def set_user_role(self, user_id, role):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def set_user_active(self, user_id, is_active: bool):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (int(is_active), user_id))
            conn.commit()
            return cursor.rowcount > 0

    def set_user_password(self, user_id, new_password):
        password_hash = self._hash_password(new_password)
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_user(self, user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def authenticate(self, username, password):
        """Authenticate user with basic lockout protection."""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,),
            )
            user = cursor.fetchone()

            if not user:
                return None

            user_dict = dict(user)

            # Check lockout
            locked_until = user_dict.get("locked_until")
            if locked_until:
                try:
                    locked_dt = datetime.fromisoformat(locked_until)
                    if locked_dt > datetime.utcnow():
                        logger.warning("Locked account login attempt for user %s", username)
                        return None
                except Exception:
                    # If parsing fails, ignore lock and continue
                    pass

            if self._verify_password(password, user_dict["password_hash"]):
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP, "
                    "failed_attempts = 0, locked_until = NULL WHERE id = ?",
                    (user["id"],),
                )
                conn.commit()
                return dict(user)

            # Failed attempt
            failed_attempts = int(user_dict.get("failed_attempts") or 0) + 1
            lock_until_ts = None
            if failed_attempts >= 5:
                # Lock for 15 minutes
                lock_until = datetime.utcnow() + timedelta(minutes=15)
                lock_until_ts = lock_until.isoformat()
                logger.warning("Locking user %s due to repeated failed logins", username)

            cursor.execute(
                "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                (failed_attempts, lock_until_ts, user["id"]),
            )
            conn.commit()
            return None
    
    # Prediction management
    def save_prediction(self, user_id, input_data, result):
        """Save prediction - works with your model's output"""
        prediction_id = f"PRED_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (
                    user_id, prediction_id, aroma, flavor, aftertaste, acidity,
                    body, balance, uniformity, clean_cup, sweetness, cupper_points,
                    altitude, processing_method, variety, country, region,
                    predicted_class, confidence, overall_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, prediction_id,
                input_data.get('Aroma'), input_data.get('Flavor'),
                input_data.get('Aftertaste'), input_data.get('Acidity'),
                input_data.get('Body'), input_data.get('Balance'),
                input_data.get('Uniformity', 10.0), input_data.get('Clean.Cup', 10.0),
                input_data.get('Sweetness', 10.0), input_data.get('Cupper.Points', 8.0),
                input_data.get('Altitude', 0), input_data.get('Processing.Method', 'Unknown'),
                input_data.get('Variety', 'Unknown'), input_data.get('Country.of.Origin', 'Unknown'),
                input_data.get('Region', 'Unknown'),
                result['predicted_class'], result['confidence'],
                result['overall_score']
            ))
            conn.commit()
            return prediction_id
    
    def get_user_predictions(self, user_id, limit=100):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM predictions 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_predictions(self, user_id, search_term=None, start_date=None, 
                          end_date=None, country=None, quality=None):
        query = "SELECT * FROM predictions WHERE user_id = ?"
        params = [user_id]
        
        if search_term:
            query += " AND (prediction_id LIKE ? OR country LIKE ? OR variety LIKE ?)"
            pattern = f"%{search_term}%"
            params.extend([pattern, pattern, pattern])
        
        if start_date:
            query += " AND date(timestamp) >= date(?)"
            params.append(start_date)
        
        if end_date:
            query += " AND date(timestamp) <= date(?)"
            params.append(end_date)
        
        if country:
            query += " AND country = ?"
            params.append(country)
        
        if quality:
            query += " AND predicted_class = ?"
            params.append(quality)
        
        query += " ORDER BY timestamp DESC"
        
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_predictions(self, limit=1000):
        """Get all predictions for admin users"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, u.username, u.full_name 
                FROM predictions p 
                JOIN users u ON p.user_id = u.id 
                ORDER BY p.timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_prediction(self, prediction_id, user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM predictions 
                WHERE prediction_id = ? AND user_id = ?
            ''', (prediction_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

# Global database instance
db = Database()