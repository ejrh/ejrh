class Controller(object):
    """Something that participates in an IRC session, at a higher level
    than the IRC client (and IRC connection).
    
    The program should ideally subclass this with a controller that actually
    does something.  This is a base version that implements the various
    callbacks but doesn't do much except maintain some state."""
    
    def __init__(self):
        pass
    
    def observe_person(self, channel, prefix, name):
        print 'See %s in %s' % (name, channel)
        
    def observe_message(self, sender, recipient, text):
        print '%s says to %s, "%s"' % (sender, recipient, text)
        
    def observe_action(self, sender, recipient, action):
        print '%s does to %s, "%s"' % (sender, recipient, action)
