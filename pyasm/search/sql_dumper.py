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

__all__ = ['TableSchemaDumper', 'TableDataDumper']

import os
import re 
import sys
import types
import datetime
import codecs
import six

from pyasm.common import TacticException, jsondumps, jsonloads, Common

from .sql import SqlException


class TableSchemaDumper(object):

    def __init__(self, search_type, delimiter=None):
        self.search_type = search_type
        self.delimiter = "#"
        self.end_delimiter = self.delimiter
        self.ignore_columns = []



    def set_delimiter(self, delimiter, end_delimiter=None):
        self.delimiter = delimiter
        if not end_delimiter:
            self.end_delimiter = self.delimiter
        else:
            self.end_delimiter = end_delimiter


    def set_ignore_columns(self, columns=[]):
        self.ignore_columns = columns



    def dump_to_tactic(self, path=None, mode='sql'):

        from pyasm.search import SearchType, Sql, DbContainer

        search_type_obj = SearchType.get(self.search_type)
        database = search_type_obj.get_database()
        table = search_type_obj.get_table()
        db_resource = SearchType.get_db_resource_by_search_type(self.search_type)
        sql = DbContainer.get(db_resource)
        exists = sql.table_exists(table)   
        if not exists:
            return

        info = sql.get_column_info(table)
        impl = sql.get_database_impl()


        columns = list(info.keys())
        columns.sort()

        # if the table does not exist, there are no columns
        if not columns:
            return

        if path:
            import os
            f = codecs.getwriter('utf8')(open(path, 'ab'))
        else:
            import sys
            f = sys.stdout

        if not self.delimiter:
            self.delimiter = "--"
            self.end_delimiter = self.delimiter


        f.write( "%s\n" % self.delimiter )

        if mode == 'sobject':
            f.write("table = CreateTable('%s')\n" % self.search_type)
        else:
            f.write("table = CreateTable()\n")
            f.write("table.set_table('%s')\n" % table)

        # Hard code this - all search types have id as the primary key at the
        # moment
        primary_key_col = 'id'

        for column in columns:

            if column in self.ignore_columns:
                continue

            col_info = info[column]
            #print(col_info)
            space = " "*(25-len(column)) 
            data_type = col_info['data_type']
            is_nullable = col_info['nullable']

            if column == "id":
                # A dump will output a database independent serial
                #data_type = impl.get_serial()   <--- Database depenedent
                data_type = 'serial'
                f.write("table.add('%s',%s'%s', primary_key=True)\n" % (column, space, data_type) )
                continue

            elif data_type in ['varchar','char','nvarchar']:
                size = col_info.get('size')
                if size == -1:
                    size = 'max'
                if not size:
                    size = 256
                if is_nullable:
                    f.write("table.add('%s',%s'%s', length='%s' )\n" % (column, space, data_type, size))
                else:
                    f.write("table.add('%s',%s'%s', length='%s', not_null=True )\n" % (column, space, data_type, size))
                continue


            if is_nullable:
                f.write("table.add('%s',%s'%s' )\n" % (column, space, data_type))
            else:
                f.write("table.add('%s',%s'%s', not_null=True )\n" % (column, space, data_type))


        # add the constraints
        constraints = impl.get_constraints(db_resource, table)
        for constraint in constraints:
            name = constraint.get("name")
            columns = constraint.get("columns")
            mode = constraint.get("mode")
            if not name:
                name = "%s_%s_idx" % (name, "_".join(columns))
            f.write('''table.add_constraint(%s, mode="%s")\n''' % (jsondumps(columns), mode))
            #def add_constraint(self, columns, mode="UNIQUE"):


        #f.write("table.set_primary_key('id')\n")

        # Disable commit for now
        #if mode == 'sobject':
        #    f.write("table.commit()\n")

        f.write( "%s\n" % self.end_delimiter )
        f.write("\n")


