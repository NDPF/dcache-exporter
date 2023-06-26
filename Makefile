DEFAULT: all

version:
	$(eval VERSION := $(shell cd src; grep 'VERSION' dcache_exporter.py))
	$(eval VERSION := $(shell python3 -c "$(VERSION) ; print(VERSION)"))

build_tar: version
	mkdir -p tar/dcache_exporter-$(VERSION)
	rm -f tar/dcache_exporter-$(VERSION)/*
	cp src/dcache_exporter.py tar/dcache_exporter-$(VERSION)/dcache_exporter
	cp redhat/dcache_exporter.default tar/dcache_exporter-$(VERSION)
	cp redhat/dcache_exporter.service tar/dcache_exporter-$(VERSION)
	cd tar ; tar -czvf ../dcache-exporter-$(VERSION).tar.gz dcache_exporter-$(VERSION)/*

build_rpm: build_tar version
	rpmbuild -bb --define '_version $(VERSION)' --define '_source dcache-exporter-$(VERSION).tar.gz' --define "_sourcedir ${PWD}" dcache_exporter.spec


all: build_rpm

.PHONY: build_tar build_rpm version all
