Summary: Prometheus exporter for dcache metrics
Name: dcache_exporter
Version: %{_version}
Release: 1
License: GPLv3
Source0: %{_source}

%description
Prometheus exporter for dcache metrics

%prep
%setup -q -n %{name}-%{version}

%install
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
mkdir -p $RPM_BUILD_ROOT/etc/default
mkdir -p $RPM_BUILD_ROOT/lib/systemd/system
cp dcache_exporter $RPM_BUILD_ROOT/usr/bin
chmod 755 $RPM_BUILD_ROOT/usr/bin/dcache_exporter
cp dcache_exporter.default $RPM_BUILD_ROOT/etc/default/dcache_exporter
cp dcache_exporter.service $RPM_BUILD_ROOT/lib/systemd/system

%files
%defattr(-,root,root,-)
%attr(755, root, root) %{_bindir}/dcache_exporter
/lib/systemd/system/dcache_exporter.service
%config /etc/default/dcache_exporter

%changelog
* Wed Oct 25 2017 Andrew Pickford <andrewp@nikhef.nl> - 0.1-1
- Initial RPM release
