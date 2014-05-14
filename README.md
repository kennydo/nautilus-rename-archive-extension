Nautilus Rename Archive Extension
=================================
This Nautilus extension renames archives based on the names of the directories inside.

By default, this supports ZIP archives. You can enable RAR archive support by installing the rarfile pypi package to your system's libraries.

Installation
============

1. Install the python bindings for Nautilus. It is named ``python-nautilus`` on Ubuntu.
1. Copy the ``rename_archive.py`` file to ``~/.local/share/nautilus-python/extensions``.
1. Quit your current Nautilus session with ``nautilus -q``, then restart nautilus.
