# The distribution process

# Make sure there is no version tag in setup.cfg
grep 'tag_build' setup.cfg

# Tag the node
git tag -u rasmus@flajm.com v1.2.3

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
hg ci -m 'New release'
hg push

# Bump the version number
# Update lib/smisk/release.py
# Add "dev" build tag to setup.cfg
