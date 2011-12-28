from debug import error, warn, notice
from replies import replies


MAX_MESSAGE = 510


class Message(object):
    """A structured but largely uninterpreted representation of an IRC message."""
    
    def __init__(self, prefix, command, params=None):
        if params is None:
            params = []
        elif type(params) is str:
            params = [params]
        
        self.prefix = prefix
        self.command = command
        self.params = params
    
    def __eq__(self, other):
        if self.prefix != other.prefix:
            return False
        if self.command != other.command:
            return False
        if len(self.params) != len(other.params):
            return False
        for sp,op in zip(self.params, other.params):
            if sp != op:
                return False
        return True
    
    def __ne__(self, other):
        return not (self == other)
        
    def __str__(self):
        return '[%s %s [%s]]' % (self.prefix, self.command, ' '.join(["'%s'" % p for p in self.params]))


def decode(line):
    """Decode a text line into a Message object."""
    
    if len(line) == 0:
        warn('Empty message')
        return None
    
    # Read optional prefix
    if line[0] == ':':
        prefix,line = line[1:].split(' ', 1)
    else:
        prefix = None
    line = line.lstrip()
    
    # Read command
    if ' ' in line:
        command,line = line.split(' ', 1)
        line = line.lstrip()
    else:
        warn('No command')
        command = None
    
    # Read params
    params = []
    while len(line) > 0 and line[0] != ':':
        if ' ' in line:
            param,line = line.split(' ', 1)
        else:
            param = line
            line = ''
        params.append(param)
        line = line.lstrip()
        
    if len(line) > 0 and line[0] == ':':
        params.append(line[1:])
    else:
        warn('No trailing parameter')
    
    # Translate command
    try:
        num = int(command)
        name = replies[num]
        command = name
    except ValueError:
        pass
    except KeyError:
        pass
    
    message = Message(prefix, command, params)
    return message


def encode(message):
    """Encode a Message object into a text line."""
    
    line = ''
    if message.prefix is not None:
        line = ':%s ' % message.prefix
    line += ' %s' % message.command
    for i in range(len(message.params)):
        if i == len(message.params) - 1:
            line += ' :%s' % message.params[i]
        else:
            line += ' %s' % message.params[i]
    if len(line) > MAX_MESSAGE:
        warn('Message length is %d, truncating!' % len(line))
        line = line[:MAX_MESSAGE]
    
    return line + '\r\n'


def test_decode(line, expected):
    message = decode(line)
    if message != expected:
        error('Test failed: "%s" decoded to %s instead of %s' % (line, message, expected))


def test():
    test_decode(':prefix command :trailing param', Message('prefix', 'command', ['trailing param']))
    test_decode('command :trailing param', Message(None, 'command', ['trailing param']))
    test_decode('123 :trailing param', Message(None, '123', ['trailing param']))
    test_decode('command param :trailing param', Message(None, 'command', ['param', 'trailing param']))
    test_decode('command  param   :trailing param', Message(None, 'command', ['param', 'trailing param']))


if __name__ == '__main__':
    test()
