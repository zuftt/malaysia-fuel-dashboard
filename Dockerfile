# Lambda container image — runs FastAPI via Mangum
FROM public.ecr.aws/lambda/python:3.13

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ${LAMBDA_TASK_ROOT}/app

# Mangum handler in main.py
CMD ["app.main.handler"]
