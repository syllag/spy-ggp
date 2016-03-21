from http.server import BaseHTTPRequestHandler, HTTPServer

import woodstock.tools.gdl_tools as gdl_tools
import re
import time
import ctypes
import getopt
import sys
import os
import pprint


CONFIG = {
    'NAME'     : 'Woodstock',
    'VERSION'  : '0.19.69',
    'IP'       : '', # correspond à INADDR_ANY
    'PORT'     : 8080,
    'DLL_PATH' : '/Users/sylvain/Work/git/phd_epiette/competition/woodstock/player/cpp', # Warning: pour linux chemin complet
    'DLL_NAME' : 'libfake_player.so',
    'LOG_LEVEL': 0,
    'GDL_VERSION': '1'
}

LOG_STACK = []

PROPERTIES = {
    'state': 'available', # autre état possible: 'busy', 'aborted', 'terminated'
    'current_id_match': '',
    'gdl': '',
    'nb_players': 0,
    'step': 0,
    'start_clock': 0,
    'play_clock': 0
}


GDL_PLAYER = None


def print_log_stack():
    pp = pprint.PrettyPrinter(indent=2)
    print()
    print('LOG_STACK')
    pp.pprint(LOG_STACK)
    print()


def do_info(args):
    assert(PROPERTIES['state'] == 'available' or PROPERTIES['state'] == 'busy')

    return PROPERTIES['state']


def do_start(args):
    if PROPERTIES['state'] == 'busy':
        msg = 'busy'

    else:
        PROPERTIES['state'] = 'busy'
        PROPERTIES['current_id_match'] = args['id_match']

        log('start', 'Starting match: '+ PROPERTIES['current_id_match'])

        PROPERTIES['gdl'] = gdl_tools.GDL_Object(args['gdl']) # TODO : directement le GDL_Object ?

        # TODO eval plus fine du delta/delay
        PROPERTIES['start_clock'] = args['start_clock']
        PROPERTIES['play_clock']  = args['play_clock']

        if min(PROPERTIES['start_clock'], PROPERTIES['play_clock']) > 3:
            delay = 2
        else:
            delay = 0.5

        parsing_time_in_millis = int((args['start_clock'] - delay) * 1000)
        choice_time_in_millis  = int((args['play_clock']  - delay) * 1000)

        gdl = PROPERTIES['gdl'].get_gdl_compact_with_eol()

        GDL_PLAYER.init_game(args['role'].encode(), gdl.encode(), parsing_time_in_millis, choice_time_in_millis)

        msg = 'ready'

    return msg


def do_play(args):
    current_id_match = PROPERTIES['current_id_match']

    if args['id_match'] != current_id_match:
        msg = 'busy'
    else:
        actions = parse_actions(args['actions'])

        if actions != None: # pas le premier coup
            PROPERTIES['step'] += 1

            nb_players = len(actions)

            array_actions_buff = (ctypes.c_char_p * nb_players)
            actions_buff = array_actions_buff()

            for i in range(nb_players):
                actions_buff[i] = actions[i].encode()

            GDL_PLAYER.update(actions_buff, nb_players)

        else:
            PROPERTIES['step'] = 0
            # pb workflow: a-t-on besoin d'un truc pour signaler qu'il faut jouer le premier coup ?
            # REPONSE: envoyer update(NULL, 0 (?) )
            pass

        # demande l'action à jouer
        buffer = ctypes.create_string_buffer(b"\0", 1024)
        GDL_PLAYER.play(buffer, 1024)

        msg = buffer.value.decode()
        log('play', msg)

    return msg


def do_play2(args):
    # print('properties:', PROPERTIES)
    # print('args', args)
    current_id_match = PROPERTIES['current_id_match']

    if args['id_match'] != current_id_match:
        msg = 'busy'
        return msg


    # mise à mise à jour de l'état:
    PROPERTIES['step'] = args['turn']

    # construction de l'array des percepts
    nb_percepts = len(args['percepts'])
    array_percepts_buff = (ctypes.c_char_p * nb_percepts)
    percepts_buff = array_percepts_buff()


    for i in range(nb_percepts):
        percepts_buff[i] = args['percepts'][i].encode()

    # update du joueur
    GDL_PLAYER.update2(args['last_move'].encode(), percepts_buff, len(args['percepts']), args['turn'])

    # demande l'action à jouer
    buffer = ctypes.create_string_buffer(b"\0", 1024)
    GDL_PLAYER.play(buffer, 1024)

    msg = buffer.value.decode()
    log('play', msg)

    return msg


