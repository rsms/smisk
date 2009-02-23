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

# MacPorts (Need to be done after source has been distributed)
# todo

# Push tags and possible changes to the master repository
git push --tags
