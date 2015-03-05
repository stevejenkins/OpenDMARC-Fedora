# systemd-compatible version

%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}

Summary: A Domain-based Message Authentication, Reporting & Conformance (DMARC) milter and library
Name: opendmarc
Version: 1.3.1
Release: 2%{?dist}
Group: System Environment/Daemons
License: BSD and Sendmail
URL: http://www.trusteddomain.org/opendmarc.html
Source0: http://downloads.sourceforge.net/project/%{name}/%{name}-%{version}.tar.gz
Requires: lib%{name} = %{version}-%{release}
Requires (pre): shadow-utils

# Uncomment for systemd version
Requires (post): systemd-units
Requires (preun): systemd-units
Requires (postun): systemd-units
Requires (post): systemd-sysv

#Uncomment for SystemV version
#Requires (post): chkconfig
#Requires (preun): chkconfig, initscripts
#Requires (postun): initscripts

# Required for all versions
BuildRequires: sendmail-devel, openssl-devel, libtool, pkgconfig
BuildRequires: mysql-devel

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# Patch0: %{name}.patchname.patch

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
#%patch0 -p1

%build
# Always use system libtool instead of opendmarc provided one to
# properly handle 32 versus 64 bit detection and settings
%define LIBTOOL LIBTOOL=`which libtool`

%configure --with-spf

# remove rpath
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make DESTDIR=%{buildroot} %{?_smp_mflags} %{LIBTOOL}

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install %{?_smp_mflags} %{LIBTOOL}
mkdir -p %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
mkdir -p %{buildroot}%{_initrddir}
install -d -m 0755 %{buildroot}%{_unitdir}
#install -m 0644 contrib/systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -m 0755 contrib/init/redhat/%{name} %{buildroot}%{_initrddir}/%{name}
install -m 0644 %{name}/%{name}.conf.sample %{buildroot}%{_sysconfdir}/%{name}.conf
mkdir -p -m 0755 %{buildroot}%{_sysconfdir}/%{name}

cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} << 'EOF'
# Set the necessary startup options
OPTIONS="-c %{_sysconfdir}/%{name}.conf -P %{_localstatedir}/run/%{name}/%{name}.pid"
EOF

cat > %{buildroot}%{_unitdir}/%{name}.service << 'EOF'
[Unit]
Description=Domain-based Message Authentication, Reporting & Conformance (DMARC) Milter
Documentation=man:opendmarc(8) man:opendmarc.conf(5) man:opendmarc-import(8) man:opendmarc-reports(8) http://www.trusteddomain.org/opendmarc/
After=network.target nss-lookup.target syslog.target

[Service]
Type=forking
PIDFile=/var/run/opendmarc/opendmarc.pid
EnvironmentFile=-/etc/sysconfig/opendmarc
ExecStart=/usr/sbin/opendmarc $OPTIONS
ExecReload=/bin/kill -USR1 $MAINPID
User=opendmarc
Group=opendmarc

[Install]
WantedBy=multi-user.target
EOF

# Set some basic settings in the default config file
sed -i 's|^# HistoryFile /var/run/opendmarc.dat|HistoryFile %{_localstatedir}/spool/%{name}/%{name}.dat|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# Socket |Socket |' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# Syslog false|Syslog true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# UMask 077|UMask 007|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# UserID  opendmarc|UserID  opendmarc:mail|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# SPFIgnoreResults false|SPFIgnoreResults true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# SPFSelfValidate false|SPFSelfValidate true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|/usr/local||' %{buildroot}%{_sysconfdir}/%{name}.conf

install -p -d %{buildroot}%{_sysconfdir}/tmpfiles.d
cat > %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf <<EOF
D %{_localstatedir}/run/%{name} 0700 %{name} %{name} -
EOF

rm -rf %{buildroot}%{_prefix}/share/doc/%{name}
#mv %{buildroot}%{_prefix}/share/doc/%{name} %{buildroot}%{_prefix}/share/doc/%{name}-%{version}
#find %{buildroot}%{_prefix}/share/doc/%{name}-%{version} -type f -exec chmod 0644 \{\} \;
#sed -i -e 's:/usr/local/bin/python:/usr/bin/python:' %{buildroot}%{_prefix}/share/doc/%{name}/dmarcfail.py
rm %{buildroot}%{_libdir}/*.{la,a}

mkdir -p %{buildroot}%{_includedir}/%{name}
install -m 0644 libopendmarc/dmarc.h %{buildroot}%{_includedir}/%{name}/

mkdir -p %{buildroot}%{_localstatedir}/spool/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
	useradd -r -g %{name} -G mail -d %{_localstatedir}/run/%{name} -s /sbin/nologin \
	-c "OpenDMARC Milter" %{name}
exit 0

%post
# Initial installation

#Uncomment for systemd:
if [ $1 -eq 1 ] ; then 
    /bin/systemctl enable %{name}.service >/dev/null 2>&1 || :
fi

#Uncomment for SysV:
#/sbin/chkconfig --add %{name} || :

%post -n libopendmarc -p /sbin/ldconfig

%preun
# Package removal, not upgrade

#Uncomment for systemd:
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi

#Uncomment for SysV:
#if [ $1 -eq 0 ]; then
#	service %{name} stop >/dev/null || :
#	/sbin/chkconfig --del %{name} || :
#fi
#exit 0

%postun
# Package upgrade, not uninstall
#Uncomment for systemd:
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

#Uncomment for SysV:
#if [ "$1" -ge "1" ] ; then
#	/sbin/service %{name} condrestart >/dev/null 2>&1 || :
#fi
#exit 0

%postun -n libopendmarc -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc LICENSE LICENSE.Sendmail README RELEASE_NOTES docs/draft-dmarc-base-13.txt
%doc db/README.schema db/schema.mysql
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_initrddir}/%{name}
%{_sbindir}/*
%{_mandir}/*/*
%dir %attr(-,%{name},%{name}) %{_localstatedir}/spool/%{name}
%dir %attr(-,%{name},mail) %{_localstatedir}/run/%{name}
%dir %attr(-,%{name},%{name}) %{_sysconfdir}/%{name}
%attr(0644,root,root) %{_unitdir}/%{name}.service

%files -n libopendmarc
%defattr(-,root,root)
%{_libdir}/libopendmarc.so.*

%files -n libopendmarc-devel
%defattr(-,root,root)
%doc libopendmarc/docs/*.html
%{_includedir}/%{name}
%{_libdir}/*.so

%changelog
* Wed Mar 04 2015 Steve Jenkins <steve@stevejenkins.com> 1.3.1-2
- Split spec files into and SysV versions with same build numbers
- Added comment for EL5 to bypass MD5 build errors
- Added .service file for systemd

* Sat Feb 28 2015 Matt Domsch <mdomsch@fedoraproject.org> 1.3.1-1
- upgrade to 1.3.1

* Tue Sep 30 2014 Matt Domsch <mdomsch@fedoraproject.org> 1.3.0-3
- add /etc/opendmarc/ config directory

* Sat Sep 27 2014 Matt Domsch <mdomsch@fedoraproject.org> 1.3.0-2
- use --with-spf

* Sat Sep 13 2014 Matt Domsch <mdomsch@fedoraproject.org> 1.3.0-1
- update to version 1.3.0

* Thu Jul 11 2013 Patrick Laimbock <patrick@laimbock.com> 1.1.3-2
- update to version 1.1.3
- updated docs
- remove rpath
- set HistoryFile to /var/spool/opendmarc/opendmarc.dat
- enable logging by default
- set umask to 007
- set UserID to opendmarc:mail

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

