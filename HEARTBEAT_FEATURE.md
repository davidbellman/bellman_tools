# 💓 Heartbeat Monitor Tab - Implementation Summary

## Overview

Added a new **Heartbeat** tab to the Task Scheduler Dashboard that displays the last heartbeat from each user/machine combination, with intelligent status indicators showing whether schedulers are active, idle, or inactive.

## 🎯 Purpose

Quickly identify:
- Which schedulers are currently running
- Which machines/users have active schedulers
- When each scheduler last reported a heartbeat
- Whether schedulers are in production or development mode

## ✨ Features

### 1. **Heartbeat Status Table**

Displays aggregated heartbeat data with the following columns:

| Column | Description |
|--------|-------------|
| **User** | The user running the scheduler (InsertedBy) |
| **Host** | The machine/hostname running the scheduler |
| **Environment** | Production or Development badge |
| **Last Heartbeat** | Timestamp of the last heartbeat |
| **Status** | Smart status indicator with time since last heartbeat |

### 2. **Smart Status Indicators**

Color-coded badges that automatically calculate time since last heartbeat:

- 🟢 **Active** - Last heartbeat < 5 minutes ago
  - Green badge: "Active"
  - Scheduler is currently running

- 🟡 **Idle (Minutes)** - Last heartbeat 5-60 minutes ago
  - Yellow badge: "Idle (Xm ago)"
  - Shows minutes since last heartbeat

- 🟠 **Idle (Hours)** - Last heartbeat 1-24 hours ago
  - Orange badge: "Idle (Xh ago)"
  - Shows hours since last heartbeat

- 🔴 **Inactive** - Last heartbeat > 24 hours ago
  - Red badge: "Inactive (Xd ago)"
  - Shows days since last heartbeat

### 3. **Environment Badges**

- 🟢 **Production** - Green badge for production environments (IsProd = True)
- 🟡 **Development** - Yellow badge for development environments (IsProd = False)

### 4. **Auto-Refresh**

- Updates every 30 seconds automatically
- Manual refresh via floating refresh button
- Status indicators recalculate in real-time

### 5. **DataTables Integration**

- Sortable columns
- Search/filter functionality
- Pagination for large datasets
- Default sort by "Last Heartbeat" (most recent first)

## 🔧 Implementation Details

### Backend (`bellman_tools/dashboard.py`)

**New API Endpoint:**
```python
@self.app.route('/api/heartbeat')
@require_auth
def get_heartbeat():
    """Get heartbeat status from all users/machines"""
```

**SQL Query:**
```sql
SELECT 
    InsertedBy,
    InsertedHost,
    IsProd,
    MAX(InsertedAt) as LastInsertedAt
FROM Task_Scheduler_Heartbeat
GROUP BY InsertedBy, InsertedHost, IsProd
ORDER BY InsertedBy, InsertedHost, IsProd
```

This query:
- Groups by user, host, and environment
- Gets the most recent heartbeat for each combination
- Returns all unique scheduler instances

### Frontend (`bellman_tools/templates/dashboard.html`)

**New Tab:**
- Added "Heartbeat" tab to navigation
- Created heartbeat table with 5 columns
- Integrated with DataTables library

**JavaScript Functions:**
- `loadHeartbeat()` - Fetches and displays heartbeat data
- Calculates time difference for status badges
- Formats data with color-coded badges
- Integrated into `refreshAllData()` for auto-refresh

**Time Calculation Logic:**
```javascript
const lastHeartbeat = new Date(heartbeat.LastInsertedAt);
const now = new Date();
const diffMinutes = Math.floor((now - lastHeartbeat) / 1000 / 60);

// Status logic:
// < 5 min    → Active (green)
// 5-60 min   → Idle with minutes (yellow)
// 1-24 hours → Idle with hours (orange)
// > 24 hours → Inactive with days (red)
```

## 📊 Use Cases

### 1. **Monitor Active Schedulers**
Quickly see which machines have schedulers currently running (Active status).

### 2. **Detect Stopped Schedulers**
Identify schedulers that have stopped unexpectedly (Inactive status).

### 3. **Multi-User Coordination**
See who else has schedulers running to avoid conflicts.

### 4. **Environment Tracking**
Distinguish between production and development schedulers.

### 5. **Troubleshooting**
When tasks aren't running, check if the scheduler is active on the expected machine.

## 🎨 Visual Design

