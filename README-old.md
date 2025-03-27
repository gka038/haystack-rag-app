# RAG Application with Haystack, React UI, OpenSearch, and OpenAI

## Overview

This project is an example Retrieval-Augmented Generation (RAG) application built with Haystack. It demonstrates how to create a functional search and generative question-answering system with a user-friendly interface.

### Backend
The [backend](https://github.com/deepset-ai/haystack-rag-app/tree/main/backend) is built with [FastAPI](https://github.com/fastapi/fastapi) and [Haystack 2](https://github.com/deepset-ai/haystack). It provides a RAG pipeline using [OpenAIGenerator](https://docs.haystack.deepset.ai/docs/openaigenerator).

### Frontend
The [frontend](https://github.com/deepset-ai/haystack-rag-app/tree/main/frontend) is a React application leveraging [Bootstrap](https://getbootstrap.com/). It offers an intuitive interface for users to interact with the RAG system, upload documents, and perform searches.

## Quick Start

To quickly test this application, do the following:

1. Clone the repository:
   ```
   git clone git@github.com:deepset-ai/haystack-rag-app.git
   ```

2. Switch to the project directory:
   ```
   cd haystack-rag-app
   ```

3. Create a `.env` configuration file by copying the example:
   ```
   cp .env.example .env
   ```
   Edit the .env file accordingly. Change the `OPENSEARCH_PASSWORD`. Add `OPENAI_API_KEY`. OpenSearch host URL doesn't have to be changed if running this example with Docker Compose.

4. Start the application using Docker Compose:
   ```
   docker-compose up
   ```
   (Or `docker-compose up -d` to run in detached mode.)

5. Once all containers are up and running, use a browser to access the UI.

The above steps will set up and run all necessary components, including the backend services, frontend, OpenSearch, and the nginx proxy. After a minute or two you can start uploading documents and querying the system as described in the "How to Use" section below.

**Note**: It may take some time for all containers to start. Check container logs if you're having trouble. For instance, the backend containers should report the following when it's ready:

```
nginx-1             | 2024/10/24 13:30:18 [notice] 1#1: nginx/1.27.2
nginx-1             | 2024/10/24 13:30:18 [notice] 1#1: start worker processes
indexing_service-1  | INFO:     127.0.0.1:37836 - "GET /health HTTP/1.1" 200 OK
query_service-1     | INFO:     127.0.0.1:58698 - "GET /health HTTP/1.1" 200 OK
```

## How to Use

### Accessing the UI

1. Ensure that all containers are running and the backend is ready.
2. Open your web browser and navigate to [http://localhost:8080](http://localhost:8080).
3. Use the interface to upload documents that you want to search through. Uploaded files are stored in the `files/uploads` directory inside the backend containers (Docker Compose will mount a volume for this). Currently, the frontend code limits a one-time upload to 110MB.
4. Uploading large files may take a while since the files are indexed synchronously.
5. Once documents are uploaded, you can ask questions and search the documents.
6. The query backend service will use the RAG pipeline to process your query and return relevant results.

**Note**: This RAG application currently supports only PDF, TXT, and Markdown file formats.

### An example query and response

<img width="1388" alt="hra-example-screenshot" src="https://github.com/user-attachments/assets/a1fb86d5-ecc1-4041-9884-2e395544506a" />

## How the Application Works with Docker

When all containers (indexing service, query service, frontend, opensearch and nginx proxy) are running, the application architecture works as follows:

1. **nginx proxy container**: This container acts as a reverse proxy and is the entry point for all incoming requests. It listens on port `8080` and routes traffic based on the request URI:

   - Requests to `/`: These are routed to the frontend container, which serves the React UI application build.
   - Requests to `/api`: These are proxied to the backend services, which handle API requests.

2. **frontend container**: This container hosts the React UI application. It doesn't normally receive external requests but is accessed through the nginx proxy.

3. **backend services containers**: These containers run the indexing and query services and process API requests.

4. **opensearch container**: This container runs OpenSearch. It is accessed by the backend services. It is set up automatically and the index is created automatically by the indexing service.

This setup allows for a clean separation of concerns:

- The nginx proxy handles request routing.
- The frontend container focuses on serving static assets and the React UI build.
- The backend containers manage API requests, indexing and the [RAG pipeline](https://github.com/deepset-ai/haystack-rag-app/blob/main/backend/src/query/service.py).

This architecture provides several benefits:
- Improved security by not exposing the backend directly.
- Simplified frontend/backend communication through a single domain.
- Easy scalability and potential for load balancing in the future.

## Accessing the UI with Containers on a Remote Server

You can access the application by navigating to [http://localhost:8080](http://localhost:8080) in your web browser. The nginx proxy will handle routing your requests based on the URL path.

If the containers are running on a remote server instead of your local machine, you can access the application via ssh port forwarding. Here's how:

1. Run `ssh` to the remote server where the containers are running, using the `-L` option to set up port tunneling. For example:

   ```
   ssh ec2-user@haystack-lab -L 8080:localhost:8080
   ```

   This command will open a local port `8080` that will be tunneled to the remote server and forwarded to the nginx proxy container running there.

2. After establishing the ssh connection with port forwarding, you can access the application by pointing your browser to [http://localhost:8080](http://localhost:8080).

This method allows you to securely access the application running on the remote server as if it were running on your local machine.

### Building and testing the UI locally

In case you want to build and test the UI locally while the containers are running on a remote server, you can do the following:

1. Clone the repository:
   ```
   git clone git@github.com:deepset-ai/haystack-rag-app.git
   ```

2. Switch to the frontend project directory:
   ```
   cd haystack-rag-app/frontend
   ```

3. Install dependencies:
   ```
   npm install
   ```

4. Run the development server:
   ```
   export REACT_APP_HAYSTACK_API_URL=http://localhost:8080/api && \
   npm start
   ```

This will start the frontend application on [http://localhost:3000](http://localhost:3000). With the active ssh port forwarding as described above, the UI will be able to connect to the backend running on the remote server.

## Kubernetes Deployment

This application can also be deployed to Kubernetes using the Helm charts provided in the `charts/` directory. For detailed deployment instructions and configuration options, see [charts/README.md](charts/README.md).

Quick start with Helm:
```bash
# Edit required values in charts/values.yaml
cd charts && \
helm install hra . -f values.yaml
```

## Important Notes

- This example application is based on Haystack 2.
- OpenSearch host URL in [.env.example](https://github.com/deepset-ai/haystack-rag-app/blob/main/.env.example) is configured by default to work with Docker Compose, there's no need to change it.
- OpenSearch password has to match a fairly strict criteria (capital letters, numbers, etc.). OpenSearch will complain along the lines of _"a minimum 8 character password and must contain at least one uppercase letter, one lowercase letter, one digit, and one special character"_ if the password does not meet the requirements.
- Do not create the OpenSearch index manually.
- This project uses [SentenceTransformersDocumentEmbedder](https://docs.haystack.deepset.ai/docs/sentencetransformersdocumentembedder) and [SentenceTransformersTextEmbedder](https://docs.haystack.deepset.ai/docs/sentencetransformerstextembedder) to embed documents and the query. Change `USE_OPENAI_EMBEDDER` in the `.env` file to `true` to use [OpenAIDocumentEmbedder](https://docs.haystack.deepset.ai/docs/openaidocumentembedder) and [OpenAITextEmbedder](https://docs.haystack.deepset.ai/docs/openaitextembedder) instead. Unless starting containers from scratch, delete the OpenSearch index before switching the embedders (vector dimensions will be different).
- If your frontend is hosted on a different domain than the API, you need to add the frontend domain to the `allow_origins` list in [backend/src/common/api_utils.py](https://github.com/deepset-ai/haystack-rag-app/blob/main/backend/src/common/api_utils.py).

## API Routes

The following _unauthenticated_ API routes are available via the nginx proxy:

- `POST /api/search`: Accepts a search query and returns results from the RAG pipeline.
- `GET /api/files`: Returns a list of all uploaded files.
- `POST /api/files`: Allows uploading of files to be indexed by the RAG pipeline.
- `GET /api/health`: Returns a simple "OK" response to check if the nginx proxy is running.

## Troubleshooting

### Checking if OpenSearch is running:

While inside the ./haystack-rag-app directory:

```
(source .env && curl -X GET https://localhost:9200 -u "admin:$OPENSEARCH_PASSWORD" --insecure)
```

### Checking OpenSearch index:

While inside the ./haystack-rag-app directory:

```
(source .env && curl -X GET https://localhost:9200/default/_search?pretty -u "admin:$OPENSEARCH_PASSWORD" --insecure)
```

### Deleting the OpenSearch index:

While inside the ./haystack-rag-app directory:

```
(source .env && curl -X DELETE https://localhost:9200/default -u "admin:$OPENSEARCH_PASSWORD" --insecure)
```

### Checking if the RAG pipeline is working:

```
curl -X POST http://localhost:8080/api/search -H "Content-Type: application/json" -d '{"query": "What is the capital of France?"}'
```

### Removing all Docker containers, images, and volumes

If you need to completely reset your Docker containers and images environment, you can do the following:

```
docker rm -f $(docker ps -aq) && \
docker rmi -f $(docker images -aq) && \
docker system prune -a --volumes && \
docker volume rm $(docker volume ls -q)
```

Careful! This will remove all containers, images, and volumes.
