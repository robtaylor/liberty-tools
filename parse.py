#--------------------------------------------------------------------------
# Originally Written by Tim Edwards
# efabless, inc. 2017
# May 17, 2017
# Updated Dec. 22, 2018 to accomodate in-lined standard cell subcircuits
# (i.e., not from a .include statement) and corrected duplicate .end statement.
#
# This script is in the public domain
#--------------------------------------------------------------------------

import re
import sys

def parse_pin(function):
    # Handle n' as way of expressing ~n or !n
    primerex = re.compile('([^ \t]+)[ \t]*\'')
    outparenrex = re.compile('^[ \t]*\([ \t]*(.+)[ \t]*\)[ \t]*$')
    parenrex = re.compile('\([ \t]*([^ \t\)|&~^]+)[ \t]*\)')
    pstring = function.strip().strip('"').strip()
    pstring = pstring.replace('*', '&').replace('+', '|').replace('!', '~')
    pstring = outparenrex.sub('\g<1>', pstring)
    pstring = parenrex.sub('\g<1>', pstring)
    pstring = primerex.sub('~\g<1>', pstring)
    return pstring

def read_liberty(filein, debug):
    global vdd

    celldefs = {}
    voltrex  = re.compile('[ \t]*nom_voltage[ \t]*:[ \t]*([^;]+);')
    cellrex  = re.compile('[ \t]*cell[ \t]*\(([^)]+)\)')
    pinrex   = re.compile('[ \t]*pin[ \t]*\(([^)]+)\)')
    busrex   = re.compile('[ \t]*bus[ \t]*\(([^)]+)\)')
    lat1rex  = re.compile('[ \t]*latch[ \t]*\(([^)]+)\)')
    lat2rex  = re.compile('[ \t]*latch[ \t]*\(([^, \t]+)[ \t]*,[ \t]*([^),]+)\)')
    ff1rex   = re.compile('[ \t]*ff[ \t]*\(([^)]+)\)')
    ff2rex   = re.compile('[ \t]*ff[ \t]*\(([^, \t]+)[ \t]*,[ \t]*([^),]+)\)')
    staterex = re.compile('[ \t]*next_state[ \t]*:[ \t]*([^;]+);')
    clockrex = re.compile('[ \t]*clocked_on[ \t]*:[ \t]*([^;]+);')
    setrex   = re.compile('[ \t]*preset[ \t]*:[ \t]*([^;]+);')
    resetrex = re.compile('[ \t]*clear[ \t]*:[ \t]*([^;]+);')
    datarex  = re.compile('[ \t]*data_in[ \t]*:[ \t]*([^;]+);')
    enarex   = re.compile('[ \t]*enable[ \t]*:[ \t]*([^;]+);')
    trirex   = re.compile('[ \t]*three_state[ \t]*:[ \t]*([^;]+);')
    funcrex  = re.compile('[ \t]*function[ \t]*:[ \t]*\"?[ \t]*([^"]+)[ \t]*\"?')
    with open(filein, 'r') as ifile:
        lines = ifile.readlines()
        if debug:
            print("Reading liberty file, " + str(len(lines)) + " lines.")
        for line in lines:
            vmatch = voltrex.match(line)
            if vmatch:
                vdd = float(vmatch.group(1))
                if debug:
                   print("Nominal process voltage is " + str(vdd))
                continue

            lmatch = cellrex.match(line)
            if lmatch:
                cellname = lmatch.group(1).strip('"')
                if debug:
                    print("Found cell " + cellname)
                cellrec = {}
                cellrec['inputs'] = []
                cellrec['outputs'] = []
                cellrec['nin'] = 0
                cellrec['nout'] = 0
                cellrec['function'] = []
                # NOTE:  average rise and fall times need to be
                # averaged from the data, to get a general relation
                # between timing and drive strength.
                cellrec['rise'] = 1.0
                cellrec['fall'] = 1.0
                cellrec['type'] = 'comb'
                celldefs[cellname] = cellrec
                continue

            pmatch = pinrex.match(line)
            if pmatch:
                pinname = pmatch.group(1)
                if debug:
                    print("Found input pin " + pinname)
                cellrec['inputs'].append(pinname)
                cellrec['nin'] += 1
                continue

            bmatch = busrex.match(line)
            if bmatch:
                pinname = bmatch.group(1)
                if debug:
                    print("Found input bus " + pinname)
                cellrec['inputs'].append(pinname)
                cellrec['nin'] += 1
                continue

            lmatch = lat2rex.match(line)
            if lmatch:
                if debug:
                    print("Found latch");
                cellrec['type'] = 'latch'
                cellrec['funcpos'] = lmatch.group(1)
                cellrec['funcneg'] = lmatch.group(2)
                continue

            lmatch = lat2rex.match(line)
            if lmatch:
                if debug:
                    print("Found latch");
                cellrec['type'] = 'latch'
                cellrec['funcpos'] = lmatch.group(1)
                continue

            rmatch = ff2rex.match(line)
            if rmatch:
                if debug:
                    print("Found flop");
                cellrec['type'] = 'flop'
                cellrec['funcpos'] = rmatch.group(1)
                cellrec['funcneg'] = rmatch.group(2)
                continue

            rmatch = ff1rex.match(line)
            if rmatch:
                if debug:
                    print("Found flop");
                cellrec['type'] = 'flop'
                cellrec['funcpos'] = rmatch.group(1)
                continue

            fmatch = funcrex.match(line)
            if fmatch:
                function = fmatch.group(1)
                if debug:
                    print("Found function " + function + " and output pin " + pinname)
                # If pin has a function, it's an output, not an input,
                # so add it to the outputs list and remove it from the
                # inputs list.
                cellrec['outputs'].append(pinname)
                cellrec['nout'] += 1
                cellrec['inputs'].remove(pinname)
                cellrec['nin'] -= 1
                cellrec['function'].append(function)
                continue

            smatch = staterex.match(line)
            if smatch:
                if debug:
                    print('Found data input')
                cellrec['data'] = parse_pin(smatch.group(1))
                continue

            cmatch = clockrex.match(line)
            if cmatch:
                if debug:
                    print('Found clock input')
                cellrec['clock'] = parse_pin(cmatch.group(1))
                continue

            smatch = setrex.match(line)
            if smatch:
                if debug:
                    print('Found set input ' + smatch.group(1))
                cellrec['set'] = parse_pin(smatch.group(1))
                continue

            rmatch = resetrex.match(line)
            if rmatch:
                if debug:
                    print('Found reset input ' + rmatch.group(1))
                cellrec['reset'] = parse_pin(rmatch.group(1))
                continue

            dmatch = datarex.match(line)
            if dmatch:
                if debug:
                    print('Found data input')
                cellrec['data'] = parse_pin(dmatch.group(1))
                continue

            ematch = enarex.match(line)
            if ematch:
                if debug:
                    print('Found enable input')
                cellrec['enable'] = parse_pin(ematch.group(1))
                continue

            tmatch = trirex.match(line)
            if tmatch:
                if debug:
                    print('Found tristate output')
                cellrec['tristate'] = parse_pin(tmatch.group(1))
                continue

            print(f"Unparsed: {line}")
    return celldefs