**Consistent with Dashboard Theme:**
- Teal/turquoise primary color (#14b8a6)
- Clean, compact design
- Modern badges and status indicators
- Responsive layout

**Status Colors:**
- Active: Light green (#d1fae5)
- Idle (minutes): Light yellow (#fef3c7)
- Idle (hours): Light orange (#fed7aa)
- Inactive: Light red (#fee2e2)

## 📝 Example Data

```
User          | Host        | Environment  | Last Heartbeat        | Status
--------------|-------------|--------------|----------------------|------------------
john.smith    | DESKTOP-01  | Production   | 2025-10-03 15:45:23  | Active
jane.doe      | LAPTOP-02   | Development  | 2025-10-03 15:30:15  | Idle (15m ago)
admin         | SERVER-03   | Production   | 2025-10-03 12:00:00  | Idle (3h ago)
test.user     | TEST-VM     | Development  | 2025-10-02 08:00:00  | Inactive (1d ago)
```

## 🚀 Usage

1. **Navigate to Heartbeat Tab:**
   - Click "Heartbeat" tab in the dashboard
   - Table loads automatically

2. **Interpret Status:**
   - Green = Scheduler running now
   - Yellow/Orange = Scheduler idle but recent
   - Red = Scheduler stopped or stale

3. **Sort and Filter:**
   - Click column headers to sort
   - Use search box to filter by user/host
   - View 25 entries per page (configurable)

4. **Monitor Changes:**
   - Auto-refreshes every 30 seconds
   - Click refresh button for immediate update
   - Status badges update based on current time

## 🔐 Security

- Protected by `@require_auth` decorator
- Same authentication as other dashboard features
- Shows all users' heartbeats (admin view)
- No ability to modify data (read-only)

## 📈 Performance

- Efficient SQL query with GROUP BY and MAX
- Lightweight data transfer (only aggregated data)
- Client-side time calculations (no server load)
- DataTables handles large datasets efficiently

## 🔄 Integration

**Automatic Integration:**
- Heartbeat data loaded with other dashboard data
- Uses existing SQL connection
- Follows same authentication flow
- Integrated into auto-refresh cycle

**No Configuration Needed:**
- Works out of the box
- Uses existing `Task_Scheduler_Heartbeat` table
- No additional environment variables
- No database changes required

## 📚 Database Schema

Uses existing `Task_Scheduler_Heartbeat` table:

```sql
CREATE TABLE [dbo].[Task_Scheduler_Heartbeat] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [SessionID] NVARCHAR(255),
    [IsProd] BIT,
    [InsertedAt] DATETIME DEFAULT GETDATE(),
    [InsertedBy] NVARCHAR(255) DEFAULT SYSTEM_USER,
    [InsertedHost] NVARCHAR(255) DEFAULT HOST_NAME()
);
```

## 🎓 Benefits

1. **Visibility**: See all scheduler activity at a glance
2. **Monitoring**: Detect inactive schedulers immediately
3. **Coordination**: Avoid running duplicate schedulers
4. **Troubleshooting**: Quick diagnosis when tasks don't run
5. **Compliance**: Track production vs development usage
6. **History**: See when schedulers were last active

## 🐛 Troubleshooting

**No Data Showing:**
- Check if schedulers have been run recently
- Verify `Task_Scheduler_Heartbeat` table exists
- Ensure schedulers are saving heartbeats

**Status Always Inactive:**
- Check server time vs database time
- Verify heartbeat inserts are working
- Review scheduler logs

**Wrong Environment Badge:**
- Check `IsProd` flag in scheduler configuration
- Verify environment detection logic

## 📋 Files Modified

1. ✅ `bellman_tools/dashboard.py`
   - Added `/api/heartbeat` endpoint
   - Protected with authentication

2. ✅ `bellman_tools/templates/dashboard.html`
   - Added "Heartbeat" tab
   - Created heartbeat table
   - Added `loadHeartbeat()` JavaScript function
   - Integrated time calculation logic

3. ✅ `README.md`
   - Updated dashboard features list
   - Added heartbeat monitor description

4. ✅ `DASHBOARD_IMPLEMENTATION.md`
   - Documented heartbeat tab
   - Added to API endpoints list
   - Updated feature count

## 🎉 Result

A powerful new monitoring tool that provides instant visibility into scheduler health across all users and machines. The smart status indicators make it immediately obvious which schedulers need attention, improving operational efficiency and reducing downtime.

---

**Quick Test:**
```python
from bellman_tools import scheduler_tools
scheduler_tools.RunDashboard(port=5000)
```

Open http://localhost:5000 and click the **Heartbeat** tab to see all scheduler heartbeats! 💓

