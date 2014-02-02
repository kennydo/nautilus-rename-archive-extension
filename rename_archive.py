from gi.repository import Nautilus, GObject, Gtk
import urllib
import urlparse
import zipfile
import os.path


SUPPORTED_ZIP_MIME_TYPES = ['application/zip',
                            'application/x-zip',
                            'application/zip-compressed']


def get_filename(file_info):
    uri = file_info.get_uri()
    return urllib.unquote(urlparse.urlparse(uri).path)


def get_zip_directory_names(filename):
    names = list()
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            names = [fname for fname in zip_file.namelist() if fname.endswith('/')]
    except zipfile.BadZipfile as e:
        pass
    return [os.path.split(dir_name[:-1])[1] for dir_name in names]

class RenameDialog(GObject.GObject):
    def __init__(self, window):
        self.dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK, "This is an info dialog")
    def run(self):
        self.dialog.run()

    def destroy(self):
        self.dialog.destroy()


class RenameArchiveProvider(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass

    def rename_directory_menuitem_cb(self, menu, cb_parameters):
        fileinfo, window = cb_parameters
        if fileinfo.is_gone() or not fileinfo.can_write():
            return

        dialog = RenameDialog(window)
        dialog.run()
        dialog.destroy()

    def get_file_items(self, window, files):
        if len(files) != 1:
            return

        selected_file = files[0]

        if selected_file.get_uri_scheme() != 'file':
            # Not sure which URIs zipfile supports reading from
            return

        if selected_file.get_mime_type() in SUPPORTED_ZIP_MIME_TYPES:
            top_menuitem = Nautilus.MenuItem(name='RenameArchiveProvider::Rename Archive',
                                             label='Rename Archive',
                                             tip='Rename archive based on its directory names',
                                             icon='')

            names_menu = Nautilus.Menu()
            top_menuitem.set_submenu(names_menu)

            # create the submenu items
            filename = get_filename(selected_file)

            directory_names = get_zip_directory_names(filename)
            if not directory_names:
                no_directories_menuitem = Nautilus.MenuItem(name='RenameArchiveProvider::No Directories',
                                                            label='No directory names found',
                                                            tip='',
                                                            icon='')
                names_menu.append_item(no_directories_menuitem)
            else:
                for directory_name in directory_names:
                    dir_menuitem = Nautilus.MenuItem(name='RenameArchiveProvider::Directory::' + directory_name,
                                                     label='Rename to "' + directory_name + '"',
                                                     tip='Rename to "' + directory_name + '"',
                                                     icon='')
                    dir_menuitem.connect('activate', self.rename_directory_menuitem_cb,
                                         (selected_file, window))
                    names_menu.append_item(dir_menuitem)

            return [top_menuitem]
        else:
            return
