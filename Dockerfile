FROM python:3-slim

RUN apt-get update -q && \
    apt-get install -y python3-pip && \
    apt-get install -y unixodbc unixodbc-dev && \
    pip3 install prometheus-client && \
    pip3 install pyodbc && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# TODO: Copy a vendor specific ODBC driver and (optionally) odbc.ini.

WORKDIR /usr/src/app

COPY prometheus_odbc_exporter/*.py ./prometheus_odbc_exporter/
COPY exporter.cfg ./
COPY setup.py ./
COPY LICENSE README.md MANIFEST.in ./

RUN pip install -e .

EXPOSE 9296

ENTRYPOINT ["prometheus-odbc-exporter", "-c", "/usr/src/app/exporter.cfg"]