if __name__ == '__main__':

    options = []
    arguments = []
    for item in sys.argv[1:]:
        if item.find('-', 0) == 0:
            options.append(item)
        else:
            arguments.append(item)

    if '-debug' in options:
        debug = True
    else:
        debug = False

    # Timing options:  Pass timing and load values as the following:
    #
    #   -io_time=<value>  Rise and fall time for signals in and out of the digital block
    #   -time=<value>     Rise and fall time of gate outputs
    #   -idelay=<value>   Input delay at gate inputs
    #   -odelay=<value>   Throughput delay of the gate
    #   -cload=<value>    Gate output load capacitance
    #
    # Note that these are just average numbers for the process.  If not
    # specified, the defaults are as assigned below.

    io_time = '10n'
    time = '1n'
    idelay = '1n'
    odelay = '50n'
    cload = '1p'

    try:
        iotimeopt = next(item for item in options if item.startswith('-io_time='))
    except:
        pass
    else:
        io_time = iotimeopt.split('=')[1]

    try:
        timeopt = next(item for item in options if item.startswith('-time='))
    except:
        pass
    else:
        time = timeopt.split('=')[1]

    try:
        idelayopt = next(item for item in options if item.startswith('-idelay='))
    except:
        pass
    else:
        idelay = idelayopt.split('=')[1]

    try:
        odelayopt = next(item for item in options if item.startswith('-odelay='))
    except:
        pass
    else:
        odelay = odelayopt.split('=')[1]

    try:
        cloadopt = next(item for item in options if item.startswith('-cload='))
    except:
        pass
    else:
        cload = cloadopt.split('=')[1]

    timing = [io_time, time, idelay, odelay, cload]

    vdd = 3.0
    celldefs = {}
    if len(arguments) >= 3:
        print("Reading liberty netlist " + arguments[0])
        print("Reading spice netlist " + arguments[1])
        print("Writing xspice netlist " + arguments[2])
        for libfile in arguments[0].split():
            celldefs.update(read_liberty(libfile, debug))
        if len(arguments) >= 4:
            modelfile = arguments[3]
        else:
            modelfile = ''
        read_spice(arguments[1], arguments[2], celldefs, debug, modelfile, timing)
        print("Done.")
    elif len(arguments) == 2:
        # Library-only option
        print("Reading liberty netlist " + arguments[0])
        print("Writing xspice model library " + arguments[1])
        for libfile in arguments[0].split():
            celldefs.update(read_liberty(libfile, debug))
        write_lib(arguments[1], celldefs, debug, timing)
        print("Done.")
    else:
        print("Usage:")
        print("spi2xspice.py <liberty file> <input spice> <output spice> [<xspice lib>]")
        print("spi2xspice.py <liberty file> <output xspice lib>")

