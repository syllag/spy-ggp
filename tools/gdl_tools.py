import re


class GDL_Parser:
    blanks = [' ', '\t', '\n']
    separators = ['(', ')'] + blanks
    keywords = ['role', 'does', 'true', 'legal', 'goal', 'terminal', 'base', 'input', 'random', 'sees']
    operators = ['<=', 'distinct', 'not']
    commands = ['start', 'info', 'play', 'stop', 'abort']

    def __init__(self):
        pass

    def verify_paren(self, st):
        n = 0

        for c in st:
            if c == '(':
                n += 1
            elif c == ')':
                n -= 1
                if n < 0:
                    return False
        return n == 0


    def parse_gdl(self,st):
        if self.verify_paren(st):
            return self.parse_gdl_rec(st.strip(), 0)[1][0]
        else:
            return None


    def parse_idf(self,st, idx):
        token = ''
        while(idx < len(st) and (st[idx] not in self.separators)):
            token += st[idx]
            idx += 1

        if token.lower() in self.keywords:
            token_type = 'K_' + token.upper()
        if token.lower() in self.commands:
            token_type = 'CMD_' + token.upper()
        elif token[0] == '?':
            token_type = 'VARIABLE'
        elif token.lower() in self.operators:
            token_type = 'OP'
        elif token.isnumeric():
            token_type = 'NUM'
        else:
            token_type = 'CONST'

        return idx, token, token_type


    def parse_gdl_rec(self, st, idx):
        i = idx

        res = []

        while(i < len(st)):
            if st[i] in self.blanks:
                i += 1
            elif st[i] == '(':
                i += 1
                i, sub = self.parse_gdl_rec(st, i)
                res.append((sub, 'CLAUSE'))
            elif st[i] == ')':
                i += 1
                return i, res
            else:
                i, idf, token_type = self.parse_idf(st, i)
                res.append((idf, token_type))
        return i, res


    def str_compact(self, expr):
        res = ''

        if expr[1] != 'CLAUSE':
            res += str(expr[0])
        else:
            res += '('
            l = expr[0]
            for i in range(0, len(l)):
                res += self.str_compact(l[i])
                if i < len(l) - 1:
                    if l[i][1] != 'CLAUSE' and l[i + 1][1] != 'CLAUSE':
                        res += ' '
            res += ')'
        return res

    def get_clauses_str_compact(self, expr_tree):
        res = []

        token, token_type = expr_tree

        if token_type == 'CLAUSE':
            for c in token:
                res.append(self.str_compact(c))

        else:
            return [expr_tree[0]]


        return res


class GDL_Object:
    def __init__(self, intial_data = '', filename = ''):
        self.raw = intial_data
        self.data = intial_data
        self.roles = None

        if filename != '':
            self.load_file(filename)

        self.remove_comments()
        self.clean()

        self.compute_version()

    def compute_version(self):
        for role in self.find_roles():
            if role.lower() == 'random':
                self.gdl_version = 2
                return

        if re.search('^\( <= \( sees ', self.data, re.IGNORECASE|re.MULTILINE):
            self.gdl_version = 2
        else:
            self.gdl_version = 1

    def __str__(self):
        return self.get_gdl_human_readable()#self.data

    def find_roles(self):
        if self.roles is None:
            self.roles = re.findall('^\s*\(\s*role\s*(\S+)\s*\)', self.data, re.IGNORECASE|re.MULTILINE)

        return self.roles

    def remove_comments(self):
        self.data = re.sub(';.*', '', self.raw, 0, re.MULTILINE)

    def load_file(self, filename):
        with open(filename, 'r') as myfile:
            self.raw = myfile.read()

    def clean(self):
        '''Une clause par ligne, séparation des token par un espace
        (ou la fin de ligne le cas échéant).'''

        nb_par = 0
        buffer = ''
        data = self.data

        # on ajoute des espaces de partout et on va à la ligne
        data = data.replace('\n', ' ')
        data = data.replace('\t', ' ')
        data = data.replace('\r', ' ')

        # passages à la ligne + espaces autour des parenthèses
        for c in data:
            if c == '(':
                nb_par += 1
                buffer += ' ' + c + ' '
            elif c == ')':
                nb_par -= 1
                buffer += ' ' + c + ' '

                if (nb_par == 0):
                    buffer += '\n'
                else:
                    buffer += ' '
            else:
                buffer += c

        assert(nb_par == 0)

        # suppression des espaces doubles
        while '  ' in buffer:
            buffer = buffer.replace('  ', ' ')

        # à virer: les lignes vides, les espaces en début et fin de ligne
        if len(buffer) == 0:
            return

        if  buffer[0] == ' ':
            buffer = buffer [1:]

        buffer = buffer.replace('\n ', '\n')
        buffer = buffer.replace(' \n', '\n')

        self.data = buffer


    def give_comments(self):
        return re.findall(';.*', self.raw, re.MULTILINE)

    def get_gdl_compact_with_eol(self):
        res = self.data.replace(' ( ','(')
        res = res.replace('( ','(')
        res = res.replace(' ) ',')')
        res = res.replace(' )',')')

        return res

    def get_gdl_compact(self):
        res = self.data.replace(' ( ','(')
        res = res.replace('( ','(')
        res = res.replace(' ) ',')')
        res = res.replace(' )',')')
        res = res.replace(')\n', ')')
        res = res.replace('\n', ' ')

        return res

    def get_gdl_human_readable(self):
        res = self.data.replace('( ','(')
        res = res.replace(' )',')')

        return res


if __name__ == '__main__':
    files = ['tst/knightsTourLarge.kif', 'tst/knightsTour.kif', 'tst/backgammon.kif', 'tst/stratego.kif', 'tst/mini.kif']

    for f in files:
        print("\n\n☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ " + f + " ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺ ☺\n\n")

        obj = GDL_Object(filename = f)

        print (obj)
        print (obj.get_gdl_compact_with_eol())
        print (obj.get_gdl_compact())
        print('roles: ' + str(obj.find_roles()))
        print('gdl_version: ' + str(obj.gdl_version))



# TODO one day...
# - verify
# • role only appears in the head of facts;
# • init only appears as head of clauses and does not depend on any of true, legal, does, next, sees, terminal, goal;
# • true only appears in the body of clauses;
# • does only appears in the body of clauses and does not depend on any of legal, terminal, goal;
# • next and sees only appear as head of clauses.
