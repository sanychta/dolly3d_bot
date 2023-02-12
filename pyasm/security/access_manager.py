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

__all__ = ['AccessManager', 'Sudo']

import types

from pyasm.common import Base, Xml, Environment, Common, Container
from pyasm.search import Search, SearchType

import six
basestring = six.string_types


class AccessException(Exception):
    pass




class Sudo(object):

    def __init__(self):
        count = Container.increment("Sudo::is_sudo")
        if count <= 0:
            raise Exception("count of sudo: ", count)

        self.security = Environment.get_security()

        # if not already logged in, login as a safe user (guest)
        if not self.security.is_logged_in():
            #self.security.login_as_guest()
            pass

        self.access_manager = self.security.get_access_manager()
        login = Environment.get_user_name()
        self.was_admin = self.access_manager.was_admin
        if self.was_admin == None:
            self.access_manager.set_up()
            self.was_admin = self.access_manager.was_admin
     
        self.access_manager.set_admin(True)

        self.already_exited = False



    def is_sudo():
        count = Container.get("Sudo::is_sudo") or 0
        is_sudo = count > 0
        if not is_sudo:
            return False
        else:
            return True
    is_sudo = staticmethod(is_sudo)
            

    def __del__(self):
        return self.exit()


    def exit(self):
        if self.already_exited == True:
            return
        self.already_exited = True

        count = Container.decrement("Sudo::is_sudo")
        if count < 0:
            raise Exception("count of sudo: ", count)

        # remove if I m not in admin group
        if self.was_admin == False:
            self.access_manager.set_admin(False)





