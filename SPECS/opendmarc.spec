%global systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7)
%global upname OpenDMARC
%global bigname OPENDMARC

Summary: A Domain-based Message Authentication, Reporting & Conformance (DMARC) milter and library
Name: opendmarc
Version: 1.3.1
Release: 9%{?dist}
Group: System Environment/Daemons
License: BSD and Sendmail
URL: http://www.trusteddomain.org/%{name}.html
Source0: http://downloads.sourceforge.net/project/%{name}/%{name}-%{version}.tar.gz

# Required for all versions
Requires: lib%{name}%{?_isa} = %{version}-%{release}
BuildRequires: sendmail-devel, openssl-devel, libtool, pkgconfig, libbsd, libbsd-devel, mysql-devel
Requires (pre): shadow-utils

#Required for all but EL5
%if (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 6)
Requires (post): policycoreutils, policycoreutils-python
%endif

%if %systemd
# Required for systemd
Requires (post): systemd-units
Requires (preun): systemd-units
Requires (postun): systemd-units
Requires (post): systemd-sysv
%else
# Required for SysV
Requires (post): chkconfig
Requires (preun): chkconfig, initscripts
Requires (postun): initscripts
%endif

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# Patch0: %{name}.patchname.patch

%description
%{upname} (Domain-based Message Authentication, Reporting & Conformance)
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
Requires: lib%{name}%{?_isa} = %{version}-%{release}

%description -n lib%{name}-devel
This package contains the static libraries, headers, and other support files
required for developing applications against libopendmarc.

%prep
%setup -q
%if %systemd
# Apply systemd patches
#%patch0 -p1
%else
# Apply SysV patches
#%patch0 -p1
%endif

%build
# Always use system libtool instead of package-provided one to
# properly handle 32 versus 64 bit detection and settings
%define LIBTOOL LIBTOOL=`which libtool`

%configure --with-spf --with-sql-backend

# remove rpath
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make DESTDIR=%{buildroot} %{?_smp_mflags} %{LIBTOOL}

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install %{?_smp_mflags} %{LIBTOOL}
mkdir -p %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
mkdir -p -m 0755 %{buildroot}%{_sysconfdir}/%{name}

cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} << 'EOF'
# Set the necessary startup options
OPTIONS="-c %{_sysconfdir}/%{name}.conf -P %{_localstatedir}/run/%{name}/%{name}.pid"
EOF

%if %systemd
install -d -m 0755 %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/%{name}.service << 'EOF'
[Unit]
Description=Domain-based Message Authentication, Reporting & Conformance (DMARC) Milter
Documentation=man:%{name}(8) man:%{name}.conf(5) man:%{name}-import(8) man:%{name}-reports(8) http://www.trusteddomain.org/%{name}/
After=network.target nss-lookup.target syslog.target

[Service]
Type=forking
PIDFile=/var/run/%{name}/%{name}.pid
EnvironmentFile=-/etc/sysconfig/%{name}
ExecStart=/usr/sbin/%{name} $OPTIONS
ExecReload=/bin/kill -USR1 $MAINPID
User=%{name}
Group=%{name}

[Install]
WantedBy=multi-user.target
EOF
%else
mkdir -p %{buildroot}%{_initrddir}
install -m 0755 contrib/init/redhat/%{name} %{buildroot}%{_initrddir}/%{name}
%endif

# Install and set some basic settings in the default config file
install -m 0644 %{name}/%{name}.conf.sample %{buildroot}%{_sysconfdir}/%{name}.conf

sed -i 's|^# AuthservID name |AuthservID HOSTNAME |' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# HistoryFile /var/run/%{name}.dat|# HistoryFile %{_localstatedir}/spool/%{name}/%{name}.dat|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# Socket |Socket |' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# SoftwareHeader false|SoftwareHeader true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# SPFIgnoreResults false|SPFIgnoreResults true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# SPFSelfValidate false|SPFSelfValidate true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# Syslog false|Syslog true|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# UMask 077|UMask 007|' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's|^# UserID %{name}|UserID %{name}:mail|' %{buildroot}%{_sysconfdir}/%{name}.conf
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
install -m 0644 lib%{name}/dmarc.h %{buildroot}%{_includedir}/%{name}/

