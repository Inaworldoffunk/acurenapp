from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename
import numpy as np

app = Flask(__name__, static_folder=".")
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization (same as before)
def init_db():
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    # Create tables based on the Excel data structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspection_tasks (
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
    
    # Create lookup tables for dropdown values
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            role TEXT DEFAULT 'Field Inspector',
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_code TEXT UNIQUE,
            site_name TEXT,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT UNIQUE,
            description TEXT,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT UNIQUE,
            description TEXT,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            role TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_id INTEGER,
            message TEXT,
            notification_type TEXT,
            read_status BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id)
        )
    ''')
    
    # Add new tables for enhanced features
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scope_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by TEXT,
            status TEXT DEFAULT 'pending_review',
            records_count INTEGER,
            review_notes TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            assigned_by TEXT,
            assigned_to TEXT,
            assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (task_id) REFERENCES inspection_tasks (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE,
            site TEXT,
            total_tasks INTEGER,
            completed_tasks INTEGER,
            in_progress_tasks INTEGER,
            overdue_tasks INTEGER,
            completion_rate REAL,
            generated_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# Enhanced Dashboard Routes
@app.route('/api/dashboard/overview')
def dashboard_overview():
    """Get comprehensive dashboard overview with process-based metrics"""
    conn = sqlite3.connect('inspection_tracker.db')
    
    # Overall statistics
    summary_query = '''
        SELECT 
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status = 'Claimed' THEN 1 END) as claimed_tasks,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as completed_tasks,
            COUNT(CASE WHEN status = 'UnInitiated' THEN 1 END) as pending_tasks,
            COUNT(CASE WHEN due_date < date('now') AND status NOT IN ('Field Complete', 'Reported') THEN 1 END) as overdue_tasks
        FROM inspection_tasks
    '''
    
    summary = pd.read_sql_query(summary_query, conn).iloc[0].to_dict()
    
    # Process 1: Scope Preparation and Review
    scope_query = '''
        SELECT 
            COUNT(*) as total_scopes,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_scopes,
            COUNT(CASE WHEN status = 'pending_review' THEN 1 END) as pending_review
        FROM scope_uploads
        WHERE upload_date >= date('now', '-30 days')
    '''
    
    try:
        scope_data = pd.read_sql_query(scope_query, conn).iloc[0].to_dict()
    except:
        scope_data = {'total_scopes': 0, 'approved_scopes': 0, 'pending_review': 0}
    
    # Process 2: Task Assignment and Execution
    assignment_query = '''
        SELECT 
            COUNT(DISTINCT inspector) as active_inspectors,
            COUNT(CASE WHEN status = 'Claimed' THEN 1 END) as assigned_tasks,
            AVG(CASE WHEN status IN ('Field Complete', 'Reported') 
                THEN julianday(current_inspection_date) - julianday(due_date) END) as avg_completion_delay
        FROM inspection_tasks
        WHERE inspector != 'Unassigned'
    '''
    
    assignment_data = pd.read_sql_query(assignment_query, conn).iloc[0].to_dict()
    
    # Process 3: Progress Monitoring and Reporting
    progress_query = '''
        SELECT 
            site,
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as completed,
            ROUND(COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) * 100.0 / COUNT(*), 2) as completion_rate
        FROM inspection_tasks
        WHERE site != ''
        GROUP BY site
        ORDER BY completion_rate DESC
    '''
    
    progress_data = pd.read_sql_query(progress_query, conn).to_dict('records')
    
    # Recent activity
    activity_query = '''
        SELECT 
            hierarchy_item_name,
            site,
            inspector,
            status,
            updated_at
        FROM inspection_tasks
        WHERE updated_at >= datetime('now', '-24 hours')
        ORDER BY updated_at DESC
        LIMIT 10
    '''
    
    recent_activity = pd.read_sql_query(activity_query, conn).to_dict('records')
    
    conn.close()
    
    return jsonify({
        'summary': summary,
        'scope_preparation': scope_data,
        'task_assignment': assignment_data,
        'progress_monitoring': progress_data,
        'recent_activity': recent_activity
    })

@app.route('/api/analytics/process-performance')
def process_performance():
    """Get performance metrics for each of the three main processes"""
    conn = sqlite3.connect('inspection_tracker.db')
    
    # Process 1: Scope Preparation Efficiency
    scope_efficiency = '''
        SELECT 
            DATE(upload_date) as date,
            COUNT(*) as scopes_uploaded,
            AVG(records_count) as avg_records_per_scope
        FROM scope_uploads
        WHERE upload_date >= date('now', '-30 days')
        GROUP BY DATE(upload_date)
        ORDER BY date
    '''
    
    try:
        scope_data = pd.read_sql_query(scope_efficiency, conn).to_dict('records')
    except:
        scope_data = []
    
    # Process 2: Task Assignment Efficiency
    assignment_efficiency = '''
        SELECT 
            DATE(updated_at) as date,
            COUNT(CASE WHEN status = 'Claimed' THEN 1 END) as tasks_claimed,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as tasks_completed
        FROM inspection_tasks
        WHERE updated_at >= date('now', '-30 days')
        GROUP BY DATE(updated_at)
        ORDER BY date
    '''
    
    assignment_data = pd.read_sql_query(assignment_efficiency, conn).to_dict('records')
    
    # Process 3: Progress Monitoring Trends
    progress_trends = '''
        SELECT 
            site,
            method,
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as completed_tasks,
            COUNT(CASE WHEN due_date < date('now') AND status NOT IN ('Field Complete', 'Reported') THEN 1 END) as overdue_tasks
        FROM inspection_tasks
        WHERE site != ''
        GROUP BY site, method
        ORDER BY site, method
    '''
    
    progress_data = pd.read_sql_query(progress_trends, conn).to_dict('records')
    
    # Inspector performance
    inspector_performance = '''
        SELECT 
            inspector,
            COUNT(*) as total_assigned,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'Claimed' THEN 1 END) as in_progress,
            ROUND(COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) * 100.0 / COUNT(*), 2) as completion_rate
        FROM inspection_tasks
        WHERE inspector != 'Unassigned' AND inspector != ''
        GROUP BY inspector
        ORDER BY completion_rate DESC
    '''
    
    inspector_data = pd.read_sql_query(inspector_performance, conn).to_dict('records')
    
    conn.close()
    
    return jsonify({
        'scope_preparation': scope_data,
        'task_assignment': assignment_data,
        'progress_monitoring': progress_data,
        'inspector_performance': inspector_data
    })

@app.route('/api/analytics/predictive-insights')
def predictive_insights():
    """Generate predictive insights for inspection planning"""
    conn = sqlite3.connect('inspection_tracker.db')
    
    # Predict completion dates based on current progress
    prediction_query = '''
        SELECT 
            site,
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as completed_tasks,
            COUNT(CASE WHEN status = 'Claimed' THEN 1 END) as in_progress_tasks,
            COUNT(CASE WHEN status = 'UnInitiated' THEN 1 END) as pending_tasks,
            AVG(CASE WHEN status IN ('Field Complete', 'Reported') 
                THEN julianday(current_inspection_date) - julianday(due_date) END) as avg_completion_time
        FROM inspection_tasks
        WHERE site != ''
        GROUP BY site
    '''
    
    prediction_data = pd.read_sql_query(prediction_query, conn)
    
    # Calculate predictions
    predictions = []
    for _, row in prediction_data.iterrows():
        completion_rate = row['completed_tasks'] / row['total_tasks'] if row['total_tasks'] > 0 else 0
        remaining_tasks = row['pending_tasks'] + row['in_progress_tasks']
        
        # Simple prediction based on current rate
        if completion_rate > 0 and remaining_tasks > 0:
            estimated_days = remaining_tasks / (completion_rate * 7)  # Assuming weekly completion rate
            estimated_completion = datetime.now() + timedelta(days=estimated_days)
        else:
            estimated_completion = None
        
        predictions.append({
            'site': row['site'],
            'completion_rate': round(completion_rate * 100, 2),
            'remaining_tasks': remaining_tasks,
            'estimated_completion_date': estimated_completion.strftime('%Y-%m-%d') if estimated_completion else None,
            'risk_level': 'high' if completion_rate < 0.3 else 'medium' if completion_rate < 0.7 else 'low'
        })
    
    # Resource allocation recommendations
    resource_query = '''
        SELECT 
            inspector,
            COUNT(*) as current_workload,
            COUNT(CASE WHEN due_date < date('now', '+7 days') THEN 1 END) as urgent_tasks
        FROM inspection_tasks
        WHERE inspector != 'Unassigned' AND inspector != '' AND status = 'Claimed'
        GROUP BY inspector
        ORDER BY current_workload DESC
    '''
    
    resource_data = pd.read_sql_query(resource_query, conn).to_dict('records')
    
    conn.close()
    
    return jsonify({
        'site_predictions': predictions,
        'resource_allocation': resource_data
    })

# Enhanced File Upload with Process Integration
@app.route('/api/scope/upload', methods=['POST'])
def upload_scope_enhanced():
    """Enhanced scope upload with process tracking"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    uploaded_by = request.form.get('uploaded_by', 'Unknown')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process the Excel file
            df = pd.read_excel(filepath, sheet_name='All Units Ext Scope Data')
            
            # Record the upload
            conn = sqlite3.connect('inspection_tracker.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO scope_uploads (filename, uploaded_by, records_count, status)
                VALUES (?, ?, ?, 'pending_review')
            ''', (filename, uploaded_by, len(df)))
            
            upload_id = cursor.lastrowid
            
            # Insert data into database (same as before but with upload tracking)
            records_processed = 0
            for _, row in df.iterrows():
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
                        row.get('Frequency'),
                        str(row.get('Interval', '')),
                        row.get('Insp Priority'),
                        row.get('Last Inspection Date'),
                        row.get('Install Date'),
                        row.get('Due Date'),
                        row.get('Current Insp Date'),
                        str(row.get('Inspector', 'Unassigned')),
                        str(row.get('Status', 'UnInitiated')),
                        str(row.get('Comments', ''))
                    ))
                    records_processed += 1
                except Exception as e:
                    print(f"Error inserting row: {e}")
                    continue
            
            # Update upload status
            cursor.execute('''
                UPDATE scope_uploads 
                SET status = 'processed', records_count = ?
                WHERE id = ?
            ''', (records_processed, upload_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': 'File uploaded and processed successfully',
                'filename': filename,
                'upload_id': upload_id,
                'records_processed': records_processed,
                'status': 'processed'
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/scope/review/<int:upload_id>', methods=['PUT'])
def review_scope(upload_id):
    """Review and approve/reject uploaded scope"""
    data = request.get_json()
    status = data.get('status')  # 'approved' or 'rejected'
    notes = data.get('notes', '')
    reviewer = data.get('reviewer', 'Unknown')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE scope_uploads 
        SET status = ?, review_notes = ?
        WHERE id = ?
    ''', (status, notes, upload_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Upload not found'}), 404
    
    # Create notification
    cursor.execute('''
        INSERT INTO notifications (message, notification_type)
        VALUES (?, ?)
    ''', (f'Scope upload {upload_id} {status} by {reviewer}', 'scope_review'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'Scope {status} successfully'})

# Enhanced Task Management
@app.route('/api/tasks/assign', methods=['POST'])
def assign_task():
    """Assign task to inspector with tracking"""
    data = request.get_json()
    task_id = data.get('task_id')
    assigned_to = data.get('assigned_to')
    assigned_by = data.get('assigned_by', 'System')
    notes = data.get('notes', '')
    
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    # Update task
    cursor.execute('''
        UPDATE inspection_tasks 
        SET inspector = ?, status = 'Claimed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (assigned_to, task_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    
    # Record assignment
    cursor.execute('''
        INSERT INTO task_assignments (task_id, assigned_by, assigned_to, notes)
        VALUES (?, ?, ?, ?)
    ''', (task_id, assigned_by, assigned_to, notes))
    
    # Create notification
    cursor.execute('''
        INSERT INTO notifications (task_id, message, notification_type)
        VALUES (?, ?, ?)
    ''', (task_id, f'Task assigned to {assigned_to} by {assigned_by}', 'task_assignment'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task assigned successfully'})

# Progress Reporting
@app.route('/api/reports/generate', methods=['POST'])
def generate_progress_report():
    """Generate comprehensive progress report"""
    data = request.get_json()
    report_date = data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
    generated_by = data.get('generated_by', 'System')
    
    conn = sqlite3.connect('inspection_tracker.db')
    
    # Generate report data for each site
    report_query = '''
        SELECT 
            site,
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) as completed_tasks,
            COUNT(CASE WHEN status = 'Claimed' THEN 1 END) as in_progress_tasks,
            COUNT(CASE WHEN due_date < date('now') AND status NOT IN ('Field Complete', 'Reported') THEN 1 END) as overdue_tasks,
            ROUND(COUNT(CASE WHEN status IN ('Field Complete', 'Reported') THEN 1 END) * 100.0 / COUNT(*), 2) as completion_rate
        FROM inspection_tasks
        WHERE site != ''
        GROUP BY site
    '''
    
    report_data = pd.read_sql_query(report_query, conn)
    
    # Save report to database
    cursor = conn.cursor()
    for _, row in report_data.iterrows():
        cursor.execute('''
            INSERT INTO progress_reports 
            (report_date, site, total_tasks, completed_tasks, in_progress_tasks, 
             overdue_tasks, completion_rate, generated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_date, row['site'], row['total_tasks'], row['completed_tasks'],
            row['in_progress_tasks'], row['overdue_tasks'], row['completion_rate'],
            generated_by
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Progress report generated successfully',
        'report_date': report_date,
        'sites_included': len(report_data),
        'report_data': report_data.to_dict('records')
    })

# All other routes from the original app.py remain the same...
# (Including tasks, dashboard/summary, dashboard/charts, lookups, notifications, etc.)

# Copy all the remaining routes from the original app.py
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = sqlite3.connect('inspection_tracker.db')
    
    # Get query parameters for filtering
    site = request.args.get('site')
    inspector = request.args.get('inspector')
    status = request.args.get('status')
    method = request.args.get('method')
    priority = request.args.get('priority')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Build query with filters
    query = 'SELECT * FROM inspection_tasks WHERE 1=1'
    params = []
    
    if site:
        query += ' AND site = ?'
        params.append(site)
    if inspector:
        query += ' AND inspector = ?'
        params.append(inspector)
    if status:
        query += ' AND status = ?'
        params.append(status)
    if method:
        query += ' AND method = ?'
        params.append(method)
    if priority:
        query += ' AND inspection_priority = ?'
        params.append(priority)
    
    # Add pagination
    offset = (page - 1) * per_page
    query += ' ORDER BY due_date ASC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    df = pd.read_sql_query(query, conn, params=params)
    
    # Get total count for pagination
    count_query = 'SELECT COUNT(*) as total FROM inspection_tasks WHERE 1=1'
    count_params = params[:-2]  # Remove LIMIT and OFFSET params
    
    if site:
        count_query += ' AND site = ?'
    if inspector:
        count_query += ' AND inspector = ?'
    if status:
        count_query += ' AND status = ?'
    if method:
        count_query += ' AND method = ?'
    if priority:
        count_query += ' AND inspection_priority = ?'
    
    total_count = pd.read_sql_query(count_query, conn, params=count_params).iloc[0]['total']
    
    conn.close()
    
    return jsonify({
        'tasks': df.to_dict('records'),
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page
        }
    })

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    conn = sqlite3.connect('inspection_tracker.db')
    df = pd.read_sql_query('SELECT * FROM inspection_tasks WHERE id = ?', conn, params=[task_id])
    conn.close()
    
    if df.empty:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(df.iloc[0].to_dict())

@app.route('/api/tasks/<int:task_id>/claim', methods=['POST'])
def claim_task(task_id):
    data = request.get_json()
    inspector = data.get('inspector')
    
    if not inspector:
        return jsonify({'error': 'Inspector name required'}), 400
    
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    # Update task
    cursor.execute('''
        UPDATE inspection_tasks 
        SET inspector = ?, status = 'Claimed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (inspector, task_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    
    # Create notification
    cursor.execute('''
        INSERT INTO notifications (task_id, message, notification_type)
        VALUES (?, ?, ?)
    ''', (task_id, f'Task claimed by {inspector}', 'task_claimed'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task claimed successfully'})

@app.route('/api/tasks/<int:task_id>/update', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    
    conn = sqlite3.connect('inspection_tracker.db')
    cursor = conn.cursor()
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    allowed_fields = [
        'status', 'method', 'inspection_priority', 'current_inspection_date',
        'mechanism', 'comments', 'inspector'
    ]
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f'{field} = ?')
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No valid fields to update'}), 400
    
    update_fields.append('updated_at = CURRENT_TIMESTAMP')
    params.append(task_id)
    
    query = f'UPDATE inspection_tasks SET {", ".join(update_fields)} WHERE id = ?'
    cursor.execute(query, params)
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    
    # Create notification for status changes
    if 'status' in data:
        cursor.execute('''
            INSERT INTO notifications (task_id, message, notification_type)
            VALUES (?, ?, ?)
        ''', (task_id, f'Task status changed to {data["status"]}', 'status_change'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task updated successfully'})

# Lookup Data Routes
@app.route('/api/lookups/inspectors')
def get_inspectors():
    conn = sqlite3.connect('inspection_tracker.db')
    df = pd.read_sql_query('SELECT * FROM inspectors WHERE active = 1', conn)
    conn.close()
    return jsonify(df.to_dict('records'))

@app.route('/api/lookups/sites')
def get_sites():
    conn = sqlite3.connect('inspection_tracker.db')
    df = pd.read_sql_query('SELECT * FROM sites WHERE active = 1', conn)
    conn.close()
    return jsonify(df.to_dict('records'))

@app.route('/api/lookups/methods')
def get_methods():
    conn = sqlite3.connect('inspection_tracker.db')
    df = pd.read_sql_query('SELECT * FROM methods WHERE active = 1', conn)
    conn.close()
    return jsonify(df.to_dict('records'))

@app.route('/api/lookups/status-types')
def get_status_types():
    conn = sqlite3.connect('inspection_tracker.db')
    df = pd.read_sql_query('SELECT * FROM status_types WHERE active = 1', conn)
    conn.close()
    return jsonify(df.to_dict('records'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)



