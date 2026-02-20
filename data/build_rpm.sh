#!/usr/bin/env bash
#
# Build an RPM package for URH (Universal Radio Hacker)
# Target: Red Hat Enterprise Linux 9.7
#
# Usage:
#   ./data/build_rpm.sh
#
# Prerequisites (install once):
#   sudo dnf install rpm-build rpmdevtools python3-devel python3-setuptools \
#                    python3-Cython python3-numpy gcc gcc-c++ desktop-file-utils
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Read version from source
VERSION=$(python3 -c "exec(open('${PROJECT_DIR}/src/urh/version.py').read()); print(VERSION)")
PACKAGE_NAME="urh"

echo "==> Building ${PACKAGE_NAME}-${VERSION} RPM"

# Set up rpmbuild directory tree
rpmdev-setuptree 2>/dev/null || {
    mkdir -p "${HOME}/rpmbuild"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
}

# Create source tarball
TARBALL_DIR="${PACKAGE_NAME}-${VERSION}"
TARBALL_NAME="${TARBALL_DIR}.tar.gz"

echo "==> Creating source tarball ${TARBALL_NAME}"
WORK_DIR=$(mktemp -d)
trap 'rm -rf "${WORK_DIR}"' EXIT
git -C "${PROJECT_DIR}" archive --format=tar.gz --prefix="${TARBALL_DIR}/" HEAD \
    -o "${WORK_DIR}/${TARBALL_NAME}"
cp "${WORK_DIR}/${TARBALL_NAME}" "${HOME}/rpmbuild/SOURCES/${TARBALL_NAME}"

# Copy spec file
cp "${SCRIPT_DIR}/urh.spec" "${HOME}/rpmbuild/SPECS/urh.spec"

# Build RPM
echo "==> Running rpmbuild"
rpmbuild -ba "${HOME}/rpmbuild/SPECS/urh.spec"

echo ""
echo "==> Build complete. Packages:"
find "${HOME}/rpmbuild/RPMS" "${HOME}/rpmbuild/SRPMS" -name '*.rpm' 2>/dev/null
