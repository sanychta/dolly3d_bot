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

__all__ = ["StatusLog"]

from pyasm.common import Environment, Date
from pyasm.search import SearchType, SObject, Search

from .pipeline import Pipeline
from .project import Project

class StatusLog(SObject):

    SEARCH_TYPE = "sthpw/status_log"

    def create(sobject, value, prev_value=None):
        if prev_value == value:
            return

        # if this is successful, the store it in the status_log
        #search_type = sobject.get_search_type()
        #search_id = sobject.get_id()
        #search_code = sobject.get_value("code")

        status_log = SearchType.create("sthpw/status_log")
        status_log.set_value("login", Environment.get_user_name() )

        status_log.set_sobject_value(sobject)
        #status_log.set_value("search_type", search_type)
        #status_log.set_value("search_code", search_id, no_exception=True)
        #status_log.set_value("search_id", search_code, no_exception=True)

        if prev_value:
            status_log.set_value("from_status", prev_value)

        status_log.set_value("to_status", value)

        project_code = Project.get_project_name()
        status_log.set_value("project_code", project_code)

        status_log.commit(cache=False)

        return status_log

    create = staticmethod(create)


