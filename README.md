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

Download the appropriate standalone installer from the [GitHub Releases](https://github.com/Saikrishna200510/ClassPlanner/releases) section:

| Platform | Installer Package | Installation Instructions |
|---|---|---|
| **Windows** | `ClassPlanner-v1.0.0-Windows-Setup.exe` | Run the installation wizard; automatically creates Start Menu & Desktop shortcuts, includes uninstaller |
| **macOS** | `ClassPlanner-v1.0.0-macOS.dmg` | Open the DMG image and drag **ClassPlanner** to your `Applications` folder |
| **Linux (Ubuntu/Debian)** | `classplanner_1.0.0_amd64.deb` | Install via terminal: `sudo dpkg -i classplanner_1.0.0_amd64.deb` |
| **Linux (Universal)** | `ClassPlanner-v1.0.0-x86_64.AppImage` | Make executable and run: `chmod +x ClassPlanner-v1.0.0-x86_64.AppImage && ./ClassPlanner-v1.0.0-x86_64.AppImage` |

*No Python, VS Code, or developer tooling required.*

### Running from Source (Developers)

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
