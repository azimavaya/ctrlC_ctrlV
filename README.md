# Panther Cloud Air (PCA)
**CSC 4710 Software Engineering — Spring 2026**
**Team:** ctrlC+ctrlV | High Point University

Airline simulation system for Panther Cloud Air — 56 aircraft, 310 daily flights, 31 airports (top 30 US + Paris CDG), 14-day simulation with daily challenges.

---

## Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| Backend | Python 3.12 + Flask |
| Database | MariaDB (Docker) |
| Orchestration | Docker Compose |
| Auth | JWT (HS256) + bcrypt |
| Version Control | GitHub (private) |
| Project Mgmt | Monday.com / Trello |

---

## Quick Start

### Prerequisites
- **Docker** (with Docker Compose) — must be running before starting services
- **Node.js 20+**
- **Python 3.12+**
- **Git**
- **Make** (build automation)

### Installing prerequisites on Ubuntu/Debian (including WSL2)

**Git and Build Tools (includes `make`):**
```bash
sudo apt update && sudo apt install -y git build-essential
```

**Docker Engine + Docker Compose:**
```bash
# Install Docker using the official convenience script
curl -fsSL https://get.docker.com | sudo sh
# Add your user to the docker group (avoids needing sudo for docker commands)
sudo usermod -aG docker $USER
# Log out and back in (or run: newgrp docker) for the group change to take effect
```

**Node.js 20+ (via NodeSource):**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**Python 3.12+:**
```bash
sudo apt install -y python3 python3-pip python3-venv
# Verify version (must be 3.12 or higher):
python3 --version
```

> **Windows 11 (WSL2) users:** Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) first (`wsl --install` in PowerShell), then follow the Linux instructions above inside your WSL terminal. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) and enable the WSL2 backend, or install Docker Engine directly inside WSL as shown above.

### 1. Clone the repo
```bash
git clone https://github.com/azimavaya/ctrlC_ctrlV.git
cd ctrlC_ctrlV
```

### 2. Start the Docker daemon
Make sure Docker is running before proceeding. On Linux/WSL2:
```bash
sudo systemctl start docker
```
On macOS/Windows, open Docker Desktop.

### 3. First-time setup
Run this once to install frontend dependencies and build Docker images:
```bash
make setup
```

### 4. Start all services
This launches the database (MariaDB), backend (Flask API), and frontend (React + Vite) in Docker containers:
```bash
make start
```

On first startup, the backend will automatically:
- Create the admin user (username: `admin`, password: `pca`)
- Create the regular user (username: `user`, password: `pass`)
- Generate the full flight timetable (this takes ~15 seconds)

Once running, the services are available at:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5001/api/health |
| Database | internal to Docker network (not exposed externally) |

### 5. View logs
```bash
make logs            # All services
make logs-backend    # Backend only
make logs-db         # Database only
```

### 6. Stop all services
```bash
make stop
```

### 7. Restart
```bash
make restart
```

### Environment variables
Copy `.env.example` to `.env` to customize. Defaults work for local development:
```bash
cp .env.example .env
```
Key variables: `DB_PASSWORD`, `JWT_SECRET`, `ADMIN_PASSWORD`, `CORS_ORIGINS`.

---

## Project Structure
```
pca/
├── frontend/          # React + Vite passenger interface
│   └── src/
│       ├── components/   # Sidebar, ProtectedRoute, shared components
│       ├── context/      # AuthContext, ThemeContext (dark mode)
│       └── pages/        # Home, BookFlight, Timetable, Simulation, Finances, Admin
├── backend/           # Python Flask REST API
│   └── app/
│       ├── routes/       # API endpoints
│       ├── models/       # Data models
│       └── services/     # Timetable & simulation logic
├── database/
│   ├── 00_init.sql       # Create database
│   ├── 01_roles_users.sql
│   ├── 02_airports.sql
│   ├── 03_aircraft.sql
│   ├── 04_routes.sql
│   ├── 05_flights.sql
│   ├── 06_simulation.sql
│   ├── 07_bookings.sql
│   └── 08_indexes.sql    # (run in numeric order by MariaDB)
├── docs/
│   ├── PCA_MASTER_REFERENCE.md  # Consolidated technical reference
│   ├── SECURITY_COMPLIANCE.md   # Security compliance documentation
│   ├── generate_flights.py      # Day 1 flight schedule SQL generator
│   └── generate_routes.py       # Route + aircraft SQL generator
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## API Endpoints

### Public (after login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/login` | Authenticate, returns JWT |
| GET | `/api/airports/` | All airports |
| GET | `/api/airports/<iata>` | Single airport |
| GET | `/api/airports/hubs` | Hub airports |
| GET | `/api/aircraft/` | Full fleet |
| GET | `/api/aircraft/types` | Aircraft types |
| GET | `/api/flights/` | All scheduled flights (timetable) |
| GET | `/api/flights/live-stats` | Home dashboard stats |
| GET | `/api/flights/departures` | Next departures |
| GET | `/api/bookings/search` | Search direct + connecting flights |
| POST | `/api/bookings` | Create a booking |
| GET | `/api/bookings` | List user's bookings |

### Admin Only
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/overview` | Dashboard stats |
| POST | `/api/admin/generate-schedule` | Regenerate timetable |
| GET | `/api/auth/users` | List all users |
| POST | `/api/auth/users` | Create user |
| PUT | `/api/auth/users/<id>` | Update user |
| DELETE | `/api/auth/users/<id>` | Delete user |
| POST | `/api/simulation/run` | Run full 14-day simulation |
| POST | `/api/simulation/progress` | Run next sim day |
| POST | `/api/simulation/reset` | Reset simulation data |
| GET | `/api/simulation/status` | Day-by-day sim summary |
| GET | `/api/simulation/day/<n>` | Flights for sim day n (1–14) |
| GET | `/api/simulation/report` | Final financial report |
| GET | `/api/simulation/aircraft/<tail>` | Aircraft history by tail number |
| GET | `/api/finances/report` | Financial breakdown |

---

## Useful Makefile Commands
```bash
make setup          # Install deps + build Docker images (run once)
make start          # Start all services
make stop           # Stop all services
make dev-frontend   # Run React dev server without Docker
make dev-backend    # Run Flask without Docker (needs DB running)
make db-shell       # Open MariaDB shell 
Hashes: (SELECT username, password_hash FROM users;)
make db-reset       # Reset database (destroys all data)
make logs           # Follow all logs
make timetable      # Generate Part 1 timetable
make simulate       # Run 14-day simulation
make report         # Print financial report
```

---
## Troubleshooting

### Database issues / corrupted data
If the database gets into a bad state (schema errors, missing tables, stale data from an old version), reset it completely:
```bash
make db-reset
```
This runs `docker compose down -v` (removes containers **and** the database volume), then restarts the DB container fresh. The `database/*.sql` scripts will re-run automatically in numeric order (`00_init.sql` → `08_indexes.sql`), recreating all tables and seed data from scratch.

After the reset, restart everything:
```bash
make start
```
The backend will re-seed the admin user and regenerate the flight timetable on startup (~15 seconds).

### Docker not responding / containers stuck
If containers are hung or Docker is acting up, stop everything, restart Docker, then bring services back up:
```bash
make stop                        # stop all containers
sudo systemctl restart docker    # Linux — restart Docker daemon
# On macOS/Windows: quit and reopen Docker Desktop
make start                       # bring everything back up
```


