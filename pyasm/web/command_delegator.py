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

#
# DEPRECATED
#


__all__ = ['CommandDelegator']

from pyasm.common import Marshaller, TacticException
from pyasm.command import Command

from .widget import *
from .html_wdg import *
from .web_container import *



class CommandDelegator(Widget):
    '''Introspects the web form and creates actions that have been
    requested by the web page. It can also contain command response info'''

    def __init__(self):
        self.registered_cmds = []
        self.executed_cmds = []
        super(CommandDelegator,self).__init__()


    def register_cmd(self, instance_cmd ):
        if instance_cmd not in self.registered_cmds:
            self.registered_cmds.append( instance_cmd )




    def get_display(self):

        html = Html()

        html.writeln("<!-- commands -->")

        for cmd in self.registered_cmds:
            hidden = HtmlElement("input")
            hidden.set_attr("type", "hidden")

            if isinstance(cmd, Marshaller):
                hidden.set_attr("name", "marshalled")
                hidden.set_attr( "value", cmd.get_marshalled() )
            else:
                hidden.set_attr("name", "command")
                hidden.set_attr("value", cmd )

            html.writeln( hidden.get_buffer_display() )

        html.writeln("<!--         -->")

        html.writeln("<!-- commands response ")
        hidden_response_list = []
        for idx, cmd in enumerate(self.executed_cmds):
            html.writeln('%s||%s'% (cmd.__class__.__name__, cmd.response) )
            if idx < len(self.executed_cmds) - 1:
                html.writeln('<br/>')
        # this <br/> is a delimiter, used in DynamicLoader.js
        html.writeln("             -->")

        return html



    def get_executed_cmds(self):
        return self.executed_cmds




    def execute(self):
        
        # get all of the commands
        web = WebContainer.get_web()

        # try the marshalled class
        marshall_list = []
        marshalled = web.get_form_values("marshalled")
        
        for marshall in marshalled:
            # skip duplicated commands
            if marshall in marshall_list:
                continue
            else:
                marshall_list.append(marshall)

            marshaller = Marshaller.get_from_marshalled(marshall)
            cmd = marshaller.get_object()
            # we want to allow the page to draw, CmdReport will display the error
            try:
                Command.execute_cmd(cmd)
            except TacticException as e:
                pass
            except OSError:
                pass
            except IOError:
                pass

            # store the commands that we executed
            self.executed_cmds.append(cmd)



