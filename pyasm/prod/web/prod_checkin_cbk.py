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

__all__ = ['CheckinException', 'AssetCheckinCbk', 'SetCheckinCbk', 'AnimCheckinCbk', 'ShotCheckinCbk', 'ShotSetCheckinCbk']

import os

from pyasm.web import WebContainer, BaseAppServer
from pyasm.command import *
from pyasm.prod.biz import *
from pyasm.prod.checkin import *
from pyasm.search import SearchKey

from .prod_context import *
from .maya_set_wdg import *
from .prod_checkin_wdg import *

class CheckinException(Exception):
    pass



class AssetCheckinCbk(Command):
    '''While other Cbk in this file are search type specific, this one is general to any kind of sTypes'''
    BUTTON_NAME = "Publish"

    def get_title(self):
        return "Asset Checkin"


    def handle_input(cls, input, search_type='', texture_search_type=''):

        # ------------
        # start test
        event_name = "publish_snapshot"
        search = Search("sthpw/trigger")
        search.add_filter("event", event_name)
        triggers = search.get_sobjects()
        javascript = ''
        for trigger in triggers:
            xxx = trigger.get_value("class_name")

            event_script = '''
            var script = spt.CustomProject.get_script_by_path("%s");
            bvr['script'] = script;
            spt.CustomProject.exec_custom_script(evt, bvr);
            ''' % xxx

            loader_script = '''spt.named_events.fire_event('%s', {})''' % event_name
            #table.add_behavior( {
            #    'type': 'listen',
            #    'event_name': event_name,
            #    'cbjs_action': event_script
            #} )
            javascript = event_script

        # end test
        # ---------


        print("setTimeout(function() {checkin_selected_assets('%s', bvr)}, 200)" % cls.BUTTON_NAME)
        if not javascript:
            javascript = "setTimeout(function() {checkin_selected_assets('%s', bvr)}, 200)" % cls.BUTTON_NAME


        batch_dir = ProdSetting.get_value_by_key('batch_dir')
        if not batch_dir:
            setting = ProdSetting.create('batch_dir', 'C:/sthpw/temp',\
                'string', 'batch script dir')
            batch_dir = setting.get_value('value')
        
        input.add_behavior({'type': "click_up",
                'cbjs_action': javascript,
                'cbk': 'pyasm.prod.web.AssetCheckinCbk',
                'batch_dir': batch_dir,
                'search_type': search_type,
                'texture_search_type': texture_search_type}
                )
    handle_input = classmethod(handle_input)



    def check(self):
        web = WebContainer.get_web()
        if web.get_form_value(MayaAssetCheckinWdg.PUBLISH_BUTTON) == "":
            return False
        self.search_type = self.kwargs.get('search_type')
        if not self.search_type:
            self.search_type = 'prod/asset'
        self.texture_search_type = self.kwargs.get('texture_search_type')
        if not self.texture_search_type:
            self.texture_search_type = 'prod/texture'

        # get the process to check this asset in (NEW)
        self.process = web.get_form_value("%s_process" %self.search_type)
        # get the context to check this asset in
        self.context = web.get_form_value("%s_context" %self.search_type)
        if not self.context:
            raise UserException('Please select a context in the drop-down.')
            return False
        
        sub_context = web.get_form_value("%s_sub_context"%self.search_type)

        if sub_context:
            self.context = "%s/%s" % (self.context, sub_context)


        return True


    def execute(self):

        #self.snapshot_dict = {}
        # get all of the selected instances
        web = WebContainer.get_web()
        instances = web.get_form_values("asset_instances")
        set_instances = web.get_form_values("set_instances")
        is_current = web.get_form_value("currency")
        checkin_status = web.get_form_value("checkin_status")

        if is_current in  ['True', 'on']:
            is_current = True
        else:
            is_current = False
        is_revision = web.get_form_value("checkin_as")
        if is_revision == "Version":
            is_revision = False
        else:
            is_revision = True

        snapshot_type = web.get_form_value("snapshot_type")

        if not instances and not set_instances:
            raise CommandExitException("No instances selected")

        # go through the asset instances and set instances and check them in
        for instance in instances:
            if instance:
                self._checkin(instance, self.context, is_current=is_current, \
                    is_revision=is_revision, snapshot_type=snapshot_type, \
                    texture_search_type=self.texture_search_type)
        for set_instance in set_instances:
            if set_instance:
                self._checkin(set_instance, self.context, asset_type='set', \
                    is_current=is_current, is_revision=is_revision, \
                    snapshot_type=snapshot_type)

        web.set_form_value('publish_search_type','prod/asset')
        #TabWdg.set_redirect('Log')
      
        self.info['context'] = self.context
        self.info['revision'] = str(is_revision)
        self.info['checkin_status'] = checkin_status

        output = {'context': self.context}
        output['search_key'] = SearchKey.build_by_sobject(self.sobject)
        output['checkin_status'] = checkin_status

        Trigger.call(self, 'app_checkin', output)

    def postprocess(self):
        pass


    def _checkin(self, instance, context, asset_type='asset', is_current=True, \
            is_revision=True, snapshot_type="asset", texture_search_type=None):
        '''retrieve the asset sobject and run the checkin command'''
        
        web = WebContainer.get_web()
        namespace, asset_code, instance_name = instance.split("|")
        description = WebContainer.get_web().get_form_value(\
            "%s_description" % instance_name)

        # get the sobject from asset_code
        
        self.sobject = Search.get_by_code(self.search_type, asset_code)
        if self.sobject == None:
            raise CommandException("SObject '%s' does not exist'" % asset_code)
        # now checkin the asset
        checkin = None

        # we assume asset_type = 'asset' by default
        if asset_type == 'asset':
            checkin = MayaAssetCheckin(self.sobject)
            checkin.set_instance(instance_name)
            checkin.set_option('texture_search_type', texture_search_type)
        elif asset_type =='set':
            checkin = MayaGroupCheckin(self.sobject)
        else:
            raise CommandException('Unknown asset type[%s] found' %asset_type)
        checkin.set_description(description)
        checkin.set_process(self.process)
        checkin.set_context(context)
        checkin.set_current(is_current)
        checkin.set_revision(is_revision)
        use_handoff_dir = web.get_form_value("use_handoff_dir")
        if use_handoff_dir in ['true','on']:
            checkin.set_use_handoff(True)
        if snapshot_type:
            checkin.set_snapshot_type(snapshot_type)

        checkin.set_option("unknown_ref", web.get_form_value("unknown_ref"))
        checkin.execute()

        snapshot = checkin.get_snapshot()
        version = snapshot.get_version()
        if description == "":
            description = "<No description>"
        self.add_description("Checked in %s '%s', context: %s, v%0.3d, %s" % \
            (asset_type.capitalize(), instance_name, context, version, description))
       
        self.sobjects = [self.sobject]
        
        #self.snapshot_dict[instance] = checkin.snapshot



