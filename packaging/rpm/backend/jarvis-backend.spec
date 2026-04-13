Name:           jarvis-backend
Version:        1.0.0
Release:        1%{?dist}
Summary:        Mark Alfa Backend Server

License:        MIT
Source0:        %{name}-%{version}.tar.gz

Requires:       python3
Requires:       systemd

%description
Servidor Backend do Mark Alfa (Open Interpreter encapsulado).

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/jarvis/backend
cp -r src/backend/* $RPM_BUILD_ROOT/opt/jarvis/backend/

mkdir -p $RPM_BUILD_ROOT%{_unitdir}
cp packaging/systemd/jarvis-backend.service $RPM_BUILD_ROOT%{_unitdir}/

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/jarvis/backend/*
%{_unitdir}/jarvis-backend.service

%post
systemctl daemon-reload
systemctl enable jarvis-backend.service
systemctl start jarvis-backend.service

%preun
if [ $1 -eq 0 ]; then
    systemctl stop jarvis-backend.service
    systemctl disable jarvis-backend.service
fi

%postun
systemctl daemon-reload
