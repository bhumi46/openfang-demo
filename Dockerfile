FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl git ca-certificates libssl3 && rm -rf /var/lib/apt/lists/*

# Install OpenFang
RUN curl -fsSL https://openfang.sh/install | sh

# Make openfang available on PATH
ENV PATH="/root/.openfang/bin:${PATH}"

WORKDIR /workspace

COPY django-minion/ ./django-minion/

EXPOSE 4200

CMD ["openfang", "start"]
