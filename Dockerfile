FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl git ca-certificates libssl3 \
    python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python tools the agent needs to lint/test Django projects
RUN pip3 install django pytest pytest-django flake8 black isort

# Configure git identity for the agent
RUN git config --global user.email "django-minion@openfang.local" && \
    git config --global user.name "django-minion"

# Install OpenFang
RUN curl -fsSL https://openfang.sh/install | sh

ENV PATH="/root/.openfang/bin:${PATH}"

WORKDIR /workspace

COPY django-minion/ ./django-minion/

EXPOSE 4200

CMD ["openfang", "start"]