mkdir -p %{buildroot}%{_localstatedir}/spool/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
	useradd -r -g %{name} -G mail -d %{_localstatedir}/run/%{name} -s /sbin/nologin \
	-c "%{upname} Milter" %{name}
exit 0

%post
%if %systemd
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl enable %{name}.service >/dev/null 2>&1 || :
fi

%else

/sbin/chkconfig --add %{name} || :
%endif

%preun
%if %systemd
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi

%else

if [ $1 -eq 0 ]; then
	service %{name} stop >/dev/null || :
	/sbin/chkconfig --del %{name} || :
fi
exit 0
%endif

%postun
%if %systemd
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%else

if [ "$1" -ge "1" ] ; then
	/sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
exit 0
%endif

%post -n libopendmarc -p /sbin/ldconfig

%postun -n libopendmarc -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%if 0%{?_licensedir:1}
%license LICENSE LICENSE.Sendmail
%else
%doc LICENSE LICENSE.Sendmail
%endif
%doc README RELEASE_NOTES docs/draft-dmarc-base-13.txt
%doc db/README.schema db/schema.mysql
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_sbindir}/*
%{_mandir}/*/*
%dir %attr(-,%{name},%{name}) %{_localstatedir}/spool/%{name}
%dir %attr(-,%{name},mail) %{_localstatedir}/run/%{name}
%dir %attr(-,%{name},%{name}) %{_sysconfdir}/%{name}

%if %systemd
%attr(0644,root,root) %{_unitdir}/%{name}.service
%else
%attr(0755,root,root) %{_initrddir}/%{name}
%endif

%files -n libopendmarc
%{_libdir}/lib%{name}.so.*

%files -n libopendmarc-devel
%doc lib%{name}/docs/*.html
%{_includedir}/%{name}
%{_libdir}/*.so

%changelog
* Mon Mar 30 2015 Steve Jenkins <steve@stevejenkins.com> - 1.3.1-9
- policycoreutils* now only required for Fedora and EL6+
- Added --with-sql-backend configure support
- Changed a few macros

* Sun Mar 29 2015 Steve Jenkins <steve@stevejenkins.com> - 1.3.1-8
- removed unecessary Requires packages
- moved libbsd back to BuildRequires
- removed unecessary %defattr
- added support for %license in place of %doc
- Changed some %{name} macro usages

* Sat Mar 28 2015 Steve Jenkins <steve@stevejenkins.com> - 1.3.1-7
- added %{?_isa} to Requires where necessary
- added sendmail-milter to Requires
- moved libbsd from BuildRequires to Requires
- added policycoreutils and policycoreutils-python to Requires (post)

* Sat Mar 28 2015 Steve Jenkins <steve@stevejenkins.com> - 1.3.1-6
- Removed uneeded _pkgdocdir reference

* Fri Mar 27 2015 Steve Jenkins <steve@stevejenkins.com> - 1.3.1-5
- Combined systemd and SysV spec files using conditionals
- Set AuthservID configuration option to HOSTNAME by default

* Thu Mar 12 2015 Steve Jenkins <steve@stevejenkins.com> 1.3.1-4
- Dropped El5/SysV support due to perl-IO-Compress dependency probs
- Fixed extra space in UserID default setting
- Disabled HistoryFile logging by default
- Set default SoftwareHeader to true
- Set default SPFIgnoreResults to true
- Set default SPFSelfValidate to true

* Fri Mar 06 2015 Steve Jenkins <steve@stevejenkins.com> 1.3.1-3
- Added libbsd and libbsd-devel build requirement to fix libstrl issue

* Thu Mar 05 2015 Steve Jenkins <steve@stevejenkins.com> 1.3.1-2
- Branched spec files into systemd and SysV versions
- Added top comment for EL5 to bypass MD5 build errors
- Added opendmarc.service file for systemd support
- Added sysconfig file support for runtime options

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

* Mon Jan 28 2013 Steve Jenkins <steve@stevejenkins.com> 1.0.1
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

