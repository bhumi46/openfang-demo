FROM python:3.11-slim

WORKDIR /openfang

# Install system deps
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Install Python deps globally (no venv needed inside container)
RUN pip install --no-cache-dir \
    groq \
    requests \
    django>=4.2 \
    pytest \
    pytest-django \
    flake8 \
    black \
    isort

# Copy project files
COPY django-minion/ ./django-minion/
COPY test-django-app/ ./test-django-app/
COPY runner/ ./runner/

# Configure git identity for the agent to commit
RUN git config --global user.email "django-minion@openfang.local" && \
    git config --global user.name "django-minion"

# Init the test app as a git repo so the agent can branch + commit
RUN cd test-django-app && git init && git add . && git commit -m "Initial buggy state"

WORKDIR /openfang

CMD ["python", "runner/run.py"]