class TableDataDumper(object):
    '''Dumps out sql statement'''

    def __init__(self):
        self.sobjects = None
        self.delimiter = "--"
        self.end_delimiter = self.delimiter

        self.database = None
        self.table = None

        self.no_exception = False

        self.pl_sql_var_out_fp = None
        self.pl_sql_ins_out_fp = None
        self.sql_out_fp = None

        self.include_id = True
        self.search_type = None
        self.ignore_columns = []
        self.replace_dict={}
        self.skip_invalid_column = False


    def set_include_id(self, flag=True):
        self.include_id = flag

    def set_ignore_columns(self, columns=[]):
        self.ignore_columns = columns
    
    def set_skip_invalid_column(self):
        self.skip_invalid_column = True
    
    def set_replace_token(self, replace, column, regex=None):
        key = column
        value = [replace, regex]
        self.replace_dict[key] = value 
        
        
        



    def set_delimiter(self, delimiter, end_delimiter=None):
        self.delimiter = delimiter
        if not end_delimiter:
            self.end_delimiter = self.delimiter
        else:
            self.end_delimiter = end_delimiter

    def set_sobjects(self, sobjects):

        from pyasm.search import Search, SObject, Insert, SearchType

        self.sobjects = sobjects
        first = self.sobjects[0]

        # get the database
        project_code = first.get_project_code()
        from pyasm.biz import Project
        project = Project.get_by_code(project_code)
        if not project:
            raise Exception("SObject [%s] has a project_code [%s] that does not exist" % (first.get_search_key(), project_code) )

        self.db_resource = project.get_project_db_resource()

        # get the search_type
        self.search_type = first.get_base_search_type()
        self.search_type_obj = SearchType.get(self.search_type)
        self.table = self.search_type_obj.get_table()


    def set_info(self, table):
        from pyasm.biz import Project
        project = Project.get()
        self.db_resource = project.get_project_db_resource()

        self.table = table

    def set_search_type(self, search_type):
        self.search_type = search_type


    def set_no_exception(self, flag):
        self.no_exception = flag


    def execute(self):
        assert self.db_resource
        assert self.table

        database = self.db_resource.get_database()

        from pyasm.search import Insert, Select, DbContainer, Search, Sql

        # get the data
        if not self.sobjects:
            search = Search("sthpw/search_object")

            # BAD assumption
            #search.add_filter("table", self.table)
            # create a search_type. This is bad assumption cuz it assumes project-specific search_type
            # should call set_search_type()
            if not self.search_type:
                self.search_type = "%s/%s" % (self.database, self.table)
            search.add_filter("search_type", self.search_type)

            self.search_type_obj = search.get_sobject()
            if not self.search_type_obj:
                if self.no_exception == False:
                    raise SqlException("Table [%s] does not have a corresponding search_type" % self.table)
                else:
                    return

            search_type = self.search_type_obj.get_base_key()
            search = Search(self.search_type)
            search.set_show_retired(True)
            self.sobjects = search.get_sobjects()
            
        # get the info for the table
        column_info = SearchType.get_column_info(self.search_type)

        for sobject in self.sobjects:
            print(self.delimiter)

            insert = Insert()
            insert.set_database(self.database)
            insert.set_table(self.table)

            data = sobject.data
            for name, value in data.items():

                if name in self.ignore_columns:
                    continue

                if not self.include_id and name == "id":
                    insert.set_value("id", '"%s_id_seq".nextval' % table, quoted=False)
                    #insert.set_value(name, value, quoted=False)
                elif value == None:
                    continue
                else:
                    # replace all of the \ with double \\
                    insert.set_value(name, value)

            print("%s" % insert.get_statement())
            print(self.end_delimiter)
            print("\n")



    def dump_tactic_inserts(self, path, mode='sql', relative_dir_column=None):
        assert self.db_resource
        assert self.table

        database = self.db_resource.get_database()

        assert mode in ['sql', 'sobject']


        if not relative_dir_column:
            if path:
                dirname = os.path.dirname(path)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
          
                #f = open(path, 'w')
                #f = codecs.open(path, 'a', 'utf-8')
                UTF8Writer = codecs.getwriter('utf8')
                f = UTF8Writer(open(path, 'ab'))
            else:
                import sys
                f = sys.stdout

        from pyasm.search import Insert, Select, DbContainer, Search, Sql

        # get the data
        if not self.sobjects:
            search = Search("sthpw/search_object")
            search.add_filter("table_name", self.table)
            search.add_order_by("id")
            self.search_type_obj = search.get_sobject()
            if not self.search_type_obj:
                if self.no_exception == False:
                    raise Exception("Table [%s] does not have a corresponding search_type" % self.table)
                else:
                    return

            search_type = self.search_type_obj.get_base_key()
            search = Search(search_type)
            search.set_show_retired(True)
            self.sobjects = search.get_sobjects()
            
        # get the info for the table
        from pyasm.search import SearchType, Sql
        column_info = SearchType.get_column_info(self.search_type)

        for sobject in self.sobjects:

            if relative_dir_column:

                if path:
                    #dirname = os.path.dirname(path)
                    subpath = "%s/%s.spt" % (path, str(sobject.get_value(relative_dir_column)).replace(".","/"))

                    if not os.path.exists(os.path.dirname(subpath)):
                        os.makedirs(os.path.dirname(subpath))
                    
                    UTF8Writer = codecs.getwriter('utf8')
                    f = UTF8Writer(open(subpath, 'ab'))
                else:
                    import sys
                    f = sys.stdout


            f.write( "%s\n" % self.delimiter )


            if mode == 'sobject':
                search_type = sobject.get_base_search_type()
                f.write("insert = SearchType.create('%s')\n" % search_type)
                if self.skip_invalid_column:
                    f.write("insert.skip_invalid_column()\n")
            else:
                f.write("insert.set_table('%s')\n" % self.table)

            data = sobject.get_data()
            data_keys = list(data.keys())
            data_keys.sort()

            #for name, value in data.items():
            for name in data_keys:
                value = data.get(name)
                
                if self.replace_dict:
                    
                    for column,replace_args in self.replace_dict.items():
                        if name == column:
                            replace_str = replace_args[0]
                            regex = replace_args[1]
                            
                            if regex:
                                #if not re.match(regex,value):
                                #    raise TacticException("%s does not conform to standard format. Expected format must match %s"%(column,regex))
                                value = re.sub(regex,replace_str,value)
                            else:
                                value = replace_str

    
                        


                if name in self.ignore_columns:
                    continue

                if name == '_tmp_spt_rownum':
                    continue
                if not self.include_id and name == "id":
                    #insert.set_value("id", '"%s_id_seq".nextval' % table, quoted=False)
                    pass
                elif value == None:
                    continue
                else:
                    # This is not strong enough
                    #if value.startswith("{") and value.endswith("}"):
                    #    f.write("insert.set_expr_value('%s', \"\"\"%s\"\"\")\n" % (name, value))
                    if isinstance(value, (int, float, bool)):
                        f.write("insert.set_value('%s', %s)\n" % (name, value))

                    elif not Common.IS_Pv3 and type(value) == types.LongType:
                        f.write("insert.set_value('%s', %s)\n" % (name, value))
                    else:

                        # if this is dictionary, then convert to string
                        if isinstance(value, list) or isinstance(value, dict):
                            value = jsondumps(value)

                        # if the value contains triple double quotes, convert to
                        # triple quotes
                        if isinstance(value, datetime.datetime):
                            value = str(value)
                        elif not Common.IS_Pv3 and isinstance(value, unicode):
                            value = value.encode("UTF-8")

                        # this fixes a problem with non-ascii characters
                        if isinstance(value, six.string_types):
                            quoted = value.startswith('"') and value.endswith('"')
                            value = repr(value)
                            quoted2 = value.startswith('"') and value.endswith('"')
                            if not quoted and quoted2:
                                value = value.strip('"')


                            # repr puts single quotes at the start and end
                            if value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # and it puts a slash in front
                            value = value.replace(r"\'", "'")
                            # replace literal \n with newline (comes from repr)
                            value = value.replace(r"\n", "\n")


                            value = value.replace('"""', "'''")
                            #value = value.replace("\\", "\\\\")

                            # handle the case where the value starts with a quote
                            if value.startswith('"'):
                                value = '\\%s' % value
                            # handle the case where the value ends starts with a quote
                            if value.endswith('"'):
                                value = '%s\\"' % value[:-1]


                        f.write("insert.set_value('%s', \"\"\"%s\"\"\")\n" % (name, value))


            # Disable commit for now
            #if mode == 'sobject':
            #    f.write("insert.commit()\n")

            f.write( "%s\n" % self.end_delimiter )
            f.write( "\n" )


            if relative_dir_column:
                f.close()

        if not relative_dir_column and path:
            f.close()


    def set_sql_out_fps(self, sql_out_fp, pl_sql_var_out_fp, pl_sql_ins_out_fp):
        self.sql_out_fp = sql_out_fp
        self.pl_sql_var_out_fp = pl_sql_var_out_fp
        self.pl_sql_ins_out_fp = pl_sql_ins_out_fp


    # DEPRECATED
    # FIXME: why is there SQLServer code in an Oracle function
    def execute_mms_oracle_dump(self):
        assert self.db_resource
        assert self.table

        database = self.db_resource.get_database()

        if not self.sql_out_fp or not self.pl_sql_var_out_fp or not self.pl_sql_ins_out_fp:
            raise Exception("SQL and PL-SQL file pointers are required for generating output.")

        from pyasm.search import Insert, Select, DbContainer, Search, Sql

        # get the data
        if not self.sobjects:
            search = Search("sthpw/search_object")
            search.add_filter("table_name", self.table)
            self.search_type_obj = search.get_sobject()
            if not self.search_type_obj:
                if self.no_exception == False:
                    raise Exception("Table [%s] does not have a corresponding search_type" % self.table)
                else:
                    return

            search_type = self.search_type_obj.get_base_key()
            search = Search(search_type)
            search.set_show_retired(True)
            self.sobjects = search.get_sobjects()

        # get the info for the table
        column_info = self.search_type_obj.get_column_info()

        for sobject in self.sobjects:

            column_list = []
            value_list = []
            update_col_list = []
            update_map = {}

            timestamp_regex = re.compile("^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})")

            data = sobject.data
            sobject_id = data.get("id")
            do_pl_sql = False
            for name, value in data.items():
                if value == None:
                    continue
                else:
                    col_name = '"%s"' % name
                    column_list.append(col_name)

                    if isinstance(value, types.StringTypes):
                        if timestamp_regex.match(value):
                            value_list.append( "TO_TIMESTAMP('%s','RR-MM-DD HH24:MI:SS')" %
                                    str(value).split('.')[0][2:] )
                        else:
                            new_value = self.get_oracle_friendly_string_value( value )
                            if len(new_value) > 3800:
                            #{
                                do_pl_sql = True
                                var_name = "%s_%s_%s__var" % \
                                                ( self.table, col_name.replace('"',''), str(sobject_id).zfill(5) )

                                self.pl_sql_var_out_fp.write( "\n%s VARCHAR2(%s) := %s ;\n" %
                                                                (var_name, len(new_value), new_value) )
                                new_value = var_name
                            #}
                            value_list.append( new_value )


                    # elif type(value) == datetime.datetime:
                    #     value_list.append( "TO_TIMESTAMP('%s','RR-MM-DD HH24:MI:SS.FF')" %
                    #             str(value).split('.')[0][2:] )
                    else:
                        value_list.append( "%s" % value )

            if do_pl_sql:
                self.pl_sql_ins_out_fp.write( '\n' )
                from sql import Sql
                if database_type == "SQLServer":
                    self.pl_sql_ins_out_fp.write( 'INSERT INTO "%s" (%s) VALUES (%s);\n' %
                                        (self.database, self.table, ','.join(column_list), ','.join(value_list)) )
                else:
                    self.pl_sql_ins_out_fp.write( 'INSERT INTO "%s" (%s) VALUES (%s);\n' %
                                        (self.table, ','.join(column_list), ','.join(value_list)) )
            else:
                self.sql_out_fp.write( '\n' )
                from sql import Sql
                if database_type == "SQLServer":
                    self.sql_out_fp.write( 'INSERT INTO "%s" (%s) VALUES (%s);\n' %
                                        (self.database, self.table, ','.join(column_list), ','.join(value_list)) )
                else:
                    self.sql_out_fp.write( 'INSERT INTO "%s" (%s) VALUES (%s);\n' %
                                        (self.table, ','.join(column_list), ','.join(value_list)) )



    def get_oracle_friendly_string_value( self, str_value ):
        return "'%s'" % str_value.replace("'","''").replace('&',"&'||'")



