import sys
import re

class Data(object):
    def __init__(self):
        self.name = None
        self.pos = (None, None, None)
        self.vel = (None, None, None)
        self.mass = None
        self.radius = None

def coalesce_params(params):
    p = params[0]
    if p is None:
        p = ""
    new_params = [p]
    for p in params[1:]:
        if p is None:
            p = 0.0
        new_params.append(p)
    return tuple(new_params)

def print_data(data):
    params = (data.name, data.pos[0], data.pos[1], data.pos[2], data.vel[0], data.vel[1], data.vel[2], data.mass, data.radius)
    params = coalesce_params(params)
    print """{ "%s", { %1.48e, %1.48e, %1.48e }, { %1.48e, %1.48e, %1.48e }, %1.48e, %1.48e },""" % params

name_re = re.compile(r'[^:]*:\s*([^(]+).*')

def parse_name(data):
    m = name_re.match(data)
    g = m.groups()
    name = g[0].strip()
    return name

with_units_re = re.compile(r'\s*[^(=]+(\s+\(([^)]+)\))(,mean)?\s+=\s*([0-9.]*).*')
sn_units_re = re.compile(r'10\^([0-9]+) (.+)')

def parse_with_units(data):
    m = with_units_re.match(data)
    g = m.groups()
    amt, units = g[3], g[1]
    if amt == '':
        return None
    amt = convert_units(float(amt), units)
    return amt

def convert_units(val, units):
    m = sn_units_re.match(units)
    if m:
        g = m.groups()
        power = int(g[0])
        units = g[1].strip()
        val *= 10**power
    if units == 'km':
        val *= 1000
    elif units == 'g':
        val /= 1000
    elif units == 'kg':
        val *= 1
    else:
        raise Exception("Unconvertible units: '%s'" % units)
    return val

def parse_orbitals(l, units):
    if units == 'KM-S':
        pos_scale = 1000
        vel_scale = 1000
    else:
        raise Exception("Unconvertible orbital units: '%s'" % units)
    parts = l.split(',')
    pos = float(parts[2]) * pos_scale, float(parts[3]) * pos_scale, float(parts[4]) * pos_scale
    vel = float(parts[5]) * vel_scale, float(parts[6]) * vel_scale, float(parts[7]) * vel_scale
    return pos, vel

def parse_file(filename):
    
    d = Data()

    orbital_units = None
    
    f = open(filename)
    line_num = 0
    for l in f:
        l = l.strip('\r\n')
        line_num += 1
        try:
            if l == ' SATELLITE PHYSICAL PROPERTIES:':
                pass
            elif l.startswith('  Mean Radius') or l.startswith('  Radius'):
                d.radius = parse_with_units(l)
            elif l.startswith('  Mass'):
                d.mass = parse_with_units(l)
            elif l.startswith('Target body name: '):
                d.name = parse_name(l)
            elif l.startswith('Output units'):
                orbital_units = l.split(':')[1].strip()
            elif l == '$$SOE':
                l = f.next()
                d.pos, d.vel = parse_orbitals(l, orbital_units)
        except Exception, ex:
            print '%s:%d: %s' % (filename, line_num, ex)
            print 'Line was: %s' % l

    f.close()
    
    #print """/* %s */""" % filename
    print_data(d)


for fn in sys.argv[1:]:
    parse_file(fn)
