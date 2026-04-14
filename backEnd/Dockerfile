FROM python:3.12-slim

# set working directory to /app
WORKDIR /app

# copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy backend code
COPY main.py .

# expose port
EXPOSE 8000

# start command to run backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
