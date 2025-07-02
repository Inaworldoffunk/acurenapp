#!/usr/bin/env python3
"""
Data loader script to populate the Acuren Inspection database with real Excel data
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os

def load_excel_data():
    """Load and process the Excel data"""
    try:
        # Read the main data sheet
        df_main = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='All Units Ext Scope Data')
        
        # Read dropdown sheets
        df_inspectors = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Inspectors')
        df_sites = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Site')
        df_methods = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Method')
        df_status = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Status')
        df_priorities = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Inspection Priority')
        df_intervals = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Interval')
        df_frequencies = pd.read_excel('AllUnitsEXTTracker.xlsx', sheet_name='Frequency')
        
        return {
            'main_data': df_main,
            'inspectors': df_inspectors,
            'sites': df_sites,
            'methods': df_methods,
            'status_types': df_status,
            'priorities': df_priorities,
            'intervals': df_intervals,
            'frequencies': df_frequencies
        }
    except Exception as e:
        print(f"Error loading Excel data: {e}")
        return None

def clean_data(df):
    """Clean and prepare the main data"""
    # Replace NaN values with appropriate defaults
    df = df.fillna({
        'Site': '',
        'Site & Project': '',
        'Hierarchy Item Name': '',
        'Description': '',
        'Mechanism': '',
        'Method': '',
        'Extent': '',
        'Frequency': 0,
        'Interval': '',
        'Insp Priority': 0,
        'Inspector': 'Unassigned',
        'Status': 'UnInitiated',
        'Comments': ''
    })
    
    # Convert dates
    date_columns = ['Last Inspection Date', 'Install Date', 'Due Date', 'Current Insp Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Clean numeric columns
    df['Frequency'] = pd.to_numeric(df['Frequency'], errors='coerce').fillna(0)
    df['Insp Priority'] = pd.to_numeric(df['Insp Priority'], errors='coerce').fillna(0)
    
    return df

def populate_database():
    """Populate the SQLite database with Excel data"""
    
    # Load Excel data
    data = load_excel_data()
    if not data:
        print("Failed to load Excel data")
        return False
    
    # Connect to database
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute('DELETE FROM inspection_tasks')
        cursor.execute('DELETE FROM inspectors')
        cursor.execute('DELETE FROM sites')
        cursor.execute('DELETE FROM methods')
        cursor.execute('DELETE FROM status_types')
        
        print("Cleared existing data...")
        
        # Populate lookup tables
        print("Populating lookup tables...")
        
        # Inspectors
        inspectors = data['inspectors']['Inspectors'].dropna().unique()
        for inspector in inspectors:
            cursor.execute('INSERT OR IGNORE INTO inspectors (name) VALUES (?)', (str(inspector),))
        
        # Sites
        sites = data['sites']['Site'].dropna().unique()
        for site in sites:
            cursor.execute('INSERT OR IGNORE INTO sites (site_code, site_name) VALUES (?, ?)', 
                          (str(site), f'Site {site}'))
        
        # Methods
        methods = data['methods']['Method'].dropna().unique()
        for method in methods:
            cursor.execute('INSERT OR IGNORE INTO methods (method_name) VALUES (?)', (str(method),))
        
        # Status types
        status_types = data['status_types']['Status Type'].dropna().unique()
        for status in status_types:
            cursor.execute('INSERT OR IGNORE INTO status_types (status_name) VALUES (?)', (str(status),))
        
        print(f"Populated {len(inspectors)} inspectors, {len(sites)} sites, {len(methods)} methods, {len(status_types)} status types")
        
        # Clean and populate main data
        print("Processing main inspection data...")
        df_main = clean_data(data['main_data'])
        
        # Insert main data
        records_inserted = 0
        for _, row in df_main.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO inspection_tasks 
                    (site, site_project, hierarchy_item_name, description, mechanism, 
                     method, extent, frequency, interval_type, inspection_priority,
                     last_inspection_date, install_date, due_date, current_inspection_date,
                     inspector, status, comments)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row.get('Site', '')),
                    str(row.get('Site & Project', '')),
                    str(row.get('Hierarchy Item Name', '')),
                    str(row.get('Description', '')),
                    str(row.get('Mechanism', '')),
                    str(row.get('Method', '')),
                    str(row.get('Extent', '')),
                    float(row.get('Frequency', 0)) if pd.notna(row.get('Frequency')) else None,
                    str(row.get('Interval', '')),
                    int(row.get('Insp Priority', 0)) if pd.notna(row.get('Insp Priority')) else None,
                    row.get('Last Inspection Date').strftime('%Y-%m-%d') if pd.notna(row.get('Last Inspection Date')) else None,
                    row.get('Install Date').strftime('%Y-%m-%d') if pd.notna(row.get('Install Date')) else None,
                    row.get('Due Date').strftime('%Y-%m-%d') if pd.notna(row.get('Due Date')) else None,
                    row.get('Current Insp Date').strftime('%Y-%m-%d') if pd.notna(row.get('Current Insp Date')) else None,
                    str(row.get('Inspector', 'Unassigned')),
                    str(row.get('Status', 'UnInitiated')),
                    str(row.get('Comments', ''))
                ))
                records_inserted += 1
            except Exception as e:
                print(f"Error inserting row {records_inserted}: {e}")
                continue
        
        # Add sample users
        sample_users = [
            ('manager1', 'manager@acuren.com', 'Inspection Manager'),
            ('analyst1', 'analyst@acuren.com', 'Analyst'),
            ('builder1', 'builder@acuren.com', 'Scope Builder'),
            ('inspector1', 'inspector@acuren.com', 'Field Inspector')
        ]
        
        for username, email, role in sample_users:
            cursor.execute('INSERT OR IGNORE INTO users (username, email, role) VALUES (?, ?, ?)',
                          (username, email, role))
        
        conn.commit()
        print(f"Successfully inserted {records_inserted} inspection tasks")
        
        # Print summary statistics
        cursor.execute('SELECT COUNT(*) FROM inspection_tasks')
        total_tasks = cursor.fetchone()[0]
        
        cursor.execute('SELECT status, COUNT(*) FROM inspection_tasks GROUP BY status')
        status_counts = cursor.fetchall()
        
        cursor.execute('SELECT site, COUNT(*) FROM inspection_tasks GROUP BY site ORDER BY COUNT(*) DESC LIMIT 5')
        top_sites = cursor.fetchall()
        
        print(f"\nDatabase Summary:")
        print(f"Total tasks: {total_tasks}")
        print(f"Status distribution: {dict(status_counts)}")
        print(f"Top 5 sites by task count: {dict(top_sites)}")
        
        return True
        
    except Exception as e:
        print(f"Error populating database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starting data loading process...")
    success = populate_database()
    if success:
        print("Data loading completed successfully!")
    else:
        print("Data loading failed!")

