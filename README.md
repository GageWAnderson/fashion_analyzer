# Fashion Analyzer
Fashion Analyzer is a web application that uses a FastAPI backend and a React frontend to analyze fashion images. The application is containerized using Docker and coordinated with Docker Compose.

It supports the following features:
1. Summary and analysis of the most recent trends in fashion.
2. A constrained AI search engine that can search the web for clothing itmes a user requests.

Fashion anaylzer runs with 100% local models! It uses [vLLM](https://github.com/vllm-project/vllm) to run the LLMs.

## Features

- **FastAPI Backend**: Provides a robust and high-performance API for image analysis.
- **React Frontend**: A modern and responsive user interface for uploading and viewing fashion images.
- **Docker Compose**: Simplifies the setup and management of the application by coordinating multiple containers.
- **Redis**: Used for caching and session management.
- **Caddy**: Used as a reverse proxy to manage incoming requests and route them to the appropriate backend service.
- **PGAdmin**: Used for storing and querying embeddings as well as other database management.
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

### Installing required models on Ollama
To leverage [Ollama](https://ollama.com/) for LLM inference, you need to install the required models. You can do this by running the following command:
```bash
ollama pull model_name
```
You will need to download `llama3.1` and `nomic-embed-text` models to get started.

#### Pre-commit Hooks
To install pre-commit hooks, run:
```bash
poetry run pre-commit install
```

### Running the Application

#### Start the Frontend
To start the frontend, run:
```bash
cd frontend
pnpm install
pnpm run prisma:generate
pnpm run dev
```

#### Start the Backend
To start the backend, run:
```bash
poetry install
poetry run uvicorn backend.app.main:app --reload --port 9090
```

### Running the LLM server
On a machine with access to an NVIDIA GPU, you can run the LLM server using the following command:
TODO: Investigate the version of CUDA and the model collapse issue on the backend.
NOTE: The Llama 3.1 architecture has better performance on the vLLM server.
```bash
vllm serve mistralai/Mistral-7B-Instruct-v0.3 --dtype bfloat16 --max_model_len 4096 --tensor_parallel_size 2 --tokenizer_mode "mistral"
```

#### Running tool calling on the LLM server
In order to run a tool calling LLM on the vLLM server, a few more arguments are required:
```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --dtype bfloat16 --max_model_len 4096 --tensor_parallel_size 2 \
--chat-template tool_chat_template_llama3.1_json.jinja --tool-call-parser llama3_json --enable-auto-tool-choice
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

## References
- [LangGraph](https://www.langchain.com/langgraph)
- [Ollama + LangGraph](https://www.youtube.com/watch?v=Nfk99Fz8H9k)