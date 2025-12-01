# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Easy Book is a lightweight swimming lesson student management system designed for personal use. It consists of a FastAPI backend with MongoDB database and a Vue 3 frontend optimized for mobile devices.

## Architecture

### Backend (Python + FastAPI)
- **Framework**: FastAPI with async/await patterns
- **Database**: MongoDB with PyMongo driver
- **Structure**: Modular design under `backend/api_server/`
  - `main.py`: FastAPI application entry point
  - `models.py`: Pydantic data models for students, appointments, and attendance
  - `services.py`: Business logic layer (StudentService, AppointmentService, AttendanceService)
  - `database.py` & `mongo_database.py`: MongoDB connection and operations
  - `api/`: Route modules (students.py, appointments.py, attendance.py)

### Frontend (Vue 3)
- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite
- **State Management**: Pinia stores
- **Mobile-First**: Designed for mobile with responsive layout
- **Structure**:
  - `src/views/`: Main pages (Home.vue, Students.vue, StudentDetail.vue, AddStudent.vue)
  - `src/api/`: Axios-based API client modules
  - `src/stores/`: Pinia state management
  - `src/utils/`: Utility functions (date.js, toast.js)

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run development server (default port 8002)
python -m api_server.main

# Run with custom port
python -m api_server.main 8003
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Run development server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Setup
```bash
# Using Docker (recommended)
docker run -d --name mongodb -p 27017:27017 mongo:6

# Or install MongoDB locally
mongod
```

## Key Development Patterns

### Backend Patterns
1. **Service Layer Pattern**: All business logic is encapsulated in service classes (StudentService, AppointmentService, AttendanceService)
2. **Pydantic Models**: All data validation and serialization uses Pydantic models in `models.py`
3. **Async/Await**: All database operations and API endpoints use async patterns
4. **MongoDB Operations**: Direct MongoDB operations through custom database abstraction in `mongo_database.py`

### Frontend Patterns
1. **Composition API**: All Vue components use `<script setup>` with Composition API
2. **Pinia Stores**: State management through modular Pinia stores
3. **API Proxy**: Frontend uses Vite proxy to forward `/api/*` requests to backend at `localhost:8002`
4. **Mobile Optimization**: Touch-friendly interfaces with bottom navigation

### Data Flow
1. **Student Management**: CRUD operations for students with lesson tracking
2. **Appointment System**: Date-based scheduling with conflict detection for 1v1 lessons
3. **Attendance Tracking**: Check-in/check-out system that automatically deducts lessons
4. **Conflict Resolution**: 1v1 lessons cannot overlap in the same time slot

## API Endpoints Structure

- **Students**: `/api/students/` - Full CRUD operations
- **Appointments**: `/api/appointments/` - Create, read by student, read by date
- **Attendance**: `/api/attendance/` - Check-in and mark absent functionality
- **Health Checks**: `/health` and `/api/health/db` for service monitoring

## Configuration Files

- **Backend**: `backend/.env` - MongoDB connection settings
- **Frontend**: `frontend/vite.config.js` - Vite configuration with API proxy
- **Database**: Uses MongoDB connection string format `mongodb://localhost:27017`

## Business Logic

### Appointment Conflicts
- 1v1 lessons cannot conflict with other 1v1 lessons in the same time slot
- 1v多 lessons can share time slots
- Students cannot have multiple appointments in the same time slot

### Lesson Deduction
- Only check-in (`checked` status) deducts lessons
- Absent (`absent` status) does not deduct lessons
- Lessons are deducted immediately upon check-in

### Student States
- `total_lessons`: Original package size
- `remaining_lessons`: Current available lessons
- `attended_lessons`: Calculated as `total_lessons - remaining_lessons`

## Mobile UI Considerations

- Touch targets are minimum 44px for iOS compliance
- Bottom navigation for thumb-friendly access
- Swipe gestures supported for date navigation
- Responsive design adapts to desktop screens (max-width: 430px)

## Testing and Quality

- API documentation available at `http://localhost:8002/docs` (when backend is running)
- FastAPI provides automatic OpenAPI schema generation
- Frontend error handling through Axios interceptors with user-friendly messages