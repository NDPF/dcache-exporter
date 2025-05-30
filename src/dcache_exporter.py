#!/usr/bin/python3

import argparse
import copy
import re
import prometheus_client as pclient
import socket
import threading
import time
import xml.etree.ElementTree as ET

from http.server import HTTPServer
from socketserver import ThreadingMixIn

VERSION = '0.7'
PROM_PORT = 9310
PROM_ADDRESS = '::'
INFO_PORT = 22112
INFO_ADDRESS = 'localhost'

def start_http6_server(port, addr=''):
    """Starts an HTTP server for prometheus metrics as a daemon thread"""
    class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
        address_family = socket.AF_INET6
    class PrometheusMetricsServer(threading.Thread):
        def run(self):
            httpd = ThreadingSimpleServer((addr, port), pclient.MetricsHandler)
            httpd.serve_forever()
    t = PrometheusMetricsServer()
    t.daemon = True
    t.start()


def get_namespace(element):
    m = re.match('\{.*\}', element.tag)
    return m.group(0)


def get_short_tag(element):
    m = re.match('(\{.*\})?(.*)', element.tag)
    return m.group(2)


class ExportTag(object):
    def __init__(self, name, prefix, default=None, include=[], exclude=[], init_func=None, filter_func=None):
        self.name = name
        self.prefix = prefix
        self.default = default
        self.include = include
        self.exclude = exclude
        self._init_func = init_func
        self._filter_func = filter_func

    def collect_init(self, element):
        if self._init_func:
            self.data = self._init_func(element)

    def collect_metric(self, name, labels):
        if self.default is None:
            return True
        if name in self.include:
            ok = True
        elif name in self.exclude:
            ok = False
        else:
            ok = self.default
        if ok and self._filter_func:
            return self._filter_func(self.data, labels)
        return ok

    @staticmethod
    def DomainInit(element):
        valid_cells = []
        for routing in element:
            if get_short_tag(routing) == 'routing':
                for route in routing:
                    if get_short_tag(route) == 'local':
                        for cell in route:
                            if get_short_tag(cell) == 'cellref':
                                name = cell.attrib.get('name')
                                valid_cells.append(('cell_name', name))
        return valid_cells

    @staticmethod
    def DomainFilter(data, labels):
        for d in data:
            if d in labels:
                return True
        return False


class DcacheCollector(object):
    ExportTags = [ ExportTag('doors', 'door', False, [ 'load' ], [], None, None),
                   ExportTag('domains', 'domain', False, [ 'event_queue_size' ], [], ExportTag.DomainInit, ExportTag.DomainFilter),
                   ExportTag('pools', 'pool', False, [ 'active', 'queued', 'total', 'precious', 'removable', 'used', 'free' ], [], None, None),
                   ExportTag('poolgroups', 'poolgroup', False, [ 'active', 'queued', 'total', 'precious', 'removable', 'used', 'free' ], [], None, None) ]

    def __init__(self, host, port, cluster):
        self._info_host = host
        self._info_port = port
        self._cluster = cluster
        self._tree = None
        self._ns = None
        self._metrics = {}

    def _get_xml_tree(self):
        data = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._info_host, self._info_port))
        sock.settimeout(10)
        while True:
            d = sock.recv(1024)
            if not d:
                break
            data.append(str(d, 'utf-8'))
        sock.close()
        text = ''.join(data)
        tree = ET.fromstring(text)
        return tree

    def _collect_metric(self, element, export, labels):
        tag = get_short_tag(element)
        if tag == 'metric':
            type = element.attrib.get('type')
            name = element.get('name').replace('-', '_')
            if export.collect_metric(name, labels):
                metric_name = 'dcache_{0}_{1}'.format(export.prefix, name)
                if type == 'float' or type == 'integer':
                    if type == 'float':
                        value = float(element.text)
                    else:
                        value = int(element.text)
                    if metric_name not in self._metrics:
                        self._metrics[metric_name] = pclient.metrics_core.GaugeMetricFamily(metric_name, '', labels=[ n for (n, v) in labels ])
                    self._metrics[metric_name].add_metric([ v for (n, v) in labels ], value)
        else:
            for child in element:
                l = copy.copy(labels)
                for n,v in element.attrib.items():
                    l.append( ('{0}_{1}'.format(tag, n), v) )
                self._collect_metric(child, export, l)

    def _collect_metrics_set(self, element, export):
        export.collect_init(element)
        name = element.attrib.get('name')
        if '@' in name:
            name = name[:name.find('@')]
        labels = [ ('dcache_cluster', self._cluster), (export.prefix, name) ]
        for child in element:
            self._collect_metric(child, export, labels)

    def _collect_all_metrics(self):
        self._metrics = {}
        for export in DcacheCollector.ExportTags:
            elements = self._tree.findall('{0}{1}'.format(self._ns, export.name))
            if len(elements) > 0:
                for elem in elements[0]:
                    self._collect_metrics_set(elem, export)

    def collect(self):
        self._tree = self._get_xml_tree()
        self._ns = get_namespace(self._tree)
        self._collect_all_metrics()
        for metric_name in sorted(self._metrics.keys()):
            yield self._metrics[metric_name]


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics-port', dest='metrics_port', type=int, default=PROM_PORT, help='port to export metrics on')
    parser.add_argument('--metrics-address', dest='metrics_address', type=str, default=PROM_ADDRESS, help='address to export metrics on')
    parser.add_argument('-c', '--cluster', dest='cluster', type=str, default='dcache_cluster', help='cluster prometheus label')
    parser.add_argument('--info-port', dest='info_port', type=int, default=INFO_PORT, help='port to export metrics on')
    parser.add_argument('--info-address', dest='info_address', type=str, default=INFO_ADDRESS, help='address to export metrics on')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    pclient.REGISTRY.register(DcacheCollector(args.info_address, args.info_port, args.cluster))
    start_http6_server(args.metrics_port, args.metrics_address)
    while True:
        time.sleep(10)


if __name__ == '__main__':
    main()
