echo "##active_line2##"
cd /home/francisco/Documentos/repos/mark
echo "##active_line3##"
mkdir -p jarvis-backend-1.0.0
echo "##active_line4##"
cp -r src/backend jarvis-backend-1.0.0/
echo "##active_line5##"
cp -r packaging jarvis-backend-1.0.0/
echo "##active_line6##"
tar -czf jarvis-backend-1.0.0.tar.gz jarvis-backend-1.0.0
echo "##active_line7##"
mkdir -p ~/rpmbuild/SOURCES
echo "##active_line8##"
cp jarvis-backend-1.0.0.tar.gz ~/rpmbuild/SOURCES/
echo "##active_line9##"
rpmbuild -ba packaging/rpm/backend/jarvis-backend.spec 2>&1
echo "##active_line10##"
ls -la ~/rpmbuild/RPMS/*
echo "##active_line11##"
