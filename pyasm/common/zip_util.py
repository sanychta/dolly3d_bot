###########################################################
#
# Copyright (c) 2011, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['ZipUtil']

import zipfile, os, codecs, datetime

class ZipUtil(object):

    def zip_dir(cls, dir, zip_path=None, ignore_dirs=[], include_dirs=[]):

        if not zip_path:
            zip_path = "./%s.zip" % os.path.basename(dir)

        print("zip_path: ", zip_path)
        if os.path.exists(zip_path):
            os.unlink(zip_path)

        # check if the folder exists
        dirname = os.path.dirname(zip_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)


        f = codecs.open(zip_path, 'wb')
        zip = zipfile.ZipFile(f, 'w', compression=zipfile.ZIP_DEFLATED)
        # Probably not, this may work better in windows without compression
        #zip = zipfile.ZipFile(f, 'w', compression=zipfile.ZIP_STORED)

        try:
            count = 0
            for root, dirs, files in os.walk(dir):

                for ignore_dir in ignore_dirs:
                    if ignore_dir in dirs:
                        dirs.remove(ignore_dir)

                if root == dir and include_dirs:
                    del dirs[:]
                    dirs.extend(include_dirs)
                    continue


                for file in files:
                    path = "%s/%s" % (root, file)
                    relpath = path.replace("%s/" % os.path.dirname(dir), "")
                    #relpath = "%s/%s" % (os.path.basename(root), file)
                    if os.path.islink(path):
                        zip_info = zipfile.ZipInfo(root)
                        zip_info.create_system = 3
                        try:
                            zip_info.external_attr = long(271663808)
                        except:
                            zip_info.external_attr = 271663808

                        zip_info.filename = relpath
                        zip.writestr(zip_info, os.readlink(path) )
                    else:
                        zip.write(path, relpath)

                    count += 1
        finally:
            zip.close()

        if not count and os.path.exists(zip_path):
            os.unlink(zip_path)

    zip_dir = classmethod(zip_dir)


    # take from: https://gist.github.com/610907
    def zip_dir2(cls, dir, zip_path=None):
        '''Zip up a directory and preserve symlinks and empty directories'''

        if not os.path.exists(dir):
            return

        if not zip_path:
            zip_path = "./%s.zip" % os.path.basename(dir)

        if os.path.exists(zip_path):
            os.unlink(zip_path)


        inputDir = dir
        outputZip = zip_path


        zipOut = zipfile.ZipFile(outputZip, 'w', compression=zipfile.ZIP_DEFLATED)
        
        rootLen = len(os.path.dirname(inputDir))
        def _ArchiveDirectory(parentDirectory):
            contents = os.listdir(parentDirectory)
            #store empty directories
            if not contents:
                #http://www.velocityreviews.com/forums/t318840-add-empty-directory-using-zipfile.html
                archiveRoot = parentDirectory[rootLen:].replace('\\', '/').lstrip('/')
                zipInfo = zipfile.ZipInfo(archiveRoot+'/')
                zipOut.writestr(zipInfo, '')
            for item in contents:
                fullPath = os.path.join(parentDirectory, item)
                if os.path.isdir(fullPath) and not os.path.islink(fullPath):
                    _ArchiveDirectory(fullPath)
                else:
                    archiveRoot = fullPath[rootLen:].replace('\\', '/').lstrip('/')
                    if os.path.islink(fullPath):
                        # http://www.mail-archive.com/python-list@python.org/msg34223.html
                        zipInfo = zipfile.ZipInfo(archiveRoot)
                        zipInfo.create_system = 3
                        # long type of hex val of '0xA1ED0000L',
                        # say, symlink attr magic...
                        try:
                            zip_info.external_attr = long(271663808)
                        except:
                            zip_info.external_attr = 271663808

                        zipOut.writestr(zipInfo, os.readlink(fullPath))
                    else:
                        zipOut.write(fullPath, archiveRoot, zipfile.ZIP_DEFLATED)
        _ArchiveDirectory(inputDir)
        
        zipOut.close()

        return zip_path

    zip_dir2 = classmethod(zip_dir2)


    def extract(cls, zip_path, base_dir=None):

        # first check if this is a zip file
        if not os.path.exists(zip_path):
            raise Exception("Path [%s] does not exist" % zip_path)

        is_zip = zipfile.is_zipfile(zip_path)
        if not is_zip:
            raise Exception("Path [%s] is not a zip file" % zip_path)

        # TODO: make sure all paths are relative

        if not base_dir:
            base_dir = os.path.dirname(zip_path)



        paths = []


        f = codecs.open(zip_path, 'rb')
        zf = zipfile.ZipFile(f, 'r')

        if hasattr(zf, 'extractall'):
            try:
                zf.extractall(path=base_dir)
            except Exception as e:
                print("WARNING extracting zip: ", e)
            return paths            # This does not fill in the paths

        name_list = zf.namelist()

        for file_path in name_list:

            try:
                data = zf.read(file_path)
            except KeyError:
                print('ERROR: Did not find %s in zip file' % filename)
            else:
                new_path = "%s/%s" % (base_dir, file_path)
                new_dir = os.path.dirname(new_path)
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)

                nf = codecs.open(new_path, 'wb')
                nf.write(data)
                nf.close()

                paths.append(new_path)

        return paths

    extract = classmethod(extract)


    def get_file_paths(cls, path):
        paths = []
        zf = zipfile.ZipFile(path)
        for info in zf.infolist():
            paths.append( info.filename )

        return paths
    get_file_paths = classmethod(get_file_paths)


    def print_info(cls, path):
        zf = zipfile.ZipFile(path)
        for info in zf.infolist():
            print(info.filename)
        print('\tComment:\t', info.comment)
        print('\tModified:\t', datetime.datetime(*info.date_time))
        print('\tSystem:\t\t', info.create_system, '(0 = Windows, 3 = Unix)')
        print('\tZIP version:\t', info.create_version)
        print('\tCompressed:\t', info.compress_size, 'bytes')
        print('\tUncompressed:\t', info.file_size, 'bytes')
        print('\n')
    print_info = classmethod(print_info)



if __name__ == '__main__':
    zip = ZipUtil()
    zip.zip_dir("C:/test/mp3", "C:/test/mp3.zip")
    zip.extract("C:/test/mp3.zip", base_dir = "C:/test/output")
    """
    zip.zip_dir("zip_this", "/home/apache/test/cow.zip")
    zip.print_info("/home/apache/test/cow.zip")

    zip.extract("/home/apache/test/cow.zip", "/home/apache/test2")
    """
