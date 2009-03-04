Developing on Debian
====================

Notes about developing on Debian


Building and testing a package
------------------------------
::

  dpkg-buildpackage -rfakeroot -uc -b -tc
  sudo dpkg -i ../python-smisk_*.deb
