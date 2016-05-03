#!/usr/bin/python
"""sshsessions.py - Terminator Plugin to See SSH Connection on terminals"""

import os
import gtk
from subprocess import Popen, PIPE
from re import split
from sys import stdout

import terminatorlib.plugin as plugin
from terminatorlib.translation import _
from terminatorlib.util import widget_pixbuf, dbg


__author__ = "Gokhan MANKARA"
__email__ = "gokhan@mankara.org"

# Every plugin you want Terminator to load *must* be listed in 'AVAILABLE'
AVAILABLE = ['SSHSessions']

class Proc(object):
    """
        Data structure for a processes . The class properties are
        process attributes
    """

    def __init__(self):
        pass

    def to_dict(self, proc_info):
        """
            Returns a dict containing minimalistic info
            about the process : pid and command
        """

        pid = proc_info[1]
        cmd = proc_info[10]

        proc_dict = {
                      "pid": pid,
                      "name": cmd
                    }
 
        
        return proc_dict

    @property
    def get_proc_list(self):
        """
            Retrieves a list [] of Proc objects representing the active
            process list list

        """

        proc_list = []
        sub_proc = Popen(['ps', 'aux'], shell=False, stdout=PIPE)
        #Discard the first line (ps aux header)
        sub_proc.stdout.readline()

        for line in sub_proc.stdout:
            #The separator for splitting is 'variable number of spaces'
            proc_info = split(" *", line.strip())
            proc_list.append(Proc().to_dict(proc_info))
    
        return proc_list
    
    @property
    def ssh_sessions(self):
        """
            SSH Connections List
            return: list
        """

        ssh_sessions_list = []

        proc_list = self.get_proc_list
       
        for proc in proc_list:

            if 'ssh' == proc['name']:
                pid = proc['pid']
           
                pid_cmdfile = '/proc/%s/cmdline' % pid

                with open(pid_cmdfile, 'r') as f:
                    line = f.readlines()[0].split('\x00')[1]
                f.close()

                ssh_sessions_list.append(line)

        return list(set(ssh_sessions_list))

class SSHSessions(plugin.MenuItem):

    def __init__(self):
        plugin.MenuItem.__init__(self)
        self.window = gtk.Window()
        self.window.set_size_request(500, -1)
        self.window.set_title("Opened SSH Sessions")
        self.window.connect("destroy", self.destroy)

        self.checkbox_action = "OFF"

        self.proc = Proc()

    def callback(self, menuitems, menu, terminal):
        """Add our menu items to the menu"""
        item = gtk.MenuItem(_('SSH Sessions'))
        item.connect("activate", self.ssh_sessions, terminal)
        menuitems.append(item)

    def destroy(self, w):
        gtk.main_quit()

    def return_item(self, item):
        return str(self.proc.ssh_sessions[item])

    def action(self, w, data=None):

        if "ON" == self.checkbox_action:
            command = 'ssh-copy-id -i %s > /dev/null 2>&1 \n ssh %s \n' % (data['command'], data['command'])
        else:
            command = 'ssh %s \n' % data['command']
        
        data['terminal'].vte.feed_child(command)
        self.window.hide()

    def check_box(self, w, data=None):
         self.checkbox_action = "%s" % ("OFF", "ON")[w.get_active()]
         
         return self.checkbox_action

    def ssh_sessions(self, _widget, terminal):

        total_session = len(self.proc.ssh_sessions)

        if total_session == 0:
            message = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK)
            message.set_markup("NO SSH Connection FOUND")
            message.run()
            message.destroy()

        else:
            self.window.show_all()
            self.mainbox = gtk.VBox()
            self.window.add(self.mainbox)

            label = gtk.Label("Select Opened SSH Sessions")
            label.set_alignment(0,0)
            self.mainbox.pack_start(label, padding=10)
            label.show()

            check_button = gtk.CheckButton("Copy SSH Keygen to Server?")
            check_button.connect("clicked", self.check_box, "")
            self.mainbox.pack_end(check_button, expand=False)
            check_button.show()

            #radio1 = gtk.RadioButton(None, self.return_item(0))
            #self.mainbox.pack_start(radio1, expand=False)
            #radio1.show()
            ##{'terminal' : terminal, 'command' : command['command']
            #radio1.connect("clicked", self.action, {'terminal': terminal, 'command': self.return_item(0)})

            for i in range(total_session):
                radio = gtk.RadioButton(None, self.return_item(i))
                self.mainbox.pack_start(radio, expand=False)
                radio.connect("clicked", self.action, {'terminal': terminal, 'command': self.return_item(i)})
                radio.show()

            self.label = gtk.Label()
            self.mainbox.pack_start(self.label, padding=10)
            self.label.show()

            separator = gtk.HSeparator()
            self.mainbox.pack_start(separator, False, True, 0)
            separator.show()

            radio = gtk.VBox(False, 10)
            self.mainbox.set_border_width(10)

            # hbox_open = gtk.HBox(False, 0)

            # button_open = gtk.Button(label='Open')
            # button_open.connect("clicked", lambda w: self.action())
            # button_open.set_flags(gtk.CAN_DEFAULT)
            # hbox_open.pack_start(button_open, True, False, 0)
            # button_open.show()

            hbox_close = gtk.HBox(False, 0)

            button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
            button_close.connect("clicked", lambda w: self.window.hide())
            # button_close.set_flags(gtk.CAN_DEFAULT)
            hbox_close.pack_end(button_close, False, False, 0)
            button_close.show()

            # hbox_open.show()
            hbox_close.show()
            # self.mainbox.add(hbox_open)
            self.mainbox.add(hbox_close)

            #button_close.grab_default()            
            
            self.mainbox.show()

