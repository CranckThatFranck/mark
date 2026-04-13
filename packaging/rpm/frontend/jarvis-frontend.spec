%define debug_package %{nil}
Name:           jarvis-frontend
Version:        1.0.0
Release:        1%{?dist}
Summary:        Mark Alfa Frontend (UI)
License:        MIT
Source0:        %{name}-%{version}.tar.gz
Requires:       python3
Requires:       python3-customtkinter
%description
Interface gráfica do Mark Alfa.
%prep
%setup -q
%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/jarvis/frontend
cp -r frontend/* $RPM_BUILD_ROOT/opt/jarvis/frontend/
mkdir -p $RPM_BUILD_ROOT/usr/share/applications
cp packaging/frontend/desktop/mark-alfa.desktop $RPM_BUILD_ROOT/usr/share/applications/
%clean
rm -rf $RPM_BUILD_ROOT
%files
/opt/jarvis/frontend/*
/usr/share/applications/mark-alfa.desktop
