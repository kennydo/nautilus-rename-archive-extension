import objc
import os
import urllib
import urlparse
import zipfile

# noinspection PyUnresolvedReferences
from AppKit import (
    NSRegisterServicesProvider,
    NSPasteboardURLReadingFileURLsOnlyKey,
    NSPasteboardURLReadingContentsConformToTypesKey,
)
from enum import Enum
# noinspection PyUnresolvedReferences
from Foundation import (
    NSObject, NSLog, NSURL, NSNumber, NSMutableDictionary,
    NSURLTypeIdentifierKey,
)
from PyObjCTools import AppHelper


class UniformTypeIdentifier(Enum):
    zip = 'public.zip-archive'
    rar = 'com.rarlab.rar-archive'


def service_selector(fn):
    """Set the selector signature to be that of a service

    Signature copied from:
    https://pythonhosted.org/pyobjc/examples/Cocoa/AppKit/SimpleService/index.html

    :param fn: the service
    :return: an objc-ified service method
    """
    return objc.selector(fn, signature='v@:@@o^@')


class RenameArchiveService(NSObject):
    # noinspection PyPep8Naming
    @service_selector
    def openRenameArchiveDialog_userData_error_(self, pasteboard, data, error):
        # We only care about file URLs with UTI that we recognize
        file_urls = get_file_urls_from_pasteboard(pasteboard, [UniformTypeIdentifier.zip.value])
        if not file_urls:
            NSLog("None of the selected files had a supported Uniform Type Identifier:")
            unsupported_urls = get_file_urls_from_pasteboard(pasteboard)
            for url in unsupported_urls:
                NSLog("- %@ (%@)", url.filePathURL().absoluteString(), get_uniform_type_identifier(url))
            return

        # We only deal with the first of the selected files.
        # Finder gives us stuff like "file:///.file/id=...", so we turn it into the path URL
        file_url = file_urls[0].filePathURL()
        file_uti = get_uniform_type_identifier(file_url)

        NSLog("Selected: %@", file_url.absoluteString())
        NSLog("UTI: %@", file_uti)

        # modules don't like dealing with the escaped path strings
        file_path = get_file_path(file_url)

        directory_names = []
        if file_uti == UniformTypeIdentifier.zip.value:
            directory_names = get_zip_directory_names(file_path)
        elif file_uti == UniformTypeIdentifier.rar.value:
            NSLog("RAR isn't supported yet!")

        NSLog("Dumping directory names in %@:", file_path)
        for d in directory_names:
            NSLog("- %@", d)
        return


def get_file_urls_from_pasteboard(pasteboard, desired_uti_types=None):
    """Return the file NSURL objects in the pasteboard.
    Specify the optional desired_uti_types is a list of UTI strings to only return

    :param NSPasteboard pasteboard: pasteboard
    :param desired_uti_types: a list of UTIs in string form
    :type desired_uti_types: list of Uniform Type Identifier strings
    :return: a list of NSURL objects satisfying the desired_uti_types restriction (if any)
    :rtype: list of NSURL
    """
    options = NSMutableDictionary.dictionaryWithCapacity_(2)
    options.setObject_forKey_(NSNumber.numberWithBool_(True),
                              NSPasteboardURLReadingFileURLsOnlyKey)
    if desired_uti_types:
        options.setObject_forKey_(desired_uti_types,
                                  NSPasteboardURLReadingContentsConformToTypesKey)
    nsurls = pasteboard.readObjectsForClasses_options_([NSURL], options)
    return nsurls


def get_uniform_type_identifier(file_url):
    """Get the resource's uniform type identifier

    :param NSURL file_url: URL to a file
    :return: the resource's uniform type identifier as a str or None
    """
    return file_url.getResourceValue_forKey_error_(None, NSURLTypeIdentifierKey, None)[1]


def get_file_path(nsurl):
    """Get the unescaped absolute path of a NSURL

    :param NSURL nsurl: a file NSURL
    :return: unescaped absolute path string
    """
    escaped_path = nsurl.path()
    return urllib.unquote(urlparse.urlparse(escaped_path).path)


def get_zip_directory_names(file_path):
    """Get the list of directories inside a ZIP archive.
    First reads the directory names inside of a ZIP archive, and then returns a list of
    each directory name (without its parent directories).

    :param str file_path: A string that can be a relative filename or file path (it
        doesn't matter as long as this script can read it) of a ZIP file
    :return: a list of directory name strings.
    """
    names = list()
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            names = [fname for fname in zip_file.namelist()
                     if fname.endswith('/')]
    except zipfile.BadZipfile as e:
        print(e)
    directory_names = [os.path.basename(dir_name[:-1]) for dir_name in names]
    return directory_names


def main():
    service_provider = RenameArchiveService.alloc().init()
    NSRegisterServicesProvider(service_provider, 'RenameArchiveService')
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()