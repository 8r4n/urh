%global pypi_name urh

Name:           %{pypi_name}
Version:        2.10.0
Release:        1%{?dist}
Summary:        Universal Radio Hacker: investigate wireless protocols like a boss

License:        GPL-3.0-or-later
URL:            https://github.com/jopohl/urh
Source0:        https://github.com/jopohl/urh/archive/v%{version}/%{pypi_name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-Cython
BuildRequires:  python3-numpy
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  desktop-file-utils

Requires:       python3-numpy
Requires:       python3-psutil
Requires:       python3-setuptools
Requires:       python3-qt6

# Optional SDR hardware support
Recommends:     rtl-sdr
Recommends:     hackrf
Recommends:     airspy

%description
The Universal Radio Hacker (URH) is a complete suite for wireless protocol
investigation with native support for many common Software Defined Radios.
URH allows easy demodulation of signals combined with an automatic detection
of modulation parameters making it a breeze to identify the bits and bytes
that fly over the air. As data often gets encoded before transmission, URH
offers customizable decodings to crack even sophisticated encodings like
CC1101 data whitening. When it comes to protocol reverse-engineering, URH is
helpful in two ways. You can either manually assign protocol fields and
message types or let URH automatically infer protocol fields with a
rule-based intelligence. Finally, URH entails a fuzzing component aimed at
stateless protocols and a simulation environment to perform stateful attacks.

%prep
%autosetup -n %{pypi_name}-%{version}

%build
%py3_build

%install
%py3_install

# Install desktop file
install -Dpm 0644 data/urh.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

# Install application icon
install -Dpm 0644 data/icons/appicon.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/%{name}.png

%files
%license LICENSE
%doc README.md
%{_bindir}/urh
%{_bindir}/urh_cli
%{_bindir}/urh_mcp
%{python3_sitearch}/%{pypi_name}/
%{python3_sitearch}/%{pypi_name}-%{version}*
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/128x128/apps/%{name}.png

%changelog
* Fri Feb 20 2026 URH Developers <Johannes.Pohl90@gmail.com> - 2.10.0-1
- Initial RPM package for Red Hat Enterprise Linux 9.7