def do_stop(args):
    if args['id_match'] != PROPERTIES['current_id_match']:
        msg = 'busy'
    else:
        PROPERTIES['state'] = 'available'
        PROPERTIES['step'] += 1
        actions = parse_actions(args['actions'])

        if actions is None:
            nb_players = 0
        else:
            nb_players = len(actions)

        array_actions_buff = (ctypes.c_char_p * nb_players)
        actions_buff = array_actions_buff()

        for i in range(nb_players):
            actions_buff[i] = actions[i].encode()

        GDL_PLAYER.end_of_game(actions_buff, nb_players)
        GDL_PLAYER.reset()

        global LOG_STACK
        LOG_STACK.append(PROPERTIES)

        msg = 'done'

    return msg


def do_stop2(args):
    if args['id_match'] != PROPERTIES['current_id_match']:
        msg = 'busy'
    else:
        # mise à mise à jour de l'état:
        PROPERTIES['step'] = args['turn']

        # construction de l'array des percepts
        nb_percepts = len(args['percepts'])
        array_percepts_buff = (ctypes.c_char_p * nb_percepts)
        percepts_buff = array_percepts_buff()


        for i in range(nb_percepts):
            percepts_buff[i] = args['percepts'][i].encode()

        # update du joueur
        GDL_PLAYER.end_of_game2(args['last_move'].encode(), percepts_buff, len(args['percepts']), args['turn'])


        msg = 'done'


    return msg





def do_abort(args):
    if args['id_match'] != PROPERTIES['current_id_match']:
        msg = 'busy'
    elif PROPERTIES['state'] == 'available':
        msg = 'busy'
    else:
        PROPERTIES['state'] = 'aborted'

        global LOG_STACK
        LOG_STACK.append(PROPERTIES)

        PROPERTIES['state'] = 'available'
        GDL_PLAYER.reset()
        msg = 'aborted'

    return msg


def do_preview(args):
    log('preview', 'TODO')
    # TODO: à traiter un jour...
    # TODO: interface avec Eric

    return 'done'


def parse_actions(actions_s):
    if actions_s.lower() == 'nil':
        return None

    # On enlève les parenthèses
    res = re.match('\(\s*(\S.*\S)\s*\)', actions_s)

    if res != None:
        actions_s = res.group(1)
    else: # on suppose que c'est le cas où il y a une action non parenthèsée...
        return [actions_s.strip()]

    # on vire les tabs
    actions_s = actions_s.replace('\t', ' ')

    # on ajoute des espaces autour des parentèses
    actions_s = actions_s.replace('(', ' ( ')
    actions_s = actions_s.replace(')', ' ) ')

    # on vire les espaces doubles
    while '  ' in actions_s:
        actions_s = actions_s.replace('  ', ' ')

    return re.findall('\([^\)]*\)|[^\(\)\s]+', actions_s)


def parse_request(request):
    request = request.decode()

    ### Calcul du nom de commande
    res = re.match('\(\s*(\S+).*\)', request, re.MULTILINE | re.DOTALL)
    if res != None:
        command = res.group(1).lower()
    else:
         return(None, None)

    ### Récupération des arguments
    args = {}
    if command == 'start':
        # TODO si problème...
        res = re.match('\(\s*\S+\s+(\S+)\s+(\S+)\s*\(\s*(.*)\s*\)\s+(\d+)\s+(\d+)\s*\)', request, re.MULTILINE | re.DOTALL)

        args['id_match'] = res.group(1)
        args['role'] = res.group(2)
        # TODO cleaner le GDL...
        args['gdl'] = res.group(3)
        args['start_clock'] = int(res.group(4))
        args['play_clock'] = int(res.group(5))

    elif command == 'play':
        # TODO si problème...
        if CONFIG['GDL_VERSION'] == '1':
           res = re.match('\(\s*\S+\s*(\S+)\s+(.*)\s*\)', request, re.MULTILINE | re.DOTALL)
           args['id_match'] = res.group(1)
           # TODO parser liste d'actions
           args['actions'] = res.group(2)

        elif CONFIG['GDL_VERSION'] == '2':
            res = re.match('\(\s*\S+\s+(\S+)\s+(\S+)\s+(.*)\)', request, re.MULTILINE | re.DOTALL)
            args['id_match'] = res.group(1)
            args['turn'] = res.group(2)

            raw_data = res.group(3)
            parser = gdl_tools.GDL_Parser()
            clauses = parser.get_clauses_str_compact(parser.parse_gdl('(' + raw_data + ')'))

            print(clauses)

            args['last_move'] = clauses[0]

            if str(clauses[1]).lower() == 'nil':
                args['percepts'] = []
            else:
                args['percepts'] = parser.get_clauses_str_compact(parser.parse_gdl(clauses[1]))


    elif command == 'stop':
        # TODO si problème...
        if CONFIG['GDL_VERSION'] == '1':
            res = re.match('\(\s*\S+\s+(\S+)\s+(.+)\s*\)', request, re.MULTILINE | re.DOTALL)
            args['id_match'] = res.group(1)
            args['actions'] = res.group(2)
        elif CONFIG['GDL_VERSION'] == '2':
            res = re.match('\(\s*\S+\s+(\S+)\s+(\S+)\s+(.*)\)', request, re.MULTILINE | re.DOTALL)
            args['id_match'] = res.group(1)
            args['turn'] = res.group(2)

            raw_data = res.group(3)
            parser = gdl_tools.GDL_Parser()
            clauses = parser.get_clauses_str_compact(parser.parse_gdl('(' + raw_data + ')'))

            args['last_move'] = clauses[0]

            if str(clauses[1]).lower() == 'nil':
                args['percepts'] = []
            else:
                args['percepts'] = parser.get_clauses_str_compact(parser.parse_gdl(clauses[1]))

    elif command == 'abort':
        # TODO si problème...
        if CONFIG['GDL_VERSION'] == '1':
            res = re.match('\(\s*\S+\s+(\S+)\s*\)', request, re.MULTILINE | re.DOTALL)
            args['id_match'] = res.group(1)
        elif CONFIG['GDL_VERSION'] == '2':
            raise NotImplementedError()

    return (command, args)