class SetCheckinCbk(Command):

        
    def get_title(self):
        return "Set Checkin"

    def check(self):
        web = WebContainer.get_web()
        if web.get_form_value(MayaSetWdg.PUBLISH_BUTTON) == "":
            return False

        # get the context to check this asset in
        self.context = web.get_form_value("%s_context" \
            %MayaSetWdg.PUBLISH_TYPE )
        if not self.context:
            return False

        return True
        
    def execute(self):

        #self.snapshot_dict = {}
        
        web = WebContainer.get_web()

        current_section_name = web.get_form_value(MayaSetWdg.CURRENT_SECTION)
        if not current_section_name:
            raise CommandExitException()

        description = web.get_form_value("description")

        current_section_instance, current_section_code = current_section_name.split("|")
        
        # get the sobject from asset_code
        current_section = Asset.get_by_code(current_section_code)
        if current_section == None:
            # try the name instead
            current_section = Asset.get_by_name(current_section_instance)
            if current_section == None:
                raise CheckinException("Cannot find asset '%s'" % current_section_code)

        # now checkin the asset
        checkin = MayaGroupCheckin(current_section)
        checkin.set_description(description)
        checkin.set_context(self.context)
        checkin.execute()

        self.add_description("Set '%s': %s" % (current_section_code,description))
        #self.snapshot_dict[current_section_name] = checkin.snapshot

        web.set_form_value('publish_search_type','prod/asset')
        #TabWdg.set_redirect('Log')
    
    def postprocess(self):
        pass
        '''
        context = "publish"
        for instance, snap in self.snapshot_dict.items():
            instance_name, asset_code = instance.split("|")
            BaseAppServer.add_onload_script("update_snapshot('%s','%s','%s','%s')"\
                % (snap.get_code(), asset_code, instance_name, context))
    
        '''

