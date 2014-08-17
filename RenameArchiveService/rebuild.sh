#!/bin/bash
python setup.py py2app -A
rm -rf ~/Library/Services/RenameArchive.app/
mv dist/RenameArchive.app ~/Library/Services
killall RenameArchive