def log(log_type = "log", msg = "", level = 1):
    FG = {
#        'normal':   '\x1B[0m',
        'black':    '\033[30m',
        'red':      '\033[31m',
        'green':    '\x1B[32m',
        'yellow':   '\x1B[33m',
        'blue':     '\x1B[34m',
        'magenta':  '\x1B[35m',
        'cyan':     '\x1B[36m',
        'white':    '\x1B[37m'
    }

    MODE = {
        'reset' : '\033[0m',
        'bold'  : '\033[1m',
        'low'   : '\033[2m',
        'reverse':  '\037[2m'
    }

    if log_type == 'log':
        color = FG['yellow']
    elif log_type == 'starting...':
        color = FG['green']
    elif log_type == 'error':
        color = FG['red']
    elif log_type == 'send':
        color = FG['green']
    elif log_type == 'receive' or log_type == 'recv':
        color = FG['magenta']
    elif log_type == 'headers':
        if CONFIG['LOG_LEVEL'] > 0:
            color = FG['yellow']
        else:
            return
    else:
        color = FG['blue']

    now = time.time()
    year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
    date = "%04d/%02d/%02d|%02d:%02d:%02d" % (year, month, day, hh, mm, ss)

    head = date + ' ' + MODE['bold']+ str(log_type) + MODE['bold'] + MODE['reset']

    msg = str(msg)

    print(color + '[' + head  + color + ']' + MODE['reset'], msg)


