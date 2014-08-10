import objc

# noinspection PyUnresolvedReferences
from AppKit import *
from enum import Enum
# noinspection PyUnresolvedReferences
from Foundation import *
from PyObjCTools import AppHelper


class UniformTypeIdentifier(Enum):
    zip = 'public.zip-archive'
    rar = 'com.rarlab.rar-archive'


def service_selector(fn):
    """
    Set the selector signature to be that of a service

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
        file_urls = get_file_urls_from_pasteboard(pasteboard, [UniformTypeIdentifier.zip])
        if not file_urls:
            NSLog("None of the selected files had a supported Uniform Type Identifier:")
            unsupported_urls = get_file_urls_from_pasteboard(pasteboard)
            for url in unsupported_urls:
                NSLog("- %@ (%@)", url.filePathURL().absoluteString(), get_uniform_type_identifier(url))
            return

        # We only deal with the first of the selected files.
        # Finder gives us stuff like "file:///.file/id=...", so we turn it into the path URL
        file_url = file_urls[0].filePathURL()

        NSLog("Selected: %@", file_url.absoluteString())
        NSLog("UTI: %@", get_uniform_type_identifier(file_url))

        return


def get_file_urls_from_pasteboard(pasteboard, desired_uti_types=None):
    """
    Returns the file NSURL objects in the pasteboard.
    Specify the optional desired_uti_types is a list of UTI strings to only return
    :param NSPasteboard pasteboard: pasteboard
    :param desired_uti_types: a list of UTIs in string form
    :type desired_uti_types: list of str
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
    """
    Gets the resource's uniform type identifier
    :param NSURL file_url: URL to a file
    :return: the resource's uniform type identifier as a str or None
    """
    return file_url.getResourceValue_forKey_error_(None, NSURLTypeIdentifierKey, None)[1]


def main():
    service_provider = RenameArchiveService.alloc().init()
    NSRegisterServicesProvider(service_provider, 'RenameArchiveService')
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()