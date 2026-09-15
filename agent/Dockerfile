FROM node:24-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts
COPY agent ./agent
COPY skills ./skills
RUN mkdir -p /app/.runtime && chown -R node:node /app/.runtime
USER node
ENV AGENT_HOST=0.0.0.0
EXPOSE 8788
CMD ["node", "agent/server.mjs"]
