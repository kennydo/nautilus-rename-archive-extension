import objc
import os
import subprocess
import urllib
import urlparse
import zipfile

# noinspection PyUnresolvedReferences
from AppKit import (
    NSRegisterServicesProvider,
    NSPasteboardURLReadingFileURLsOnlyKey,
    NSPasteboardURLReadingContentsConformToTypesKey,
    NSAlert,
    NSWarningAlertStyle,
    NSApp,
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
        file_urls = get_file_urls_from_pasteboard(
            pasteboard,
            [UniformTypeIdentifier.zip.value])
        if not file_urls:
            NSLog("None of the selected files had a supported "
                  "Uniform Type Identifier:")
            unsupported_urls = get_file_urls_from_pasteboard(pasteboard)
            for url in unsupported_urls:
                NSLog("- %@ (%@)",
                      url.filePathURL().absoluteString(),
                      get_uniform_type_identifier(url))
            return

        # We only deal with the first of the selected files.
        # Finder gives us stuff like "file:///.file/id=...",
        # so we turn it into the path URL.
        file_url = file_urls[0].filePathURL()
        file_uti = get_uniform_type_identifier(file_url)

        # NSLog("Selected: %@", file_url.absoluteString())
        # NSLog("UTI: %@", file_uti)

        # modules don't like dealing with the escaped path strings
        file_path = get_file_path(file_url)

        directory_names = []
        if file_uti == UniformTypeIdentifier.zip.value:
            try:
                directory_names = get_zip_directory_names(file_path)
            except zipfile.BadZipfile as e:
                display_alert(
                    "Invalid ZIP Archive",
                    "Unable to parse directory names: " + str(e)
                )
                return
        elif file_uti == UniformTypeIdentifier.rar.value:
            display_alert("Unsupported Archive", "RAR isn't supported yet!")

        archive_name = os.path.basename(file_path)

        selected_name = prompt_user_rename_archive_dialog(
            archive_name,
            directory_names)
        if not selected_name:
            return

        # NSLog("Selected: %@", selected_name)
        new_file_path = get_new_file_path(file_path, selected_name)
        # NSLog("Destination: %@", new_file_path)

        if os.path.exists(new_file_path):
            # we don't want to overwrite the existing file
            display_alert(
                'Unable to Rename Archive',
                'Unable to rename "{old_name}" to "{new_name}" because '
                '"{new_name}" already exists.'.format(
                    old_name=os.path.basename(file_path),
                    new_name=os.path.basename(new_file_path),
                )
            )
            return

        try:
            os.rename(file_path, new_file_path)
        except OSError as e:
            display_alert(
                'Error while renaming "{old_path}"" to "{new_path}":'
                '{exception}'.format(
                    old_path=file_path,
                    new_path=new_file_path,
                    exception=str(e)
                )
            )
            return
        return


def display_alert(title, message):
    """Display a warning alert with the given ``title`` and ``message``.

    :param title: the big bold title
    :param message: the body of the alert
    """
    alert = NSAlert.alloc().init()
    alert.setAlertStyle_(NSWarningAlertStyle)
    alert.setMessageText_(title)
    alert.setInformativeText_(message)
    NSApp.activateIgnoringOtherApps_(True)
    alert.runModal()


def get_file_urls_from_pasteboard(pasteboard, uti_type_filter=None):
    """Return the file NSURL objects in the pasteboard with an optional UTI
    type filter.

    :param NSPasteboard pasteboard: pasteboard
    :param uti_type_filter: a list of UTIs in string form
    :type uti_type_filter: list of Uniform Type Identifier strings
    :return: NSURL objects satisfying the UTI restriction (if any)
    :rtype: list of NSURL
    """
    options = NSMutableDictionary.dictionaryWithCapacity_(2)
    options.setObject_forKey_(NSNumber.numberWithBool_(True),
                              NSPasteboardURLReadingFileURLsOnlyKey)
    if uti_type_filter:
        options.setObject_forKey_(
            uti_type_filter,
            NSPasteboardURLReadingContentsConformToTypesKey)
    nsurls = pasteboard.readObjectsForClasses_options_([NSURL], options)
    return nsurls


def get_uniform_type_identifier(file_url):
    """Get the resource's uniform type identifier

    :param NSURL file_url: URL to a file
    :return: the resource's uniform type identifier as a str or None
    """
    return file_url.getResourceValue_forKey_error_(
        None,
        NSURLTypeIdentifierKey,
        None)[1]


def get_file_path(nsurl):
    """Get the unescaped absolute path of a NSURL

    :param NSURL nsurl: a file NSURL
    :return: unescaped absolute path string
    """
    escaped_path = nsurl.path()
    return urllib.unquote(urlparse.urlparse(escaped_path).path)


def get_zip_directory_names(file_path):
    """Get the list of directories inside a ZIP archive.
    First reads the directory names inside of a ZIP archive, and then returns a
    list of each directory name (without its parent directories).

    :param str file_path: A string that can be a relative filename or file path
        (it doesn't matter as long as this script can read it) of a ZIP file
    :return: a list of directory name strings
    :raises zipfile.BadZipFile: if ``file_path`` is not a valid zip file
    """
    names = list()
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            names = [fname for fname in zip_file.namelist()
                     if fname.endswith('/')]
    except zipfile.BadZipfile:
        raise
    directory_names = [os.path.basename(dir_name[:-1]) for dir_name in names]
    return directory_names


def get_new_file_path(old_path, new_name):
    """Get the proposed new path for afile if it's renamed.

    Creates the full path of a file if it is renamed.
    It keeps the path of directories leading up to the base name, as
    well as the file extension.
    Calling this function with "/path/to/file.zip" and "new-name" would
    return "/path/to/new-name.zip".

    :param str old_path: full absolute path of a file
    :param str new_name: new name of the file (without file extension)
    :returns: the proposed file path after the file has been renamed
    :rtype: str
    """
    if '.' in old_path:
        extension = old_path.rsplit('.', 1)[1]
        base_name = new_name + '.' + extension
    else:
        base_name = new_name
    return os.path.join(os.path.dirname(old_path), base_name)


def prompt_user_rename_archive_dialog(archive_name, directory_names):
    """Prompt the user to select a new name for ``archive_name``. Their
    choices are ``directory_names``.

    :param str archive_name: full path of an archive
    :param directory_names: all of the directory names within ``archive_name``
    :type directory_names: list of str
    :returns: the selected directory name, or None if the user didn't select
        one
    :rtype: str or None
    """
    result = run_applescript('RenameArchiveDialog.scpt', {
        'ARCHIVENAME': archive_name,
        'DIRECTORYNAMES': '\n'.join(directory_names),
    })
    if not result or not result.startswith("true:"):
        display_alert(
            "Prompt Failed",
            "Prompting the user for directory name failed")
        return None

    selected_name = result[5:].strip()
    if selected_name not in directory_names:
        display_alert(
            "Invalid Name",
            'User selected invalid choice "' + selected_name +
            '" from choices ' + str(directory_names))
        return None

    return selected_name


def run_applescript(scpt_path, env):
    """Run ``scpt_path`` with the given ``env`` dictionary as its environment.

    :param str scpt_path: path to an AppleScript script
    :param dict env: the complete environment that the AppleScript will run in
    :returns: the complete stdout of the executed AppleScript, or None if it
        failed
    :rtype: str or None
    """
    try:
        return subprocess.check_output(
            ['/usr/bin/osascript', scpt_path],
            env=env)
    except subprocess.CalledProcessError as e:
        NSLog("Running AppleScript failed: " + str(e))
    return None


def main():
    service_provider = RenameArchiveService.alloc().init()
    NSRegisterServicesProvider(service_provider, 'RenameArchiveService')
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()
