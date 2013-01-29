Summary: DMARC milter and library
Name: opendmarc
Version: 1.0.1
Release: 1%{?dist}
License: BSD and Sendmail
URL: http://www.trusteddomain.org/opendmarc.html
Group: System Environment/Daemons
Requires: lib%{name} = %{version}-%{release}
Requires (pre): shadow-utils
Requires (post): chkconfig
Requires (preun): chkconfig, initscripts
Requires (postun): initscripts

BuildRequires: sendmail-devel, openssl-devel, libtool, pkgconfig
BuildRequires: mysql-devel

Source0: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
OpenDMARC (Domain-based Message Authentication, Reporting & Conformance)
provides an open source library that implements the DMARC verification
service plus a milter-based filter application that can plug in to any
milter-aware MTA, including sendmail, Postfix, or any other MTA that supports
the milter protocol.

The DMARC sender authentication system is still a draft standard, working
towards RFC status.

%package -n libopendmarc
Summary: An open source DMARC library
Group: System Environment/Libraries

%description -n libopendmarc
This package contains the library files required for running services built
using libopendmarc.

%package -n libopendmarc-devel
Summary: Development files for libopendmarc
Group: Development/Libraries
Requires: libopendmarc = %{version}-%{release}

%description -n libopendmarc-devel
This package contains the static libraries, headers, and other support files
required for developing applications against libopendmarc.

%prep
%setup -q

%build
# Always use system libtool instead of opendmarc provided one to
# properly handle 32 versus 64 bit detection and settings
%global LIBTOOL LIBTOOL=`which libtool`

%configure
make DESTDIR=%{buildroot} %{?_smp_mflags} %{LIBTOOL}

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install %{?_smp_mflags} %{LIBTOOL}
mkdir -p %{buildroot}%{_sysconfdir}
mkdir -p %{buildroot}%{_initrddir}
install -m 0755 contrib/init/redhat/%{name} %{buildroot}%{_initrddir}/%{name}
install -m 0755 opendmarc/%{name}.conf.sample %{buildroot}%{_sysconfdir}/%{name}.conf

# Set some basic settings in the default config file
sed -i 's|^# HistoryFile |HistoryFile |' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# Socket |Socket |' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# UserID|UserID |' %{buildroot}%{_sysconfdir}/%{name}.conf

install -p -d %{buildroot}%{_sysconfdir}/tmpfiles.d
cat > %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf <<EOF
D %{_localstatedir}/run/%{name} 0700 %{name} %{name} -
EOF

mv %{buildroot}%{_prefix}/share/doc/%{name} %{buildroot}%{_prefix}/share/doc/%{name}-%{version}
rm %{buildroot}%{_libdir}/*.{la,a}

mkdir -p %{buildroot}%{_includedir}/%{name}
install -m 0755 libopendmarc/dmarc.h %{buildroot}%{_includedir}/%{name}/

mkdir -p %{buildroot}%{_localstatedir}/spool/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}


%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
	useradd -r -g %{name} -G mail -d %{_localstatedir}/run/%{name} -s /sbin/nologin \
	-c "OpenDMARC Milter" %{name}
exit 0

%post
/sbin/chkconfig --add %{name} || :

%post -n libopendmarc -p /sbin/ldconfig

%preun
if [ $1 -eq 0 ]; then
	service %{name} stop >/dev/null || :
	/sbin/chkconfig --del %{name} || :
fi
exit 0

%postun
if [ "$1" -ge "1" ] ; then
	/sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
exit 0

%postun -n libopendmarc -p /sbin/ldconfig


%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc INSTALL README RELEASE_NOTES docs/draft-dmarc-base-00-02.txt
%doc db/README.schema db/schema.mysql
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%{_initrddir}/%{name}
%{_sbindir}/*
%{_mandir}/*/*
%dir %attr(-,%{name},%{name}) %{_localstatedir}/spool/%{name}
%dir %attr(-,%{name},%{name}) %{_localstatedir}/run/%{name}

%files -n libopendmarc
%defattr(-,root,root)
%{_libdir}/libopendmarc.so.*

%files -n libopendmarc-devel
%defattr(-,root,root)
%doc libopendmarc/docs/*.html
%{_includedir}/%{name}
%{_libdir}/*.so

%changelog
* Mon Jan 28 2013 Steve Jenkins <steve@stevejenkins.com.com> 1.0.1
- Accepted Fedora SPEC file management from Todd Lyons (thx, Todd!)
- Fixed some default config file issues by using sed
- Removed BETA references
- Fixed URL in Header

* Wed Jan 23 2013 Todd Lyons <tlyons@ivenue.com> 1.0.1-1iv
- New release (behind schedule)

* Wed Oct 10 2012 Todd Lyons <tlyons@ivenue.com> 1.0.0-0.Beta1.1iv
- New release

* Fri Sep 14 2012 Todd Lyons <tlyons@ivenue.com> 0.2.2-1iv
- Update to current release.

* Fri Aug 31 2012 Todd Lyons <tlyons@ivenue.com> 0.2.1-1iv
- New Release

* Tue Aug  7 2012 Todd Lyons <tlyons@ivenue.com> 0.1.8-1iv
- Initial Packaging of opendmarc
