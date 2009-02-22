# 1. Test working copy
for PV in  2.4  2.5  2.6  2.7 ; do
  if (which python$PV>/dev/null); then
    echo "Building and testing working copy Smisk with Python $PV"
    python$PV setup.py build -f > /dev/null
    PYTHONPATH=$(echo $(pwd)/build/lib.*-$PV) python$PV -c 'import smisk.test as t;t.test()' > /dev/null || break
  fi
done

# 2. Build package
./setup.py debian > /dev/null

# 3. Test package
dpkg -i dist/debian/python-smisk_VERSION.deb
for PV in  2.4  2.5  2.6  2.7 ; do
  if (which python$PV>/dev/null); then
    echo "Testing installed Smisk with Python $PV"
    python$PV -c 'import smisk.test as t;t.test()' > /dev/null || break
  fi
done
apt-get remove python-smisk

# 4. Upload package(s)
dupload -t hunch dist/debian
