#!/bin/bash

# Script to set up backend and frontend development dependencies for StratOS

# Reuse status printing functions from run_dev.sh
print_status() {
  echo -e "\e[1;34m>>> $1\e[0m"
}

print_error() {
  echo -e "\e[1;31m>>> $1\e[0m"
}

print_success() {
  echo -e "\e[1;32m>>> $1\e[0m"
}

# Change to script directory (project root) so it can be run from anywhere
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Verify required commands
if ! command -v python3 >/dev/null 2>&1; then
  print_error "python3 is not installed or not in PATH"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  print_error "npm is not installed or not in PATH"
  exit 1
fi

print_status "python3 and npm found"

# ---------------- Backend Setup ----------------
print_status "Setting up backend Python environment..."

if [ ! -d "backend/venv" ]; then
  python3 -m venv backend/venv
  print_success "Created virtual environment at backend/venv"
else
  print_status "Using existing virtual environment at backend/venv"
fi

print_status "Installing backend requirements..."
backend/venv/bin/python -m pip install -r backend/requirements.txt
print_success "Backend requirements installed"

# ---------------- Frontend Setup ----------------
print_status "Installing frontend dependencies..."
(
  cd frontend && npm install
)
print_success "Frontend dependencies installed"

# ---------------- Environment File Hints ----------------
if [ ! -f "backend/.env" ]; then
  if [ -f "backend/.env.example" ]; then
    print_status "Create backend/.env based on backend/.env.example before running run_dev.sh"
  else
    print_status "Create backend/.env with required environment variables"
  fi
fi

if [ ! -f "frontend/.env" ]; then
  if [ -f "frontend/.env.example" ]; then
    print_status "Create frontend/.env based on frontend/.env.example for custom configuration"
  else
    print_status "Consider creating frontend/.env. Example: REACT_APP_API_BASE_URL=http://localhost:8000"
  fi
fi

print_success "Setup complete. You can now start the development servers with ./run_dev.sh"