class AccessManager(Base):

    def __init__(self):
        self.is_admin_flag = False
        self.groups = {}
        self.summary = {}
        self.project_codes = None
        
        self.was_admin = None 



    def get_access_summary(self):
        return self.summary


    def set_up(self):
        if self.was_admin == None:
            security = Environment.get_security()

            if security._login and not security._is_logged_in:
                security._groups = []
                security._group_names = []
                security._find_all_login_groups()
            self.was_admin = security.is_in_group('admin')


    def set_admin(self, flag, sudo=False):
        self.set_up()
        security = Environment.get_security()

        if security.get_user_name() == "admin":
            self.is_admin_flag = True
            return


        self.is_admin_flag = flag

        """
        if flag == False:
            import traceback, sys
            # print the stacktrace
            tb = sys.exc_info()[2]
            stacktrace = traceback.format_tb(tb)
            stacktrace_str = "".join(stacktrace)
            print("-"*50)
            print("TRACE: ", self.was_admin)
            print(stacktrace_str)
            print("-"*50)
        """


        if not self.was_admin and flag:
            if 'admin' not in security.get_group_names():
                security._group_names.append('admin')
        elif 'admin' in security.get_group_names():
            if not self.was_admin:
                security._group_names.remove('admin')
                




    def is_admin(self):
        return self.is_admin_flag


    # access level definitions
    (DENY, VIEW, EDIT, INSERT, RETIRE, DELETE) = range(6)

    def _get_access_enum(self, access_level_attr):
        '''converts text access levels to their corresponding enum'''
        if access_level_attr == "false":
            access_level = AccessManager.DENY
        elif access_level_attr == "true":
            access_level = AccessManager.VIEW

        elif access_level_attr == "deny":
            access_level = AccessManager.DENY
        elif access_level_attr == "view":
            access_level = AccessManager.VIEW
        elif access_level_attr == "edit":
            access_level = AccessManager.EDIT
        elif access_level_attr == "insert":
            access_level = AccessManager.INSERT
        elif access_level_attr == "retire":
            access_level = AccessManager.RETIRE
        elif access_level_attr == "delete":
            access_level = AccessManager.DELETE

        # allow is the highest and you can do anything
        elif access_level_attr == "allow":
            access_level = AccessManager.DELETE

        elif access_level_attr == None:
            access_level = None

        else:
            raise Exception("[%s] is not a valid access_level_attr" %access_level_attr)

        return access_level




    def add_xml_rules(self, xml, project_code=None):
        '''xml should be an XML object with the data in the form of
        <rules>
          <group type='sobject' default='<default>'>
            <rule key='<key>' access='<access>'/>
          </group>
        </rules>
        '''

        from pyasm.search import SObject
        if isinstance(xml, SObject):
            sobject = xml
            xml = sobject.get_xml_value("access_rules")
            if not project_code:
                project_code = sobject.get_value("project_code")

        project_override = project_code
        if isinstance(xml, basestring):
            xmlx = Xml()
            xmlx.read_string(xml)
            xml = xmlx


        # parse shorthand rules
        rule_nodes = xml.get_nodes("rules/rule")
        if not rule_nodes:
            return

        # store all of the project codes (this will only run once)
        if self.project_codes == None:
            search = Search('sthpw/project')
            projects = search.get_sobjects()
            self.project_codes = [x.get_code() for x in projects]
            self.project_codes.append('*')

        for rule_node in rule_nodes:
            # initiate the project_code here for each loop
            project_code = '*'
            group_type = Xml.get_attribute( rule_node, "group" )
            if not group_type:
                # category is the preferred name over group now
                # TODO: phase out the use of group completely
                group_type = Xml.get_attribute( rule_node, "category" )

            # get an existing rule set or create a new one
            if group_type in self.groups:
                rules = self.groups[group_type]
            else:
                rules = {}
                self.groups[group_type] = rules

            # set the default, if specified
            group_default = xml.get_attribute( rule_node, "default" )
            if group_default:
                rules['__DEFAULT__'] = group_default
                continue


            # generate the rule key
            #rule_key = xml.get_attribute(rule_node, 'key')
            attrs = xml.get_attributes(rule_node)
            attrs2 = {}
            count = 0
            for name, value in attrs.items():
                if name in ['access', 'group', 'category', 'project']:
                    continue
                # have to turn everything into strings
                attrs2[str(name)] = str(value)
                count += 1


            if count == 1 and 'key' in attrs2:
                # backwards compatibility
                rule_key = attrs2['key']
            else:
                #rule_key = str(attrs2)
                rule_key = str(Common.get_dict_list(attrs2))

            if project_override:
                rule_project = project_override
            else:
                rule_project =  xml.get_attribute(rule_node, 'project')

            if rule_project:
                project_code = rule_project
                # special treatment for search_filter to enable
                # project-specific search
                if group_type=='search_filter':
                    attrs2['project'] = rule_project
            
            # if there is a value, then combine it with the key
            rule_value = xml.get_attribute(rule_node, 'value')
            if rule_value:
                rule_key = "%s||%s" % (rule_key, rule_value)

            # add a project code qualifier
            rule_keys = []
         
            # project rule is special
            if group_type == 'project':
                key = str(rule_key)
                rule_keys.append(key)
            elif project_code == '*' and group_type != 'search_filter':
                for code in self.project_codes:
                    key = "%s?project=%s" % (rule_key, code)
                    rule_keys.append(key)
            else:
                key= "%s?project=%s" % (rule_key, project_code)

                #key = str(key) # may need to stringify unicode string
                rule_keys.append(key)
                    
                #key= "%s?project=*" % (rule_key)
                #rule_keys.append(key)

            rule_access = xml.get_attribute(rule_node, 'access')

            #if rule_access == "":
            #    raise AccessException("Cannot have empty 'access':\n%s" \
            #        % xml.to_string(rule_node) )

            # if no key is specified, it is considered a DEFAULT
            if not rule_keys and not rule_value:
                rule_keys = ['__DEFAULT__']
            for rule_key in rule_keys:
                # check if rule_access exists first, which doesn't for search_filter,
                # but it has to go into the rules regardless
                # if the rule already exists, take the highest one
                if rule_access and rule_key in rules:
                    curr_access, cur_attrs = rules[rule_key]

                    try:
                        access_enum = self._get_access_enum(rule_access)
                        if self._get_access_enum(curr_access) > access_enum:
                            continue
                    except:
                        if group_type == "builtin":
                            continue
                        else:
                            raise


                rules[rule_key] = rule_access, attrs2
            

        # FIXME: this one doesn't support the multi-attr structure
        # convert this to a python data structure
        group_nodes = xml.get_nodes("rules/group")
        for group_node in group_nodes:

            group_type = Xml.get_attribute( group_node, "type" )

            # get an existing rule set or create a new one
            if group_type in self.groups:
                rules = self.groups[group_type]
            else:
                rules = {}
                self.groups[group_type] = rules

            # set the default, if specified
            group_default = xml.get_attribute( group_node, "default" )
            if group_default != "":
                rules['__DEFAULT__'] = group_default


            # get all of the rule nodes
            rule_nodes = Xml.get_children(group_node)
            for rule_node in rule_nodes:
                project_code='*'

                if Xml.get_node_name(rule_node) != 'rule':
                    continue

                rule_key = xml.get_attribute(rule_node, 'key')
                rule_access = xml.get_attribute(rule_node, 'access')

                if project_override:
                    rule_project = project_override
                else:
                    rule_project =  xml.get_attribute(rule_node, 'project')

                if rule_project:
                    project_code = rule_project
                if rule_access == "":
                    raise AccessException("Cannot have empty 'access':\n%s" \
                        % xml.to_string(rule_node) )

                rule_keys = []
                attrs2 = {'key': rule_key}

                # add a project code qualifier
                if project_code == '*' and group_type != 'search_filter':
                    for code in self.project_codes:
                        key = "%s?project=%s" % (rule_key, code)
                        rule_keys.append(key)
                else:
                    key= "%s?project=%s" % (rule_key, project_code)
                    rule_keys.append(key)

                for rule_key in rule_keys:
                    rules[rule_key] = rule_access, attrs2


    def get_access(self, group, key, default=None):

        # if a list of keys is provided, then go through each key
        if isinstance(key, list):
            for item in key:
                user_access = self.get_access(group, item)
                if user_access != None:
                    return user_access

            return None


        # qualify the key with a project_code 
        project_code = "*"
        rule_project = None
        
        
        if isinstance(key, dict):
            # this avoids get_access() behavior changes on calling it twice
            key2 = key.copy()
            rule_project = key.get('project')
            if rule_project:
                project_code = rule_project
                key2.pop('project')
            
            # backward compatibility with the key attribute
            if len(key2) == 1 and list(key2.keys()) == ['key']:
                key = key2['key']
            else:
                key = Common.get_dict_list(key2)
       
        if group == 'project':
            key = str(key)
        else:
            key = "%s?project=%s" % (key, project_code)
        
        # Fix added below to remove any unicode string markers from 'key' string ... sometimes the values
        # of the 'key' dictionary that is passed in contains values that are unicode strings, and sometimes
        # values that are ascii.
        #
        # FIXME: however might not necessarily be the best fix here, so this should be re-assessed at
        #        some point to see if a better fix can be put in place

        # boris: Since we took out str() in Common.get_dict_list(), we have to re-introduce this back, but with , instead of : since it's a tuple 
        key = key.replace("', u'", "', '")
      
        # if there are no rules, just return the default

        rules = self.groups.get(group)
       

        if not rules:
            return default



        result = None
        value = rules.get(key)
        
        if value:
            result, dct = value
    
        # if default is explicitly turned off by caller, don't use __DEFAULT__
        if not result and default != None:
            result = rules.get('__DEFAULT__')

        if not result:
            result = default
        return result


    def compare_access(self, user_access, required_access):
        required_access = self._get_access_enum(required_access)
        user_access = self._get_access_enum(user_access)

        if user_access >= required_access:
            return True
        else:
            return False




    def check_access(self, group, key, required_access, value=None, is_match=False, default="edit"):
        '''Check the access level of the user for a given group of rule and category key
            group - rule category like built-in or element
            key - string or list of dictiorary like view_side_bar or ['search_type':'sthpw/task', 'project','main']
            required_access - speific access level like allow, deny, edit, view, delete'''

        if self.is_admin() or Sudo.is_sudo():
            return True

        if Sudo.is_sudo():
            return True


        if isinstance(key, basestring):
            from pyasm.biz import Project
            # order of keys shouldn't matter
            if group == 'project':
                key = [{'code': key}, {'code': '*'}]
            else:
                key = [{'key': key, 'project': Project.get_project_code()}, {'key': key, 'project': '*'}]
            #key = [ {'key': key, 'project': '*'}, {'key': key, 'project': Project.get_project_code()}]
        
        # if a list of keys is provided, then go through each key
        if isinstance(key, list):
            # use default only on the last item in list
            for idx, item in enumerate(key):
                use_default = idx == len(key) - 1
                if use_default:
                    rule_default = default
                else:
                    rule_default = None
                user_access = self.get_access(group, item, default=rule_default)
               
                if user_access != None:
                    break
        else:
            if value:
                key = "%s||%s" % (key, value)
                
            user_access = self.get_access(group, key)


        # this means that there are now rules defined for this
        if user_access == None:
            user_access = default

        # ignore value checks in the summary (way too many)
        if not value:
            if not isinstance(key, basestring):
                key = str(key)
            self.summary[key] = "%s | %s" % (required_access, user_access)

        # convert access to integers
        required_access = self._get_access_enum(required_access)
        user_access = self._get_access_enum(user_access)


        
        if is_match:
            if user_access == required_access:
                return True
            else:
                return False

        if user_access >= required_access:
            return True
        else:
            return False



    def alter_search(self, search):
        if self.is_admin_flag:
            return True

        group = "search_filter"
        search_type = search.get_base_search_type()

        self.alter_search_type_search(search)
        rules = self.groups.get(group)
        if not rules:
            return


        from pyasm.biz import ExpressionParser
        parser = ExpressionParser()
        current_project = None


        # preprocess to get a list of rule that will apply
        rules_dict = {}
        for rule_item in rules.values():
            access, dct = rule_item

            rule = dct
            rule_search_type = rule.get('search_type')
            if not rule_search_type:
                print("No [search_type] defined in security rule")
                continue

            # search types must match
            if rule_search_type != search_type:
                continue

            project = rule.get('project')
           
            # to avoid infinite recursion, get the project here
            if not current_project:
                from pyasm.biz import Project
                current_project = Project.get_project_code()
            
            if project and project not in ['*', current_project]:
                continue


            column = rule.get('column')
            rules_list = rules_dict.get(column)
            if rules_list == None:
                rules_list = []
                rules_dict[column] = rules_list

            rules_list.append(rule)



        for column, rules_list in rules_dict.items():

            if len(rules_list) > 1:
                search.add_op("begin")


            for rule in rules_list:

                column = rule.get('column')
                value = rule.get('value')
                op = rule.get('op')


                # If a relationship is set, then use that
                related = rule.get('related')

                sudo = Sudo()
                if related:
                    sobjects = parser.eval(related)
                    if isinstance(sobjects, Search):
                        search.add_relationship_search_filter(sobjects, op=op)
                    else:
                        search.add_relationship_filters(sobjects, op=op)

                    del sudo
                    continue


                # interpret the value
                # since the expression runs float(), we want to avoid that a number 5 being converted to 5.0
                # if we can't find @ or $
                if value.find('@') != -1 or value.find('$') != -1:
                    values = parser.eval(value, list=True)
                elif value.find("|") == -1:
                    values = value.split("|")
                else:
                    values = [value]

                

                # TODO: made this work with search.add_op_filters() with the expression parser instead of this
                # simpler implementation
                if len(values) == 1:
                    if not op:
                        op = '='
                    quoted = True
                    # special case for NULL
                    if values[0] == 'NULL':
                        quoted = False
                    if op in ['not in', '!=']:
                        search.add_op('begin')
                        search.add_filter(column, values[0], op=op, quoted=quoted)
                        search.add_filter(column, None)
                        search.add_op('or')
                    else:
                        search.add_filter(column, values[0], op=op, quoted=quoted)
                elif len(values) > 1:
                    if not op:
                        op = 'in'
                    if op in ['not in', '!=']:
                        search.add_op('begin')
                        search.add_filter(column, values, op=op)
                        search.add_filter(column, None)
                        search.add_op('or')
                    else:
                        search.add_filters(column, values, op=op)

                del sudo


            if len(rules_list) > 1:
                search.add_op("or")



    def alter_search_type_search(self, search):
        # special provision for various search types, particularly in
        # the sthpw database
        if self.is_admin():
            return

        return
        """        
        # Ignore this problem for now ...
        search_type = search.get_base_search_type()
        if search_type == 'sthpw/transaction_log':
            search.add_filter("namespace", "project")

        # normal users can only see those search types of the current
        # project
        # FIXME: is this too restrictive???
        if search_type in ['sthpw/note', 'sthpw/snapshot', 'sthpw/task']:
            from pyasm.biz import Project
            project_code = Project.get_project_code()
            search.add_filter("project_code", project_code)
        """


    def to_string(self):
        rule = ''
        rule += "<rules>\n"
        for group, data in self.groups.items():
            for key, access in data.items():
                rule += "  <rule group='%s' key='%s' access='%s'/>\n" % (group, key,access)

        #group, key, access

        rule += "</rules>\n"

        return rule



    #
    # static methods
    #

    def get_by_group(group):
        access_manager = AccessManager()

        #access_rules_xml = group.get_xml_value("access_rules")
        #project_code = group.get_value("project_code")
        #access_manager.add_xml_rules(access_rules_xml, project_code=project_code)
        access_manager.add_xml_rules(group)

        return access_manager
    get_by_group = staticmethod(get_by_group)

    def print_rules(self, group):
        '''For debugging, printing out the rules for a particular group'''
        rules = self.groups.get(group)
        if not rules:
            print("no rules for %s" %group)
            return
        for rule, values in rules.items():
            if isinstance(values, tuple):
                v = values[0]
            else:
                v = values


