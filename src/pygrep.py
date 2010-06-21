#! /usr/bin/env python

import re,sys

class TextRef(object):
    """
    """
    
    def __init__(self, filename, lineno, linetext,  start, end, ):
        """
        
        Arguments:
        - `lineno`:
        - `start`:
        - `end`:
        """
        self._filename = filename
        self._lineno = lineno
        self._start = start
        self._end = end
        self._linetext = linetext

    def __str__(self):
        return "(Line %d: %s, @%d::%d)"%(self._lineno,self._linetext,self._start,self._end)

class Match(object):
    """
    """
    
    def __init__(self, filename, refs = [], outtext = None):
        """
        
        Arguments:
        - `filename`:
        - `refs`:
        - `outtext`:
        """
        self._filename = filename
        self._refs = refs
        self._outtext = outtext

    def __str__(self):
        return self._filename + str(self._refs) + self._outtext

def find(pattern, f):
    """
    
    Arguments:
    - `pattern`:
    - `f`:
    """
    refs = []
    p = re.compile(r"%s"%pattern)
    lineno = 0
    lines = open(f).readlines()
    for line in lines:
        line = line.replace("\n","")
        ms = p.finditer(line)
        for m in ms:
            refs.append(TextRef(f,lineno,line,m.start(),m.end()))        
        lineno +=1
    text = ""    

    for ref in refs:
        if ref._lineno >= 1:
            text += "%3d:"%(ref._lineno-1) + lines[ref._lineno - 1]
        text +=  "%3d:"%(ref._lineno) + lines[ref._lineno]
        if ref._lineno < lineno-1:
            text +=  "%3d:"%(ref._lineno+1) + lines[ref._lineno + 1]
        text += "---\n"
    
    if len(refs) > 0:
        match = Match(f,refs,text)
        return match
    
    return None
        
def main():
    """
    """
    print find(sys.argv[1],sys.argv[2])



if __name__ == '__main__':
    main()
