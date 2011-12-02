#!/usr/bin/python

class VertexKind(object):
    GOLD    = 0x01
    BARRIER = 0x02
    EMPTY   = 0x04
    START   = 0x08
    FINISH  = 0x10
    DANGER  = 0x20
    
    @classmethod
    def to_string(cls, value):
        if not isinstance(value, int):
            raise TypeError('Expecting integer argument')
        result = [ k for (k,v) in cls.__dict__.iteritems() if v == value ]
        if len(result) == 0: return None
        else: return result[0]
    
    def __init__(self, value):
        if VertexKind.to_string(value) is None:
            raise TypeError('Unknown token kind')
        self.value = value
    def __str__(self):
        return '%s' % VertexKind.to_string(self.value)
    def __repr__(self):
        return '<VertexKind %s>' % str(self)
    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        elif isinstance(other, VertexKind):
            return self.value == other.value
        else:
            raise TypeError('Wrong comparison')

class Token(object):
    def __init__(self, row, col, kind):
        if not isinstance(kind, VertexKind):
            kind = VertexKind(kind)
        self.row = row
        self.col = col
        self.kind = kind
    def __str__(self):
        return '%s at (%d, %d)' % (str(self.kind), self.row, self.col)
    def __repr__(self):
        return '<Token %s>' % str(self)

class Vertex(object):
    def __init__(self, token):
        if not isinstance(token, Token) and not isinstance(token, Vertex):
            raise TypeError('Expecting instance of class "Token" or "Vertex"')
        self.kind = token.kind
        self.col = token.col
        self.row = token.row
        self.edges = []
        self.dropped = False
    def add_edge(self, edge):
        self.edges += edge,
    def drop(self):
        for e in list(self.edges):
            e.drop()
        self.dropped = True
    def __str__(self):
        return '%s at (%d, %d)' % (str(self.kind), self.row, self.col)
    def __repr__(self):
        return '<Vertex %s>' % str(self)
    def __eq__(self, other):
        if isinstance(other, Vertex):
            return (self.kind == other.kind) and ((self.row, self.col) == (other.row, other.col))
        else: return False



class Edge(object):
    def __init__(self, node1, node2):
        if not isinstance(node1, Vertex) or not isinstance(node2, Vertex):
            raise TypeError('Expecting instance of class Vertex')
        self.nodes = (node1, node2)
        node1.add_edge(self)
        node2.add_edge(self)
        self.dropped = False
    def drop(self):
        for n in self.nodes:
            n.edges.remove(self)
        self.nodes = ()
        self.dropped = True
    def other(self, node):
        return self.nodes[self.nodes.index(node)^1]
    def __str__(self):
        return '[%s]_[%s]' % self.nodes
    def __repr__(self):
        return '<Edge %s>' % str(self)
    def __eq__(self, other):
        if isinstance(other, Edge):
            if self.nodes == () or other.nodes == ():
                return self.__class__.__base__.__eq__(other)
            return (((self.nodes[0] == other.nodes[0]) and (self.nodes[1] == other.nodes[1])) or 
                   ((self.nodes[0] == other.nodes[1]) and (self.nodes[1] == other.nodes[0])))
        else: return False

