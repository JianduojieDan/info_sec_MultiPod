FROM python:3.12-slim

# set working directory to /app
WORKDIR /app

# copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy frontend code
COPY app.py .

# expose port
EXPOSE 8501

# FUCK streamlit email collection dialog
ENV STREAMLIT_SERVER_GATHER_USAGE_STATS=false

# start command to run frontend
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
