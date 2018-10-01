#!/usr/bin/python

import copy
import httplib
import re
import prometheus_client as pclient
import socket
import threading
import time
import xml.etree.ElementTree as ET

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

VERSION = '0.2'

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


class DcacheCollector(object):
    def __init__(self, host, port, url):
        self._info_host = host
        self._info_port = port
        self._info_url = url
        self._export_tags = [ ('doors', 'door'), ('domains', 'domain'), ('pools', 'pool'), ('poolgroups', 'poolgroup') ]
        self._tree = None
        self._ns = None
        self._metrics = {}

    @staticmethod
    def _get_namespace(element):
        m = re.match('\{.*\}', element.tag)
        return m.group(0)

    @staticmethod
    def _get_short_tag(element):
        m = re.match('(\{.*\})?(.*)', element.tag)
        return m.group(2)

    def _get_xml_tree(self):
        data = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._info_host, self._info_port))
        sock.settimeout(10)
        while True:
            d = sock.recv(1024)
            if not d:
                break
            data.append(d)
        sock.close()
        text = ''.join(data)
        tree = ET.fromstring(text)
        return tree

    def _collect_metric(self, element, set_name, labels):
        tag = self._get_short_tag(element)
        if tag == 'metric':
            type = element.attrib.get('type')
            metric_name = '{0}_{1}'.format(set_name, element.get('name').replace('-', '_'))
            if type == 'float' or type == 'integer':
                if type == 'float':
                    value = float(element.text)
                else:
                    value = int(element.text)
                if metric_name not in self._metrics:
                    self._metrics[metric_name] = pclient.core.GaugeMetricFamily(metric_name, '', labels=[ n for (n, v) in labels ])
                self._metrics[metric_name].add_metric([ v for (n, v) in labels ], value)
        else:
            for child in element:
                l = copy.copy(labels)
                for n,v in element.attrib.iteritems():
                    l.append( ('{0}_{1}'.format(tag, n), v) )
                self._collect_metric(child, set_name, l)

    def _collect_metrics_set(self, element, set_name):
        name = element.attrib.get('name')
        if '@' in name:
            name = name[:name.find('@')]
        labels = [ (set_name, name) ]
        for child in element:
            self._collect_metric(child, set_name, labels)

    def _collect_all_metrics(self):
        self._metrics = {}
        for tag_name, tag_prefix in self._export_tags:
            elements = self._tree.findall("{0}{1}".format(self._ns, tag_name))
            for elem in elements[0]:
                self._collect_metrics_set(elem, tag_prefix)

    def collect(self):
        self._tree = self._get_xml_tree()
        self._ns = self._get_namespace(self._tree)
        self._collect_all_metrics()
        for metric_name in sorted(self._metrics.keys()):
            yield self._metrics[metric_name]

def main():
    pclient.REGISTRY.register(DcacheCollector("localhost", 22112))
    start_http6_server(9310, '::')
    while True:
        time.sleep(10)


if __name__ == '__main__':
    main()
