#!/bin/bash

# Install frontend dependencies for StratOS
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

if ! command -v npm >/dev/null 2>&1; then
  print_error "npm is not installed or not in PATH"
  exit 1
fi

print_status "Installing frontend dependencies..."
(cd frontend && npm install)
print_success "Frontend dependencies installed"

