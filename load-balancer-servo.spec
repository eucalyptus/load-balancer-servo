%if 0%{?el5}
%global pybasever 2.6
%global __python_ver 26
%global __python /usr/bin/python%{pybasever}
%global __os_install_post %{__multiple_python_os_install_post}
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           load-balancer-servo
Version:        1.0.0
Release:        0%{?build_id:.%build_id}%{?dist}
Summary:        Configuration tool for the Eucalyptus LB

Group:          Applications/System
License:        GPLv3 
URL:            http://www.eucalyptus.com
Source0:        %{name}-%{version}%{?tar_suffix}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch

BuildRequires:  python%{?__python_ver}-devel
BuildRequires:  python%{?__python_ver}-setuptools

Requires:       python%{?__python_ver}
Requires:       python%{?__python_ver}-boto
Requires:       python%{?__python_ver}-httplib2
Requires:       haproxy >= 1.5
Requires:       sudo
Requires(pre):  %{_sbindir}/useradd

%description
Configuration tool for the Eucalyptus LB

%prep
%setup -q -n %{name}-%{version}%{?tar_suffix}

%build
# Build CLI tools
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT

# Install CLI tools
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/sudoers.d/

#
# There is no extension on the installed sudoers file for a reason
# It will only be read by sudo if there is *no* extension
#
install -m 0440 scripts/servo-sudoers.conf $RPM_BUILD_ROOT/%{_sysconfdir}/sudoers.d/servo

mkdir -p $RPM_BUILD_ROOT/%{_initddir}
install -m 755 scripts/load-balancer-servo-init $RPM_BUILD_ROOT/%{_initddir}/load-balancer-servo
install -m 700 -d $RPM_BUILD_ROOT/%{_var}/{run,lib,log}/load-balancer-servo

%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent passwd servo >/dev/null || \
    useradd -d /var/lib/load-balancer-servo \
    -M -s /sbin/nologin servo

# Stop running services for upgrade
if [ "$1" = "2" ]; then
    /sbin/service load-balancer-servo stop 2>/dev/null || :
fi

%files
%defattr(-,root,root,-)
%{python_sitelib}/*
%{_bindir}/load-balancer-servo
%{_sysconfdir}/sudoers.d/servo-sudoers.conf
%{_initddir}/load-balancer-servo
%doc README.md LICENSE

%defattr(-,servo,servo,-)
%dir %{_sysconfdir}/load-balancer-servo
%dir %{_var}/run/load-balancer-servo
%dir %{_var}/log/load-balancer-servo
%dir %{_var}/lib/load-balancer-servo
%config(noreplace) %{_sysconfdir}/load-balancer-servo/haproxy_template.conf

%changelog
* Thu Mar 07 2013 Eucalyptus Release Engineering <support@eucalyptus.com> - 0-0.8
- Initial build

