#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"
BUILD_DIR="$(mktemp -d /tmp/mark-rpm-build.XXXXXX)"
RPMBUILD_DIR="${HOME}/rpmbuild"

mkdir -p "$RPMBUILD_DIR/SOURCES"

prepare_backend_source() {
    local source_dir="$BUILD_DIR/jarvis-backend-$VERSION"
    mkdir -p "$source_dir/backend" "$source_dir/packaging/systemd"

    tar -C "$ROOT_DIR/src/backend" --exclude='__pycache__' --exclude='*.pyc' -cf - . | tar -C "$source_dir/backend" -xf -
    cp -a "$ROOT_DIR/packaging/systemd/jarvis-backend.service" "$source_dir/packaging/systemd/"
    cp -a "$ROOT_DIR/requirements-backend.txt" "$source_dir/requirements-backend.txt"

    tar -C "$BUILD_DIR" -czf "$RPMBUILD_DIR/SOURCES/jarvis-backend-$VERSION.tar.gz" "jarvis-backend-$VERSION"
}

prepare_frontend_source() {
    local source_dir="$BUILD_DIR/jarvis-frontend-$VERSION"
    mkdir -p "$source_dir/frontend" "$source_dir/packaging/frontend/desktop"

    tar -C "$ROOT_DIR/src/frontend" --exclude='__pycache__' --exclude='*.pyc' -cf - . | tar -C "$source_dir/frontend" -xf -
    cp -a "$ROOT_DIR/packaging/frontend/desktop/mark-alfa.desktop" "$source_dir/packaging/frontend/desktop/"
    cp -a "$ROOT_DIR/requirements-frontend.txt" "$source_dir/requirements-frontend.txt"

    tar -C "$BUILD_DIR" -czf "$RPMBUILD_DIR/SOURCES/jarvis-frontend-$VERSION.tar.gz" "jarvis-frontend-$VERSION"
}

prepare_backend_source
prepare_frontend_source

rpmbuild -ba "$ROOT_DIR/packaging/rpm/backend/jarvis-backend.spec"
rpmbuild -ba "$ROOT_DIR/packaging/rpm/frontend/jarvis-frontend.spec"

find "$RPMBUILD_DIR/RPMS" -name "jarvis-backend-$VERSION-*.rpm" -exec cp -a {} "$ROOT_DIR/" \;
find "$RPMBUILD_DIR/RPMS" -name "jarvis-frontend-$VERSION-*.rpm" -exec cp -a {} "$ROOT_DIR/" \;

find "$ROOT_DIR" -maxdepth 1 -name "jarvis-*-*.rpm" -print | sort
