FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY crawler.py .

CMD ["poetry", "run", "python", "crawler.py"]