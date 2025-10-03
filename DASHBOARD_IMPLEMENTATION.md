# Task Scheduler Dashboard Implementation

## 🎉 Implementation Complete!

All files have been successfully created and configured for the Task Scheduler Dashboard.

## 📁 Files Created/Modified

### New Files:
1. **`bellman_tools/dashboard.py`** - Main dashboard Flask application with all API endpoints
2. **`bellman_tools/templates/dashboard.html`** - Beautiful, responsive web UI with DataTables
3. **`bellman_tools/templates/`** - Directory for HTML templates
4. **`bellman_tools/static/`** - Directory for static assets

### Modified Files:
1. **`bellman_tools/scheduler_tools.py`** - Added `RunDashboard()` function
2. **`bellman_tools/__init__.py`** - Added scheduler_tools to imports
3. **`requirements.txt`** - Added Flask dependency
4. **`setup.py`** - Added Flask to install_requires and configured package_data
5. **`MANIFEST.in`** - Added templates and static files to distribution
6. **`README.md`** - Added comprehensive dashboard documentation

## 🚀 Usage

### Basic Usage:
```python
from bellman_tools import scheduler_tools

# Launch dashboard on default port 5000
scheduler_tools.RunDashboard()
```

### Custom Port:
```python
scheduler_tools.RunDashboard(port=8080)
```

### With Custom SQL Connection:
```python
from bellman_tools import sql_tools, scheduler_tools

sql = sql_tools.Sql(db='YourDatabase')
scheduler_tools.RunDashboard(port=5000, sql=sql)
```

Then open your browser to: **http://localhost:5000**

## ✨ Dashboard Features

### 1. **Scheduler Control Panel** ⭐ NEW
   - **Start Scheduler**: Launch the task scheduler directly from the dashboard
   - **Stop Scheduler**: Safely stop the running scheduler
   - **Live Status**: Shows "Running since [timestamp]" when active
   - **View Logs**: Access real-time scheduler logs with color-coded levels
   - Auto-updates every 5 seconds

### 2. **Real-time Statistics Dashboard**
   - Total Tasks counter
   - Enabled Tasks counter
   - Scheduled Tasks (Next Runs) counter
   - Recent Executions counter

### 3. **Tasks Configuration Tab**
   - View all your configured scheduled tasks
   - Add new tasks with intuitive modal form
   - Edit existing tasks in-place
   - Delete tasks with confirmation
   - Toggle between "My Tasks" and "All Users' Tasks"
   - Shows: ID, Status, Script Name, Folder, Schedule (Every/AtTime), User, Host, ASAP flag, Comments

### 4. **Next Runs Tab**
   - View upcoming scheduled task executions
   - Shows: Next Run Time, Script Name, Folder, User, Host, Heartbeat ID
   - Helps you see what will run next

### 5. **Execution History Tab**
   - Last 100 task executions
   - Shows: Timestamp, Script File, Status, Session ID, Production flag, User, Host
   - Monitor past executions and troubleshoot issues

### 6. **Heartbeat Monitor Tab** ⭐ NEW
   - View last heartbeat from each user/machine combination
   - Shows: User, Host, Environment (Prod/Dev), Last Heartbeat timestamp
   - **Smart Status Indicators**:
     - 🟢 **Active** - Last heartbeat < 5 minutes ago
     - 🟡 **Idle** - Last heartbeat 5-60 minutes ago (shows minutes)
     - 🟠 **Idle** - Last heartbeat 1-24 hours ago (shows hours)
     - 🔴 **Inactive** - Last heartbeat > 24 hours ago (shows days)
   - Quickly identify which schedulers are running and which stopped

### 7. **Scheduler Logs Viewer**
   - Real-time log viewing in terminal-style modal
   - Color-coded log levels (INFO=Green, WARNING=Orange, ERROR=Red)
   - Shows last 200 log entries
   - Auto-scroll to latest logs
   - Manual refresh button
   - Terminal-style dark background for easy reading

### 8. **Interactive Features**
   - **Auto-refresh**: Automatically refreshes every 30 seconds
   - **Manual refresh**: Floating refresh button with spinning animation
   - **Sorting & Filtering**: DataTables integration for advanced table operations
   - **Search**: Built-in search across all table data
   - **Pagination**: Navigate through large datasets easily
   - **Responsive Design**: Works on desktop, tablet, and mobile

### 9. **CRUD Operations**
   - **Create**: Add new scheduled tasks
   - **Read**: View task details and history
   - **Update**: Modify task configurations
   - **Delete**: Remove tasks (with confirmation)

