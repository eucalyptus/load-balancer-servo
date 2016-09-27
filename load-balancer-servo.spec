%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           load-balancer-servo
Version:        1.3.0
Release:        0%{?build_id:.%build_id}%{?dist}
Summary:        Configuration tool for the Eucalyptus LB

Group:          Applications/System
License:        GPLv3 
URL:            http://www.eucalyptus.com
Source0:        %{tarball_basedir}.tar.xz
Source1:        %{name}.tmpfiles
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch

BuildRequires:  python%{?__python_ver}-devel
BuildRequires:  python%{?__python_ver}-setuptools
BuildRequires:  systemd

Requires:       python%{?__python_ver}
Requires:       python%{?__python_ver}-boto
Requires:       python%{?__python_ver}-httplib2
Requires:       haproxy >= 1.5
Requires:       sudo
Requires:       crontabs
Requires:       ntp
Requires:       ntpdate
Requires:       m2crypto
Requires:       redis
Requires:       python-redis
Requires:       java-1.8.0-openjdk
Requires:       eucalyptus-common-java-libs
Requires(pre):  %{_sbindir}/useradd
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts

%description
Configuration tool for the Eucalyptus LB

%prep
%setup -q -n %{tarball_basedir}

%build
# Build CLI tools
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT

# Install CLI tools
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

#
# There is no extension on the installed sudoers file for a reason
# It will only be read by sudo if there is *no* extension
#
install -p -m 0440 -D scripts/servo-sudoers.conf $RPM_BUILD_ROOT/%{_sysconfdir}/sudoers.d/servo
install -p -m 755 -D scripts/load-balancer-servo-init $RPM_BUILD_ROOT/%{_initddir}/load-balancer-servo
install -p -m 755 -D scripts/servo-prep $RPM_BUILD_ROOT%{_libexecdir}/%{name}/servo-prep
install -m 6700 -d $RPM_BUILD_ROOT/%{_var}/{run,lib,log}/load-balancer-servo
mkdir -p $RPM_BUILD_ROOT/%{_tmpfilesdir}
install -m 644 %{SOURCE1} $RPM_BUILD_ROOT/%{_tmpfilesdir}/%{name}.conf
install -p -m 755 -D scripts/log4j.xml $RPM_BUILD_ROOT/%{_var}/lib/%{name}/log4j.xml
%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent passwd servo >/dev/null || \
    useradd -d %{_var}/lib/load-balancer-servo \
    -M -s /sbin/nologin servo

# Stop running services for upgrade
if [ "$1" = "2" ]; then
    /sbin/service %{name} stop 2>/dev/null || :
fi

%post
/sbin/chkconfig --add %{name}

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%files
%defattr(-,root,root,-)
%doc README.md LICENSE
%{python_sitelib}/*
%{_bindir}/load-balancer-servo
%{_sysconfdir}/sudoers.d/servo
%{_initddir}/load-balancer-servo
%{_libexecdir}/%{name}

%defattr(-,servo,servo,-)
%dir %{_sysconfdir}/load-balancer-servo
%dir %{_var}/run/load-balancer-servo
%dir %{_var}/log/load-balancer-servo
%dir %{_var}/lib/load-balancer-servo
%{_var}/lib/%{name}/log4j.xml
%config(noreplace) %{_sysconfdir}/load-balancer-servo/haproxy_template.conf
%config(noreplace) %{_sysconfdir}/load-balancer-servo/boto.cfg
%config(noreplace) %{_sysconfdir}/load-balancer-servo/503.http
%{_tmpfilesdir}/%{name}.conf

%changelog
* Tue Sep 27 2016 Sang-Min Park <smpark.uva@gmail.com> - 1.3.0
- Rename ntp-update script file to servo-prep

* Mon Aug 08 2016 Sang-Min Park <smpark.uva@gmail.com> - 1.3.0
- Add Jar dependicies into library directory

* Fri Jul 22 2016 Garrett Holmstrom <gholms@hpe.com> - 1.3.0
- Version bump (1.3.0)

* Tue Dec 16 2014 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.2-0
- Added chkconfig changes

* Mon Jan 20 2014 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.2-0
- Add m2crypto as a dependency

* Tue Dec 10 2013 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.2-0
- Fix port for communication with CLC

* Tue Sep 24 2013 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.1-0
- Add requires for ntp and ntpdate

* Mon Sep 09 2013 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.1-0
- Add ntp update script and cron job
- Spec file cleanup

* Thu Mar 07 2013 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.0-0
- Initial build
