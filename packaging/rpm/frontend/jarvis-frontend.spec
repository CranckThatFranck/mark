echo "##active_line5##"
Name:           jarvis-frontend
echo "##active_line6##"
Version:        1.0.0
echo "##active_line7##"
Release:        1%{?dist}
echo "##active_line8##"
Summary:        Mark Alfa Frontend (UI)
echo "##active_line9##"

echo "##active_line10##"
License:        MIT
echo "##active_line11##"
Source0:        %{name}-%{version}.tar.gz
echo "##active_line12##"

echo "##active_line13##"
Requires:       python3
echo "##active_line14##"
Requires:       python3-customtkinter
echo "##active_line15##"

echo "##active_line16##"
%description
echo "##active_line17##"
Interface gráfica do Mark Alfa.
echo "##active_line18##"

echo "##active_line19##"
%prep
echo "##active_line20##"
%setup -q
echo "##active_line21##"

echo "##active_line22##"
%install
echo "##active_line23##"
rm -rf $RPM_BUILD_ROOT
echo "##active_line24##"
mkdir -p $RPM_BUILD_ROOT/opt/jarvis/frontend
echo "##active_line25##"
cp -r src/frontend/* $RPM_BUILD_ROOT/opt/jarvis/frontend/
echo "##active_line26##"

echo "##active_line27##"
mkdir -p $RPM_BUILD_ROOT/usr/share/applications
echo "##active_line28##"
cp packaging/frontend/desktop/mark-alfa.desktop $RPM_BUILD_ROOT/usr/share/applications/
echo "##active_line29##"

echo "##active_line30##"
%clean
echo "##active_line31##"
rm -rf $RPM_BUILD_ROOT
echo "##active_line32##"

echo "##active_line33##"
%files
echo "##active_line34##"
/opt/jarvis/frontend/*
echo "##active_line35##"
/usr/share/applications/mark-alfa.desktop
echo "##active_line36##"