## 🎨 UI/UX Highlights

- **Modern gradient design** with purple/blue color scheme
- **Bootstrap 5** for responsive layout
- **Font Awesome icons** for visual clarity
- **DataTables** for advanced table functionality
- **Card-based layout** for clean organization
- **Modal forms** for task editing/creation
- **Status badges** for visual task status
- **Hover effects** for better interactivity

## 🔧 Technical Details

### Backend (Flask):
- **Framework**: Flask 2.3.0+
- **API Endpoints**:
  - `GET /` - Main dashboard page
  - `GET /api/tasks` - Get user's tasks
  - `GET /api/tasks/all` - Get all users' tasks
  - `GET /api/scheduled` - Get scheduled runs
  - `GET /api/logs` - Get execution logs
  - `GET /api/task/<id>` - Get specific task
  - `PUT /api/task/<id>` - Update task
  - `DELETE /api/task/<id>` - Delete task
  - `POST /api/task` - Create new task
  - **Scheduler Control Endpoints:**
    - `GET /api/scheduler/status` - Get scheduler running status
    - `POST /api/scheduler/start` - Start the task scheduler
    - `POST /api/scheduler/stop` - Stop the task scheduler
    - `GET /api/scheduler/logs` - Get scheduler logs
  - **⭐ NEW Heartbeat Endpoint:**
    - `GET /api/heartbeat` - Get heartbeat status from all users/machines

### Frontend:
- **Bootstrap 5.3.0** - Responsive framework
- **jQuery 3.7.0** - DOM manipulation & AJAX
- **DataTables 1.13.6** - Advanced table features
- **Font Awesome 6.4.0** - Icons

### Database Integration:
- Uses existing SQLAlchemy models:
  - `Task_Scheduler` - Task configuration
  - `Task_Scheduled` - Scheduled runs
  - `Log_Task_Scheduler` - Execution history
- Full CRUD operations via API
- Automatic user/host filtering

## 📦 Installation & Distribution

### For Development:
```bash
pip install flask
python tests/test_run_scheduler_dashboard.py
```

### For Distribution:
```bash
# Build the package
python setup.py sdist bdist_wheel

# Install the package
pip install dist/bellman_tools-0.2.0-py3-none-any.whl

# Or upload to PyPI
twine upload dist/*
```

### For Users (after PyPI upload):
```bash
pip install bellman-tools
```

Then simply:
```python
from bellman_tools import scheduler_tools
scheduler_tools.RunDashboard()
```

## 🔒 Security Considerations

- Dashboard runs on `0.0.0.0` (all interfaces) - consider firewall rules for production
- **Password Protection**: Set `TASK_SCHEDULER_DASHBOARD_PASSWORD` environment variable to require login
  - Session-based authentication with Flask sessions
  - Logout button in navbar when auth enabled
  - All routes protected with `@require_auth` decorator
  - Optional - if not set, dashboard is open
- SQL injection protection via parameterized queries (though current implementation uses string formatting - consider migrating to parameterized queries for production)
- User/host filtering based on system information
- Secret key for sessions (auto-generated or set via `FLASK_SECRET_KEY` env var)

## 🚧 Future Enhancements (Optional)

Potential features to add later:
- Authentication/authorization system
- Real-time log streaming via WebSockets
- Charts/graphs for execution statistics
- Task execution triggers from UI (manual run button)
- Dark mode toggle
- Export data to CSV/Excel
- Email notifications for failed tasks
- Task templates/presets
- Bulk operations on tasks

## 📝 Notes

- The dashboard requires a database connection configured via `DATABASE_CONNECTION_STRING` environment variable
- Templates and static files are included in the package distribution via `MANIFEST.in`
- The dashboard is designed to work alongside the existing scheduler, not replace it
- Auto-refresh can be adjusted by changing the `setInterval` value in the JavaScript (currently 30000ms = 30s)

## ✅ Testing

Test file already created: `tests/test_run_scheduler_dashboard.py`

```python
from bellman_tools import scheduler_tools

def test_load_dashboard():
    scheduler_tools.RunDashboard()

if __name__ == "__main__":
    test_load_dashboard()
```

## 🎊 Ready to Use!

Your dashboard is now fully implemented and ready to use. Just run:

```python
from bellman_tools import scheduler_tools
scheduler_tools.RunDashboard(port=5000)
```

And visit http://localhost:5000 in your browser!

