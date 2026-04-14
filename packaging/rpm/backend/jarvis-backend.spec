%define debug_package %{nil}
Name:           jarvis-backend
Version:        1.0.0
Release:        1%{?dist}
Summary:        Mark Alfa backend daemon
License:        MIT
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3
Requires:       systemd

%description
Daemon WebSocket do Mark Alfa com Open Interpreter encapsulado e suporte apenas a modelos Gemini via GOOGLE_API_KEY.

%prep
%setup -q

%install
install -d %{buildroot}/opt/jarvis/backend
cp -a backend/. %{buildroot}/opt/jarvis/backend/
install -Dm0644 requirements-backend.txt %{buildroot}/opt/jarvis/backend/requirements.txt
install -Dm0644 packaging/systemd/jarvis-backend.service %{buildroot}%{_unitdir}/jarvis-backend.service

%files
/opt/jarvis/backend
%{_unitdir}/jarvis-backend.service

%post
python3 -m venv /opt/jarvis/venv || true
/opt/jarvis/venv/bin/pip install --upgrade pip "setuptools<70.0.0"
/opt/jarvis/venv/bin/pip install -r /opt/jarvis/backend/requirements.txt
systemctl daemon-reload || true
systemctl enable jarvis-backend.service || true
systemctl restart jarvis-backend.service || systemctl start jarvis-backend.service || true

%preun
if [ $1 -eq 0 ]; then
    systemctl stop jarvis-backend.service || true
    systemctl disable jarvis-backend.service || true
fi

%postun
systemctl daemon-reload || true
