cat > README.md << 'EOF'
# Allo Health - Hospital Management System

A comprehensive Django-based hospital management system designed for front desk staff to efficiently manage patients, appointments, queues, and doctor availability.

## 🏥 Features

### Patient Management
- Register and manage patient records with complete medical history
- Store patient demographics, contact information, and emergency contacts
- Track allergies, chronic conditions, and current medications
- Search and filter patients by ID, name, phone, or email
- View patient appointment and queue history
- Get patients visit history
- Get the data in the csv format

### Appointment Scheduling
- Schedule, reschedule, and cancel appointments
- Real-time doctor availability checking
- Multiple appointment statuses (scheduled, confirmed, checked-in, in-progress, completed)
- Appointment types (new patient, follow-up, routine, emergency)
- Calendar view for appointment management
- Automated appointment ID generation

### Queue Management
- Walk-in patient queue system
- Priority-based queue (normal, urgent, emergency)
- Real-time queue status tracking
- Automated wait time estimation
- Queue statistics and analytics
- Doctor assignment for queue entries

### Doctor Management
- Comprehensive doctor profiles with specializations
- Weekly schedule management
- Daily availability slot creation
- Real-time availability status (available, busy, off duty)
- Doctor consultation fee tracking
- Professional credentials and qualifications

### Front Desk Operations
- Intuitive dashboard with real-time statistics
- Quick patient search and registration
- Appointment check-in system
- Queue monitoring and management
- Doctor availability overview

## 🚀 Technology Stack

- **Backend**: Django 4.2+
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML, CSS, Bootstrap (implied from template structure)
- **Authentication**: Django built-in authentication system

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/Tejas132005/Frontdesk_Clinic_Management
cd Allo_Health
```