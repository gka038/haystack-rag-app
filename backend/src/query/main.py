from pathlib import Path
import sys

from contextlib import asynccontextmanager
import json
import logging
from typing import List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from common.api_utils import create_api
from common.models import SearchQuery, QueryResultsResponse
from common.document_store import initialize_document_store
from common.config import settings
from query.service import QueryService
from query.serializer import serialize_query_result


logging.basicConfig(
    format="%(levelname)s - %(name)s - [%(process)d] - %(message)s",
    level=settings.log_level
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Set Haystack logger to INFO level
logging.getLogger("haystack").setLevel(settings.haystack_log_level)

# Create a single instance of QueryService
document_store = initialize_document_store()
query_service = QueryService(document_store)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    yield
    # Shutdown
    logger.info("Shutting down")
    # Add any cleanup code here if needed

app = create_api(title="RAG Query Service", lifespan=lifespan)

def get_query_service():
    if query_service.pipeline is None:
        raise HTTPException(status_code=500, detail="QueryService not initialized")
    return query_service

@app.post("/search", response_model=QueryResultsResponse)
async def search(
    query: SearchQuery,
    service: QueryService = Depends(get_query_service)
) -> QueryResultsResponse:
    """
    Perform a search based on the provided query and filters.

    Parameters:
    - query (SearchQuery): The search query object containing the query string and filters.
    - service (QueryService): The query service instance (automatically injected).

    Returns:
    - SearchResponse: The search results containing a list of replies and any error information.

    Raises:
    - HTTPException: If an error occurs during the search process.

    Description:
    This endpoint accepts a POST request with a SearchQuery object and returns search results.
    It uses the QueryService to perform the search based on the provided query and filters.
    If successful, it returns a SearchResponse with the results. If an error occurs, it logs
    the error and raises an HTTPException with a 500 status code.
    """
    logger.info(f"Received search query: {query.query}")

    try:
        answer = service.search(query.query, query.filters)
        response = serialize_query_result(query.query, answer)

        logger.info(f"QueryResultsResponse:\n{response}")

        return response
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
