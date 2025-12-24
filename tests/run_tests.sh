#!/bin/bash

# ZeroDB Embeddings API Test Suite Runner
# Issue #3: Test ZeroDB Embeddings API integration

set -e

echo "=========================================="
echo "Ocean Backend - ZeroDB Embeddings API Tests"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env from .env.test.example and add your credentials."
    echo ""
    echo "  cp .env.test.example .env"
    echo "  # Edit .env and add ZERODB_API_KEY and ZERODB_PROJECT_ID"
    echo ""
    exit 1
fi

# Check if test dependencies are installed
echo "Checking test dependencies..."
python3 -c "import pytest, pytest_asyncio, httpx, dotenv" 2>/dev/null || {
    echo "Installing test dependencies..."
    pip install -r tests/requirements-test.txt
}

echo ""
echo "Environment Configuration:"
echo "------------------------------------------"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('ZERODB_API_KEY', 'NOT_SET')
project_id = os.getenv('ZERODB_PROJECT_ID', 'NOT_SET')
api_url = os.getenv('ZERODB_API_URL', 'https://api.ainative.studio')

if api_key == 'NOT_SET' or project_id == 'NOT_SET':
    print('ERROR: Missing credentials in .env file!')
    exit(1)

print(f'API URL: {api_url}')
print(f'API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else \"***\"}')
print(f'Project ID: {project_id}')
print(f'Model: BAAI/bge-base-en-v1.5')
print(f'Dimensions: 768')
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo "------------------------------------------"
echo ""

# Run tests based on argument
case "${1:-all}" in
    "all")
        echo "Running ALL tests..."
        python3 -m pytest tests/test_embeddings_api.py -v --tb=short
        ;;
    "generate")
        echo "Running embeddings generation tests..."
        python3 -m pytest tests/test_embeddings_api.py::TestEmbeddingsGenerate -v
        ;;
    "store")
        echo "Running embed-and-store tests..."
        python3 -m pytest tests/test_embeddings_api.py::TestEmbedAndStore -v
        ;;
    "search")
        echo "Running semantic search tests..."
        python3 -m pytest tests/test_embeddings_api.py::TestSemanticSearch -v
        ;;
    "errors")
        echo "Running error case tests..."
        python3 -m pytest tests/test_embeddings_api.py::TestErrorCases -v
        ;;
    "dimensions")
        echo "Running dimension consistency tests..."
        python3 -m pytest tests/test_embeddings_api.py::TestDimensionConsistency -v
        ;;
    "coverage")
        echo "Running tests with coverage report..."
        python3 -m pytest tests/test_embeddings_api.py -v --cov=tests --cov-report=term-missing --cov-report=html
        echo ""
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    *)
        echo "Usage: ./tests/run_tests.sh [all|generate|store|search|errors|dimensions|coverage]"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Test execution complete!"
echo "=========================================="
