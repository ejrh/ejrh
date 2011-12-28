import sys
import socket

from debug import error, warn, notice
from message import Message, encode, decode
from replies import replies
from controller import Controller

DEFAULT_PORT = 6667

BUFFER_SIZE = 1024

READ_TIMEOUT = 5

class Connection(object):
    def __init__(self, addr=None):
        if addr is None:
            return
        
        if ':' in addr:
            self.host, self.port = addr.split(':')
        else:
            self.host, self.port = addr, DEFAULT_PORT
        
        self.socket = None
        self.buffer = ''

    def open(self):
        s = None
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
            except socket.error, msg:
                s = None
                continue
            
            try:
                s.connect(sa)
            except socket.error, msg:
                s.close()
                s = None
                continue
            
            break
        
        if s is None:
            raise Exception('Unable to connect to %s:%d' % (self.host, self.port))
        
        s.setblocking(True)
        self.socket = s
    
    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
    
    def read(self):
        while self.socket is not None and '\n' not in self.buffer:
            self.socket.settimeout(READ_TIMEOUT)
            try:
                input = self.socket.recv(BUFFER_SIZE)
            except socket.timeout:
                return None
            if len(input) == 0:
                self.close()
                break
            #print 'received "%s"' % input
            self.buffer = self.buffer + input.replace('\r\n', '\n')
        
        if '\n' in self.buffer:
            line,self.buffer = self.buffer.split('\n', 1)
        else:
            warn('No CRLF in buffer')
            line = self.buffer
        
        message = decode(line)
        notice('In: %s' % message)
        return message
    
    def send(self, message):
        if type(message) is str:
            line = message
        else:
            notice('Out: %s' % message)
            line = encode(message)
        while True:
            try:
                self.socket.send(line)
                break
            except socket.timeout:
                pass

STATE_START, STATE_OPEN, STATE_REGISTER, STATE_RUN, STATE_QUIT, STATE_CLOSE = range(6)

ACTION_PREFIX = '\x01ACTION '
ACTION_SUFFIX = '\x01'

class Client(object):
    
    def __init__(self):
        self.connection = None
        self.nick = None
        self.hostname = None
        self.servername = None
        self.realname = None
        self.state = STATE_START
        self.channels = {}
        self.send_queue = []
        self.controller = Controller()
    
    def connect(self, addr):
        conn = Connection(addr)
        conn.open()
        self.conn = conn
        self.state = STATE_OPEN
    
    def disconnect(self):
        self.conn.close()
        self.state = STATE_CLOSE
    
    def send(self, message):
        self.send_queue.append(message)
    
    def update(self):
        if self.state == STATE_OPEN:
            nick = Message(None, 'NICK', [self.nick])
            self.conn.send(nick)
        
            user = Message(None, 'USER', [self.nick, self.hostname, self.servername, self.realname])
            self.conn.send(user)
            
            self.state = STATE_REGISTER
        
        if self.state == STATE_RUN:
            while len(self.send_queue) > 0:
                message = self.send_queue.pop(0)
                self.conn.send(message)
        
        message = self.conn.read()
        if message is not None:
            self.process_message(message)
        
        if self.conn.socket is None:
            self.disconnect()
    
    def process_message(self, message):
        if self.state == STATE_REGISTER and message.command != 'NOTICE':
            self.state = STATE_RUN
        
        if message.command == 'RPL_TOPIC':
            channel = message.params[-2]
            self.channels[channel] = message.params[-1]
        elif message.command == 'RPL_NAMREPLY':
            channel = message.params[-2]
            self.channels[channel] = None
            for name in message.params[-1].split(' '):
                if name[0] in ['@', '+']:
                    prefix = name[0]
                    name = name[1:]
                else:
                    prefix = ''
                self.controller.observe_person(channel, prefix, name)
        elif message.command == 'PRIVMSG':
            name = message.prefix
            if '!' in name:
                name = name.split('!', 1)[0]
            recipient = message.params[0]
            text = message.params[-1]
            if text.startswith(ACTION_PREFIX) and text.endswith(ACTION_SUFFIX):
                action = text[len(ACTION_PREFIX):len(text) - len(ACTION_SUFFIX)]
                self.controller.observe_action(name, recipient, action)
            else:
                self.controller.observe_message(name, recipient, text)
        elif message.command == 'JOIN':
            name = message.prefix
            if '!' in name:
                name = name.split('!', 1)[0]
            channel = message.params[-1]
            self.controller.observe_person(channel, '', name)
        elif message.command == 'PING':
            server = message.params[-1]
            pong = Message(None, 'PONG', [self.servername, server])
            self.send(pong)            
    
    def speak(self, channel, text):
        privmsg = Message(None, 'PRIVMSG', [channel, text])
        self.send(privmsg)
    
    def act(self, channel, action):
        privmsg = Message(None, 'PRIVMSG', [channel, '%s%s%s' % (ACTION_PREFIX, action, ACTION_SUFFIX)])
        self.send(privmsg)
    
    def join(self, channel):
        join = Message(None, 'JOIN', [channel])
        self.send(join)
    
    def part(self, channel):
        part = Message(None, 'PART', [channel])
        self.send(part)
    
    def quit(self):
        quit = Message(None, 'QUIT', ['Bye!'])
        self.conn.send(quit)
        self.state = STATE_QUIT
    
    def run(self):
        while self.state != STATE_CLOSE:
            self.update()
