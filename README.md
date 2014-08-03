Rename Archive Extension
========================

Sometimes, I want to rename archive files based on the names of the directories within the archive.
This repository has extensions to facilitate this behavior on Gnome's Nautilus and Mac's Finder.

By default, this supports ZIP archives. You can enable RAR archive support by installing the rarfile pypi package to your system's libraries.

Installation
============

Nautilus
--------
1. Install the python bindings for Nautilus. It is named ``python-nautilus`` on Ubuntu.
1. Copy the ``Nautilus/rename_archive.py`` file to ``~/.local/share/nautilus-python/extensions``.
1. Quit your current Nautilus session with ``nautilus -q``, then restart nautilus.

Mac
---
1. Double click on the workflow to install.
