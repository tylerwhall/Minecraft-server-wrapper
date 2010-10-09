#!/usr/bin/env python

#    cryzed's Minecraft server script
#    Copyright (C) 2009 cryzed

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import shutil
import random
import threading
import subprocess
import re
import datetime
import yaml

# ---------------------------- COMMANDS -------------------------------------- #
class HelpCommand(object):
    def __init__(self, server, user):
        server.tell(user, "Available commands:")
        for key in COMMANDS.keys():
            server.tell(user, key)

#class QuoteCommand(object):
#    def __init__(self, server, output, config):
#        tokens = output.message.split()
#        if len(tokens) >= 2:
#            command = tokens[1]
#            if command == "add":
#                if len(tokens) >= 3:
#                    if not os.path.exists(config.quotes):
#                        quotes = open(config.quotes, "w")
#                    existing_quotes = open(config.quotes).read().splitlines()
#                    if " ".join(tokens[2:]) in existing_quotes:
#                        server.say("Quote already exists.")
#                        return
#                    quotes = open(config.quotes, "a")
#                    quotes.write("%s\n" % " ".join(tokens[2:]))
#                else:
#                    server.say("You need to enter a quote.")
#        else:
#            if os.path.exists(config.quotes):
#                quote = random.choice(open(config.quotes).read().splitlines())
#                server.say(quote)
#            else:
#                server.say("No quotes added yet. Add a new quote via \"add\".")

class BackupCommand(object):
    def __init__(self, server, user):
        if not server.is_op(user):
            server.tell(user, "Only operators are allowed to !backup.")
            return
        server.backup()
        
class ListCommand(object):
    def __init__(self, server, user):
#    	server.tell(user, "Ok. I will try")
    	server.list(user)

# ---------------------------- COMMANDS -------------------------------------- #
# ---------------------------- PLUGINS --------------------------------------- #
class TimedPlugin:
    def __init__(self, server):
        self.server = server

    def start(self):
        config = self.server.get_config(self)
        self.timer = threading.Timer(config['interval'], self.run)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def run(self):
        self.start()

class BackupPlugin(TimedPlugin):
    def run(self):
        self.server.backup()
        self.start()

class MotdPlugin(TimedPlugin):
    def run(self):
        config = self.server.get_config(self)
        for msg in config['messages']:
            self.server.say(msg)
        self.start()

    def event(self, event, **kwargs):
        pass
        #if event == 'logon':
        #    for msg in self.config.messages:
        #        self.server.tell(kwargs['user'], msg)

class SnapshotPlugin(TimedPlugin):
    def run(self):
        import c10
        config = self.server.get_config(self)
        worldname = 'world'
        self.server.save_all()
        time.sleep(3)
        limits=(-30,16,-16,40)
        if not os.path.exists(config['directory']):
            os.mkdir(config.directory)
        outname = worldname + '-' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + '.png'
        path = os.path.join(config['directory'], outname)
        c10.gen_image(worldname, path, limits=limits, oblique=45)
        path = os.path.join(config['directory'], 'night' + outname)
        c10.gen_image(worldname, path, limits=limits, oblique=45, night=True)
        path = os.path.join(config['directory'], 'cave' + outname)
        c10.gen_image(worldname, path, limits=limits, oblique=45, caves=True)
        self.start()

#class KickPlugin(threading.Thread):
#    def __init__(self, server, config):
#        threading.Thread.__init__(self)
#        self.server = server
#        self.config = config
#        self.stop = False
#
#    def run(self):
#        while not self.stop:
#            time.sleep(0.1)
#        for player in self.server.players:
#            print "Kicking %s" % player
#            self.server.kick(player)
# ---------------------------- PLUGINS --------------------------------------- #
RESTART_TIME = 3
COMMAND = ("java", "-Xmx1024M", "-Xms1024M", "-jar", "minecraft_server.jar", "nogui")
COMMANDS = {
    "help": HelpCommand,
    #"quote": QuoteCommand,
    "backup": BackupCommand,
    #"restore": RestoreCommand,
    "list": ListCommand,
}
PLUGINS = (
    BackupPlugin,
    MotdPlugin,
    SnapshotPlugin,
#    KickPlugin
)

def start_plugins(server):
    print "Starting plugins"
    plugins = []
    config = server.get_config
    for plugin in PLUGINS:
        if plugin.__name__ in server.config.config['Plugins']:
            print "Starting", plugin.__name__
            plugins.append(plugin(server))
            plugins[-1].start()
    return plugins

def stop_plugins(plugins):
    for plugin in plugins:
        plugin.stop()
    return []

def run_command(command, user, server):
    if not command in COMMANDS:
        server.tell(user, command + ' is not a valid command')
    else:
        COMMANDS[command](server, user)

class Config(object):
    def __init__(self):
        self.reload()

    def reload(self):
        self.config = yaml.load(open('server.yaml'))
        for key, value in self.config.items():
            setattr(self, key, value)

