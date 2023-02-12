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

__all__ = ['ProdFileNaming']

import os, re

from pyasm.biz import FileNaming, Project, Snapshot
from pyasm.common import TacticException
from pyasm.search import SearchType
from .prod_setting import ProdSetting

class ProdFileNaming(FileNaming):

    def add_ending(self, parts, auto_version=True):

        context = self.snapshot.get_value("context")
        filename = self.file_object.get_full_file_name()

        # make sure that the version in the file name does not yet exist
        version = self.get_version_from_file_name(filename)
        if not auto_version and version:

            # if the file version is not the same as the snapshot version
            # then check to see if the snapshot already exists
            if not context.startswith("cache") and version != self.snapshot.get_value("version"):
                existing_snap = Snapshot.get_by_version(self.snapshot.get_value("search_type"),\
                    self.snapshot.get_value("search_id"), context, version)
                if existing_snap:
                    raise TacticException('A snapshot with context "%s" and version "%s" already exists.' % (context, version) )


            self.snapshot.set_value("version", version)
            self.snapshot.commit()
        else:
            version = self.snapshot.get_value("version")

        if version == 0:
            version = "CURRENT"
        elif version == -1:
            version = "LATEST"
        else:
            version = "v%0.3d" % int(version)

        revision = self.snapshot.get_value("revision", no_exception=True)
        if revision:
            revision = "r%0.2d" % int(revision)

        ext = self.get_ext()

        parts.append(context.replace("/", "_"))

        if self.is_tactic_repo():
            parts.append(version)
            if revision:
                parts.append(revision)


        # should all files be named with file_type ending?
        file_type = self.get_file_type()

        # backwards compatibility
        if file_type and file_type not in ['maya','main','geo','xml']:
            parts.append(file_type)
        #if file_type in ['web','icon']:
        #    parts.append(file_type)

        value = ProdSetting.get_value_by_key("naming/add_initials")
        if value == "true":
            project = Project.get()
            initials = Project.get().get_initials()
            if initials:
                parts.append(initials)

        filename = "_".join(parts)
        if ext:
            filename = "%s%s" % (filename, ext)

        return filename


    def prod_sequence(self):

        # handle icons
        context = self.snapshot.get_value("context")
        if context == "icon" or self.get_file_type() =='icon_main':
           return self.get_default()

        parts = []
        sequence_code = self.sobject.get_code()
        parts.append(sequence_code)
        return self.add_ending(parts)


    def prod_shot(self):

        context = self.snapshot.get_value("context")

        # handle icons
        if context == "icon":
           return self.get_default()


        parts = []

        shot_code = self.sobject.get_code()
        parts.append(shot_code)

        filename = self.file_object.get_full_file_name()

        if context.startswith("cache/"):

            context_tmp = context.replace("/", "_")

            # HACK: Missing information here.  Extract it from filename
            file_parts, ext = os.path.splitext(filename)
            file_parts = file_parts.split("_")
            if file_parts[0] == shot_code:
                code = file_parts[1]
            else:
                code = file_parts[0]
            #code, ext = os.path.splitext(filename)
            #p = re.compile('%s_(\w+)_%s_v\d+' % (shot_code,context_tmp) )
            #m = p.match(filename)
            #if m:
            #    code = m.groups()[0]
            
            parts.append(code)
            return self.add_ending(parts, auto_version=False)
        else:
            return self.add_ending(parts)



    def prod_asset(self):

        context = self.snapshot.get_value("context")

        # handle icons
        if context == "icon":
           return self.get_default()
        
        # handle icon_main file type
        if self.get_file_type() =='icon_main':
           return self.get_default()

        parts = []

        asset_code = self.sobject.get_code()
        parts.append(asset_code)

        return self.add_ending(parts)




    def prod_shot_instance(self):
        shot_code = self.sobject.get_value("shot_code")
        instance = self.sobject.get_value("name")

        parts = []
        parts.append( shot_code )
        parts.append( instance )

        return self.add_ending(parts)



    def prod_texture(self):
        
        parts = []

        code = self.sobject.get_code()
        parts.append(code)

        # handle file_type for icons
        file_type = self.get_file_type()
        if file_type == 'web' or file_type == 'icon':
            parts.append(file_type)

        file_name = self.add_ending(parts, auto_version=True)

        if self.file_object.get_file_range():
            orig_file_name = self.file_object.get_file_name()
            pat = re.compile('\.(#+)\.')
            m = pat.search(orig_file_name)
            if m:
                padding = len(m.groups()[0])
                padding_str = '#'*padding
            else:
                raise TacticException('no # found in the file name') 
            base, ext = os.path.splitext(file_name)
            file_name = "%s.%s%s" % (base, padding_str, ext)

        return file_name


    def prod_texture_source(self):
        return self.get_default()


       
    def prod_render(self):
        # NOT IMPLEMENTED because self.get_ext() can't handle frame ranges
        # code
        # XG001_BG1_anim_v001.png.0006

        parts = []
        parent = self.sobject.get_parent()
        parent_code = parent.get_code()

        search_type = SearchType.get( self.sobject.get_value("search_type") )
        base_search_type = search_type.get_base_search_type()
        if base_search_type =='prod/layer':
            # layer name is sufficient
            parent_code = parent.get_value('name')
        parts.append(parent_code)
        
        '''
        parent_snapshot_code = self.sobject.get_value("snapshot_code")
        if parent_snapshot_code:
            parent_snapshot = Snapshot.get_by_code(parent_snapshot_code)
            context = parent_snapshot.get_value("context")
            parts.append(context)
        '''
        file_type = self.get_file_type()
        if file_type in ['web','icon']:
            parts.append(file_type)

        version = self.snapshot.get_value("version")
        if not version:
            version = 1
        version = "v%0.3d" % int(version)

        ext = self.get_ext()

        filename = "_".join(parts)
        filename = "%s_%s.####%s" % (filename, version, ext)

        return filename


    def effects_plate(self):
        code = self.sobject.get_value('code')
        if not code:
            shot_code = self.sobject.get_value('shot_code')
            id = self.sobject.get_id()
            code = '%s_%s' %(shot_code, id)
        parts = [code]
       
        file_name = self.add_ending(parts, auto_version=False)
        base, ext = os.path.splitext(file_name)
        if self.file_object.get_file_range():
            file_name = "%s.####%s" % (base, ext)
        return file_name

    def prod_plate(self):
        return self.effects_plate()

    def prod_submission(self):
        base_name, ext = os.path.splitext(self.file_object.get_file_name())
        parts = [base_name]
        file_name = self.add_ending(parts, auto_version=False)
        base, ext = os.path.splitext(file_name)
        file_code = self.file_object.get_code()
        file_name = "%s_%s%s" % (base, file_code, ext)
        return file_name

    def sthpw_note(self):
        base_name, ext = os.path.splitext(self.file_object.get_file_name())
        parts = [base_name]
        file_name = self.add_ending(parts, auto_version=False)
        base, ext = os.path.splitext(file_name)
        file_code = self.file_object.get_code()
        file_name = "%s_%s%s" % (base, file_code, ext)
        return file_name



