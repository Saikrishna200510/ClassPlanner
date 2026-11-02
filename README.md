# ClassPlanner

**Multi-College Automated Timetable Management System**

ClassPlanner is a desktop application designed to simplify college timetable management.

## Features

- Multi-college management
- Super Admin dashboard
- College Admin dashboard
- Supabase authentication
- Faculty management
- Department management
- Subject management
- Classroom management
- Automatic timetable generation
- Faculty and classroom conflict detection
- PDF and Excel exports

## Technology Stack

- Python
- PySide6
- FastAPI
- Supabase
- PostgreSQL
- Google Cloud Run
- Google OR-Tools

## Supported Platforms

- Windows
- macOS
- Linux

## Installation

Download the appropriate installer from the GitHub Releases section.

### Running from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Saikrishna200510/ClassPlanner.git
   cd ClassPlanner
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Launch the application:**
   ```bash
   python run.py
   ```

4. **Default Demonstration Credentials:**
   - **Super Admin Portal**:
     - Email: `superadmin@classplanner.edu`
     - Password: `Admin@12345`
   - **College Admin Portal**:
     - Email: `admin@gec.edu`
     - Password: `College@12345`

## Security

College data is isolated using authenticated access, backend authorization and PostgreSQL Row Level Security (RLS).

## Developer

SL IT Solutions

## Project Status

Under Development.
