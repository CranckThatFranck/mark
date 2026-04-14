%define debug_package %{nil}
Name:           jarvis-frontend
Version:        1.0.0
Release:        1%{?dist}
Summary:        Mark Alfa desktop frontend
License:        MIT
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3

%description
Interface grafica em CustomTkinter para o Mark Alfa.

%prep
%setup -q

%install
install -d %{buildroot}/opt/jarvis/frontend
cp -a frontend/. %{buildroot}/opt/jarvis/frontend/
install -Dm0644 requirements-frontend.txt %{buildroot}/opt/jarvis/frontend/requirements.txt
install -Dm0644 packaging/frontend/desktop/mark-alfa.desktop %{buildroot}/usr/share/applications/mark-alfa.desktop

%files
/opt/jarvis/frontend
/usr/share/applications/mark-alfa.desktop

%post
python3 -m venv /opt/jarvis/venv || true
/opt/jarvis/venv/bin/pip install --upgrade pip "setuptools<70.0.0"
/opt/jarvis/venv/bin/pip install -r /opt/jarvis/frontend/requirements.txt
update-desktop-database || true
