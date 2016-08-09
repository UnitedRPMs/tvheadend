%global tvheadend_user %{name}
%global tvheadend_group video

Name:           tvheadend
Version:        4.0.9
Release:        2%{?dist}
Summary:        TV streaming server and digital video recorder

Group:          Applications/Multimedia
License:        GPLv3+
URL:            https://tvheadend.org/
Source0:        https://github.com/tvheadend/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz
# Fix build, see https://github.com/tvheadend/tvheadend/commit/9ddcb8d
Patch0:         %{name}-4.0.9-build.patch
# Fix build with FFmpeg >= 3.0, based on:
# - https://github.com/tvheadend/tvheadend/commit/ea02889
# - https://github.com/tvheadend/tvheadend/commit/c63371c
# - https://github.com/tvheadend/tvheadend/commit/3cbee55
Patch1:         %{name}-4.0.9-ffmpeg_3.0.patch
# Use system queue.h header
Patch2:         %{name}-4.0.9-use_system_queue.patch
# Fix build with hdhomerun
Patch3:         %{name}-4.0.9-hdhomerun.patch
# Fix system DTV scan tables path
Patch4:         %{name}-4.0.9-dtv_scan_tables.patch
# Fix systemd service and configuration:
# - Fix daemon user path
# - Fix daemon group (use video to access DVB devices)
# - Add -C option to allow UI access without login at first run
Patch5:         %{name}-4.0.9-service.patch
# Enforcing system crypto policies, see
# https://fedoraproject.org/wiki/Packaging:CryptoPolicies
Patch6:         %{name}-4.0.9-crypto_policies.patch
# Fix build with FFmpeg >= 3.1, based on
# https://github.com/tvheadend/tvheadend/commit/374ab83
Patch7:         %{name}-4.0.9-ffmpeg_3.1.patch

BuildRequires:  bzip2
BuildRequires:  gcc
BuildRequires:  gzip
BuildRequires:  hdhomerun-devel
BuildRequires:  pkgconfig(avahi-client)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavfilter)
BuildRequires:  pkgconfig(libavformat)
BuildRequires:  pkgconfig(libavresample)
BuildRequires:  pkgconfig(libavutil)
BuildRequires:  pkgconfig(liburiparser)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  python2
BuildRequires:  systemd
Requires:       dtv-scan-tables
%{?systemd_requires}
Provides:       bundled(extjs) = 3.4.1

%description
Tvheadend is a TV streaming server and recorder supporting DVB-S, DVB-S2, DVB-C,
DVB-T, ATSC, IPTV, SAT>IP and HDHomeRun as input sources.

Tvheadend offers the HTTP (VLC, MPlayer), HTSP (Kodi, Movian) and SAT>IP
streaming.

Multiple EPG sources are supported (over-the-air DVB and ATSC including OpenTV
DVB extensions, XMLTV, PyXML).

The Analog video (V4L) is supported directly up to version 3.4. In recent
version, the pipe:// source (in IPTV network) might be used to obtain the
MPEG-TS stream generated by ffmpeg/libav from a V4L device.


%prep
%setup -q
%patch0 -p0 -b .build
# RPM Fusion provides FFMpeg 3.0 for Fedora >= 24
%if 0%{?fedora} >= 24
%patch1 -p0 -b .ffmpeg_3.0
%endif
%patch2 -p0 -b .use_system_queue
%patch3 -p0 -b .hdhomerun
%patch4 -p0 -b .dtv_scan_tables
%patch5 -p0 -b .service
%patch6 -p0 -b .crypto_policies
# RPM Fusion provides FFMpeg 3.1 for Fedora >= 25
%if 0%{?fedora} >= 25
%patch7 -p0 -b .ffmpeg_3.1
%endif

# Delete bundled system headers
rm -r vendor/{dvb-api,include}/


%build
# Use touch to be sure that configure, after being patched, is still older than
# generated .config.mk file (otherwise the build fails)
touch -r Makefile configure
%configure \
    --disable-dvbscan \
    --disable-hdhomerun_static \
    --disable-libffmpeg_static_x264 \
    --enable-hdhomerun_client
%make_build V=1


%install
%make_install

install -Dpm 0644 rpm/%{name}.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
install -Dpm 0644 rpm/%{name}.sysconfig $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}

install -dm 0755 $RPM_BUILD_ROOT%{_sharedstatedir}/%{name}/

# Fix permissions
chmod 0644 $RPM_BUILD_ROOT%{_mandir}/man1/%{name}.1

# Drop bundled Ext JS resources not required by Tvheadend UI
pushd $RPM_BUILD_ROOT%{_datadir}/%{name}/src/webui/static/extjs/
rm -r *.js adapter/ examples/ resources/css/ resources/images/{access,gray,vista,yourtheme}/
popd


%pre
getent passwd %{tvheadend_user} >/dev/null || useradd -r -g %{tvheadend_group} -d %{_sharedstatedir}/%{name}/ -s /sbin/nologin -c "%{name} daemon account" %{name}
exit 0


%post
%systemd_post %{name}.service


%preun
%systemd_preun %{name}.service


%postun
%systemd_postun_with_restart %{name}.service


%files
%doc CONTRIBUTING.md README.md
%license LICENSE.md licenses/gpl-3.0.txt 
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(-,%{tvheadend_user},%{tvheadend_group}) %dir %{_sharedstatedir}/%{tvheadend_user}/
%{_mandir}/man1/*.1.*


%changelog
* Tue Aug 09 2016 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.9-2
- Fix build with FFmpeg 3.1

* Thu Jul 28 2016 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.9-1
- Initial RPM release
