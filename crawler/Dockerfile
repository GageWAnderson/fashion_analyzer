FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for unstructured IO
RUN apt clean && apt update && apt install -y curl libpq-dev tesseract-ocr poppler-utils

# Install poetry
RUN pip install poetry

# Copy the poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Install NLTK and required datasets
RUN python -m nltk.downloader punkt punkt_tab averaged_perceptron_tagger averaged_perceptron_tagger_eng

COPY . .