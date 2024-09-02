# Fashion Analyzer
Fashion Analyzer is a web application that uses a FastAPI backend and a React frontend to analyze fashion images. The application is containerized using Docker and coordinated with Docker Compose.

## Features

- **FastAPI Backend**: Provides a robust and high-performance API for image analysis.
- **React Frontend**: A modern and responsive user interface for uploading and viewing fashion images.
- **Docker Compose**: Simplifies the setup and management of the application by coordinating multiple containers.
- **Redis**: Used for caching and session management.
- **Caddy**: Used as a reverse proxy to manage incoming requests and route them to the appropriate backend service.
- **Chroma**: Used for storing and querying embeddings.
- **Web Crawler**: Used to crawl the web for fashion images.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

### Clone the Repository
```bash
git clone https://github.com/GageWAnderson/fashion_analyzer.git
cd fashion_analyzer
```

### Installing Dependencies

#### Frontend Dependencies
To install frontend dependencies, navigate to the frontend directory and use pnpm:
```bash
cd frontend
pnpm install
```

#### Backend Dependencies
To install backend dependencies, navigate to the backend directory and use pip:
```bash
cd backend
pip install -r requirements.txt
```

### Running the Application

#### Start the Frontend
To start the frontend, run:
```bash
cd frontend
pnpm run dev
```

#### Start the Backend
To start the backend, run:
```bash
cd backend
uvicorn main:app --reload
```

### Run the Application
To run the application, navigate to the root directory and run:
```bash
docker-compose -f docker-compose.yml up -d --build
```

This will start the frontend and backend containers and run the application.

### Run the Web Crawler
To run the web crawler, use the Poetry script:
```bash
poetry run crawl_all_sites
```

### Authentication & Authorization
TODO: Implement

## Contributing

We welcome contributions to the Fashion Analyzer project! If you have any ideas or suggestions, please feel free to open an issue or submit a pull request.