class Graph(object):
    def __init__(self, edges, verticles, attributes):
        self.edges = edges
        self.verticles = verticles
        self.attributes = attributes
    def drop(self, item):
        if isinstance(item, Vertex):
            item.drop()
            self.validate()
        elif isinstance(item, Edge):
            item.drop()
            self.validate()
        else:
            raise TypeError('Expecting instance of class Vertex or Edge')
    def filter(self, kind, cls = Vertex, exclude = False):
        if cls == Vertex:
            return [ v for v in self.verticles if exclude ^ (v.kind == kind) ]
        elif cls == Edge:
            s = set()
            for vert in ( v for v in self.verticles if exclude ^ (v.kind == kind) ):
                s.update(vert.edges)
            return list(s)
        else:
            raise TypeError('Expecting class Edge or Vertex')
    def validate(self):
        for e in list(self.edges):
            if e.dropped: self.edges.remove(e)
        for v in list(self.verticles):
            if v.dropped: self.verticles.remove(v)
    def __str__(self):
        return '%d edges, %d verticles' % (len(self.edges), len(self.verticles))
    def __repr__(self):
        return '<Graph %s>' % str(self)
    def __eq__(self, other):
        if isinstance(other, Graph):
            s = list(self.verticles); o = list(other.verticles)
            for v in self.verticles:
                if v in other.verticles:
                    s.remove(v); o.remove(v)
            ignore = self.attributes['ignore'] if 'ignore' in self.attributes else None
            if ignore:
                result = (0 == len( v for v in o+s if not v.kind in ignore ))
            else:
                result = 0 == (len( s ) + len( o ))
            s = list(self.edges); o = list(other.edges)
            for v in self.edges:
                if v in other.edges:
                    s.remove(v); o.remove(v)
            if ignore:
                result &= 0 == len(v for v in o+s if not ((v.nodes[0].kind in ignore) or (v.nodes[1].kind in ignore)))
            else:
                result &= 0 == (len( s ) + len( o ))
            return result
        else: return False


class Parser:
    import sys
    TOKENS = {
        '#': VertexKind.BARRIER,
        'G': VertexKind.GOLD, 
        '-': VertexKind.EMPTY, 
        'S': VertexKind.START, 
        'D': VertexKind.FINISH, 
        'E': VertexKind.DANGER
        }
    def __init__(self, infile = sys.stdin):
        self.tokens = []
        self.rowCount = int(infile.readline())
        self.colCount = int(infile.readline())
        self.cols = dict((i, []) for i in range(self.colCount))
        self.rows = dict((i, []) for i in range(self.rowCount))
        for row in range(self.rowCount):
            col = 0
            for token in infile.readline():
                if col >= self.colCount: break
                token = Token(row, col, Parser.TOKENS[token])
                self.cols[col] += token,
                self.rows[row] += token,
                self.tokens += token,
                col += 1
        self.attributes = { 'thiefs': int(infile.readline()), 'accuracy': float(infile.readline()) }
    
    def graph(self):
        verticles = []
        edges = []
        d = {}
        for t in self.tokens:
            v = Vertex(t)
            d[t] = v
            verticles += v,
        for (colnum, values) in self.cols.iteritems():
            tokens = list(values)
            last = d[tokens.pop(0)]
            while len(tokens) > 0:
                v = d[tokens.pop(0)]
                edges += Edge(last, v),
                last = v
        for (rownum, values) in self.rows.iteritems():
            tokens = list(values)
            last = d[tokens.pop(0)]
            while len(tokens) > 0:
                v = d[tokens.pop(0)]
                edges += Edge(last, v),
                last = v
        return Graph(edges, verticles, self.attributes)

