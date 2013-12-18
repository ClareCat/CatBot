#!/usr/env python

import ConfigParser
import datetime
import functions
import sys
import time
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl
from twisted.python import log
from twisted.protocols.policies import TrafficLoggingFactory
from functions import Seen

class CatBot(irc.IRCClient):

    def __init__(self, nickname, password):
        self.nickname = nickname
        self.password = password
        self.seen = Seen()
    
    def dataReceived(self, bytes):
        print "Got", repr(bytes)
        # Make sure to up-call - otherwise all of the IRC logic is disabled!
        return irc.IRCClient.dataReceived(self, bytes)

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)     

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.setNick("CatBot")
        self.seen.load_dict()

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        self.seen.update_dict(user, msg, str(datetime.datetime.utcnow()))
        self.seen.store_dict()
        user = user.split('!', 1)[0]

        #Check to see if they're executing the user command
        if msg.startswith("!"):
            self.parseFunctions(user, channel, msg)

        # Check to see if they're sending me a private message
        elif channel == self.nickname:
            msg = "Go away"
            self.msg(user, msg)

        # Otherwise check to see if it is a message directed at me
        elif msg.startswith(self.nickname + ":"):
            msg = "Meow {usr}".format(usr=user)
            self.msg(channel, msg)

    def parseFunctions(self, user, channel, msg):
        """Executes all of the function commands"""

        if msg.startswith("!user"):
            msg = functions.get_user(msg)

        elif msg.startswith("!weather"):
            msg = functions.weather(msg)

        elif msg.startswith("!jerkcity"):
            msg = functions.jerkcity()

        elif msg.startswith("!seen"):
            msg = self.seen.get_seen(msg)

        else:
            msg = "Invalid Request"
        self.msg(channel, msg)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        self.seen.update_dict(user, msg, str(datetime.datetime.utcnow()))
        user = user.split('!', 1)[0]

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]

    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'


class CatBotFactory(protocol.ClientFactory):
    """
    A factory for CatBots.
    A new protocol instance will be created each time we connect to the server.
    """
    def __init__(self, config):
        self.channel = config.get("irc", "channel")
        self.nickname = config.get("irc", "nickname")
        self.password = config.get("irc", "password")

    def buildProtocol(self, addr):
        p = CatBot(self.nickname, self.password)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        print "Connection lost - goodbye!"
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)
    try:
        #open config file
        config = ConfigParser.ConfigParser()
        config.read(sys.argv[1])
        # create factory protocol and application
        f = CatBotFactory(config)
        # connect factory to this host and port
        reactor.connectSSL(config.get("irc", "host"), int(config.get("irc", "port")), f, ssl.ClientContextFactory())
        # run bot
        reactor.run()    
    except IndexError:
        print "Correct usage is python bot.py <config_filename.ini>"