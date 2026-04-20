#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"
BUILD_DIR="$(mktemp -d /tmp/mark-deb-build.XXXXXX)"

prepare_backend_package() {
    local pkg_dir="$BUILD_DIR/jarvis-backend_${VERSION}_all"

    mkdir -p "$pkg_dir/DEBIAN" "$pkg_dir/opt/jarvis/backend" "$pkg_dir/lib/systemd/system"
    tar -C "$ROOT_DIR/src/backend" --exclude='__pycache__' --exclude='*.pyc' -cf - . | tar -C "$pkg_dir/opt/jarvis/backend" -xf -
    cp -a "$ROOT_DIR/requirements-backend.txt" "$pkg_dir/opt/jarvis/backend/requirements.txt"
    cp -a "$ROOT_DIR/packaging/systemd/jarvis-backend.service" "$pkg_dir/lib/systemd/system/jarvis-backend.service"
    cp -a "$ROOT_DIR/packaging/deb/backend/control" "$pkg_dir/DEBIAN/control"
    cp -a "$ROOT_DIR/packaging/deb/backend/postinst" "$pkg_dir/DEBIAN/postinst"
    cp -a "$ROOT_DIR/packaging/deb/backend/prerm" "$pkg_dir/DEBIAN/prerm"
    chmod 0755 "$pkg_dir/DEBIAN/postinst" "$pkg_dir/DEBIAN/prerm"

    dpkg-deb --root-owner-group --build "$pkg_dir" "$ROOT_DIR/jarvis-backend_${VERSION}_all.deb"
}

prepare_frontend_package() {
    local pkg_dir="$BUILD_DIR/jarvis-frontend_${VERSION}_all"

    mkdir -p "$pkg_dir/DEBIAN" "$pkg_dir/opt/jarvis/frontend" "$pkg_dir/usr/share/applications"
    tar -C "$ROOT_DIR/src/frontend" --exclude='__pycache__' --exclude='*.pyc' -cf - . | tar -C "$pkg_dir/opt/jarvis/frontend" -xf -
    install -Dm0644 "$ROOT_DIR/jarvisicon.svg" "$pkg_dir/opt/jarvis/frontend/assets/jarvisicon.svg"
    cp -a "$ROOT_DIR/requirements-frontend.txt" "$pkg_dir/opt/jarvis/frontend/requirements.txt"
    cp -a "$ROOT_DIR/packaging/frontend/desktop/mark-alfa.desktop" "$pkg_dir/usr/share/applications/mark-alfa.desktop"
    cp -a "$ROOT_DIR/packaging/deb/frontend/control" "$pkg_dir/DEBIAN/control"
    cp -a "$ROOT_DIR/packaging/deb/frontend/postinst" "$pkg_dir/DEBIAN/postinst"
    chmod 0755 "$pkg_dir/DEBIAN/postinst"

    dpkg-deb --root-owner-group --build "$pkg_dir" "$ROOT_DIR/jarvis-frontend_${VERSION}_all.deb"
}

prepare_backend_package
prepare_frontend_package

ls -1 "$ROOT_DIR"/jarvis-backend_"${VERSION}"_all.deb "$ROOT_DIR"/jarvis-frontend_"${VERSION}"_all.deb
