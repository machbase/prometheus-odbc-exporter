Prometheus ODBC Exporter
========================

This Prometheus exporter periodically runs configured queries against an ODBC-compatible database and exports the results as Prometheus gauge metrics.

# Prerequisites

The exporter requires prometheus_client and pyodbc modules. See also [pyodbc manual](https://github.com/mkleehammer/pyodbc/wiki/Install).

Python 2.7 and 3.x are supported.

# Installation

To install the exporter, run:

```
pip install .
```

# Usage

By default, it will bind to port 9296, connect to an ODBC database and run queries configured in a file `exporter.cfg` in the working directory. You can change any defaults as required by passing in options:

```
prometheus-odbc-exporter -s <connect string> -e <encoding> -c <path to query config file>
```

The connect string can be as simple as `DSN=mydb` (if you've already prepared the `odbc.ini` file), or have all parameters in it, e.g. `Driver=/path/to/driver.so;SERVER=127.0.0.1;PORT_NO=5656;UID=SYS;PWD=MANAGER;NLS_USE=UTF8`.

The connect string can also be passed by the environment variable `ODBC_CONNECT_STRING`, e.g:

```
ODBC_CONNECT_STRING="DSN=mydb" prometheus-odbc-exporter -c ~/exporter.cfg -e utf-8
```

(The string specified in `-s` option, if exists, takes precedence.)

Run with the `-h` flag to see details on all the available options.

See the provided `exporter.cfg` file for query configuration examples and explanation.