class MinecraftServer(object):
    def __init__(self, process):
        self.process = process
        self.config = Config()
        self.plugins = start_plugins(self)

    def get_config(self, crass):
        self.config.reload()
        if crass.__class__.__name__ in self.config.config.keys():
            return self.config.config[crass.__class__.__name__]

    def backup(self):
        self.say('Server is backing up now')
        self.save_all()
        time.sleep(5) #awful hack, need to wait for "Save complete"
        backupdir = "backups"
        worldname = 'world' #should get this from config
        backupname = worldname + '-' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        if not os.path.exists(backupdir):
            os.mkdir(backupdir)
        os.system("tar cjf backups/" + backupname + ".tar.bz2" + " " + worldname + "/*")
        #shutil.make_archive("backups/" + backupname, 'bztar', root_dir='world') requires python 2.7
        self.say("Backup %s finished." % backupname)

    def event(self, event, **kwargs):
        for p in self.plugins:
            if hasattr(p, 'event'):
                p.event(event, **kwargs)

    #Server commands
    def kick(self, name):
        self.stdin("kick %s\n" % name)

    def ban(self, name):
        self.stdin("ban %s\n" % name)

    def unban(self, name):
        self.stdin("pardon %s\n" % name)

    def banip(self, name):
        self.stdin("ban-ip %s\n" % name)

    def unbanip(self, name):
        self.stdin("pardon-ip %s\n" % name)

    def op(self, name):
        self.stdin("op %s\n" % message)

    def deop(self, name):
        self.stdin("deop %s\n" % name)

    def tp(self, player1, player2):
        self.stdin("tp %s %s\n" % message)

    def say(self, message):
        self.stdin("say %s\n" % message)

    def tell(self, user, message):
        self.stdin("tell %s %s\n" % (user, message))

    def save_all(self):
        self.stdin("save-all\n")

    def save_off(self, message):
        self.stdin("save-off\n")

    def save_on(self, message):
        self.stdin("save-on\n")

    def stop(self):
        self.stdin("stop\n")

    def stdin(self, input):
        self.process.stdin.write(input)
        
    def	list(self, user):
    	line = ""
    	self.process.stdin.write("list \n")
	line = self.process.stderr.readline().strip()
	self.tell(user, 'Currently In-Game: ' + line[(line.index('players:') + 9):] + '\n')

    def shutdown(self):
        self.plugins = stop_plugins(self.plugins)
        self.stop()
        time.sleep(2)
        self.process.terminate()

    def start(self):
        time.sleep(RESTART_TIME)
        self.process = subprocess.Popen(COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.plugins = start_plugins(self)

    def is_op(self, player):
        return player.lower() in self.operators

    @property
    def stdout(self):
        return self.process.stdout.readline().strip()

    @property
    def stderr(self):
        return self.process.stderr.readline().strip()

    @property
    def operators(self):
        with open("ops.txt") as operators:
            return (o.lower() for o in operators.read().splitlines() if o)

    #@property
    #def players(self):
    #    with open("players.txt") as players:
    #        return (p for p in players.read().splitlines() if p)

class Output(object):
    def __new__(self, output):
      self.output = output.split()
      match = re.match('(\S+) (\S+) (\S+) (.+)', output)
      if match:
        self.groups = match.groups()
        return object.__new__(self)
      else:
        return None

    @property
    def date(self):
        return self.groups[0]

    @property
    def time(self):
        return self.groups[1]

    @property
    def type(self):
        return self.groups[2]

    @property
    def content(self):
        return self.groups[3]

    @property
    def message(self):
        return " ".join(self.output[3:])

def main():
    server = MinecraftServer(subprocess.Popen(COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE))
    if not os.path.exists("minecraft.log"):
        log = open("minecraft.log", "w")
    log = open("minecraft.log", "a")
    log.flush()
    print "Ops are:", list(server.operators)
    while True:
        try:
            output = server.stderr
            if not output:
                continue
            print output
            log.write("%s\n" % output)
            log.flush()
            output = Output(output)
            if output:
                chat = re.match(r'<(.+)> (.+)', output.message)
                if chat and chat.group(2)[0] == '!':
                    user = chat.group(1)
                    command = chat.group(2)[1:]
                    run_command(command, user, server)
                logon = re.match(r'(\S+) \[\S+\] logged in', output.message)
                #if logon:
                #    server.event('logon', user=logon.groups(1)[0])
            #elif "Exception" in output.message:
            #    print "Fatal exception occured, restarting server. (%s...)" % output
            #    log.write("Fatal exception occured, restarting server. (%s...)\n" % output)
            #    print "Stopping plugins..."
            #    log.write("Stopping plugins...\n")
            #    log.flush()
            #    server.shutdown()
            #    server.start()
            #    print "Starting plugins..."
            #    log.write("Starting plugins...\n")
            #    log.flush()
            time.sleep(0.1)
        except(KeyboardInterrupt):
            print "Stopping plugins..."
            log.write("Stopping plugins...\n")
            log.flush()
            server.shutdown()
            sys.exit()
        except(Exception), exception:
            print "Exception: %s" % exception
            log.write("Exception: %s\n" % exception)
            log.flush()

if __name__ == "__main__":
    main()
