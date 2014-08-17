#!/bin/bash
python setup.py py2app -A
rm -rf ~/Library/Services/renamearchive.app/
mv dist/renamearchive.app ~/Library/Services
killall renamearchive
