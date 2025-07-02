#!/usr/bin/env python3
"""
Complete database schema implementation based on the provided data model
"""

import sqlite3
from datetime import datetime

def create_complete_schema():
    """Create the complete database schema matching the data model"""
    
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    # Drop existing tables to recreate with proper schema
    tables_to_drop = [
        'inspection_task_inspection_scope_join',
        'inspection_task_role_join', 
        'inspection_task_notification_join',
        'inspection_task_employee_join',
        'inspection_tasks',
        'employees',
        'notifications',
        'roles',
        'inspection_scopes',
        'inspection_records',
        'connection_methods',
        'site_records',
        'time_intervals',
        'service_status',
        'frequency_records',
        'inspector_records'
    ]
    
    for table in tables_to_drop:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
    
    print("Creating complete database schema...")
    
    # 1. Inspection Task (Main entity)
    cursor.execute('''
        CREATE TABLE inspection_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT,
            site_project TEXT,
            hierarchy_item_name TEXT,
            description TEXT,
            mechanism TEXT,
            method TEXT,
            extent TEXT,
            frequency REAL,
            interval_type TEXT,
            inspection_priority INTEGER,
            last_inspection_date DATE,
            install_date DATE,
            due_date DATE,
            current_inspection_date DATE,
            inspector TEXT,
            status TEXT,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Employee
    cursor.execute('''
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            role_id INTEGER,
            department TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
    ''')
    
    # 3. Notification
    cursor.execute('''
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER,
            sender_id INTEGER,
            message TEXT,
            notification_type TEXT,
            read_status BOOLEAN DEFAULT 0,
            priority TEXT DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipient_id) REFERENCES employees (id),
            FOREIGN KEY (sender_id) REFERENCES employees (id)
        )
    ''')
    
    # 4. Role
    cursor.execute('''
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE,
            description TEXT,
            permissions TEXT, -- JSON string of permissions
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. Inspection Scope
    cursor.execute('''
        CREATE TABLE inspection_scopes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope_name TEXT,
            description TEXT,
            site_id INTEGER,
            created_by INTEGER,
            status TEXT DEFAULT 'draft',
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES site_records (id),
            FOREIGN KEY (created_by) REFERENCES employees (id)
        )
    ''')
    
    # 6. Inspection Record
    cursor.execute('''
        CREATE TABLE inspection_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            inspector_id INTEGER,
            inspection_date DATE,
            findings TEXT,
            recommendations TEXT,
            photos TEXT, -- JSON array of photo paths
            documents TEXT, -- JSON array of document paths
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id),
            FOREIGN KEY (inspector_id) REFERENCES employees (id)
        )
    ''')
    
    # 7. Connection Method
    cursor.execute('''
        CREATE TABLE connection_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT UNIQUE,
            description TEXT,
            category TEXT,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    # 8. Site Record
    cursor.execute('''
        CREATE TABLE site_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_code TEXT UNIQUE,
            site_name TEXT,
            location TEXT,
            manager_id INTEGER,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES employees (id)
        )
    ''')
    
    # 9. Time Interval
    cursor.execute('''
        CREATE TABLE time_intervals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interval_name TEXT UNIQUE,
            interval_value INTEGER,
            interval_unit TEXT, -- days, weeks, months, years
            description TEXT
        )
    ''')
    
    # 10. Service Status
    cursor.execute('''
        CREATE TABLE service_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT UNIQUE,
            description TEXT,
            color_code TEXT,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    # 11. Frequency Record
    cursor.execute('''
        CREATE TABLE frequency_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency_value REAL,
            frequency_unit TEXT,
            description TEXT
        )
    ''')
    
    # 12. Inspector Record
    cursor.execute('''
        CREATE TABLE inspector_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            certification_level TEXT,
            specializations TEXT, -- JSON array
            active BOOLEAN DEFAULT 1,
            last_training_date DATE,
            next_training_due DATE,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # Join Tables
    
    # 13. Inspection Task and Employee Join
    cursor.execute('''
        CREATE TABLE inspection_task_employee_join (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            employee_id INTEGER,
            relationship_type TEXT, -- assigned, reviewed, approved, etc.
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # 14. Inspection Task and Notification Join
    cursor.execute('''
        CREATE TABLE inspection_task_notification_join (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            notification_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id),
            FOREIGN KEY (notification_id) REFERENCES notifications (id)
        )
    ''')
    
    # 15. Inspection Task and Role Join
    cursor.execute('''
        CREATE TABLE inspection_task_role_join (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            role_id INTEGER,
            access_level TEXT, -- read, write, approve, etc.
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id),
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
    ''')
    
    # 16. Inspection Task and Inspection Scope Join
    cursor.execute('''
        CREATE TABLE inspection_task_inspection_scope_join (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            scope_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id),
            FOREIGN KEY (scope_id) REFERENCES inspection_scopes (id)
        )
    ''')
    
    conn.commit()
    print("Database schema created successfully!")
    
    return conn

def populate_lookup_data(conn):
    """Populate lookup tables with initial data"""
    cursor = conn.cursor()
    
    print("Populating lookup data...")
    
    # Roles
    roles = [
        ('Inspection Manager', 'Manager responsible for overseeing all inspection activities', '["view_all", "assign_tasks", "generate_reports", "manage_users"]'),
        ('Analyst', 'Employee reviewing scope, validating data, and monitoring progress', '["view_tasks", "review_scope", "update_status", "generate_analytics"]'),
        ('Scope Builder', 'Employee preparing inspection scopes', '["upload_scope", "create_scope", "view_tasks"]'),
        ('Field Inspector', 'Employee performing inspections', '["claim_tasks", "update_status", "upload_results", "view_assigned"]')
    ]
    
    for role_name, description, permissions in roles:
        cursor.execute('''
            INSERT OR IGNORE INTO roles (role_name, description, permissions)
            VALUES (?, ?, ?)
        ''', (role_name, description, permissions))
    
    # Connection Methods
    methods = [
        ('VI-EXT', 'Visual Inspection - External', 'Visual'),
        ('VI-INT', 'Visual Inspection - Internal', 'Visual'),
        ('Partial-VI INT', 'Partial Visual Inspection - Internal', 'Visual'),
        ('CUI-VI', 'Corrosion Under Insulation - Visual Inspection', 'Visual'),
        ('RT', 'Radiographic Testing', 'NDT'),
        ('UTT', 'Ultrasonic Thickness Testing', 'NDT'),
        ('Profile RT', 'Profile Radiographic Testing', 'NDT')
    ]
    
    for method_name, description, category in methods:
        cursor.execute('''
            INSERT OR IGNORE INTO connection_methods (method_name, description, category)
            VALUES (?, ?, ?)
        ''', (method_name, description, category))
    
    # Service Status
    statuses = [
        ('Out of Service', 'Equipment is out of service', '#FF4757'),
        ('UnInitiated', 'Task has not been started', '#94A3B8'),
        ('Claimed', 'Task has been claimed by inspector', '#42A5F5'),
        ('Field Complete', 'Field work completed', '#66BB6A'),
        ('Reported', 'Report submitted', '#00FFB3'),
        ('RT-Profile Crew', 'Assigned to RT Profile crew', '#AB47BC')
    ]
    
    for status_name, description, color in statuses:
        cursor.execute('''
            INSERT OR IGNORE INTO service_status (status_name, description, color_code)
            VALUES (?, ?, ?)
        ''', (status_name, description, color))
    
    # Time Intervals
    intervals = [
        ('Days', 1, 'days', 'Daily intervals'),
        ('Weeks', 7, 'days', 'Weekly intervals'),
        ('Months', 30, 'days', 'Monthly intervals'),
        ('Years', 365, 'days', 'Yearly intervals')
    ]
    
    for interval_name, value, unit, description in intervals:
        cursor.execute('''
            INSERT OR IGNORE INTO time_intervals (interval_name, interval_value, interval_unit, description)
            VALUES (?, ?, ?, ?)
        ''', (interval_name, value, unit, description))
    
    # Frequency Records
    frequencies = [
        (1, 'times', 'Once'),
        (3, 'times', 'Three times'),
        (5, 'times', 'Five times'),
        (7, 'times', 'Seven times'),
        (10, 'times', 'Ten times'),
        (15, 'times', 'Fifteen times')
    ]
    
    for freq_value, freq_unit, description in frequencies:
        cursor.execute('''
            INSERT OR IGNORE INTO frequency_records (frequency_value, frequency_unit, description)
            VALUES (?, ?, ?)
        ''', (freq_value, freq_unit, description))
    
    # Sample Employees
    sample_employees = [
        ('EMP001', 'John', 'Manager', 'manager@acuren.com', 1, 'Management'),
        ('EMP002', 'Jane', 'Analyst', 'analyst@acuren.com', 2, 'Analysis'),
        ('EMP003', 'Bob', 'Builder', 'builder@acuren.com', 3, 'Scope Building'),
        ('EMP004', 'Kent', 'Manuel', 'kent.manuel@acuren.com', 4, 'Field Operations'),
        ('EMP005', 'Brad', 'Sisk', 'brad.sisk@acuren.com', 4, 'Field Operations'),
        ('EMP006', 'Hunter', 'Doucet', 'hunter.doucet@acuren.com', 4, 'Field Operations')
    ]
    
    for emp_id, first_name, last_name, email, role_id, department in sample_employees:
        cursor.execute('''
            INSERT OR IGNORE INTO employees (employee_id, first_name, last_name, email, role_id, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (emp_id, first_name, last_name, email, role_id, department))
    
    # Sample Sites
    sites = [
        ('1201', 'Site 1201', 'Location A', 1),
        ('1401', 'Site 1401', 'Location B', 1),
        ('1501', 'Site 1501', 'Location C', 1),
        ('2901', 'Site 2901', 'Location D', 1),
        ('7101', 'Site 7101', 'Location E', 1),
        ('7201', 'Site 7201', 'Location F', 1)
    ]
    
    for site_code, site_name, location, manager_id in sites:
        cursor.execute('''
            INSERT OR IGNORE INTO site_records (site_code, site_name, location, manager_id)
            VALUES (?, ?, ?, ?)
        ''', (site_code, site_name, location, manager_id))
    
    conn.commit()
    print("Lookup data populated successfully!")

def migrate_existing_data(conn):
    """Migrate existing inspection tasks to new schema"""
    cursor = conn.cursor()
    
    # Check if old data exists
    try:
        cursor.execute("SELECT COUNT(*) FROM inspection_tasks")
        count = cursor.fetchone()[0]
        print(f"Found {count} existing inspection tasks")
        
        if count > 0:
            print("Data migration not needed - tasks already exist in new schema")
            return
            
    except sqlite3.OperationalError:
        print("No existing data to migrate")
    
    conn.commit()

if __name__ == '__main__':
    print("Creating complete database schema...")
    conn = create_complete_schema()
    populate_lookup_data(conn)
    migrate_existing_data(conn)
    conn.close()
    print("Database setup completed successfully!")