class AnimCheckinCbk(Command):

    BUTTON_NAME = "Publish"
    def get_title(self):
        return "Anim Checkin"

    def check(self):
        web = WebContainer.get_web()
        if web.get_form_value(MayaAnimCheckinWdg.PUBLISH_BUTTON) == "":
            #raise CommandExitException()
            return

        # get the process to check this asset in (NEW)
        self.process = web.get_form_value("prod/shot_instance_process")

        # get the context to check this asset in
        self.context = web.get_form_value("prod/shot_instance_context")
        if not self.context:
            #raise UserException('Please select a context in the drop-down.')
            return False
       
        sub_context = web.get_form_value("prod/shot_instance_sub_context")

        if sub_context:
            self.context = "%s/%s" % (self.context, sub_context)
           
       

        return True

    def handle_input(cls, input, search_type):
        javascript = "setTimeout(function() {checkin_selected_anim('%s', bvr)}, 200)" % cls.BUTTON_NAME
        input.add_behavior({'type': "click_up",
                'cbjs_action': javascript,
                'cbk': 'pyasm.prod.web.AnimCheckinCbk',
                'search_type': search_type}
                )

    handle_input = classmethod(handle_input)

    def execute(self):
        #self.snapshot_dict = {}

        web = WebContainer.get_web()

        node_values = web.get_form_values("asset_instances")
        if not node_values:
            raise CommandExitException()
        shot_code = web.get_form_value("shot_code")
        shot = Shot.get_by_code(shot_code)
 
        if shot == None:
            raise CommandException("Shot does not exist")

        # go through asset code and check it in
        for node_value in node_values:
            namespace, asset_code, instance_name  = node_value.split("|")

            description = web.get_form_value("%s_description" % instance_name)
            # get the instance to check this object in with
            instance = ShotInstance.get_by_shot(shot, instance_name)
            if not instance:
                parent_code = shot.get_value("parent_code")
                if parent_code:
                    parent_code = [parent_code]
                else:
                    parent_code = []
                instance = ShotInstance.get_by_shot(shot, instance_name, \
                parent_codes=parent_code)
           
                if instance:
                    # if it is inheriting from its parents, make a new shot instance
                    # for the current shot
                    if instance.get_value('shot_code') != shot.get_code():
                        asset = Asset.get_by_code(asset_code)
                        instance = ShotInstance.create(shot, asset, instance_name,\
                            "asset", unique=True)
                else:
                    # it is probably part of a set
                    asset = Asset.get_by_code(asset_code)
                    instance = ShotInstance.create(shot, asset, instance_name, \
                            "set_item", unique=True)
             
            # now checkin the asset
            export_method = web.get_form_value("export_method")
            if export_method == "Export":
                checkin = MayaAnimExportCheckin(instance)
                checkin.set_option("remove_namespace", "false")
            else:
                checkin = MayaAnimCheckin(instance)

            checkin.set_instance(instance_name)
            checkin.set_description(description)
            checkin.set_process(self.process)
            checkin.set_context(self.context)
            use_handoff_dir = web.get_form_value("use_handoff_dir")
            if use_handoff_dir in ['true','on']:
                checkin.set_use_handoff(True)

            checkin.execute()

            #self.snapshot_dict[node_value] = checkin.snapshot
            
        self.add_description("Instance '%s': %s" % (instance_name, description))

        web.set_form_value('publish_search_type','prod/shot_instance')
        #TabWdg.set_redirect('Log')

    def postprocess(self):
        pass
        '''
        for node_value, snap in self.snapshot_dict.items():
            namespace, asset_code, instance_name = node_value.split("|")
            BaseAppServer.add_onload_script("update_snapshot('%s','%s','%s','%s')"\
                % (snap.get_code(), asset_code, namespace, self.context))
        '''

from pyasm.checkin import FileCheckin
from pyasm.biz import File
import re, shutil