class WoodstockHTTPRequestHandler(BaseHTTPRequestHandler):
    __version__ = CONFIG['VERSION']
    server_version = CONFIG['NAME'] + '-server/' + __version__
    protocol_version = 'HTTP/1.0'
    # protocol_version = 'HTTP/1.1'
    nb_GET = 0


    def send_msg(self, msg_s, keep_alive = False, content_type = 'text/acl'):
        msg_b = msg_s.encode()

        self.send_response(200, 'OK')
        self.send_header('Content-Length', len(msg_b))

        if keep_alive:
            self.send_header('Connection', 'keep-alive')
        else:
            self.send_header('Connection', 'close')

        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET')
        # self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        # self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # self.send_header('Access-Control-Allow-Age', '86400')

        self.send_header('Content-Type', content_type)
        self.end_headers()

        self.wfile.write(msg_b)
        self.wfile.flush()

        if content_type == 'text/acl':
            log('send', msg_s)


    def build_headers(self):
        dico = {}
        for k in self.headers:
            dico[k.lower()] = self.headers[k].lower()

        return dico


    def build_data(self, content_length):
        post_data = self.rfile.read(content_length)

        return post_data.strip(b' \t\n\r')


    def do_GET(self):
        name    = CONFIG['NAME']
        version = CONFIG['VERSION']

        msg  =  '\n☮ ☮ ☮  '+ name + ' is running !  ☮ ☮ ☮\n\n'
        msg += '♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬\n\n'

        for k in CONFIG:
            msg += k + ': ' + str(CONFIG[k]) + '\n'

        msg += '\n'

        for k in PROPERTIES:
            msg += k + ': '

            if k == 'gdl':
                msg += '\n'

            msg += str(PROPERTIES[k]) + '\n'


        log(msg = 'GET request from ' + str(self.client_address))


        with open('html/skeleton.html', 'r') as file:
            skeleton =  file.read()

        msg = str.format(skeleton, name + ' ' + version, msg)

        self.send_msg(msg, content_type = 'text/html')

    def do_OPTIONS(self):
        log(msg = 'OPTIONS request from ' + str(self.client_address))

        self.send_response(200, 'OK')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type, Accept, Origin')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()


    def do_POST(self):
        # log('receive', msg = str(self.requestline))
        # log ('receive', ' from ' + str(self.client_address))
        # log('headers', self.headers)

        headers = self.build_headers()
        request = self.build_data(int(headers['content-length']))


        log('recv', 'from ' + str(self.client_address[0]) + ':' + str (self.client_address[1]))
        log('headers', '\n' + str(self.headers))

        log('recv', request.decode())

        command, args = parse_request(request)

        if command == 'info':
            status = do_info(args)
            PROPERTIES['status'] = status
            msg_s = str.format('((name {0}) (status {1}) (version {2}))', CONFIG['NAME'], status, CONFIG['VERSION'])
        elif command == 'start':
            msg_s = do_start(args)
        elif command == 'play':
            if CONFIG['GDL_VERSION'] == '1':
                msg_s = do_play(args)
            elif CONFIG['GDL_VERSION'] == '2':
                msg_s = do_play2(args)

        elif command == 'stop':
            if CONFIG['GDL_VERSION'] == '1':
                msg_s = do_stop(args)
            elif CONFIG['GDL_VERSION'] == '2':
                msg_s = do_stop2(args)

        elif command == 'abort':
            msg_s = do_abort(args)

        # TODO: preview OPTIONAL

        else:
            log('error', 'unkown command: ' + command)
            msg_s = '()'

        self.send_msg(msg_s)


    ### Pour supprimer les logs de la classe mère
    def log_message(self, format, *args):
         pass


def usage():
    print('usage: python3 ' + __file__ + ' [-h|--help] [--lib_path=path] [--lib_name=name] [-i|--interface=ip] [-p|--port=port] [-l|--loglevel=level] [--gdl_version=version]')


def treat_opts(argv):
    try:
        opts, args = getopt.getopt(argv, 'hp:i:l::', ['help', 'lib_path=','lib_name=', 'port=', 'interface=', 'loglevel=', 'gdl_version='])

    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(-1)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt == '--lib_path':
            CONFIG['DLL_PATH']  = os.path.normpath(arg)
            print(CONFIG)
        elif opt == '--lib_name':
            CONFIG['DLL_NAME']  = arg
        elif opt == '--gdl_version':
            CONFIG['GDL_VERSION']  = arg
        elif opt in ('--port', '-p'):
            CONFIG['PORT']      = int(arg)
        elif opt in ('--interface', '-i'):
            CONFIG['IP']        = arg
        elif opt in ('loglevel=', '-l'):
            CONFIG['LOG_LEVEL'] = int(arg)


def run(server_class, handler_class):
    log('starting...', '☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮')
    log('starting...', '☮                   ☮')
    log('starting...', '☮     ' + CONFIG['NAME'] + '     ☮')
    log('starting...', '☮                   ☮')
    log('starting...', '☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮ ☮')
    log('starting...', '')
    log('starting...', '♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ♩ ♪ ♫ ♬ ')
    log('starting...', '')

    server_address = (CONFIG['IP'], CONFIG['PORT'])
    if CONFIG['IP'] == '':
        interface = 'INET_ADDR_ANY'
    else:
        interface = str(CONFIG['IP'])

    log('starting...', 'listening on ' + interface + ':' + str(CONFIG['PORT']))

    # Gestion du joueur CPP
    global GDL_PLAYER

    lib_location = os.path.join(CONFIG['DLL_PATH'], CONFIG['DLL_NAME'])
    log('starting...', 'loading lib ' + lib_location)
    ctypes.cdll.LoadLibrary(lib_location)

    GDL_PLAYER = ctypes.CDLL(lib_location)

    GDL_PLAYER.init_player();

    log('starting...', 'GDL player initialized')

    try:
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()
    except KeyboardInterrupt:
        log('KeyboardInterrupt', 'Bye...')
        print_log_stack()
        print()



if __name__ == '__main__':
    treat_opts(sys.argv[1:])
    run(HTTPServer, WoodstockHTTPRequestHandler)
