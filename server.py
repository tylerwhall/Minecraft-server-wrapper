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

# ----------------------------- CONFIG --------------------------------------- #
# ---------------------------- COMMANDS -------------------------------------- #
class RunCommand(object):
    IDENTIFIER = "RunCommand"
    def __init__(self, server, output, config):
        server.say("%s runs away!" % output.name)

class KillCommand(object):
    IDENTIFIER = "KillCommand"
    def __init__(self, server, output, config):
        tokens = output.message.split()
        if len(tokens) >= 2:
            server.say("%s was killed by %s!" % (tokens[1], output.name))
        else:
            server.say("%s killed himself!" % output.name)

class HappyCommand(object):
    IDENTIFIER = "HappyCommand"
    def __init__(self, server, output, config):
        tokens = output.message.split()
        if len(tokens) >= 2:
            server.say("%s made %s happy!" % (" ".join(tokens[1:]), output.name))
        else:
            server.say("%s is happy!" % output.name)

class SadCommand(object):
    IDENTIFIER = "SadCommand"
    def __init__(self, server, output, config):
        tokens = output.message.split()
        if len(tokens) >= 2:
            server.say("%s made %s sad!" % (" ".join(tokens[1:]), output.name))
        else:
            server.say("%s is sad!" % output.name)

class HelpCommand(object):
    IDENTIFIER = "HelpCommand"
    def __init__(self, server, output, config):
        server.say("Available commands:")
        for key in COMMANDS.keys():
            server.say(key)

class QuoteCommand(object):
    IDENTIFIER = "QuoteCommand"
    def __init__(self, server, output, config):
        tokens = output.message.split()
        if len(tokens) >= 2:
            command = tokens[1]
            if command == "add":
                if len(tokens) >= 3:
                    if not os.path.exists(config.quotes):
                        quotes = open(config.quotes, "w")
                    existing_quotes = open(config.quotes).read().splitlines()
                    if " ".join(tokens[2:]) in existing_quotes:
                        server.say("Quote already exists.")
                        return
                    quotes = open(config.quotes, "a")
                    quotes.write("%s\n" % " ".join(tokens[2:]))
                else:
                    server.say("You need to enter a quote.")
        else:
            if os.path.exists(config.quotes):
                quote = random.choice(open(config.quotes).read().splitlines())
                server.say(quote)
            else:
                server.say("No quotes added yet. Add a new quote via \"add\".")

class BanCommand(object):
    IDENTIFIER = "BanCommand"
    def __init__(self, server, output, config):
        if not output.name.lower() in server.operators:
            server.say("Only operators are allowed to !ban.")
            return
        for target in output.message.split()[1:]:
            if target.lower() in server.operators:
                server.say("Player %s was not banned. You can't ban operators." % target)
                continue
            server.banip(target)
            server.ban(target)

class KickCommand(object):
    IDENTIFIER = "KickCommand"
    def __init__(self, server, output, config):
        if not output.name.lower() in server.operators:
            server.say("Only operators are allowed to !kick.")
            return
        for target in output.message.split()[1:]:
            if target.lower() in server.operators:
                server.say("Player %s was not kicked. You can't kick operators." % target)
                continue
            server.kick(target)

class BackupCommand(object):
    IDENTIFIER = "BackupCommand"
    def __init__(self, server, output, config):
        if not output.name.lower() in server.operators:
            server.say("Only operators are allowed to !backup.")
            return
        if not os.path.exists(config.directory):
            os.mkdir(config.directory)
        backups = os.listdir(config.directory)
        backups.sort(lambda x, y: int(x) - int(y))
        path = os.path.join(config.directory, "0")
        if backups:
            path = os.path.join(config.directory, str(int(backups[-1])+1))
        os.mkdir(path)
        shutil.copy("server_level.dat", path)
        server.say("Backup %s saved." % str(int(backups[-1])+1))

class RestoreCommand(object):
    IDENTIFIER = "RestoreCommand"
    def __init__(self, server, output, config):
        if not output.name.lower() in server.operators:
            server.say("Only operators are allowed to !restore.")
            return
        tokens = output.message.split()
        if not len(tokens) >= 2:
            server.say("No valid backup specified.")
            return
        if not os.path.exists(config.directory):
            server.say("No backups made yet.")
            return
        backups = os.listdir(config.directory)
        backups.sort(lambda x, y: int(x) - int(y))
        if not os.path.exists(os.path.join(config.directory, tokens[1])):
            server.say("Backup doesn't exist.")
            return
        server.shutdown()
        path = os.path.join(config.directory, tokens[1], "server_level.dat")
        os.remove("server_level.dat")
        shutil.copy(path, os.getcwdu())
        server.start()

class EightBallCommand:
    IDENTIFIER = "EightBallCommand"
    def __init__(self, server, output, config):
        if os.path.exists(config.responses):
            response = random.choice(open(config.responses).read().splitlines())
            server.say(response)
        else:

            server.say("%s not found." % config.responses)
# ---------------------------- COMMANDS -------------------------------------- #
# ---------------------------- PLUGINS --------------------------------------- #
class BackupPlugin(threading.Thread):
    IDENTIFIER = "BackupPlugin"
    def __init__(self, server, config):
        threading.Thread.__init__(self)
        self.server = server
        self.config = config
        self.stop = False

    def run(self):
        while not self.stop:
            time.sleep(self.config.interval)
            if self.stop:
                break
            if not os.path.exists(self.config.directory):
                os.mkdir(self.config.directory)
            backups = os.listdir(self.config.directory)
            backups.sort(lambda x, y: int(x) - int(y))
            path = os.path.join(self.config.directory, "0")
            if backups:
                path = os.path.join(self.config.directory, str(int(backups[-1])+1))
            os.mkdir(path)
            shutil.copy("server_level.dat", path)
            self.server.say("Backup %s saved." % str(int(backups[-1])+1))

