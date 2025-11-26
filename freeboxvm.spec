%global pypi_name freeboxvm

Name:           freeboxvm
Version:        0.0.1
Release:        1%{?dist}
Summary:        A command-line tool to manage and access virtual machines on a Freebox

License:        GPL-3.0-or-later
URL:            https://github.com/vivier/freeboxvm
Source0:        %{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3dist(packaging)
BuildRequires:  python3dist(pip)
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(wheel)
BuildRequires:  python3dist(websockets) >= 12
BuildRequires:  python3dist(requests)
BuildRequires:  python3dist(humanize)
BuildRequires:  python3dist(tqdm)
BuildRequires:  python3dist(pygobject)

Requires:       python3dist(requests)
Requires:       python3dist(websockets) >= 12
Requires:       python3dist(tqdm)
Requires:       python3dist(humanize)

Provides:       %{pypi_name} = %{version}-%{release}

%description

A command-line tool to manage and access virtual machines on a Freebox
via the Freebox OS API v8.

%prep
%autosetup -n %{pypi_name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files freeboxvm freeboxvm_version

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%doc README.en.md
%{_bindir}/freeboxvm
%{_mandir}/man1/freeboxvm.1*

%changelog
* Tue Nov 26 2025 Laurent Vivier <laurent@vivier.eu> - 0.0.1-1
- Initial packaging with pyproject macros
