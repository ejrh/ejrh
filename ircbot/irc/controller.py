class Context(object):
    """The context of a message in an IRC channel, that the Bot or a Handler might want to respond to."""

    def __init__(self, bot, client, channel=None, nick=None):
        self.bot = bot
        self.client = client
        self.channel = channel
        self.nick = nick

    def speak(self, text):
        """Speak in reply to whomever or whatever originated the message."""
        
        if self.channel is not None:
            recipient = self.channel
        else:
            recipient = self.nick
        self.client.speak(recipient, text)

    def act(self, action):
        """Act in response to whomever or whatever originated the message."""
        
        if self.channel is not None:
            recipient = self.channel
        else:
            recipient = self.nick
        self.client.act(recipient, action)


class Controller(object):
    """Something that participates in an IRC session, at a higher level
    than the IRC client (and IRC connection).
    
    The program should ideally subclass this with a controller that actually
    does something.  This is a base version that implements the various
    callbacks but doesn't do much except maintain some state."""
    
    def __init__(self):
        pass
    
    def handle_person(self, channel, name):
        pass
    
    def handle_message(self, context, text):
        pass
    
    def handle_action(self, context, action):
        pass
    
    def observe_person(self, client, channel, prefix, name):
        print 'See %s in %s' % (name, channel)
        
        self.handle_person(channel, name)
        
    def observe_message(self, client, sender, recipient, text):
        print '%s says to %s, "%s"' % (sender, recipient, text)
        
        context = Context(self, client)
        if recipient[0] == '#':
            context.channel = recipient
        context.nick = sender
        context.text = text
        
        self.handle_message(context, text)

    def observe_action(self, client, sender, recipient, action):
        print '%s does to %s, "%s"' % (sender, recipient, action)
        
        context = Context(self, client)
        if recipient[0] == '#':
            context.channel = recipient
        context.nick = sender
        context.action = action
        context.text = '%s %s' % (sender, action)
        
        self.handle_action(context, action)
