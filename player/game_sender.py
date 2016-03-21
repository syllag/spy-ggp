import argparse
import urllib.request
import sys
import hashlib

import woodstock.tools.gdl_tools as gdl_tools

#
#
# TODO --id_match
#
#


URL = 'http://localhost:8080'
GDL = None
ROLES = []
ROLE = ''
START_CLOCK = 10
PLAY_CLOCK  = 5
MATCH_ID = ''


def do_play(st = '(fake1 play1) (fake2 play2) (fake3 play3)'):
    msg = str.format('(play {0})', st)

    res = urllib.request.urlopen(URL, msg.encode())
    body = res.read()

    return body.decode()


# (PLAY <MATCHID> <TURN> <LASTMOVE> <PERCEPTS>)
def do_play2(st = 'fake1 12 (do something) ((fluent 1 ex) ( fluent2 2) fluent3 (play  somebody (do something else) ))'):
    msg = str.format('(play {0})', st)

    res = urllib.request.urlopen(URL, msg.encode())
    body = res.read()

    return body.decode()


def do_info():
    print(URL)

    res = urllib.request.urlopen(URL, b'(info)')
    body = res.read()

    return body.decode()


def do_get(path = '/'):
    res = urllib.request.urlopen(URL + path)
    body = res.read()

    return body.decode()


def do_abort(st = ''):
    global MATCH_ID
    if MATCH_ID == '':
        MATCH_ID = hashlib.md5(file_content.encode()).hexdigest()

    msg = str.format('(abort {0})', MATCH_ID)

    res = urllib.request.urlopen(URL, msg.encode())

    body = res.read()

    return body.decode()

def do_stop(st = ''):
    global MATCH_ID
    if MATCH_ID == '':
        MATCH_ID = hashlib.md5(file_content.encode()).hexdigest()

    msg = str.format('(stop {0} nil)', MATCH_ID)
    res = urllib.request.urlopen(URL, msg.encode())

    body = res.read()

    return body.decode()

# (STOP <MATCHID> <TURN> <LASTMOVE> <PERCEPTS>)
def do_stop2(st = ''):
    global MATCH_ID
    if MATCH_ID == '':
        MATCH_ID = hashlib.md5(file_content.encode()).hexdigest()

    msg = str.format('(stop {0} nil)', MATCH_ID)
    res = urllib.request.urlopen(URL, msg.encode())

    body = res.read()

    return body.decode()



def do_start(st = '', role = 'unknown', start_clock = 60, play_clock = 10):
    global MATCH_ID
    if MATCH_ID == '':
        MATCH_ID = hashlib.md5(file_content.encode()).hexdigest()

    msg = str.format('(start {0} {1} ({2}) {3} {4})', MATCH_ID, role, st, start_clock, play_clock)
    res = urllib.request.urlopen(URL, msg.encode())
    body = res.read()

    return body.decode()


def load_kif(filename):
    global GDL, ROLES
    GDL = gdl_tools.GDL_Object(filename = filename)
    ROLES = GDL.find_roles()

    return GDL.get_gdl_compact()


def test():
    print(do_info())
    print(do_get())
    print(load_kif('tst/backgammon.kif'))


def treat_args():
    parser = argparse.ArgumentParser(description='Send command to server')

    parser.add_argument('command', metavar='COMMAND', choices=['get', 'start', 'stop','info', 'abort', 'play', 'play2'], help = 'start, stop, get, info, abort, play, play2')
    parser.add_argument('--url', help='provide URL of the server (by default http://localhost:8080)', default='http://localhost:8080')

    parser.add_argument('--kif', metavar='KIF_FILENAME', help='kiff filename, necessary for start and abort', type = argparse.FileType('r'), nargs = 1)
    parser.add_argument('--role', help='considered role (by default first role in file)', type = str, nargs = 1)
    parser.add_argument('--start_clock', help='start clock value in s (by default 60)', type = int, nargs = 1)
    parser.add_argument('--play_clock', help='play clock value in s (by default 10)', type = int, nargs = 1)
    parser.add_argument('--match_id', help='id of the considered match', type = str, nargs = 1)
    parser.add_argument('--play_content', help='play content', type = str, nargs = 1)

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = treat_args()

    if args.url:
        URL = args.url

    if args.command == 'abort':
        file_content = ''

        if args.match_id:
            MATCH_ID = args.match_id[0]
        elif args.kif:
            file_content = args.kif[0].read()
        else:
            print('error: no given kif filename or match id')
            sys.exit(-1)

        GDL = gdl_tools.GDL_Object(file_content)
        print(do_abort(GDL.get_gdl_compact()))

    elif args.command == 'stop':
        file_content = ''

        if args.match_id:
            MATCH_ID = args.match_id[0]
        elif args.kif:
            file_content = args.kif[0].read()
        else:
            print('error: no given kif filename or match id')
            sys.exit(-1)

        GDL = gdl_tools.GDL_Object(file_content)
        print(do_stop(GDL.get_gdl_compact()))

    elif args.command == 'start':
        file_content = ''

        if args.kif:
            file_content = args.kif[0].read()
        else:
            print('error: no given kif filename')
            sys.exit(-1)

        if args.match_id:
            MATCH_ID = args.match_id[0]

        if args.start_clock:
            START_CLOCK = args.start_clock[0]
        if args.play_clock:
            PLAY_CLOCK = args.play_clock[0]

        GDL = gdl_tools.GDL_Object(file_content)
        ROLES = GDL.find_roles()

        if args.role:
            if args.role[0] in ROLES:
                ROLE = args.role[0]
            else:
                print("Error: role " + args.role[0] + " not found.")
                sys.exit(-1)
        elif len(ROLES) > 0:
            ROLE = ROLES[0]
        else:
            print("Error: no role found." )
            sys.exit(-1)

        print(do_start(GDL.get_gdl_compact(), ROLE, START_CLOCK, PLAY_CLOCK))

    elif args.command == 'info':
        print(do_info())

    elif args.command == 'get':
        print(do_get())

    elif args.command == 'play':
        if args.play_content:
            print(args.play_content[0])
            print(do_play(args.play_content[0]))
        else:
            print(do_play())

    elif args.command == 'play2':
        if args.play_content:
            print(args.play_content[0])
            print(do_play2(args.play_content[0]))
        else:
            print(do_play2())


