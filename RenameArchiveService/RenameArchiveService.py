import objc

from AppKit import *
from Foundation import *
from PyObjCTools import AppHelper


def service_selector(fn):
    """
    Set the selector signature to be that of a service

    Signature copied from:
    https://pythonhosted.org/pyobjc/examples/Cocoa/AppKit/SimpleService/index.html

    :param fn: the service
    :return: an objc-ified service method
    """
    return objc.selector(fn, signature="v@:@@o^@")


class RenameArchiveService(NSObject):
    @service_selector
    def openRenameArchiveDialog_userData_error_(self, pboard, data, error):
        # We only care about file URLs
        options = NSDictionary.dictionaryWithObject_forKey_(NSNumber.numberWithBool_(True),
                                                           NSPasteboardURLReadingFileURLsOnlyKey)
        file_urls = pboard.readObjectsForClasses_options_([NSURL], options)
        if not file_urls:
            return

        # We only deal with the first of the selected files.
        # Finder gives us stuff like "file:///.file/id=...", so we turn it into the path URL
        file_url = file_urls[0].filePathURL()

        NSLog("Selected: " + file_url.absoluteString())
        return



def main():
    service_provider = RenameArchiveService.alloc().init()
    NSRegisterServicesProvider(service_provider, 'RenameArchiveService')
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()