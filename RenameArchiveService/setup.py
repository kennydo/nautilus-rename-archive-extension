from setuptools import setup
# noinspection PyUnresolvedReferences
import py2app


plist = dict(
    CFBundleIdentifier='com.github.kennydo.RenameArchiveService',
    LSUIElement=1,
    NSServices=[
        dict(
            NSMessage='openRenameArchiveDialog',
            NSPortName='RenameArchiveService',
            NSMenuItem=dict(default='Rename Archive'),
            NSSendTypes=[
                'NSURLPboardType',
            ],
            NSSendFileTypes=[
                'public.zip-archive',
                'com.rarlab.rar-archive',
            ],
        ),
    ],
)

setup(
    name='renamearchive',
    version='0.0.1',
    description='Simple service to rename archives based on the directories within',

    # py2app arguments
    app=['RenameArchiveService.py'],
    options=dict(py2app=dict(plist=plist)),
    data_files=['MainMenu.xib'],

    url='https://github.com/kennydo/rename-archive-extension',
    license='3-clause BSD',
    classifiers=[
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.4',
    ],
)