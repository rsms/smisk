# The distribution process

# Tag the node
git tag -s v1.2.3

# Debian
# On each Debian build machine:
git clone rasmus@vmware-host:src/smisk smisk
cd smisk
./setup.py debian -b
# On ONE of the Debian build machines, also create source package:
./setup.py debian -b -s
dupload -t hunch dist/debian

# Source
./admin/sdist.sh --upload # python-smisk.org
./setup.py sdist upload --sign # PyPI

# MacPorts
# Update version number
# Update port revision
# Update checksums (copy from http://python-smisk.org/dist/)
# Commit changes upstream

# Documentation
./admin/docsdist.sh

# Push tags and possible changes to the master repository
git push --tags

# Update the smisk website http://python-smisk.org/
# Update version in app.py

# Bump the version number
# Update lib/smisk/release.py
# Add "dev" build tag to setup.cfg
