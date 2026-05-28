# Admin Dashboard MVP Scope

## Context

This document defines the practical Admin Dashboard scope for the Markdown IT / Doc2LLM internal SaaS.

The admin panel should help you manage users, conversions, failed jobs, files, and basic system health without becoming a bloated analytics or observability product.

---

# Core Principle

Use one common login page for both users and admins.

```txt
/login
```

After login, redirect based on role:

```txt
admin -> /admin
user  -> /dashboard
```

The role should come from the application profile table.

Recommended field:

```txt
profiles.role
```

Allowed roles:

```txt
admin
user
```

---

# Final Admin Dashboard Features

## 1. Authentication & Access Control

### Features

- Admin login through the same login page as normal users
- Admin logout
- Protected admin routes
- Role-based access control
- Unauthorized redirect if a normal user tries to open `/admin`

### Rule

```txt
Admin -> can access admin dashboard
User  -> can access only their own dashboard
```

---

## 2. Dashboard Overview

### Stat cards

- Total users
- Total converted files
- Files processed today
- Failed conversions
- Pending conversions
- Basic system health status

### Why files processed today is needed

This is useful because it shows real product usage.

It answers:

```txt
How many people used the tool today?
Is the product being used actively?
Did conversions suddenly drop?
```

This should be a simple count from `conversion_jobs` or `files` where the job was completed today.

---

## 3. User Management

### Features

- View all users
- Add user
- Enable user
- Disable user
- Change user role
- View user file count

### User table columns

- Name
- Email
- Role
- Status
- Created date
- Files converted

### Why user file count is useful

User file count is useful because it quickly shows:

- Which users are active
- Which users are not using the tool
- Which users are heavy users
- Which users may be causing many failed conversions

This can be calculated from the files table or conversion jobs table.

For MVP, it does not need a separate storage analytics system.

---

## 4. File Management

### Features

- View all converted files
- View which user owns each file
- View file name
- View file type
- View upload date
- View conversion status
- Download markdown output
- Delete file if needed

### File table columns

- User
- File name
- File type
- Upload date
- Conversion status
- Markdown output available

---

## 5. Conversion Job Management

### Features

- View conversion jobs
- View job status
- Retry failed conversion
- Cancel stuck job
- View basic error message

### Job statuses

- Queued
- Processing
- Completed
- Failed
- Cancelled

### Job table columns

- User
- File
- Status
- Created at
- Started at
- Completed at
- Error message

### Why cancel stuck job is useful

Cancel stuck job is useful because PDF conversion can sometimes hang.

This can happen when:

- OCR takes too long
- Parser gets stuck
- Railway worker crashes mid-job
- A large file never completes
- The job stays in `queued` or `processing` forever

For MVP, cancellation can be simple.

```txt
queued/processing -> cancelled
```

You do not need a complex queue control system at the start.

---

## 6. Logs

### Conversion logs

Track:

- User
- File
- Status
- Processing time
- Error message if failed

### Error logs

Track:

- Parser failed
- OCR failed
- Timeout
- Storage upload failed
- Database update failed

### Purpose

Logs are required because this product depends on file conversion. When a conversion fails, the admin should know why.

---

## 7. System Health Dashboard

### Features

Keep this simple, but include it.

Health indicators:

- Railway converter/worker status
- Supabase connection status
- Conversion queue status
- Storage write status

### Status values

```txt
Healthy
Warning
Down
```

### Why system health is important

System health is crucial because the user-facing product depends on external services.

If conversion is not working, the admin should immediately know whether the issue is:

- the converter worker
- the database
- storage
- stuck jobs
- queue backlog

For MVP, this can be a small section on the admin overview page, not a separate complex monitoring dashboard.

---

## 8. Search, Filters & Pagination

### Search

Add search for:

- User name
- User email
- File name
- Job status

### Filters

Add filters for:

- Status
- Date
- User
- File type

### Pagination

Pagination is required on all history/table-heavy pages.

Use pagination for:

- User list
- File history
- Conversion history
- Logs
- Error logs
- Admin history if added later

### Why pagination is needed

Without pagination, the frontend will become slow as records grow.

Do not load all records at once.

Recommended MVP behavior:

```txt
Show 10/20/50 records per page
Sort latest first
Fetch next page on demand
```

---

# Features Removed From MVP

The following are still not needed in the first version.

## 1. Full Storage Monitoring Dashboard

### Removed

- Total storage dashboard
- Top storage users
- Average file size dashboard
- Markdown storage usage charts

### Why removed

Supabase already shows storage usage in its own dashboard.

For the app, just store file size in the database. Full storage analytics can come later.

---

## 2. Separate File Metadata Page

### Removed

A separate detailed page for every file is not needed in MVP.

### Why removed

The file table can show enough useful metadata.

---

## 3. Admin Activity Logs

### Removed for MVP unless multiple admins are using the system immediately.

### Why removed

Useful later, but not urgent if there is only one admin or a small internal team.

Can be added later when multiple admins start managing users/files.

---

## 4. Advanced Log Filters

### Removed

- Severity filter
- Complex error categorization
- Advanced log analytics

### Why removed

Basic search, date filter, and status filter are enough for MVP.

---

## 5. Recent Activity Feed

### Removed as a separate component.

### Why removed

The same information can be seen by sorting users, files, conversions, and logs by latest date.

No need for a separate feed yet.

---

# Final MVP Sidebar

```txt
Admin Dashboard
│
├── Overview
├── Users
├── Files
├── Conversions
├── Logs
└── System Health
```

System Health can also be shown inside Overview if you want fewer sidebar items.

---

# Final MVP Checklist

- Same login page for admin and user
- Role-based redirect after login
- Protected `/admin` routes
- View users
- Add users
- Enable/disable users
- Change user role
- View user file count
- View converted files
- Download markdown output
- Delete files if needed
- View conversion jobs
- Retry failed conversions
- Cancel stuck jobs
- View conversion logs
- View error logs
- Basic system health status
- Files processed today
- Search users/files/jobs
- Filter by status/date/user/file type
- Pagination on users, files, conversion history, and logs

---

# Recommended Database Tables

## profiles

Stores app-level user data.

Suggested fields:

```txt
id
auth_user_id
name
email
role
is_active
created_at
updated_at
```

---

## files

Stores uploaded file and markdown output metadata.

Suggested fields:

```txt
id
user_id
original_file_name
file_type
file_size
source_file_path
markdown_file_path
conversion_status
created_at
updated_at
```

---

## conversion_jobs

Stores conversion process status.

Suggested fields:

```txt
id
file_id
user_id
status
started_at
completed_at
error_message
created_at
updated_at
```

---

## conversion_logs

Stores useful conversion/debug logs.

Suggested fields:

```txt
id
job_id
file_id
user_id
level
message
created_at
```

---

# Final Recommendation

The strongest MVP admin panel is:

```txt
Users + Files + Conversions + Logs + Basic System Health
```

This is not overengineering.

It is the minimum needed to safely operate a file conversion SaaS.
