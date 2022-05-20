# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --upgrade pip
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get -y install libsasl2-dev gcc g++ python3-dev gnupg2 curl libiodbc2-dev
RUN apt install unixodbc-dev --yes
RUN pip install yfinance
RUN pip3 install pyodbc
RUN pip3 install --no-cache-dir -r requirements.txt
#RUN wget http://archive.ubuntu.com/ubuntu/pool/main/g/glibc/multiarch-support_2.27-3ubuntu1.4_amd64.deb
#RUN apt-get install ./multiarch-support_2.27-3ubuntu1.4_amd64.deb

# Install Microsoft ODBC 17/18 Driver and unixodbc for testing SQL Server samples
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && ACCEPT_EULA=Y apt-get install -y  \
    mssql-tools msodbcsql17 msodbcsql18 mssql-tools18 \
  && apt-get clean autoclean \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/* \
  && rm -f /var/cache/apt/archives/*.deb 
RUN export PATH="$PATH:/opt/mssql-tools/bin"
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc 
RUN apt-get update
RUN apt-get install libxslt-dev libffi-dev libssl-dev -y
RUN apt-get upgrade -y


# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app