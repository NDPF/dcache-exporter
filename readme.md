Build dcache_exporter rpm

Requires (centos7/python2): make, rpm-build, python, python2-prometheus_client (available in epel)
         (rocky8/python3): make, rpm-build, python, python3-prometheus_client (available in epel)

The centos 7 version uses python2, the last released version for python is 0.6 (see the v0.6 tag).

New releases will be for python 3 (tested on rocky 8) and have a version number of 0.7 or higher.

Usage: make


