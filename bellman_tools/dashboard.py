import os
import json
import datetime
import getpass
import socket
import threading
import io
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from pathlib import Path
from functools import wraps

from bellman_tools import sql_tools, scheduler_tools
from bellman_tools.database import Task_Scheduler, Log_Task_Scheduler, Task_Scheduled


class SchedulerDashboard:
    """Dashboard for monitoring and managing the task scheduler"""
    
    def __init__(self, sql: sql_tools.Sql, port=5000, debug=False):
        self.sql = sql
        self.port = port
        self.debug = debug
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / 'templates'),
            static_folder=str(Path(__file__).parent / 'static')
        )
        
        # Secret key for sessions
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
        
        # Password protection
        self.dashboard_password = os.getenv('TASK_SCHEDULER_DASHBOARD_PASSWORD')
        self.require_auth = bool(self.dashboard_password)
        
        # Scheduler control
        self.scheduler_thread = None
        self.scheduler_manager = None
        self.scheduler_running = False
        self.scheduler_start_time = None
        self.scheduler_logs = []
        self.max_logs = 500
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        def require_auth(f):
            """Decorator to require authentication"""
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if self.require_auth and not session.get('authenticated'):
                    return redirect(url_for('login'))
                return f(*args, **kwargs)
            return decorated_function
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page"""
            if not self.require_auth:
                return redirect(url_for('index'))
            
            if request.method == 'POST':
                password = request.form.get('password')
                if password == self.dashboard_password:
                    session['authenticated'] = True
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error='Invalid password')
            
            return render_template('login.html', error=None)
        
        @self.app.route('/logout')
        def logout():
            """Logout"""
            session.pop('authenticated', None)
            return redirect(url_for('login'))
        
        @self.app.route('/')
        @require_auth
        def index():
            """Main dashboard page"""
            current_user = getpass.getuser()
            current_host = socket.gethostname()
            return render_template('dashboard.html', user=current_user, host=current_host, require_auth=self.require_auth)
        
        @self.app.route('/api/tasks')
        @require_auth
        def get_tasks():
            """Get all tasks from Task_Scheduler"""
            try:
                user = request.args.get('user', getpass.getuser().lower())
                host = request.args.get('host', socket.gethostname())
                
                query = f"""
                    SELECT * FROM Task_Scheduler
                    WHERE RunBy = '{user}' AND RunHost = '{host}'
                    ORDER BY Enable DESC, ScriptName
                """
                df = self.sql.load_dataframe_from_query(query)
                
                if df is not None and not df.empty:
                    # Convert datetime columns to strings
                    for col in df.columns:
                        if df[col].dtype == 'datetime64[ns]':
                            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    # Replace NaN with None for JSON serialization
                    df = df.where(df.notna(), None)
                    return jsonify(df.to_dict('records'))
                return jsonify([])
            except Exception as e:
                print(f"Error in get_tasks: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tasks/all')
        @require_auth
        def get_all_tasks():
            """Get all tasks (not filtered by user/host)"""
            try:
                query = "SELECT * FROM Task_Scheduler ORDER BY Enable DESC, RunBy, ScriptName"
                df = self.sql.load_dataframe_from_query(query)
                
                if df is not None and not df.empty:
                    for col in df.columns:
                        if df[col].dtype == 'datetime64[ns]':
                            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    df = df.where(df.notna(), None)
                    return jsonify(df.to_dict('records'))
                return jsonify([])
            except Exception as e:
                print(f"Error in get_all_tasks: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scheduled')
        @require_auth
        def get_scheduled():
            """Get currently scheduled tasks (next runs)"""
            try:
                user = request.args.get('user', getpass.getuser().lower())
                host = request.args.get('host', socket.gethostname())
                
                query = f"""
                    SELECT * FROM Task_Scheduled
                    WHERE RunBy = '{user}' AND RunHost = '{host}'
                    AND InsertedAt >= DATEADD(hour, -2, GETDATE())
                    ORDER BY NextRun
                """
                df = self.sql.load_dataframe_from_query(query)
                
                if df is not None and not df.empty:
                    for col in df.columns:
                        if df[col].dtype == 'datetime64[ns]':
                            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    df = df.where(df.notna(), None)
                    return jsonify(df.to_dict('records'))
                return jsonify([])
            except Exception as e:
                print(f"Error in get_scheduled: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs')
        @require_auth
        def get_logs():
            """Get execution logs"""
            try:
                user = request.args.get('user', getpass.getuser().lower())
                host = request.args.get('host', socket.gethostname())
                limit = request.args.get('limit', 100)
                
                query = f"""
                    SELECT TOP {limit} * FROM Log_Task_Scheduler
                    WHERE InsertedBy = '{user}' AND InsertedHost = '{host}'
                    ORDER BY InsertedAt DESC
                """
                df = self.sql.load_dataframe_from_query(query)
                
                if df is not None and not df.empty:
                    for col in df.columns:
                        if df[col].dtype == 'datetime64[ns]':
                            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    df = df.where(df.notna(), None)
                    return jsonify(df.to_dict('records'))
                return jsonify([])
            except Exception as e:
                print(f"Error in get_logs: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/task/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
        @require_auth
        def manage_task(task_id):
            """Get, update or delete a specific task"""
            try:
                if request.method == 'GET':
                    query = f"SELECT * FROM Task_Scheduler WHERE ID = {task_id}"
                    df = self.sql.load_dataframe_from_query(query)
                    if df is not None and not df.empty:
                        for col in df.columns:
                            if df[col].dtype == 'datetime64[ns]':
                                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                        df = df.where(df.notna(), None)
                        return jsonify(df.to_dict('records')[0])
                    return jsonify({'error': 'Task not found'}), 404
                
                elif request.method == 'PUT':
                    data = request.json
                    # Build update query
                    update_fields = []
                    for key, value in data.items():
                        if key != 'ID':
                            if isinstance(value, str):
                                update_fields.append(f"{key} = '{value}'")
                            elif isinstance(value, bool):
                                update_fields.append(f"{key} = {1 if value else 0}")
                            elif value is None:
                                update_fields.append(f"{key} = NULL")
                            else:
                                update_fields.append(f"{key} = {value}")
                    
                    if update_fields:
                        query = f"""
                            UPDATE Task_Scheduler 
                            SET {', '.join(update_fields)}
                            WHERE ID = {task_id}
                        """
                        self.sql.execute_sql(query)
                        return jsonify({'success': True, 'message': 'Task updated successfully'})
                    return jsonify({'error': 'No fields to update'}), 400
                
                elif request.method == 'DELETE':
                    query = f"DELETE FROM Task_Scheduler WHERE ID = {task_id}"
                    self.sql.execute_sql(query)
                    return jsonify({'success': True, 'message': 'Task deleted successfully'})
                    
            except Exception as e:
                print(f"Error in manage_task: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/task', methods=['POST'])
        @require_auth
        def create_task():
            """Create a new task"""
            try:
                data = request.json
                
                # Add default values
                data['InsertedAt'] = datetime.datetime.now()
                data['InsertedBy'] = getpass.getuser()
                data['InsertedHost'] = socket.gethostname()
                
                # Use SQLAlchemy to insert
                new_task = Task_Scheduler.Task_Scheduler(**data)
                self.sql.add_to_session_and_commit(new_task)
                
                return jsonify({'success': True, 'message': 'Task created successfully'})
            except Exception as e:
                print(f"Error in create_task: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/status')
        @require_auth
        def get_scheduler_status():
            """Get scheduler status"""
            try:
                return jsonify({
                    'running': self.scheduler_running,
                    'start_time': self.scheduler_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.scheduler_start_time else None
                })
            except Exception as e:
                print(f"Error in get_scheduler_status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/start', methods=['POST'])
        @require_auth
        def start_scheduler():
            """Start the task scheduler"""
            try:
                if self.scheduler_running:
                    return jsonify({'error': 'Scheduler is already running'}), 400
                
                # Create scheduler manager
                self.scheduler_manager = scheduler_tools.TaskSchedulerManager(sql=self.sql)
                self.scheduler_running = True
                self.scheduler_start_time = datetime.datetime.now()
                self.scheduler_logs = []
                
                # Start scheduler in background thread
                self.scheduler_thread = threading.Thread(
                    target=self._run_scheduler_with_logging,
                    daemon=True
                )
                self.scheduler_thread.start()
                
                self._add_log("INFO", "Task Scheduler started successfully")
                
                return jsonify({
                    'success': True,
                    'message': 'Scheduler started successfully',
                    'start_time': self.scheduler_start_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                print(f"Error in start_scheduler: {e}")
                self.scheduler_running = False
                self.scheduler_start_time = None
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/stop', methods=['POST'])
        @require_auth
        def stop_scheduler():
            """Stop the task scheduler"""
            try:
                if not self.scheduler_running:
                    return jsonify({'error': 'Scheduler is not running'}), 400
                
                self.scheduler_running = False
                self._add_log("INFO", "Task Scheduler stopped by user")
                
                # Clear scheduler resources
                if self.scheduler_manager and hasattr(self.scheduler_manager, 'schedule'):
                    self.scheduler_manager.schedule.clear()
                
                return jsonify({
                    'success': True,
                    'message': 'Scheduler stopped successfully'
                })
            except Exception as e:
                print(f"Error in stop_scheduler: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/logs')
        @require_auth
        def get_scheduler_logs():
            """Get scheduler logs"""
            try:
                limit = int(request.args.get('limit', 100))
                logs = self.scheduler_logs[-limit:] if len(self.scheduler_logs) > limit else self.scheduler_logs
                return jsonify(logs)
            except Exception as e:
                print(f"Error in get_scheduler_logs: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/heartbeat')
        @require_auth
        def get_heartbeat():
            """Get heartbeat status from all users/machines"""
            try:
                query = """
                    SELECT 
                        InsertedBy,
                        InsertedHost,
                        IsProd,
                        MAX(InsertedAt) as LastInsertedAt
                    FROM Task_Scheduler_Heartbeat
                    GROUP BY InsertedBy, InsertedHost, IsProd
                    ORDER BY InsertedBy, InsertedHost, IsProd
                """
                df = self.sql.load_dataframe_from_query(query)
                
                if df is not None and not df.empty:
                    for col in df.columns:
                        if df[col].dtype == 'datetime64[ns]':
                            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    df = df.where(df.notna(), None)
                    return jsonify(df.to_dict('records'))
                return jsonify([])
            except Exception as e:
                print(f"Error in get_heartbeat: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _add_log(self, level, message):
        """Add a log entry"""
        log_entry = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'message': message
        }
        self.scheduler_logs.append(log_entry)
        
        # Keep only last max_logs entries
        if len(self.scheduler_logs) > self.max_logs:
            self.scheduler_logs = self.scheduler_logs[-self.max_logs:]
    
    def _run_scheduler_with_logging(self):
        """Run scheduler with log capture"""
        try:
            # Capture stdout to logs
            original_stdout = sys.stdout
            
            class LogCapture(io.StringIO):
                def __init__(self, dashboard):
                    super().__init__()
                    self.dashboard = dashboard
                
                def write(self, text):
                    if text.strip():
                        self.dashboard._add_log("INFO", text.strip())
                    return len(text)
            
            # Redirect stdout
            log_capture = LogCapture(self)
            sys.stdout = log_capture
            
            try:
                self._add_log("INFO", "Initializing scheduler...")
                
                # Run the scheduler loop
                heartbeat = self.scheduler_manager.heartbeat
                schedule = self.scheduler_manager.schedule
                
                while self.scheduler_running:
                    heartbeat.save_heartbeat()
                    
                    if not heartbeat.is_another_next_heartbeat_session_running(
                        heartbeat_table_in_last_x_minutes=3,
                        heartbeat_in_log_task_scheduler_in_last_x_minutes=60 * 24,
                    ):
                        # Get Tasks from DB
                        dico_tasks = self.scheduler_manager.get_tasks_from_db()
                        
                        if dico_tasks:
                            self._add_log("INFO", f"Loaded {len(dico_tasks)} tasks from database")
                        
                        self.scheduler_manager.dico_tasks_to_scheduler_task(
                            dico_tasks, heartbeat_id=heartbeat.session_id
                        )
                        
                        self.scheduler_manager.save_scheduled_job_to_db()
                        
                        for i in range(60):
                            if not self.scheduler_running:
                                break
                            try:
                                schedule.run_pending()
                            except Exception as e:
                                self._add_log("ERROR", f"Error running scheduled task: {str(e)}")
                            threading.Event().wait(1)
                        
                        schedule.clear()
                    else:
                        self._add_log("WARNING", "Another scheduler instance is running")
                        threading.Event().wait(60)
                
                self._add_log("INFO", "Scheduler stopped")
            finally:
                # Restore stdout
                sys.stdout = original_stdout
                
        except Exception as e:
            self._add_log("ERROR", f"Scheduler error: {str(e)}")
            self.scheduler_running = False
    
    def run(self):
        """Run the dashboard"""
        print(f"\n{'='*60}")
        print(f"🚀 Task Scheduler Dashboard Starting...")
        print(f"{'='*60}")
        print(f"📊 Dashboard URL: http://localhost:{self.port}")
        print(f"👤 User: {getpass.getuser()}")
        print(f"💻 Host: {socket.gethostname()}")
        if self.require_auth:
            print(f"🔒 Password Protection: ENABLED")
        else:
            print(f"🔓 Password Protection: DISABLED")
        print(f"{'='*60}\n")
        
        self.app.run(host='0.0.0.0', port=self.port, debug=self.debug)


def RunDashboard(port=5000, debug=False, sql=None):
    """
    Launch the Task Scheduler Dashboard
    
    Args:
        port (int): Port to run the dashboard on (default: 5000)
        debug (bool): Run in debug mode (default: False)
        sql (Sql): SQL connection object (optional, will create one if not provided)
    
    Example:
        from bellman_tools import scheduler_tools
        scheduler_tools.RunDashboard(port=5000)
    """
    if sql is None:
        sql = sql_tools.Sql()
    
    dashboard = SchedulerDashboard(sql=sql, port=port, debug=debug)
    dashboard.run()

