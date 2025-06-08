# Smart Construction Platform

A modern platform for monitoring construction sites through video streaming. This system provides real-time video streaming from Raspberry Pi cameras with a clean, minimalist user interface.

## Features

- Real-time video streaming from Raspberry Pi cameras using RTP over UDP
- Vue.js frontend with Vuetify
- FastAPI backend for handling video streams and API requests
- WebSocket support for low-latency communication
- Responsive design for desktop and mobile devices

## System Architecture

```
                +----------------+
                | Raspberry Pi   |
                | (Camera)       |
                +-------+--------+
                        |
                        | RTP Stream (UDP port 5004)
                        |
                +-------v--------+
                |                |
                | FastAPI Server |
                |                |
                +-------+--------+
                        |
        +---------------+---------------+
        |                               |
+-------v------+                +-------v------+
| HTTP Stream  |                | WebSocket    |
| (Browser)    |                | (Real-time)  |
+--------------+                +--------------+
```

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- ffmpeg

## Installation

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install Node.js dependencies:
   ```
   npm install
   ```

## Running the Application

### Start the Backend Server

```
cd backend
python run.py
```

The FastAPI server will start on http://localhost:8000

### Start the Frontend Development Server

```
cd frontend
npm run dev
```

The Vue.js development server will start on http://localhost:3000

## Raspberry Pi Setup

On your Raspberry Pi, use the following ffmpeg command to stream video to the server:

```
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 \
-i /dev/video0 -c:v copy -f rtp rtp://192.168.3.7:5004
```

Replace `192.168.3.7` with the IP address of your server.

## Usage

Access the web interface at http://localhost:3000 to view the live video stream 