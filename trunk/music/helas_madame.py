import sys
from music import NoteMixture, make_piano_melody, SAMPLE_RATE


def helas_madame():
    minim_length=6/6.0
    bar_length = minim_length*4
    
    soprano = []
    alto = []
    tenor = []
    bass = []
    
    #0 - 1
    soprano.append("""
T4 Bb1 T2 Bb1 Bb1
T6 A1 T2 Bb1
T2 A1 G G F#
T8 G
""")
    alto.append("""
T4 D1 T2 D1 D1
T6 C1 T2 D1
T1 C1 Bb1 A1 G T2 A1 A1
T8 G
""")
    tenor.append("""
T3 G T1 F G A1 Bb1 C1
T1 D1 E1 T4 F1 T2 G1
T2 F1 Eb1 T3 D1 T1 D1
T8 D1
""")
    bass.append("""
T3 G-2 T1 A-1 Bb-1 C-1 D-1 E-1
T6 F-1 T2 Bb-1
T2 F-1 G-1 D-1 D-1
T8 G-2
""")

    #1 - 5
    soprano.append("""
T4 Bb1 T2 Bb1 Bb1
T1 A1 G A1 Bb1 T2 A1 Bb1
T2 A1 G G F#
T4 G T2 , G
""")
    alto.append("""
T4 D1 T2 D1 D1
T6 C1 T2 D1
T2 C1 Bb1 A1 A1
T4 G T2 , G
""")
    tenor.append("""
T4 Bb1 T2 Bb1 Bb1
T6 F1 T2 G1
T2 F1 Eb1 T3 D1 T1 D1
T4 D1 T2 , Bb1
""")
    bass.append("""
T4 G-1 T2 G-1 G-1
T1 F-1 E-2 F-1 G-1 T2 F-1 Bb-1
T2 F-1 G-1 D-1 D-1
T4 G-2 T2 , G-1
""")

    #2 - 9
    soprano.append("""
T2 G F G A1
T4 Bb1 T2 Bb1 Bb1
T2 C1 Bb1 Bb1 A1
T4 Bb1 T2 , Bb1
""")
    alto.append("""
T3 Bb1 T1 A1 T2 Bb1 C1
T4 D1 T2 D1 D1
T3 Eb1 T1 D1 T2 C1 C1
T6 Bb1 T2 Bb1
""")
    tenor.append("""
T2 D1 D1 T1 D1 C1 D1 E1
T4 F1 T2 F G
T2 C1 T1 F G A1 F T2 F1
T6 D1 T2 D1
""")
    bass.append("""
T2 G-1 D-1 G-1 F-1
T4 Bb-1 T2 Bb-1 Bb-1
T2 A-1 Bb-1 T3 F-1 T0.5 E-1 F-1
T2 G-1 T1 F-1 E-1 D-1 C-1 T2 Bb-1
""")

    #3 - 13
    soprano.append("""
T3 Bb1 T1 Bb1 T2 Bb1 Bb1
T6 A1 T2 Bb1
T2 A1 G G F#
T6 G T2 G
""")
    alto.append("""
T3 D1 T1 D1 T2 D1 D1
T6 C1 T2 D1
T1 C1 Bb1 A1 G T2 A1 A1
T6 G T2 G
""")
    tenor.append("""
T2 D1 T1 G F G A1 Bb1 C1
T1 D1 E1 T4 F1 T2 G1
T2 F1 Eb1 T3 D1 T1 D1
T8 D1
""")
    bass.append("""
T3 G-2 T1 A-1 Bb-1 C-1 D-1 E-1
T6 F-1 T2 Bb-1
T2 F-1 G-1 T3 D-1 T1 D-1
T8 G-2
""")

    #4 - 17
    soprano.append("""
T3 Bb1 T1 Bb1 T2 Bb1 Bb1
T1 A1 G A1 Bb1 T2 A1 Bb1
T2 A1 G G F#
T8 G
""")
    alto.append("""
T2 G G T6 D1
T2 D1 C1 D1
T2 C1 Bb1 A1 A1
T8 G
""")
    tenor.append("""
T3 Bb1 T1 Bb1 T2 Bb1 Bb1
T6 F1 T2 G1
T2 F1 Eb1 T3 D1 T1 D1
T8 D1
""")
    bass.append("""
T4 G-1 T2 G-1 G-1
T1 F-1 E-1 F-1 G-1 T2 F-1 Bb-1
T2 F-1 G-1 D-1 D-1
T8 G-2
""")

    print >>sys.stderr, 'Parsing %d lines' % len(soprano)
    
    n = NoteMixture()
    for series in [soprano, alto, tenor, bass][0:4]:
        mix = NoteMixture()
        series = series[0:]
        for line in series:
            try:
                line_note = make_piano_melody(line, duration=minim_length)
            except ValueError, ex:
                print >>sys.stderr, "Error parsing: [%s]" % line
                raise
            minim_count = line_note.length/SAMPLE_RATE/minim_length
            if minim_count % 4 != 0:
                print >>sys.stderr, "Warning: bar length is: %d minims" % minim_count
            mix.append_note(line_note)
        n.append_note(mix, offset=0)
    
    n = n.collapse().trim()
    print >>sys.stderr, 'Total of %d notes' % len(n.list)
    return n


if __name__ == '__main__':
    helas_madame().play()
