#!/bin/bash

# Initialize conda in bash
eval "$(conda shell.bash hook)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TKF - Start Development Servers      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# Kill existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2

# Start Backend
echo -e "\n${GREEN}Starting Backend (Django)...${NC}"
cd /home/lidruf/TRANSPORT/backend
conda activate envrl
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "  URL: http://localhost:8000"
echo -e "  Admin: http://localhost:8000/admin"

# Wait for backend to start
sleep 3

# Start Frontend
echo -e "\n${GREEN}Starting Frontend (React/Vite)...${NC}"
cd /home/lidruf/TRANSPORT/frontend
yarn dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "  URL: http://localhost:3001"

# Wait for frontend to start
sleep 3

# Print summary
echo -e "\n${BLUE}════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Both servers are running!${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "  ${BLUE}Frontend:${NC}     http://localhost:3001"
echo -e "  ${BLUE}Backend API:${NC}  http://localhost:8000/api/v1"
echo -e "  ${BLUE}Admin Panel:${NC}  http://localhost:8000/admin"
echo -e "  ${BLUE}API Docs:${NC}     http://localhost:8000/api/v1/docs/"

echo -e "\n${YELLOW}Login Credentials:${NC}"
echo -e "  ${BLUE}Email:${NC}    admin@transport.local"
echo -e "  ${BLUE}Password:${NC} admin123456"

echo -e "\n${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo -e "\n${BLUE}════════════════════════════════════════${NC}\n"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