class Main(object):
    ARGS = [('inFile', str), ('outFile', str), ('test', )]
    KW_ARGS = {'-i': 0, '-o': 1, }
    FLAG_ARGS = { '--test': 2, }
    MANDATORY_ARGS = [0,1]
    MULTISET_ARGS = [1]
    def __init__(self, argv):
        self.kwargs, self.args = self.parseArgs(argv)
    def parseArgs(self, argv):
        i = 1
        kwargs = {}
        args = []
        mandatory = list(Main.MANDATORY_ARGS)
        while i < len(argv):
            if argv[i] in Main.KW_ARGS:
                arg = Main.KW_ARGS[argv[i]]
                key = Main.ARGS[arg][0]
                value = Main.ARGS[arg][1](argv[i+1])
                if key in kwargs:
                    if arg not in Main.MULTISET_ARGS:
                        raise ValueError('Unexpected multiple occurences of argument "%s".' % key)
                    else:
                        kwargs[key] += value,
                else:
                    kwargs[key] = [ value ]
                i += 2
            elif argv[i] in Main.FLAG_ARGS:
                arg = Main.FLAG_ARGS[argv[i]]
                key = Main.ARGS[arg][0]
                if key not in args:
                    args += key,
                elif arg in Main.MULTISET_ARGS:
                    args += key,
                i += 1
            else:
                raise ValueError('Unexpected argument "%s".' % argv[i])
            if arg in mandatory:
                mandatory.remove(arg)
        if len(mandatory) > 0:
            raise ValueError('Some of the madatory arguments were not found: %s' % 
                        ', '.join('"%s"'%Main.ARGS[i][0] for i in mandatory))
        return (kwargs, args)
            
    def dfs(self, graph, vertex, visited, solutions):
        if vertex in visited:
            return False
        visited = list(visited)
        visited += vertex,
        if vertex.kind == VertexKind.FINISH:
            solutions += tuple(visited),
            return True
        result = False
        for v in ( e.other(vertex) for e in vertex.edges ):
            result |= self.dfs(graph, v, visited, solutions)
        return result
    def permutations(self, universe, select):
        # verticles - universe to select from
        # select - number of elements in each subset
        if len(universe) < select or select == 0:
            return ([],)
        if len(universe) == select:
            return (universe[:],)
        solutions = []
        for i in xrange(len(universe)-select+1):
             for s in self.permutations(universe[i+1:], select-1):
                s.insert(0, universe[i])
                solutions += (s,)
        return solutions
    def util(self, accuracy, a, b): #attackers, gems):
        attackers = len([v for v in a.filter(kind=VertexKind.DANGER) if v in b])
        gems = len(a.filter(kind=VertexKind.GOLD))
        import math
        return math.pow((1-accuracy), attackers)*(gems+10)
    def run(self):
        import io
        if self.kwargs['inFile'][0] == '-':
            import sys
            f = sys.stdin
        else:
            f = io.open(self.kwargs['inFile'][0], 'r')
        outFile = self.kwargs['outFile'][0]
        try:
            p = Parser(f)
            self.g = p.graph()
        finally:
            f.close()
        for v in self.g.filter(VertexKind.BARRIER):
            self.g.drop(v)
        self.g.attributes['ignore'] = VertexKind.EMPTY,
        start = self.g.filter(VertexKind.START, Vertex)
        self.solutionsA = []
        solutions = []
        for v in start:
            self.dfs(self.g, v, [], solutions)
        for sol in solutions:
            verticles = [ Vertex(v) for v in sol ]
            iterate = list(verticles)
            edges = []
            last = iterate.pop(0)
            while len(iterate):
                v = iterate.pop(0)
                edges += Edge(last, v),
                last = v
            self.solutionsA += Graph(edges, verticles, self.g.attributes),
        self.solutionsB = self.permutations(self.g.filter(VertexKind.DANGER), self.g.attributes['thiefs'])
        
        u = {};
        accuracy = self.g.attributes['accuracy']
        for row in xrange(len(self.solutionsA)):
            for col in xrange(len(self.solutionsB)):
                u[row,col] = self.util(accuracy, self.solutionsA[row], self.solutionsB[col])
        self.util = u
        print 'AGENT:'
        i = 1
        for a in self.solutionsA:
            print 'A%d: %s' % (i, str(tuple( (v.row, v.col) for v in a.verticles) ))
            i += 1
        print '\nATTACKER:'
        i = 1
        for b in self.solutionsB:
            print 'B%d: %s' % (i, str(tuple( (v.row, v.col) for v in b)))
            i += 1
        s = '\nAGENT\ATTACKER |'
        for i in range(len(self.solutionsB)):
            s += ' B%-7d |' % (i+1)
        print s
        print '----------------' + ('-----------'*(len(self.solutionsB)))
        for row in xrange(len(self.solutionsA)):
            s = 'A%-13d |' % (row+1)
            for col in xrange(len(self.solutionsB)):
                s += ' %*.4f |' % (8, u[row,col])
            print s
        print '----------------' + ('-----------'*(len(self.solutionsB)))
        #self.cpxlp(outFile)
        self.write(outFile)
    
    def write(self, outFile):
        rows = len(self.solutionsA)+1;
        cols = len(self.solutionsB)+1;
        matrix = dict(((k[0]+1,k[1]+1),-v) for k,v in self.util.iteritems())
        matrix[0,0] = 0
        for i in xrange(1,rows):
            matrix[i,0] = 1
        for i in xrange(1,cols):
            matrix[0,i] = 1
        
        lines = []
        lines += u'Minimize',
        lines += u' obj: +B0',
        lines += u'Subject To',
        for r in xrange(rows):
            s = u' A%d: ' % r
            for c in xrange(cols):
                if matrix[r,c] == 1:
                    s += u'+ B%d ' % (c,)
                elif matrix[r,c] == -1:
                    s += u'- B%d ' % (c,)
                elif matrix[r,c] > 0:
                    s += u'+%f B%d ' % (matrix[r,c], c)
                elif matrix[r,c] < 0:
                    s += u'%f B%d ' % (matrix[r,c], c)
            if r == 0:
                s += u' = 1'
            else:
                s += u' >= 0'
            lines += s,
        lines +=  u'Bounds',
        for c in xrange(cols):
            if c == 0:
                lines +=  (u' B%d free' % c),
            else:
                lines +=  (u' 0 <= B%d <= 1' % c),
        lines +=  u'End','\n',

        import io
        import os
        import re
        fo = io.open(outFile, 'w')
        try: fo.write('\n'.join(lines))
        finally: fo.close()
        solFile = 'borarpet.out'
        os.system('glpsol --interior --lp %s -w %s > /dev/null' % (outFile, solFile, ))
        fi  = io.open(solFile, 'r')
        try:
            m = re.match(r'([0-9]+)\s+([0-9]+)', fi.readline())
            rows = int(m.group(1))
            cols = int(m.group(2))
            m = re.match(r'^([0-9.\-eE]+)\s+([0-9.\-eE]+)', fi.readline())
            value = float(m.group(2))
            A = []
            for i in xrange(rows):
                m = re.match(r'^([0-9.\-eE]+)\s+([0-9.\-eE]+)', fi.readline())
                if m is not None:
                    A += float(m.group(2)),
            B = []
            for i in xrange(cols):
                m = re.match(r'^([0-9.\-eE]+)\s+([0-9.\-eE]+)', fi.readline())
                if m is not None:
                    B += float(m.group(1)),
        finally: fi.close()
        print '\nSOLUTION_AGENT:'
        for r in xrange(1,rows):
            print 'A%d: %s' % (r, A[r])
        print '\nSOLUTION_ATTACKER:'
        for c in xrange(1,cols):
            print 'B%d: %s' % (c, B[c])
        print '\nSOLUTION_VALUE: %f\n' % value

    def cpxlp(self, outFile):
        import glpk
        
        lp = glpk.LPX()
        lp.name = 'game'
        lp.obj.maximize = False
        #lp.obj.name = 'value'
        lp.rows.add(len(self.solutionsA)+1)
        lp.cols.add(len(self.solutionsB)+1)
        for r in lp.rows:
            r.name = 'A%d'%r.index
            if r.index == 0:
                r.bounds = 1, 1
            else:
                r.bounds = 0.0, None
        for c in lp.cols:
            if c.index == 0:
                c.name = 'value'
                c.bounds = None, None
            else:
                c.name = 'B%d'%c.index
                c.bounds = 0.0, 1.0
        lp.obj[0] = 1
        matrix = dict(((k[0]+1,k[1]+1),-v) for k,v in self.util.iteritems())
        matrix[0,0] = 0
        for i in xrange(1,len(lp.cols)):
            matrix[0,i] = 1
        for i in xrange(1,len(lp.rows)):
            matrix[i,0] = 1
        lp.matrix = [ matrix[r,c]  for r in xrange(len(lp.rows)) for c in xrange(len(lp.cols)) ]
        lp.interior()
        #lp.simplex()
        print '\nSOLUTION_AGENT:'
        for r in lp.rows:
            if r.index>0:
                print 'A%d: %s' % (r.index, r.dual)
        print '\nSOLUTION_ATTACKER:'
        for c in lp.cols:
            if c.index>0:
                print 'B%d: %s' % (c.index, c.primal)
        print '\nSOLUTION_VALUE: %f\n' % lp.obj.value
        lp.write(cpxlp=outFile)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        argv = [None, '-i', sys.argv[1], '-o', 'borarpet.log' ]
    else:
        argv = [None, '-i', 'example.in', '-o', 'borarpet.log' ] #sys.argv
    main = Main(argv)
    main.run()
    

