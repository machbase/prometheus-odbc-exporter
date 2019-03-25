import argparse
try:
    import configparser
except: # for Python 2
    import ConfigParser as configparser
import json
import logging
import sched
import sys
import os
import time
try:
    from time import monotonic as time_now
except: # for Python 2
    from time import time as time_now
from numbers import Number

import pyodbc
from prometheus_client import start_http_server, Gauge


gauges = {}


def update_gauges(metrics):
    def format_label_value(value_list):
        return '_'.join(value_list)

    def format_metric_name(name_list):
        return '_'.join(name_list)

    metric_dict = {}
    for (name_list, label_dict, value) in metrics:
        metric_name = format_metric_name(name_list)
        if metric_name not in metric_dict:
            metric_dict[metric_name] = (tuple(label_dict.keys()), {})

        label_keys = metric_dict[metric_name][0]
        label_values = tuple([
            format_label_value(label_dict[key])
            for key in label_keys
        ])

        metric_dict[metric_name][1][label_values] = value

    for metric_name, (label_keys, value_dict) in metric_dict.items():
        if metric_name in gauges:
            (old_label_values_set, gauge) = gauges[metric_name]
        else:
            old_label_values_set = set()
            gauge = Gauge(metric_name, '', label_keys)

        new_label_values_set = set(value_dict.keys())

        for label_values in old_label_values_set - new_label_values_set:
            gauge.remove(*label_values)

        for label_values, value in value_dict.items():
            if label_values:
                gauge.labels(*label_values).set(value)
            else:
                gauge.set(value)

        gauges[metric_name] = (new_label_values_set, gauge)


def parse_response(value_columns, response, metric=[], labels={}):
    result = []

    for row in response:
        result_labels = {}
        for column in row:
            if column not in value_columns:
                result_labels[column] = (str(row[column]),)
        final_labels = labels.copy()
        final_labels.update(result_labels)
        for value_column in value_columns:
            value = row[value_column]
            try:
                if not isinstance(value, Number):
                    value = float(value)
                result.append((metric + [value_column], final_labels, value))
            except ValueError:
                pass

    return result


def run_scheduler(scheduler, odbc_conn, name, interval, query, value_columns):
    def scheduled_run(scheduled_time):
        all_metrics = []

        with odbc_conn.cursor() as cursor:
            try:
                cursor.execute(query)
                raw_response = cursor.fetchall()

                columns = [column[0] for column in cursor.description]
                response = [{column: row[i] for i, column in enumerate(columns)} for row in raw_response]

                metrics = parse_response(value_columns, response, [name])
            except Exception:
                logging.exception('Error while querying [%s], query [%s].', name, query)
            else:
                all_metrics += metrics

        update_gauges(all_metrics)

        current_time = time_now()
        next_scheduled_time = scheduled_time + interval
        while next_scheduled_time < current_time:
            next_scheduled_time += interval

        scheduler.enterabs(
            next_scheduled_time,
            1,
            scheduled_run,
            (next_scheduled_time,)
        )

    next_scheduled_time = time_now()
    scheduler.enterabs(
        next_scheduled_time,
        1,
        scheduled_run,
        (next_scheduled_time,)
    )


def main():
    def server_address(address_string):
        if ':' in address_string:
            host, port_string = address_string.split(':', 1)
            try:
                port = int(port_string)
            except ValueError:
                msg = "port '{}' in address '{}' is not an integer".format(port_string, address_string)
                raise argparse.ArgumentTypeError(msg)
            return (host, port)
        else:
            return (address_string, 5656)

    parser = argparse.ArgumentParser(description='Export ODBC query results to Prometheus.')
    parser.add_argument('-p', '--port', type=int, default=9296,
        help='port to serve the metrics endpoint on. (default: 9296)')
    parser.add_argument('-c', '--config-file', default='exporter.cfg',
        help='path to query config file. Can be absolute, or relative to the current working directory. (default: exporter.cfg)')
    parser.add_argument('-s', '--connect-string', default=os.environ.get('ODBC_CONNECT_STRING', None),
        help='connection description string for ODBC.')
    parser.add_argument('-e', '--char-encoding', default=None,
        help='force this character encoding to encode/decode character types.')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='turn on verbose logging.')
    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(name)s.%(levelname)s %(threadName)s %(message)s',
        level=logging.DEBUG if args.verbose else logging.INFO
    )

    port = args.port

    config = configparser.ConfigParser()
    config.read(args.config_file)

    connect_string = args.connect_string
    char_encoding = args.char_encoding

    query_prefix = 'query_'
    queries = {}
    for section in config.sections():
        if section.startswith(query_prefix):
            query_name = section[len(query_prefix):]
            query_interval = config.getfloat(section, 'QueryIntervalSecs')
            query = config.get(section, 'QueryStatement')
            value_columns = config.get(section, 'QueryValueColumns').split(',')

            queries[query_name] = (query_interval, query, value_columns)

    scheduler = sched.scheduler(time_now, time.sleep)

    logging.info('Starting server...')
    start_http_server(port)
    logging.info('Server started on port %s', port)

    for name, (interval, query, value_columns) in queries.items():
        odbc_conn = pyodbc.connect(connect_string, autocommit=True)

        if char_encoding:
            # see https://github.com/mkleehammer/pyodbc/wiki/Connection
            if sys.version_info[0] < 3:
                odbc_conn.setencoding(str, encoding=char_encoding)
                odbc_conn.setencoding(unicode, encoding=char_encoding)
            else:
                odbc_conn.setencoding(encoding=char_encoding)

            odbc_conn.setdecoding(pyodbc.SQL_CHAR, encoding=char_encoding)
            odbc_conn.setdecoding(pyodbc.SQL_WCHAR, encoding=char_encoding)
            #odbc_conn.setdecoding(pyodbc.SQL_WMETADATA, encoding=char_encoding)

        run_scheduler(scheduler, odbc_conn, name, interval, query, value_columns)

    try:
        scheduler.run()
    except KeyboardInterrupt:
        pass

    logging.info('Shutting down')
