#!/bin/bash

echo "Starting Smart Construction Platform..."

# Create necessary directories
mkdir -p data/video_frames

# Check if MongoDB is running
echo "Checking MongoDB status..."
if ! pgrep -x "mongod" > /dev/null
then
    echo "MongoDB is not running! Please start MongoDB first."
    echo "You can start it by running: sudo systemctl start mongod"
    exit 1
fi

# Set up the database
echo "Setting up database..."
cd database
python3 setup.py
cd ..

# Start the backend
echo "Starting backend server..."
cd backend
python3 run.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Start the frontend
echo "Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Smart Construction Platform is starting up..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to shut down the platform."

# Handle shutdown
trap "echo 'Shutting down platform...'; kill $BACKEND_PID $FRONTEND_PID; echo 'Platform shutdown complete.'; exit 0" INT TERM

# Keep script running
while true; do
    sleep 1
done 