class ShotCheckinCbk(Command):

    BUTTON_NAME = "Publish"
    def get_title(self):
        return "Shot Checkin"

    def check(self):
        web = WebContainer.get_web()
        if web.get_form_value(MayaShotCheckinWdg.PUBLISH_BUTTON) == "":
            return False

        self.search_type = self.kwargs.get('search_type')
        if self._check_context():
            return True
        else:
            return False
       
    def _check_context(self):
        # get the context to check this asset in
        web = WebContainer.get_web()

        
        # get the process to check this asset in (NEW)

        self.process = web.get_form_value("%s_process" %self.search_type)

        self.context = web.get_form_value("%s_context" %self.search_type)
        if not self.context:
            raise UserException('Please select a context in the drop-down.')
            return False

        sub_context = web.get_form_value("%s_sub_context"%self.search_type)

        if sub_context:
            self.context = "%s/%s" % (self.context, sub_context)
            
        return True

    
    def handle_input(cls, input, search_type='', texture_search_type=''):
        javascript = "setTimeout(function() {checkin_shot('%s', bvr)}, 200)" % cls.BUTTON_NAME
        input.add_behavior({'type': "click_up",
                'cbjs_action': javascript,
                'cbk': 'pyasm.prod.web.ShotCheckinCbk',
                'search_type': search_type,
                'texture_search_type': texture_search_type}
                )
    handle_input = classmethod(handle_input)

    def execute(self):
 
        #self.snapshot_dict = {}
        web = WebContainer.get_web()
        
        shot_code = web.get_form_value("shot_code")
        search = Search(self.search_type)
        search.add_filter('code', shot_code)
        shot = search.get_sobject()
        #shot = Shot.get_by_code(shot_code)

        is_current = web.get_form_value("currency")
        if is_current in  ['True', 'on']:
            is_current = True
        else:
            is_current = False
        is_revision = web.get_form_value("checkin_as")
        if is_revision == "Version":
            is_revision = False
        else:
            is_revision = True

        checkin_status = web.get_form_value("checkin_status")
        checkin = ShotCheckin(shot)
        checkin.set_option("unknown_ref", web.get_form_value("unknown_ref"))
        checkin.set_process(self.process)

        description = web.get_form_value("%s_description" % shot.get_code() )
        checkin.set_context(self.context)
        checkin.set_description(description)

        checkin.set_current(is_current)
        checkin.set_revision(is_revision)

        use_handoff_dir = web.get_form_value("use_handoff_dir")
        if use_handoff_dir in ['true','on']:
            checkin.set_use_handoff(True)

        checkin.execute()
        
        snapshot = checkin.snapshot
        version = snapshot.get_version()

        self.sobjects = [shot]

        #self.snapshot_dict['%s' %shot.get_code()] = snapshot
        self.add_description("%s checkin '%s': v%0.3d, %s" % (self.context, shot.get_code(), version, description))

        web.set_form_value('publish_search_type','prod/shot')
        TabWdg.set_redirect('Log')

        self.info['context'] = self.context
        self.info['revision'] = str(is_revision)
        self.info['checkin_status'] = checkin_status

        output = {'context': self.context}
        output['search_key'] = SearchKey.build_by_sobject(shot)
        output['checkin_status'] = checkin_status

        Trigger.call(self, 'app_checkin', output)

    def postprocess(self):
        pass




class ShotSetCheckinCbk(ShotCheckinCbk):
    '''All this does is check redirect the page to the log.  Checkin occurs
    through XMLRPC'''

    def get_title(self):
        return "Shot Set Checkin"

    def check(self):
        web = WebContainer.get_web()
        if web.get_form_value(MayaShotCheckinWdg.PUBLISH_SET_BUTTON) == "":
            return False
         
        if not self._check_context():
            return False

        # if there is publish error, exit
        error_path = '%s/error.txt' %FileCheckin.get_upload_dir()
        if os.path.exists(error_path):
            return False

        return True

    def handle_input(cls, input, search_type=''):
        javascript = "setTimeout(function() {checkin_shot_set('%s', bvr)}, 200)" % cls.BUTTON_NAME
        input.add_behavior({'type': "click_up",
                'cbjs_action': javascript,
                'cbk': 'pyasm.prod.web.ShotSetCheckinCbk',
                'search_type': search_type}
                )
    handle_input = classmethod(handle_input)

    def execute(self):
        #self.snapshot_dict = {}
        web = WebContainer.get_web()
        
        shot_code = web.get_form_value("shot_code")
        self.shot = Shot.get_by_code(shot_code)

        # remember the sobject
        self.sobjects = [self.shot]

        web.set_form_value('publish_search_type','prod/shot')
        #TabWdg.set_redirect('Log')

        

    def get_description(self):
        return "Shot Checkin: %s" % (self.shot.get_code())

    def postprocess(self):
        pass

                        






