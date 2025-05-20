#!/bin/bash

# Setup script for backend only
print_status() {
  echo -e "\e[1;34m>>> $1\e[0m"
}

print_error() {
  echo -e "\e[1;31m>>> $1\e[0m"
}

print_success() {
  echo -e "\e[1;32m>>> $1\e[0m"
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  print_error "python3 is not installed or not in PATH"
  exit 1
fi

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

if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
  print_status "Remember to create backend/.env based on backend/.env.example"
fi

print_success "Backend setup complete"

