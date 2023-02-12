#!/usr/bin/python 
###########################################################
#
# Copyright (c) 2005-2009, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

import tacticenv

from pyasm.security import *
from pyasm.search import Search, SearchType, Transaction
from pyasm.unittest import UnittestEnvironment
from pyasm.biz import Project

from .widget_config import WidgetConfigView

import unittest

class WidgetConfigTest(unittest.TestCase):

    def setUp(self):
        # intitialize the framework as a batch process
        self.batch = Batch()

        from pyasm.web.web_init import WebInit
        WebInit().execute()

        self.test_env = UnittestEnvironment()
        self.test_env.create()

        # remove any existing widget config entries left over
        old_wdg_configs = Search.eval("@SOBJECT(config/widget_config)")
        for item in old_wdg_configs:
            item.delete()


    def test_all(self):

        # set up some widget configs in the database

        self.transaction = Transaction.get(create=True)

        widget_config_type = 'config/widget_config'

        def_config = '''
        <config>
        <definition>
          <element name='test'>
            <display class='SelectWdg'/>
          </element>
        </definition>
        </config>
        '''

        config = '''
        <config>
        <test>
          <element name='dan'/>
          <element name='dan2'>
             <display class='SelectWdg'/>
          </element>
          <element name='test'/>
          <element name='test2'>
            <display class='CheckboxWdg'/>
          </element>
          <element name='drop'/>
        </test>
        </config>
        '''

        edit_config = '''
        <config>
        <edit layout='EditWdg'>
          <element name='asset_category'/>
          <element name='code'>
            <display class='EditLevelTextWdg'/>
          </element>
          <element name='drop'/>
        </edit>
        </config>
        '''
        edit_def_config = '''
        <config>
        <edit_definition>
        <element name='asset_category'>
          <display class='ProcessSelectWdg'/>
        </element>
            
        <element name='code'>
            <display class='TextAreaWdg'/>
          </element>
        <element name='drop'>
            <action class='DropElementAction'>
               <path>path_test</path>
            </action>   
        </element>
        </edit_definition>
        </config>
        '''

        ALL_def_config = '''
        <config>
        <definition>
          <element name='dan'>
            <display class='tactic.ui.table.ExpressionElementWdg'/>
          </element>
        </definition>
        </config>
        '''

        try:
            # add the ALL definition view
            widget_config = SearchType.create(widget_config_type)
            widget_config.set_value("search_type", "ALL")
            widget_config.set_value("view", "definition")
            widget_config.set_value("config", ALL_def_config)
            widget_config.commit()

            # add the definition view
            widget_config = SearchType.create(widget_config_type)
            widget_config.set_value("search_type", "unittest/person")
            widget_config.set_value("view", "definition")
            widget_config.set_value("config", def_config)
            widget_config.commit()

            # add the test view for person
            widget_config = SearchType.create(widget_config_type)
            widget_config.set_value("search_type", "unittest/person")
            widget_config.set_value("view", "test")
            widget_config.set_value("config", config)
            widget_config.commit()

            # add the test view for city
            widget_config = SearchType.create(widget_config_type)
            widget_config.set_value("search_type", "unittest/city")
            widget_config.set_value("view", "test")
            widget_config.set_value("config", config)
            widget_config.commit()

            # add the edit view
            widget_config = SearchType.create(widget_config_type)
            widget_config.set_value("search_type", "unittest/person")
            widget_config.set_value("view", "edit")
            widget_config.set_value("config", edit_config)
            widget_config.commit()


            # add the edit def view
            widget_config = SearchType.create(widget_config_type)
            widget_config.set_value("search_type", "unittest/person")
            widget_config.set_value("view", "edit_definition")
            widget_config.set_value("config", edit_def_config)
            widget_config.commit()

            self._test_get_display_handler()
            self._test_get_action_handler()

        finally:
            self.transaction.rollback()
            Project.set_project('unittest')

            self.test_env.delete()


    def _test_get_action_handler(self):
        search_type = "unittest/person"


        # get the definition directly
        view = "edit"
        config = WidgetConfigView.get_by_search_type(search_type, view)
        action_handler = config.get_action_handler("drop")
        self.assertEqual("DropElementAction", action_handler)
        action_handler = config.get_action_handler("code")
        self.assertEqual("", action_handler)

        config = WidgetConfigView.get_by_search_type(search_type, 'test')
        action_handler = config.get_action_handler("drop")
        self.assertEqual("", action_handler)

        # get_by_elemnet_names will get it
        config = WidgetConfigView.get_by_element_names(search_type, ['drop'], 'test')
        action_handler = config.get_action_handler("drop")
        self.assertEqual("DropElementAction", action_handler)
        options = config.get_action_options("drop")
        self.assertEqual("path_test", options.get('path'))
        


    def _test_get_display_handler(self):
        search_type = "unittest/person"


        # get the definition directly
        view = "definition"
        config = WidgetConfigView.get_by_search_type(search_type, view)
        display_handler = config.get_display_handler("test")
        self.assertEqual("SelectWdg", display_handler)

        # use a non-existent view
        view = "whatever"
        config = WidgetConfigView.get_by_search_type(search_type, view)
        display_handler = config.get_display_handler("test")
        self.assertEqual("SelectWdg", display_handler)

        # get element_names
        #element_names = config.get_element_names()
        #self.assertEqual(['test'], element_names)


        # use an existing view
        view = "test"
        config = WidgetConfigView.get_by_search_type(search_type, view)
        display_handler = config.get_display_handler("test")
        self.assertEqual("SelectWdg", display_handler)
        display_handler = config.get_display_handler("test2")
        self.assertEqual("CheckboxWdg", display_handler)

        display_handler = config.get_display_handler("dan")
        self.assertEqual("tactic.ui.table.ExpressionElementWdg", display_handler)
        
        city_config = WidgetConfigView.get_by_search_type('unittest/city', view)
        display_handler = city_config.get_display_handler("dan")
        self.assertEqual("tactic.ui.table.ExpressionElementWdg", display_handler)
        display_handler = city_config.get_display_handler("dan2")
        self.assertEqual("SelectWdg", display_handler)
            
        # get element_names
        element_names = config.get_element_names()
        self.assertEqual(['dan','dan2','test','test2','drop'], element_names)



        # get a non-existent view using local_search
        view = "whatever"
        config = WidgetConfigView.get_by_search_type(search_type, view, local_search=True, use_cache=False)
        display_handler = config.get_display_handler("test")
        self.assertEqual("SelectWdg", display_handler)



        # check edit view
        view = "edit"
        config = WidgetConfigView.get_by_search_type(search_type, view)
        display_handler = config.get_display_handler("code")
        self.assertEqual("EditLevelTextWdg", display_handler)
        display_handler = config.get_display_handler("asset_category")

        self.assertEqual("ProcessSelectWdg", display_handler)


if __name__ == "__main__":
    unittest.main()