class MessagePlugin(threading.Thread):
    IDENTIFIER = "MessagePlugin"
    def __init__(self, server, config):
        threading.Thread.__init__(self)
        self.server = server
        self.config = config
        self.stop = False

    def run(self):
        index = 0
        while not self.stop:
            time.sleep(self.config.interval)
            if self.stop:
                break
            self.server.say(self.config.messages[index])
            index += 1
            if index == len(self.config.messages):
                index = 0

class KickPlugin(threading.Thread):
    IDENTIFIER = "KickPlugin"
    def __init__(self, server, config):
        threading.Thread.__init__(self)
        self.server = server
        self.config = config
        self.stop = False

    def run(self):
        while not self.stop:
            time.sleep(0.1)
        for player in self.server.players:
            print "Kicking %s" % player
            self.server.kick(player)
# ---------------------------- PLUGINS --------------------------------------- #
RESTART_TIME = 3
COMMAND = ("java", "-cp", "minecraft-server.jar", "com.mojang.minecraft.server.MinecraftServer")
COMMANDS = {
    "!run": RunCommand,
    "!help": HelpCommand,
    "!quote": QuoteCommand,
    "!ban": BanCommand,
    "!kick": KickCommand,
    "!kill": KillCommand,
    "!sad": SadCommand,
    "!happy": HappyCommand,
    "!backup": BackupCommand,
    "!restore": RestoreCommand,
    "!8ball": EightBallCommand
}
PLUGINS = (
    BackupPlugin,
    MessagePlugin,
    KickPlugin
)
CONFIG = {
    "BackupPlugin": {
        "interval": 30 * 60,
        "directory": "backups"
    },
    "MessagePlugin": {
        "interval": 2 * 60,
        "messages": ("Running cMss 0.3.", "Visit http://minecraft.cryzed.de/ for more information.", "Enter !help for a list of available commands.")
    },
    "QuoteCommand": {
        "quotes": "quotes.txt"
    },
    "BackupCommand": {
        "directory": "backups"
    },
    "RestoreCommand": {
        "directory": "backups"
    },
    "EightBallCommand": {
        "responses": "eightball.txt"
    }
}
# ----------------------------- CONFIG --------------------------------------- #

def start_plugins(server):
    plugins = []
    for plugin in PLUGINS:
        if CONFIG.has_key(plugin.IDENTIFIER):
            plugins.append(plugin(server, Config(CONFIG[plugin.IDENTIFIER])))
        else:
            plugins.append(plugin(server, None))
        plugins[-1].start()
    return plugins

def stop_plugins(plugins):
    for plugin in plugins:
        plugin.stop = True
    time.sleep(3)
    return []

def run_command(command, server, output):
    if CONFIG.has_key(COMMANDS[command].IDENTIFIER):
        COMMANDS[command](server, output, Config(CONFIG[COMMANDS[command].IDENTIFIER]))
    else:
        COMMANDS[command](server, output, None)

class MinecraftServer(object):
    def __init__(self, process):
        self.process = process
        self.plugins = start_plugins(self)

    def op(self, name):
        self.stdin("/op %s\n" % message)

    def deop(self, name):
        self.stdin("/deop %s\n" % name)

    def kick(self, name):
        self.stdin("/kick %s\n" % name)

    def ban(self, name):
        self.stdin("/ban %s\n" % name)

    def banip(self, name):
        self.stdin("/banip %s\n" % name)

    def unban(self, name):
        self.stdin("/unban %s\n" % name)

    def say(self, message):
        self.stdin("/say %s\n" % message)

    def stdin(self, input):
        self.process.stdin.write(input)

    def shutdown(self):
        self.plugins = stop_plugins(self.plugins)
        self.process.terminate()

    def start(self):
        time.sleep(RESTART_TIME)
        self.process = subprocess.Popen(COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.plugins = start_plugins(self)

    @property
    def stdout(self):
        return self.process.stdout.readline().strip()

    @property
    def stderr(self):
        return self.process.stderr.readline().strip()

    @property
    def operators(self):
        with open("admins.txt") as operators:
            return (o for o in operators.read().splitlines() if o)

    @property
    def players(self):
        with open("players.txt") as players:
            return (p for p in players.read().splitlines() if p)

class Output(object):
    def __init__(self, output):
        self.output = output.split()

    @property
    def time(self):
        return self.output[0]

    @property
    def name(self):
        return self.output[1]

    @property
    def action(self):
        return self.output[2][:-1]

    @property
    def message(self):
        return " ".join(self.output[3:])

class Config(object):
    def __init__(self, config):
        for key, value in config.items():
            setattr(self, key, value)

def main():
    server = MinecraftServer(subprocess.Popen(COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE))
    if not os.path.exists("minecraft.log"):
        log = open("minecraft.log", "w")
    log = open("minecraft.log", "a")
    print "Starting plugins..."
    log.write("Starting plugins...\n")
    log.flush()
    while True:
        try:
            output = server.stderr
            if not output:
                continue
            print output
            log.write("%s\n" % output)
            log.flush()
            if "says:" in output or "admins:" in output:
                output = Output(output)
                command = output.message.split()[0]
                if COMMANDS.has_key(command):
                    run_command(command, server, output)
            elif "Exception" in output.split()[0]:
                print "Fatal exception occured, restarting server. (%s...)" % output
                log.write("Fatal exception occured, restarting server. (%s...)\n" % output)
                print "Stopping plugins..."
                log.write("Stopping plugins...\n")
                log.flush()
                server.shutdown()
                server.start()
                print "Starting plugins..."
                log.write("Starting plugins...\n")
                log.flush()
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
