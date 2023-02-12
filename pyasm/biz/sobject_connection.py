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

__all__ = ["SObjectConnection"]

from pyasm.common import Environment, Container, Common
from pyasm.search import SearchType, SObject, Search

from .project import Project

class SObjectConnection(SObject):

    SEARCH_TYPE = "sthpw/connection"


    def get_sobject(self, direction="dst"):
        assert direction in ['src', 'dst']

        search_type = self.get_value("%s_search_type" % direction)
        search_id = self.get_value("%s_search_id" % direction)

        sobject = Search.get_by_id(search_type, search_id)
        return sobject


    # Static methods
    def get_connections(cls, sobjects, direction="dst", context='', context_filters=[], src_search=None):
        '''return a Search instance if src_search is provided'''
        if not sobjects and not src_search:
            return []
        search = Search(SObjectConnection)

        if direction == "dst":
            prefix = "src"
        else:
            prefix = "dst"
        
        if src_search:
            search.add_filter("%s_search_type" % prefix, src_search.get_search_type() )
            search.add_search_filter('%s_search_id'%prefix, src_search, op="in") 
        else:
            search_types = [x.get_search_type() for x in sobjects]
            search_ids = [x.get_id() for x in sobjects]

            if len(Common.get_unique_list(search_types)) == 1:
                search.add_filter("%s_search_type" % prefix, search_types[0] )
                search.add_filters("%s_search_id" % prefix, search_ids)
            else:
                search.add_op("begin")
                for search_type, search_id in zip(search_types, search_ids):
                    search.add_op("begin")
                    search.add_filter("%s_search_type" % prefix, search_type )
                    search.add_filter("%s_search_id" % prefix, search_id )
                    search.add_op("and")
                search.add_op("or")

        if context:
            search.add_filter("context", context)
        elif context_filters:
            search.add_op_filters(context_filters)

        if src_search:
            return search

		# cache for connection sobjects
        key = search.get_statement()
        cache = Container.get("SObjectConnection:cache")
        if cache == None:
            cache = {}
            Container.put("SObjectConnection:cache", cache)

        ret_val = cache.get(key)
        if ret_val != None:
            return ret_val

        
        connections = search.get_sobjects()
        
        return connections
        
    get_connections = classmethod(get_connections)



    def get_sobjects(self, connections, direction='dst', filters=None, return_search=False):

        if not connections:
            return []

        if direction == "dst":
            prefix = "dst"
        else:
            prefix = "src"

        search_type = connections[0].get_value("%s_search_type" % prefix)

        search = Search(search_type)
        search_ids = [x.get_value("%s_search_id" % prefix) for x in connections]
        search.add_filters("id", search_ids )

        if filters:
            search.add_op_filters(filters)

        if return_search:
            return search

        sobjects = search.get_sobjects()

        return sobjects

    get_sobjects = classmethod(get_sobjects)


    def get_search(self, connections, direction='dst', filters=None):
 
        search = self.get_sobjects(connections, direction=direction, filters=filters, return_search=True)
        return search

    get_search = classmethod(get_search)


    def get_connected_sobjects(cls, sobjects, direction="dst", order_by=None, context='', filters=None):
        '''get the sobjects that are connect to this sobject.'''
        unique_stype = False
        single_sobject = False
        src_search_types = []
        src_search_ids = []
        if not sobjects:
            return [], []
        if isinstance(sobjects, list):
            search_types = [x.get_search_type() for x in sobjects]
            search_ids = [x.get_id() for x in sobjects]
            if len(Common.get_unique_list(search_types)) == 1:
                unique_stype = True
              
 
        else:
            search_types = [sobjects.get_search_type()]
            search_ids = [sobjects.get_id()]
            unique_stype = True
            single_sobject = True


        if direction == "dst":
            prefixA = "dst"
            prefixB = "src"
        else:
            prefixA = "src"
            prefixB = "dst"

        connections = []
        if unique_stype:
            search = Search(SObjectConnection)
            search.add_filter("%s_search_type" % prefixA, search_types[0] )
            search.add_filters("%s_search_id" % prefixA, search_ids )

            if context:
                search.add_filter("context", context)

            if order_by:
                search.add_order_by(order_by)


            key = search.get_statement()
            cache = Container.get("SObjectConnection:cache")
            if cache == None:
                cache = {}
                Container.put("SObjectConnection:cache", cache)
            ret_val = cache.get(key)
            if ret_val != None:
                return ret_val
            


            connections = search.get_sobjects()

            """
            new_search = Search(src_search_types[0])
            select = new_search.get_select()
            from_table = new_search.get_table()
            to_table = 'connection'
            from_col = 'id'
            to_col = 'src_search_id'
            select.add_join(from_table, to_table, from_col, to_col, join='INNER', database2='sthpw')
            """


        else:
            raise TacticException('Only unique stypes are supported for the passed in sobjects')

        src_sobjects = []
         
        src_stype = None
        src_stypes = SObject.get_values(connections, "%s_search_type" % prefixB, unique=True)
        src_ids = SObject.get_values(connections, "%s_search_id" % prefixB, unique=True)
        if len(src_stypes) == 1:
            src_stype = src_stypes[0]
           
        if src_stype:
            single_src_ids = len(src_ids) == 1
            if not filters and single_src_ids:

                src = Search.get_by_id(src_stype, src_ids[0])
                src_sobjects.append(src)
            else:
                new_search = Search(src_stype)
                if single_src_ids:
                    new_search.add_filter('id', src_ids[0])
                else:
                    new_search.add_filters('id', src_ids)
                if filters:
                    new_search.add_op_filters(filters)
                src_sobjects = new_search.get_sobjects()

        else:
            for connection in connections:
                src_search_type = connection.get_value("%s_search_type" % prefixB)
                src_search_id = connection.get_value("%s_search_id" % prefixB)

                # TODO: this could be made faster because often, these will be
                # of the same stype
                if not filters:
                    src = Search.get_by_id(src_search_type, src_search_id)
                else:
                    src_search = Search(src_search_type)
                    src_search.add_filter("id", src_search_id)
                    src_search.add_op_filters(filters)
                    src = src_search.get_sobject()

                #if not src.is_retired():
                # don't check for retired here. check it at the caller for
                # css manipulation
                if src:
                    src_sobjects.append(src)
                else:
                    print("WARNING: connection sobject does not exist .. deleting")
                    connection.delete()

        cache[key] = connections, src_sobjects
        return connections, src_sobjects

        
    get_connected_sobjects = classmethod(get_connected_sobjects)    



    def get_connected_sobject(cls, sobject, direction="dst", order_by=None, context='', filters=None):
        connections, sobjects = cls.get_connected_sobjects(sobject, direction=direction, order_by=order_by, context=context, filters=filters)
        if not sobjects:
            return None
        else:
            return sobjects[0]
    get_connected_sobject = classmethod(get_connected_sobject)    


    def create(src_sobject, dst_sobject, context="reference", direction="both"):

        project_code = Project.get_project_code()

        if not context:
            context = "reference"

        # ensure that the connection doesn't already exist
        search = Search("sthpw/connection")
        search.add_sobject_filter(src_sobject, prefix="src_")
        search.add_sobject_filter(dst_sobject, prefix="dst_")
        if search.get_count():
            Environment.add_warning("Already connected", "%s is already connected to %s" % (src_sobject.get_code(), dst_sobject.get_code() ) )
            return


        connection = SearchType.create("sthpw/connection")
        connection.set_value("src_search_type", src_sobject.get_search_type() )
        connection.set_value("dst_search_type", dst_sobject.get_search_type() )
        connection.set_value("src_search_id", src_sobject.get_id() )
        connection.set_value("dst_search_id", dst_sobject.get_id() )
        connection.set_value("context", context)
        connection.set_value("project_code", project_code)
        connection.commit()

        if direction == "both":
            connection = SearchType.create("sthpw/connection")
            connection.set_value("src_search_type", dst_sobject.get_search_type() )
            connection.set_value("dst_search_type", src_sobject.get_search_type() )
            connection.set_value("src_search_id", dst_sobject.get_id() )
            connection.set_value("dst_search_id", src_sobject.get_id() )
            connection.set_value("context", context)
            connection.set_value("project_code", project_code)
            connection.commit()


        return connection


    create = staticmethod(create)    


