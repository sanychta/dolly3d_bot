#!/usr/bin/env python
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

__all__ = ["SecurityTest"]

import tacticenv


from pyasm.common import Environment, SecurityException, Xml, Config
from pyasm.search import *
from pyasm.unittest import *
from pyasm.biz import Project, ExpressionParser
from pyasm.security import Login

from .security import *
from .drupal_password_hasher import DrupalPasswordHasher
from .access_manager import *
from .batch import *
from .crypto_key import *

import unittest

class SecurityTest(unittest.TestCase):

    def _setup(self):

        # intialiaze the framework as a batch process
        Site.set_site('default')
        security = Environment.get_security()
        from pyasm.biz import Project
        Project.set_project("unittest")
        self.security = Environment.get_security()
        self.user = 'unittest_guy'
        self.password = 'cow'
        self.encrypted = Login.encrypt_password(self.password)
        self.person = None

        # start a transaction
        self.transaction = Transaction.get(create=True)
        #self.transaction.start()


        # IF Portal
        portal_enabled = Config.get_value("portal", "enabled") == "true"
        if portal_enabled:
            try:
                site = Site.set_site("default")

                # create the user
                login = SObjectFactory.create("portal/client")
                login.set_value("login", self.user)
                login.set_value("password", self.encrypted)
                login.commit()
            
            finally:
                Site.pop_site()



        # create the user
        login = SObjectFactory.create("sthpw/login")
        login.set_value("login", self.user)
        login.set_value("password", self.encrypted)
        login.set_value("login_groups", "test")
        login.commit()

        s = Search('sthpw/login_group')
        s.add_filter('login_group','user')
        group = s.get_sobject()
        if not group:
            group = SObjectFactory.create("sthpw/login_group")
            group.set_value("login_group", 'user')
            group.set_value('access_level','min')
            group.commit()

        s = Search('sthpw/login_in_group')
        s.add_filter('login',self.user)
        s.add_filter('login_group', 'user')
        lng = s.get_sobject()
        if lng:
            lng.delete()


        # create the user2
        login = SObjectFactory.create("sthpw/login")
        login.set_value("login", 'unittest_gal')
        login.set_value("password", self.encrypted)
        login.set_value("login_groups", "test")
        login.commit()


        # create the user3 and add to a group
        login = SObjectFactory.create("sthpw/login")
        login.set_value("login", 'unittest_dan')
        login.set_value("password", self.encrypted)
        login.commit()

        login = SObjectFactory.create("sthpw/login_group")
        login.set_value("login_group", 'unittest_med')
        login.commit()

        login = SObjectFactory.create("sthpw/login_group")
        login.set_value("login_group", 'test')
        login.commit()

        l_in_g = SObjectFactory.create("sthpw/login_in_group")
        l_in_g.set_value("login", 'unittest_dan')
        l_in_g.set_value("login_group", 'unittest_med')
        l_in_g.commit()

        l_in_g = SObjectFactory.create("sthpw/login_in_group")
        l_in_g.set_value("login", self.user)
        l_in_g.set_value("login_group", 'test')
        l_in_g.commit()

    def _tear_down(self):
        #self.transaction = Transaction.get()
        self.transaction.rollback()
        # this is necessary cuz the set_value() was caught in a security exception possibly, needs investigation
        #if self.person:
        #    self.person.delete()
        tasks = Search.eval("@SOBJECT(sthpw/task['project_code','in','unittest|sample3d'])")
        for task in tasks:
            task.delete(triggers=False)

    def test_all(self):
        batch = Batch()
        Environment.get_security().set_admin(True)

        from pyasm.unittest import UnittestEnvironment, Sample3dEnvironment
        test_env = UnittestEnvironment()
        test_env.create()

        sample3d_env = Sample3dEnvironment(project_code='sample3d')
        sample3d_env.create()

        Project.set_project("unittest")
        try:
            self.access_manager = Environment.get_security().get_access_manager()
            self._test_all()

        finally:
            # Reset access manager for tear down
            Environment.get_security()._access_manager =  self.access_manager
            Environment.get_security().reset_access_manager()
            self._tear_down()
            Environment.get_security().set_admin(True)
            test_env.delete()
            Environment.get_security().set_admin(True)
            sample3d_env.delete()
            Site.pop_site()

    def _test_initial_access_level(self):
        # before adding process unittest_guy in user group is in MIN access_level
        # so no access to process, but access to search_types
        self.security.set_admin(False)
        security = Environment.get_security()


        process_keys = [{'process': 'anim'}]
        proc_access = security.check_access("process", process_keys, "allow")
        self.assertEqual(proc_access, False)

        stype_keys = [{'code':'*'}, {'code':'unittest/city'}]
        stype_access = security.check_access("search_type", stype_keys, "allow")
        a = security.get_access_manager()
        self.assertEqual(stype_access, True)

        # we don't have this sType specified explicitly, should be False
        stype_keys = [{'code':'unittest/city'}]
        stype_access = security.check_access("search_type", stype_keys, "allow")
        a = security.get_access_manager()
        self.assertEqual(stype_access, False)



    def _test_all(self):

        try:
            self._setup()

            self._test_crypto()
            self._test_drupal()

            self._test_security_fail()
            self._test_security_pass()
            self._test_initial_access_level()
            self._test_sobject_access_manager()

            # order matters here
            self._test_search_filter()
            self._test_access_level()
            self._test_access_manager()

            self._test_guest_allow()



        except Exception as e:
            print("Error: ", e)
            raise


    def _test_drupal(self):
        password = "tactic"
        salt = "DPRNKWLY"
        new = DrupalPasswordHasher().encode(password, salt, 'D')
        encoded = "$S$DDPRNKWLY5IwB.aQlCm/OLRrFxZmpa7Rk/kjm/J45bGNGTXUsRxq"
        self.assertEqual(new, encoded)

        verify = DrupalPasswordHasher().verify("tactic", encoded)
        self.assertEqual(True, verify)
        

    def _test_security_fail(self):

        # should fail
        password = 'test'

        fail = False
        try:
            self.security.login_user(self.user,password)
        except SecurityException as e:
            fail = True

        self.assertEqual( True, fail )


    def _test_security_pass(self):

        fail = False
        try:
            self.security.login_user(self.user,self.password)
        except SecurityException as e:
            fail = True

        user = Environment.get_user_name()

        # set this user as admin
        self.security.set_admin(True)


        self.assertEqual('unittest_guy', user)
        self.assertEqual( False, fail )

    def count(self, it):
        from collections import defaultdict
        d = defaultdict(int)
        for j in it:
            d[j] += 1
        return d

    def _test_search_filter(self):

        # NOTE: this unittest is flawed because it relies on project
        # that may not exist

        self.security.set_admin(False)

        # exclude sample3d tasks and include unittest tasks only
        rules = """
        <rules>
        <rule value='sample3d' search_type='sthpw/task' column='project_code' op='!=' group='search_filter'/>
        <rule value='unittest' search_type='sthpw/task' column='project_code' group='search_filter'/>
        </rules>
        """

        xml = Xml()
        xml.read_string(rules)
        access_manager = Environment.get_security().get_access_manager()
        access_manager.add_xml_rules(xml)

        search = Search('sthpw/task')
        tasks = search.get_sobjects()
        project_codes = SObject.get_values(tasks,'project_code', unique=True)
        self.assertEqual(False, 'sample3d' in project_codes)
        self.assertEqual(True, 'unittest' in project_codes)

        # test list-based expression
        rules = """
        <rules>
        <rule value='$PROJECT' search_type='sthpw/task' column='project_code' group='search_filter'/>
        <rule value="@GET(sthpw/login['login','EQ','unittest'].login)" search_type='sthpw/task' op='in' column='assigned' group='search_filter' project='*'/>
        </rules>
        """
        xml = Xml()
        xml.read_string(rules)
        # reset it
        Environment.get_security().reset_access_manager()

        self.security.set_admin(False)
        access_manager = Environment.get_security().get_access_manager()
        access_manager.add_xml_rules(xml)

        search = Search('sthpw/task')
        tasks = search.get_sobjects()
        # 3 tasks were created above for a person
        self.assertEqual(3, len(tasks))
        assigned_codes = SObject.get_values(tasks,'assigned', unique=True)
        project_codes = SObject.get_values(tasks,'project_code', unique=True)
        self.assertEqual({'unittest_guy': 1,'unittest_gal': 1}, self.count(assigned_codes))
        self.assertEqual(True, ['unittest'] == project_codes)

        rules = """
        <rules>
        <rule group="project" code='sample3d' access='allow'/>
        <rule group="project" code='unittest' access='allow'/>
        <rule group="project" code='art' access='allow'/>
        <rule value='$PROJECT' search_type='sthpw/task' column='project_code' group='search_filter'/>
        <rule value='@GET(login.login)' search_type='sthpw/task' column='assigned' group='search_filter' project='*'/>
        </rules>
        """
        xml = Xml()
        xml.read_string(rules)
        # reset it
        security = Environment.get_security()
        security.reset_access_manager()

        access_manager = security.get_access_manager()
        access_manager.add_xml_rules(xml)


        search = Search('sthpw/task')

        tasks = search.get_sobjects()

        # 2 tasks were created above for unittest_guy
        self.assertEqual(2, len(tasks))
        assigned_codes = SObject.get_values(tasks,'assigned', unique=True)
        project_codes = SObject.get_values(tasks,'project_code', unique=True)
        self.assertEqual(True, ['unittest_guy'] == assigned_codes)
        self.assertEqual(True, ['unittest'] == project_codes)

        Project.set_project('sample3d')
        try:
            search = Search('sthpw/task')
            tasks = search.get_sobjects()

            self.assertEqual(1, len(tasks))
            assigned_codes = SObject.get_values(tasks,'assigned', unique=True)
            project_codes = SObject.get_values(tasks,'project_code', unique=True)
            self.assertEqual(True, ['unittest_guy'] == assigned_codes)
            self.assertEqual(True, ['sample3d'] == project_codes)
        finally:
            Project.set_project('unittest')




        # project specific rule
        proj_rules = """
        <rules>
        <rule group="project" code='sample3d' access='allow'/>
        <rule group="project" code='unittest' access='allow'/>
        <rule value='$PROJECT' search_type='sthpw/task' column='project_code' group='search_filter'/>
        <rule value='@GET(login.login)' search_type='sthpw/task' column='assigned' group='search_filter' project='unittest'/>
        <rule group="process" process="anim" access="allow"/>
        <rule group="process" process="comp" access="allow"/>
        </rules>
        """
        xml = Xml()
        xml.read_string(proj_rules)
        # reset it
        Environment.get_security().reset_access_manager()

        access_manager = Environment.get_security().get_access_manager()
        access_manager.add_xml_rules(xml)

        project = Project.get_by_code('sample3d')
        if project:
            Project.set_project('sample3d')
            search = Search('sthpw/task')
            tasks = search.get_sobjects()

            assigned_codes = SObject.get_values(tasks,'assigned', unique=True)
            project_codes = SObject.get_values(tasks,'project_code', unique=True)
            # should fail since project is switched to sample3d.. and it should have more than just unittest
            self.assertEqual(False, ['unittest'] == assigned_codes)
            self.assertEqual(True, ['sample3d'] == project_codes)




            # unittest specific rule that uses negation !=, this takes care of NULL value automatically
            rules = """
            <rules>
                <rule group="project" code='sample3d' access='allow'/>
                <rule value='5' search_type='sthpw/task' column='priority' op='!=' group='search_filter' project='sample3d'/>
                 <rule group="process" process="anim" access="allow"/>
                <rule group="process" process="comp" access="allow"/>
            </rules>
            """
            xml = Xml()
            xml.read_string(rules)
            # reset it
            Environment.get_security().reset_access_manager()

            access_manager = Environment.get_security().get_access_manager()
            access_manager.add_xml_rules(xml)

            Project.set_project('sample3d')
            search = Search('sthpw/task')
            tasks = search.get_sobjects()

            priorities = SObject.get_values(tasks,'priority', unique=True)
            #project_codes = SObject.get_values(tasks,'project_code', unique=True)

            for p in priorities:
                self.assertEqual(True, p != 5)

        try:
            Project.set_project('unittest')
        except SecurityException as e:
            # should get an SecurityException
            self.assertEqual('User [unittest_guy] is not permitted to view project [unittest]', e.__str__())
            xml = Xml()
            xml.read_string(proj_rules)
            # reset it
            Environment.get_security().reset_access_manager()


            access_manager = Environment.get_security().get_access_manager()
            access_manager.add_xml_rules(xml)
        except Exception as e:
            print("Error : %s", str(e))
        else:
            # this should not happen
            raise Exception('unittest_guy should not be allowed to use Project unittest here.')

        # One should be able to insert a task that is outside the query restriction of the above rule
        task = SearchType.create('sthpw/task')
        task.set_sobject_value(self.person)
        task.set_value('assigned', 'made_up_login')
        task.set_value('project_code', 'sample3d')
        task.set_value('description', 'a new task')
        task.set_value('process', 'unittest')
        task.set_value('context', 'unittest')
        task.commit()

        self.assertEqual('made_up_login', task.get_value('assigned'))

    # DEPRECATED: column level security has been disabled for now (for
    # performance reasons)
    def _test_sobject_access_manager(self):
        '''test a more realistic example'''

        # create a test person
        person = Person.create("Donald", "Duck", "DisneyLand", "A duck!!!")
        self.person = person

        for project_code in ['unittest','unittest','sample3d']:
            task = SearchType.create('sthpw/task')
            task.set_sobject_value(person)
            task.set_value('assigned', 'unittest_guy')
            task.set_value('project_code', project_code)
            task.set_value('description', 'do something good')
            task.set_value('process', 'unittest')
            task.set_value('context', 'unittest')
            task.commit()

        # an extra task for list-based search_filter test
        task = SearchType.create('sthpw/task')
        task.set_sobject_value(person)
        task.set_value('assigned', 'unittest_gal')
        task.set_value('project_code', 'unittest')
        task.set_value('description', 'do something good')
        task.set_value('process', 'unittest2')
        task.set_value('context', 'unittest2')
        task.commit()
        # add these rules to the current user
        rules = """
        <rules>
          <rule group="sobject_column" default="edit"/>
          <rule group="sobject_column" search_type="unittest/person" column="name_first" access="edit"/>
          <rule group="sobject_column" search_type="unittest/person" column="name_last" access="deny"/>
          <rule group="sobject_column" search_type="unittest/person" column="nationality" access="deny"/>
        </rules>
        """

        xml = Xml()
        xml.read_string(rules)
        access_manager = Environment.get_security().get_access_manager()
        access_manager.add_xml_rules(xml)

        # disable admin for this test
        access_manager.set_admin(False)


        # should succeed
        person.set_value("name_first", "Donny")
        # should fail
        try:
            person.set_value("name_last", "Ducky")
        except SecurityException as e:
            pass
        else:
            self.fail("Expected a SecurityException")

        # should succeed
        name_last = person.get_value("name_last")
        self.assertEqual("Duck", name_last)

        # should fail
        # DISABLED for now since Search._check_value_security() is commented out
        """
        try:
            nationality = person.get_value("nationality")
        except SecurityException as e:
            pass
        else:
            self.fail("Expected a SecurityException")
        """
        # disable admin for this test
        access_manager.set_admin(True)


    def _test_access_manager(self):
        # reset it
        Environment.get_security().reset_access_manager()

        access_manager = Environment.get_security().get_access_manager()

        xml = Xml()
        xml.read_string('''
        <rules>


          <rule group='sobject' key='corporate/budget' access='allow'/>
          <rule group='sobject'  key='corporate/salary' access='allow'/>
          <rule group='sobject'  key='prod/asset' access='edit'/>
          <rule group='sobject' search_type='sthpw/note'  project='sample3d' access='edit'/>
          <group type='url' default='deny'>
            <rule key='/tactic/bar/Partner' access='view'/>
            <rule key='/tactic/bar/External' access='view'/>
          </group>



            <rule group='sobject' search_type='prod/layer'  project='sample3d' access='view'/>
            <rule column='description'  search_type='prod/shot' access='view' group='sobject_column'/>

          <group type='sobject_column' default='edit'>
            <rule key='prod/asset|director_notes' access='deny'/>
            <rule key='prod/asset|sensitive_data' access='deny'/>
          </group>


          <rule group='search_type' code='prod/asset'   access='allow'/>

          <rule group='search_type' code='sthpw/note' project='unittest' access='edit'/>


          <rule group='search_type' code='unittest/person'  project='unittest' access='allow'/>
          <rule group='builtin' key='view_site_admin' access='allow'/>
          <rule group='builtin' key='export_all_csv' project='unittest' access='allow'/>
          <rule group='builtin' key='import_csv' access='allow'/>

          <rule group='builtin' key='retire_delete' project='*' access='allow'/>
          <rule group='builtin' key='view_side_bar' access='allow'/>

           </rules>
        ''')
        access_manager.add_xml_rules(xml)



        # try mixing in a 2nd login_group rule with a project override, mimmicking a
        # login_group with project_code. but project group is special it doesn't get the usual
        # project_override treatment
        xml2 = Xml()
        xml2.read_string('''
        <rules>
          <rule group="project" code="sample3d" access="allow"/>
          <rule group="project" code="unittest" access="allow"/>

          <rule group='builtin' key='view_side_bar' project='sample3d' access='allow'/>
        </rules>
        ''')

        access_manager.add_xml_rules(xml2)

        access_manager.print_rules('project')

        test = access_manager.check_access('builtin', 'view_site_admin','allow')
        self.assertEqual(test, True)


        Project.set_project('sample3d')
        test = access_manager.check_access('builtin', 'export_all_csv','allow')
        self.assertEqual(test, False)

        # old way of checking project
        test = access_manager.check_access('project', 'sample3d','allow')
        self.assertEqual(test, True)

        Project.set_project('unittest')
        # old way should work as well
        test = access_manager.check_access('builtin', 'export_all_csv','allow')
        self.assertEqual(test, True)

        # default to the system's hardcoded deny for builtin
        test = access_manager.check_access('builtin', 'export_all_csv','allow', default='deny')
        self.assertEqual(test, True)



        # this is the new way to control per project csv export
        keys = [{'key':'export_all_csv', 'project': 'unittest'}, {'key':'export_all_csv','project': '*'}]
        test = access_manager.check_access('builtin', keys ,'allow')
        self.assertEqual(test, True)
        keys = [{'key':'import_csv', 'project': '*'}, {'key':'import_csv','project': Project.get_project_code()}]
        test = access_manager.check_access('builtin', keys ,'allow')
        self.assertEqual(test, True)


        test = access_manager.check_access('builtin', 'view_side_bar','allow')
        self.assertEqual(test, True)
        key = { "project": 'unittest', 'key':'view_side_bar' }
        key1 = { "project": 'sample3d', 'key':'view_side_bar' }
        key2 = { "project": "*",'key': 'view_side_bar' }
        keys = [key, key2]
        test = access_manager.check_access('builtin', keys,'allow')
        self.assertEqual(test, True)
        keys = [key1, key2]
        test = access_manager.check_access('builtin', keys,'allow')
        self.assertEqual(test, True)

        test = access_manager.check_access('builtin', 'retire_delete','allow')

        self.assertEqual(test, True)

        # test sensitive sobject
        test = access_manager.get_access('sobject', 'corporate/budget')
        self.assertEqual(test, "allow")

        # test allowed sobject
        test = access_manager.get_access('sobject', 'prod/asset')
        self.assertEqual(test, "edit")

        test = access_manager.get_access('sobject', [{'search_type':'sthpw/note', 'project':'sample3d'}])
        self.assertEqual(test, "edit")
        # test url
        test = access_manager.get_access('url', '/tactic/bar/Partner')
        self.assertEqual(test, "view")

        # test with access values ... a more typical usage
        test = access_manager.check_access('sobject','prod/asset','view')
        self.assertEqual(test, True)

        test = access_manager.check_access('sobject','corporate/budget','edit')
        self.assertEqual(test, True)

        test = access_manager.check_access('sobject_column', 'prod/asset|director_notes','deny')
        self.assertEqual(test, True)

        test = access_manager.check_access('sobject_column',{'search_type':'prod/shot','column':'description'},'edit')
        self.assertEqual(test, False)

        test = access_manager.check_access('sobject_column',{'search_type':'prod/shot','column':'description'},'view')
        self.assertEqual(test, True)


        test = access_manager.get_access('sobject',  {'search_type':'sthpw/note', 'project':'sample3d'} )
        self.assertEqual(test, "edit")
        test = access_manager.get_access('sobject', {'search_type':'sthpw/note'} )
        self.assertEqual(test, None)

        test = access_manager.get_access('sobject', {'search_type':'prod/layer', 'project':'sample3d'} )
        self.assertEqual(test, "view")
        test = access_manager.get_access('sobject', 'prod/layer' )
        self.assertEqual(test, None)

        Project.set_project('sample3d')
        # security version 2 uses group = search_type
        asset = SearchType.create('prod/asset')
        asset.set_value('name','unit test obj')
        asset.commit(triggers=False)
        # replace the access manager with this
        Environment.get_security()._access_manager = access_manager

        test = access_manager.check_access('search_type',{'search_type':'prod/asset','project':'sample3d'},'delete')
        self.assertEqual(test, False)

        asset.delete()

        note = SearchType.create('sthpw/note')
        note.set_value('note','unit test note obj')
        note.set_value('project_code','unittest')
        note.commit(triggers=False)


        test = access_manager.get_access('search_type', [{'code':'sthpw/note', 'project':'unittest'}] )
        self.assertEqual(test, 'edit')
        msg = ''
        # delete of unittest note should fail
        try:
            note.delete()
        except SObjectException as e:
            msg = 'delete error'
        self.assertEqual(msg, 'delete error')

        note = SearchType.create('sthpw/note')
        note.set_value('note','unit test sample3d note obj')
        note.set_value('project_code','sample3d')
        note.commit(triggers=False)

        # this should pass since it's a sthpw/ prefix
        note.delete()

        test = access_manager.check_access('search_type',{'search_type':'sthpw/note','project':'unittest'},'delete')
        self.assertEqual(test, False)

        self.assertEqual('unittest_guy',  Environment.get_user_name())


    def _test_crypto(self):

        key = CryptoKey()
        key.generate()


        # test verifying a string
        test_string = "Holy Moly"
        signature = key.get_signature(test_string)
        check = key.verify(test_string, signature)
        self.assertEqual(True, check)

        # verify an incorrect string
        check = key.verify("whatever", signature)
        self.assertEqual(False, check)


        # encrypt and decrypt a string
        test_string = "This is crazy"
        coded = key.encrypt(test_string)

        # create a new key
        private_key = key.get_private_key()
        key2 = CryptoKey()
        key2.set_private_key(private_key)
        test_string2 = key2.decrypt(coded)

        self.assertEqual(test_string, test_string2)

    def _test_access_level(self):
        security = Environment.get_security()
        from pyasm.security import get_security_version
        security_version = get_security_version()


        projects = Search.eval('@SOBJECT(sthpw/project)')
        if security_version >= 2:
            for project in projects:
                key = { "code": project.get_code() }
                key2 = { "code": "*" }
                keys = [key, key2]
                default = "deny"
                # other than sample3d, unittest as allowed above, a default low access level user
                # should not see other projects
                access = security.check_access("project", keys, "allow", default=default)
                process_keys = [{'process': 'anim'}]
                proc_access = security.check_access("process", process_keys, "allow")
                self.assertEqual(proc_access, True)
                if project.get_code() in ['sample3d','unittest']:
                    self.assertEqual(access, True)
                else:
                    self.assertEqual(access, False)
        else:
            raise SecurityException('Please test with security version 2. Set it in your config file')



    def _test_guest_allow(self):
        '''test Config tag allow_guest in security tag.
        Note: Since it is hard to emulate AppServer class,
        this is based on logic which handles in _get_display
        of BaseAppServer.

        1. If allow_guest is false, then it is necessary that
        Sudo is instantiated.

        2. If allow_guest is true, then it is necessary that
        guest login rules are added and login_as_guest is
        executed.
        '''

        security = Security()
        Environment.set_security(security)

        #1. allow_guest is false
        fail = False
        try:
            sudo = Sudo()
        except Exception as e:
            fail = True
        self.assertEqual( False, fail )
        sudo.exit()

        key = [{'code': "*"}]
        project_access = security.check_access("project", key, "allow")
        self.assertEqual(project_access, False)

        #2. allow_guest is true
        Site.set_site("default")
        try:
            security.login_as_guest()
            ticket_key = security.get_ticket_key()
            access_manager = security.get_access_manager()
            xml = Xml()
            xml.read_string('''
            <rules>
              <rule column="login" value="{$LOGIN}" search_type="sthpw/login" access="deny" op="!=" group="search_filter"/>
              <rule group="project" code="default" access="allow"/>
            </rules>
            ''')
            access_manager.add_xml_rules(xml)
        finally:
            Site.pop_site()


        default_key = [{'code': "default"}]
        project_access = security.check_access("project", default_key, "allow")
        self.assertEqual(project_access, True)

        unittest_key = [{'code', "sample3d"}]
        project_access = security.check_access("project", unittest_key, "allow")
        self.assertEqual(project_access, False)





if __name__ == "__main__":
    unittest.main()

