###########################################################
#
# Copyright (c) 2005, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['PerforceException', 'Perforce', 'PerforceRepo', 'PerforceTransaction']

import os, shutil, re

from pyasm.common import *
from pyasm.command import CommandException
from pyasm.search import Search

from pyasm.application.perforce import Perforce

from .file_checkin import *
from .repo import BaseRepo


# DEPRECATED


class PerforceException(SetupException):
    pass

class PerforceTransaction(object):

    def __init__(self):
        self.perforce = Perforce()

        self.description = "None"
        self.changelist = -1

        self.opened = []


    def get_perforce(self):
        return self.perforce


    def set_description(self, description):
        self.description = description


    # FIXME: not sure if the should be here.
    def get_sync_path(self):
        return self.perforce.get_root()
        #return Config.get_value("perforce", "sync")


    def start(self):
        pass


    def commit(self):
        return self.perforce.commit(self.description)


    def checkin(self, from_path, sub_dir):
        file_name = os.path.basename(from_path)
        repo_path = self.get_sync_path()


        # get the path to put this into the repo
        to_dir = "%s/%s" % (repo_path, sub_dir)
        System().makedirs(to_dir)

        to_path = "%s/%s" % (to_dir, file_name)


        if os.path.exists(to_path):
            self.edit_file(from_path, to_path)
        else:
            self.add_file(from_path, to_path)


    def add_opened_file(self, path):
        '''add a file that is already opened (by the perforce client)'''
        self.opened.append(path)



    def edit_file(self, from_path, to_path):
        # make sure the to_paths have no null directories
        to_path = to_path.replace("//", "/")

        # edit the file
        file_name = os.path.basename(from_path)
        repo_path = self.get_sync_path()
        self.perforce.edit(to_path)
        shutil.copy(from_path, to_path)


    def add_file(self, from_path, to_path):
        '''add a new external file to the repository
        (that is not in the sync)'''

        # make sure the to_paths have no null directories
        to_path = to_path.replace("//", "/")

        # add the file
        file_name = os.path.basename(from_path)
        repo_path = self.get_sync_path()
        shutil.copy(from_path, to_path)
        self.perforce.add_file(to_path)








class PerforceRepo(BaseRepo):
    '''Checks in files into perforce instead of copy to the sthpw repo'''

    def __init__(self, repo_code=None):
        if repo_code == None:
            repo_code = "perforce"

        repos = Container.get("PerforceRepo")
        if not repos:
            repos = {}
            Container.put("PerforceRepo", repos)
        try:
            self.repo = repos[repo_code]
        except KeyError:
            search = Search("sthpw/repo")
            search.add_filter("code", repo_code)
            self.repo = search.get_sobject()
            repos[repo_code] = self.repo



    def handle_system_commands(self, snapshot, files, file_objects):
        '''check into perforce'''
        transaction = PerforceTransaction()


        current_file_paths = snapshot.get_all_lib_paths()

        prev_snapshot = snapshot.get_previous()
        if prev_snapshot:

            prev_file_paths = prev_snapshot.get_all_lib_paths()

            # check if new files already exist in the repo
            for current_file_path in current_file_paths:
                if current_file_path not in prev_file_paths and \
                        os.path.exists(current_file_path):
                    raise CommandException("File '%s' already exists in another asset" % current_file_path)

            # delete all file not in new the snapshot
            for prev_file_path in prev_file_paths:
                if prev_file_path not in current_file_paths:
                    transaction.get_perforce().delete(prev_file_path)


        else:
            # check if new files already exist in the repo
            for current_file_path in current_file_paths:
                if os.path.exists(current_file_path):
                    raise CommandException("File '%s' already exists in another asset" % current_file_path)



        # match perforce sub_dir with tactic sub_dir for the asset
        from pyasm.biz import Project
        project = Project.get()
        naming = Project.get_dir_naming()
        base_lib_dir = naming.get_base_dir("file")[0]
        lib_dir = snapshot.get_lib_dir()


        sub_dir = lib_dir.replace(base_lib_dir, "")
        for i in range( 0, len(files) ):
            transaction.checkin( files[i], sub_dir )


        # add a description
        version = snapshot.get_value("version")
        sobject = snapshot.get_sobject()
        transaction.set_description("Checked in asset '%s', version '%s'" % \
            (sobject.get_code(),version) )

        result = transaction.commit()

        print(result)

        # get the version of the first file
        files = result.get("files")
        if not files:
            raise PerforceException("No files checked in")

        version = files[0]['version']
        print("setting snapshot to version: %s" % version)

        snapshot.set_value("version", version)
        snapshot.commit()
            






"""
class Perforce:
    '''class that abstracts out perforce commands'''
    PORT = "1666"

    def __init__(self):
        port = Config.get_value("perforce", "port")
        os.putenv("P4PORT", port )

        #exec_path = self.get_exec_path()
        #if not os.path.exists(exec_path):
        #    raise SetupException( "Executable '%s' does not exist" % exec_path )

    def get_exec_path(self):
        return Config.get_value("perforce", "p4")

    def get_repo_path(self):
        return Config.get_value("perforce", "repo")

    def get_sync_path(self):
        return Config.get_value("perforce", "sync")



    def execute(self, cmd, input=None):
        cmd = '%s %s' % (self.get_exec_path(), cmd)
        print("--> %s" % cmd)

        # use popen3
        # TODO: Simple implementation, will have problems with buffering
        # and hanging
        #stdin, stdout, stderr = os.popen3(cmd)
        #error = stderr.readlines()
        #if error:
        #    print(error)
        #else:
        #    if input != None:
        #        stdin.write(input)
        #output = stdout.readlines()
        #stdin.close()
        #stdout.close()
        #stderr.close()

        stdin, stdouterr = os.popen4(cmd)
        if input != None:
            stdin.write(input)
        stdin.close()

        output = stdouterr.readlines()
        stdouterr.close()

        # simple error handling
        if output and output[0] == "Perforce client error:\n":
            raise PerforceException( "".join(output) )

        print(output)
        return output


    def add_file(self, path):
        path = path.replace("//", "/")
        cmd = 'add "%s"' % path
        ret_val = self.execute(cmd)
        print(ret_val)


    def edit_file(self, path):
        path = path.replace("//", "/")
        cmd = 'edit "%s"' % path
        ret_val = self.execute(cmd)
        print(ret_val)

    def delete_file(self, path):
        cmd = 'delete "%s"' % path
        ret_val = self.execute(cmd)
        print(ret_val)



    def get_log(self, path):
        cmd = 'filelog "%s"' % path
        ret_val = self.execute(cmd)
        return ret_val


    def submit(self, path):
        cmd = 'submit -r "%s"' % path
        ret_val = self.execute(cmd)
        return ret_val


    def get_opened(self):
        cmd = 'opened'
        ret_val = self.execute(cmd)
        return ret_val


    def files(self, paths):
        cmd = 'files %s' % " ".join( ['"%s"' % x for x in paths] )
        ret_val = self.execute(cmd)
        return ret_val


    def have(self, paths):
        cmd = 'files %s' % " ".join( ['"%s"' % x for x in paths] )
        ret_val = self.execute(cmd)
        return ret_val
"""



