from gi.repository import Nautilus, GObject, Gtk

import functools
import os
import os.path
import urllib
import urlparse
import zipfile
try:
    import rarfile
except ImportError:
    rarfile = None


if rarfile:
    # The default separator is '\\', which is different from what zipfile uses
    rarfile.PATH_SEP = '/'


# I put these in a tuple so that they don't accidentally get mutated.
ZIP_MIME_TYPES = tuple(['application/zip',
                       'application/x-zip',
                       'application/zip-compressed'])
RAR_MIME_TYPES = tuple(['application/rar',
                        'application/x-rar',
                        'application/x-rar-compressed'])


def get_file_path(file_info):
    """Returns the simple file path from a Nautilus.FileInfo.

    Gets the "/path/to/file" part from "file:///path/to/file".

    Args:
        file_info: a Nautilus.FileInfo instance

    Returns:
        A string representing a Unix path
    """
    uri = file_info.get_uri()
    return urllib.unquote(urlparse.urlparse(uri).path)


def get_new_file_path(archive_path, directory_name):
    """Gets the proposed new path for an archive if it's renamed

    Creates the full path of an archive if it is renamed after a directory.
    It keeps the path of directories leading up to the base name, as well as
    the file extension.

    Calling this function with "/path/to/file.zip" and "dir-name" would return:
    "/path/to/dir-name.zip".

    Args:
        archive_path: A string representing the full path of the archive
        directory_name: String value of the directory we want to rename this
            archive after.

    Returns:
        A string of the proposed file path after the archive has been renamed
        after the given directory name.
    """
    if '.' in archive_path:
        extension = archive_path.rsplit('.', 1)[1]
        base_name = directory_name + '.' + extension
    else:
        base_name = directory_name
    return os.path.join(os.path.dirname(archive_path), base_name)


def lru_cache(size):
    """Simple LRU cache"""
    def outer(f):
        prev_inputs = list()
        prev_outputs = dict()

        @functools.wraps(f)
        def wrapper(function_input):
            if function_input in prev_inputs:
                return prev_outputs[function_input]

            function_output = f(function_input)

            if len(prev_inputs) >= size:
                dead_path = prev_inputs[0]
                del prev_inputs[0]
                del prev_outputs[dead_path]

            prev_inputs.append(function_input)
            prev_outputs[function_input] = function_output
            return function_output
        return wrapper
    return outer


@lru_cache(32)
def get_zip_directory_names(filename):
    """Gets the list of directories inside a ZIP archive

    Reads the directory names inside of a ZIP archive, and returns a list of
    each directory name (without its parent directories).

    Args:
        filename: A string that can be a relative filename or file path (it
            doesn't matter as long as this script can read it) of a ZIP file

    Returns:
        A list of directory name strings.
    """
    names = list()
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            names = [fname for fname in zip_file.namelist()
                     if fname.endswith('/')]
    except zipfile.BadZipfile as e:
        print(e)
    directory_names = [os.path.basename(dir_name[:-1]) for dir_name in names]
    return directory_names


@lru_cache(32)
def get_rar_directory_names(filename):
    """Gets the list of directories inside a RAR archive

    Reads the directory names inside of a RAR archive, and returns a list of
    each directory name (without its parent directories).

    Args:
        filename: A string that can be a relative filename or file path (it
            doesn't matter as long as this script can read it) of a ZIP file

    Returns:
        A list of directory name strings.
    """
    names = list()
    try:
        with rarfile.RarFile(filename, 'r') as rar_file:
            names = [info.filename for info in rar_file.infolist() if info.isdir()]
    except rarfile.Error as e:
        print(e)
    directory_names = [os.path.basename(dir_name) for dir_name in names]
    return directory_names


class RenameDialog(GObject.GObject):
    """Wrapped Gtk Message Dialog class"""
    def __init__(self, window, original_name, new_name):
        self.dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.QUESTION,
                                        Gtk.ButtonsType.YES_NO,
                                        "Rename Archive?")
        self.dialog.format_secondary_text(
            "Do you want to rename\n\"{0}\" to\n\"{1}\"".format(
                original_name, new_name))

    def run(self):
        self.response = self.dialog.run()

    def destroy(self):
        self.dialog.destroy()


class RenameArchiveProvider(GObject.GObject, Nautilus.MenuProvider):
    """Creates a submenu to rename archives after the name of a directory
    within the archive.
    """
    def __init__(self):
        self.supported_mime_types = list(ZIP_MIME_TYPES)
        if rarfile:
            self.supported_mime_types += list(RAR_MIME_TYPES)

    def rename_directory_menuitem_cb(self, menu, cb_parameters):
        """Callback for when the user clicks on a directory name
        to rename an archive after.

        This displays a dialog that the user responds to with a Yes or No.
        If the user clicks Yes, then this attempts to rename the file.

        Args:
            menu: the Nautilus.Menu that was the source of the click
            cb_parameters: a tuple of type (Nautilus.FileInfo,
                                            Gtk.Window,
                                            string)
        Returns:
            Nothing.

        """
        file_info, window, directory_name = cb_parameters
        if file_info.is_gone() or not file_info.can_write():
            return
        old_path = get_file_path(file_info)
        old_name = os.path.basename(old_path)
        new_path = get_new_file_path(old_path, directory_name)
        new_name = os.path.basename(new_path)

        dialog = RenameDialog(window, old_name, new_name)
        dialog.run()
        dialog.destroy()

        if dialog.response == Gtk.ResponseType.YES:
            try:
                os.rename(old_path, new_path)
            except os.OSError as e:
                print(e)

    def get_file_items(self, window, files):
        if len(files) != 1:
            return

        selected_file = files[0]

        if selected_file.get_uri_scheme() != 'file':
            # Not sure which URIs zipfile supports reading from
            return

        mime_type = selected_file.get_mime_type()

        if mime_type in self.supported_mime_types:
            top_menuitem = Nautilus.MenuItem(
                name='RenameArchiveProvider::Rename Archive',
                label='Rename Archive',
                tip='Rename archive based on its directory names',
                icon='')

            names_menu = Nautilus.Menu()
            top_menuitem.set_submenu(names_menu)

            # create the submenu items
            file_path = get_file_path(selected_file)
            if mime_type in ZIP_MIME_TYPES:
                directory_names = get_zip_directory_names(file_path)
            elif mime_type in RAR_MIME_TYPES:
                directory_names = get_rar_directory_names(file_path)
            else:
                directory_names = None

            if not directory_names:
                no_directories_menuitem = Nautilus.MenuItem(
                    name='RenameArchiveProvider::No Directories',
                    label='No directory names found',
                    tip='',
                    icon='')
                names_menu.append_item(no_directories_menuitem)
            else:
                for directory_name in directory_names:
                    name = 'RenameArchiveProvider::Directory::' + \
                        directory_name
                    label = 'Rename to "' + \
                        directory_name.replace('_', '__') + '"'
                    # we have to perform the underscore replacement in the label to get it to show up

                    dir_menuitem = Nautilus.MenuItem(
                        name=name,
                        label=label,
                        tip=label,
                        icon='')
                    dir_menuitem.connect(
                        'activate', self.rename_directory_menuitem_cb,
                        (selected_file, window, directory_name))
                    names_menu.append_item(dir_menuitem)

            return [top_menuitem]
        else:
            return
