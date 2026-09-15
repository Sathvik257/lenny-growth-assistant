FROM node:24-bookworm-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
COPY public ./public
RUN npm run build && npm prune --omit=dev --ignore-scripts

FROM python:3.12-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
COPY --from=frontend /app/node_modules ./node_modules
COPY --from=frontend /app/dist ./dist
COPY package.json requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY agent ./agent
COPY skills ./skills
COPY scripts/fetch-transcripts.py scripts/render-start.py ./scripts/
# Bound the real corpus to fit the combined API/agent in free-tier RAM.
# The native installation continues to use all 303 transcripts.
RUN python scripts/fetch-transcripts.py --limit 40 --revision be8ab89a890a833cbba2c892178f823fff178c65
RUN useradd --create-home app && mkdir -p /app/.runtime && chown -R app:app /app
USER app
ENV AGENT_HOST=127.0.0.1
ENV AGENT_URL=http://127.0.0.1:8788
EXPOSE 10000
CMD ["python", "scripts/render-start.py"]
