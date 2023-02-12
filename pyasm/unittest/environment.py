###########################################################
#
# Copyright (c) 2013, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['UnittestEnvironment', 'Sample3dEnvironment']

import tacticenv

from pyasm.common import TacticException
from pyasm.biz import Project
from pyasm.security import Batch
from pyasm.command import Command
from pyasm.search import SearchType, Search, DbResource, DbContainer
from tactic.command import CreateProjectCmd, PluginInstaller

class UnittestEnvironment(object):

    def __init__(self, **kwargs):
        self.project_code = kwargs.get('project_code')
        if not self.project_code:
            self.project_code = 'unittest'

    def create(self):

        project = Project.get_by_code(self.project_code)
        if project:

            self.delete()

        # create the project
        create_cmd = CreateProjectCmd(project_code=self.project_code, project_title="Unittest") #, project_type="unittest")
        create_cmd.execute()

        # install the unittest plugin
        installer = PluginInstaller(relative_dir="TACTIC/internal/unittest", verbose=False)
        installer.execute()



    def delete(self):
        related_types = ["sthpw/schema", "sthpw/task","sthpw/snapshot", "sthpw/file"]
        self.commit()
        from tactic.ui.tools import DeleteProjectCmd
        delete_cmd = DeleteProjectCmd(project_code=self.project_code, related_types=related_types)
        delete_cmd.execute()


    def commit(self):
        db_res = DbResource.get_default(self.project_code)
        sql = DbContainer.get(db_res)
        impl = sql.get_database_impl()
        if impl.commit_on_schema_change():
            DbContainer.commit_thread_sql()



class Sample3dEnvironment(UnittestEnvironment):

    def __init__(self, **kwargs):
        self.project_code = kwargs.get('project_code')
        if not self.project_code:
            self.project_code = 'sample3d'


    def create(self):

        project = Project.get_by_code(self.project_code)
        if project:
            self.delete()

        print("Setting up a basic Sample3d project")

        # create the project
        create_cmd = CreateProjectCmd(project_code=self.project_code, project_title="Sample 3D") #, project_type="unittest")
        create_cmd.execute()

        # install the unittest plugin
        installer = PluginInstaller(relative_dir="TACTIC/internal/sample3d", verbose=False)
        installer.execute()

        # add 30 shots
        for x in range(30):
            shot = SearchType.create("prod/shot")
            shot.set_value('name','shot%s'%x)
            shot.set_value('sequence_code','SEQ_01')
            shot.commit(triggers=False)

        if not Search.eval("@SOBJECT(prod/sequence['code','SEQ_01'])"):
            seq = SearchType.create("prod/sequence")
            seq.set_value('code','SEQ_01')
            seq.commit(triggers=False)


if __name__ == '__main__':
    Batch(project_code="unittest")
    
    cmd = UnittestEnvironment()
    cmd.create()

    #cmd.delete()

