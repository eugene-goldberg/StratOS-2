#!/bin/bash

# Script to start both frontend and backend for StratOS development

# Print colored status messages
print_status() {
  echo -e "\e[1;34m>>> $1\e[0m"
}

print_error() {
  echo -e "\e[1;31m>>> $1\e[0m"
}

print_success() {
  echo -e "\e[1;32m>>> $1\e[0m"
}

# Check if .env files exist
if [ ! -f "./backend/.env" ]; then
  print_error "Backend .env file not found!"
  print_status "Please create a backend/.env file based on backend/.env.example"
  exit 1
fi

if [ ! -f "./frontend/.env" ]; then
  print_error "Frontend .env file not found!"
  print_status "Using default environment variables. Create a frontend/.env file for custom configuration."
fi

# Function to kill all child processes when the script exits
cleanup() {
  print_status "Shutting down development servers..."
  kill 0
  exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start backend
print_status "Starting StratOS backend server..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
backend_pid=$!
cd ..

# Check if backend started successfully
sleep 2
if ! ps -p $backend_pid > /dev/null; then
  print_error "Failed to start backend server!"
  print_status "Please check the backend logs for errors."
  exit 1
fi

print_success "Backend server started successfully! (PID: $backend_pid)"

# Start frontend
print_status "Starting StratOS frontend development server..."
cd frontend
npm start &
frontend_pid=$!
cd ..

# Check if frontend started successfully
sleep 5
if ! ps -p $frontend_pid > /dev/null; then
  print_error "Failed to start frontend server!"
  print_status "Please check the frontend logs for errors."
  cleanup
  exit 1
fi

print_success "Frontend development server started successfully! (PID: $frontend_pid)"
print_success "StratOS development environment is now running!"
print_status "Backend API: http://localhost:8000"
print_status "Frontend UI: http://localhost:3000"
print_status "Press Ctrl+C to stop all servers"

# Wait for user to cancel (Ctrl+C)
wait