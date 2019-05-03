Summary: Prometheus exporter for dcache metrics
Name: dcache_exporter
Version: %{_version}
Release: 1
License: GPLv3
Source0: %{_source}
Requires: python2-prometheus_client
%{?systemd_requires}

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

%post
%systemd_post dcache_exporter.service

%preun
%systemd_preun dcache_exporter.service

%postun
%systemd_postun_with_restart dcache_exporter.service

%files
%defattr(-,root,root,-)
%attr(755, root, root) %{_bindir}/dcache_exporter
/lib/systemd/system/dcache_exporter.service
%config /etc/default/dcache_exporter

%changelog
* Fri May 03 2019 Andrew Pickford <andrewp@nikhef.nl> - 0.5-1
  Add service restarts and stops on package update and removal
  Follow prometheus best practices and prepend dcache metrics with dcache_
  Add requirements to spec file

* Wed Oct 25 2017 Andrew Pickford <andrewp@nikhef.nl> - 0.1-1
- Initial RPM release
