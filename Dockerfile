FROM python:3.10-slim

LABEL org.opencontainers.image.base.name="python:3.10-slim" \
      org.opencontainers.image.description="GPT-Swarm is an open-source project that harnesses the power of swarm intelligence to enhance the capabilities of state-of-the-art language models. By leveraging collective problem-solving and distributed decision-making, GPT-Swarm creates a robust, adaptive, and scalable framework for tackling complex tasks across various domains." \
      org.opencontainers.image.licenses="Apache License 2.0" \
      org.opencontainers.image.ref.name="nicelir1996/GPT-Swarm" \
      org.opencontainers.image.source="https://github.com/nicelir1996/GPT-Swarm" \
      org.opencontainers.image.url="https://github.com/nicelir1996/GPT-Swarm.git"

WORKDIR /app

COPY requirements.txt ./

# Installing gcc fixes the following error on ARM CPUs:
# ERROR: Could not build wheels for psutil, which is required to install pyproject.toml-based projects
RUN apt-get update && apt-get install -y \
  gcc \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY swarmai /app/swarmai

CMD [ "python", "-m", "swarmai.__main__" ]
