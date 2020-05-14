#!/usr/bin/python3

import sys
import os
import json
import types
import math
import re
from subprocess import Popen, PIPE, DEVNULL
from optparse import OptionParser
from pathlib import Path
from multiprocessing import Pool

gem5_mcpat_parser = Path("/home/jcma/gem5-mcpat-parser/gem5-mcpat-parser")
mcpat = Path("/home/jcma/cMcPAT/mcpat/mcpat")
template = Path("/home/jcma/gem5-mcpat-parser/template-xeon.xml")


###################################################################
# Copied from cMcPAT/Scripts/print_energy.py
###################################################################
class parse_node:
    def __init__(this,key=None,value=None,indent=0):
        this.key = key
        this.value = value
        this.indent = indent
        this.leaves = []
    
    def append(this,n):
        #print 'adding parse_node: ' + str(n) + ' to ' + this.__str__() 
        this.leaves.append(n)

    def get_tree(this,indent):
        padding = ' '*indent*2
        me = padding + this.__str__()
        kids = list(map(lambda x: x.get_tree(indent+1), this.leaves))
        return me + '\n' + ''.join(kids)
        
    def getValue(this,key_list):
        #print 'key_list: ' + str(key_list)
        if (this.key == key_list[0]):
            #print 'success'
            if len(key_list) == 1:
                return this.value
            else:
                kids = list(map(lambda x: x.getValue(key_list[1:]), this.leaves))
                #print 'kids: ' + str(kids) 
                return ''.join(kids)
        return ''        
        
    def __str__(this):
        return 'k: ' + str(this.key) + ' v: ' + str(this.value)

class parser:

    def dprint(this,astr):
        if this.debug:
            print(this.name,astr)

    def __init__(this, data_in):
        this.debug = False
        this.name = 'mcpat:mcpat_parse'
        buf = open(data_in)

        this.root = parse_node('root',None,-1)
        trunk = [this.root]

        for line in buf:
            	   
            indent = len(line) - len(line.lstrip())
            equal = '=' in line
            colon = ':' in line
            useless = not equal and not colon
            items = list(map(lambda x: x.strip(), line.split('=')))

            branch = trunk[-1]

            if useless: 
                #this.dprint('useless')
                pass 

            elif equal:
                assert(len(items) > 1)

                n = parse_node(key=items[0],value=items[1],indent=indent)
                branch.append(n)

                this.dprint('new parse_node: ' + str(n) )

            else:
                
                while ( indent <= branch.indent):
                    this.dprint('poping branch: i: '+str(indent) +\
                                    ' r: '+ str(branch.indent))
                    trunk.pop()
                    branch = trunk[-1]
                
                this.dprint('adding new leaf to ' + str(branch))
                #print(list(items))
                n = parse_node(key=items[0],value=None,indent=indent)
                branch.append(n)
                trunk.append(n)
                
        
    def get_tree(this):
        return this.root.get_tree(0)

    def getValue(this,key_list):
        value = this.root.getValue(['root']+key_list) 
        assert(value != '')
        return value
###################################################################################

def run_mcpat(stats_dir):
    stats_dir = Path(stats_dir)
    config = stats_dir / "config.ini"
    stats = stats_dir / "stats.backup.txt"
    confxml = stats_dir / "configuration.xml"
    result = stats_dir / "result.txt"

    if not stats_dir.exists():
        print("{} does not exist".format(str(stats_dir)))
        return (False, None, None, None, None)
    if not config.exists():
        print("{} does not exist".format(str(config)))
        return (False, None, None, None, None)
    if not stats.exists():
        print("{} does not exist".format(str(stats)))
        return (False, None, None, None, None)

    if options.rerun or not confxml.exists():
        parser_args = []
        parser_args.append(str(gem5_mcpat_parser))
        parser_args.append("-s")
        parser_args.append(str(stats))
        parser_args.append("-c")
        parser_args.append(str(config))
        parser_args.append("-x")
        parser_args.append(str(template))
        parser_args.append("-o")
        parser_args.append(str(confxml))
        if options.dolma:
            parser_args.append("--dolma")

        try:
            parser_process = Popen(parser_args, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
            parser_process.wait()
        except:
            print("{}: parsing gem5 stats failed".format(stats_dir.name))
            return (False, None, None, None, None)

    if not confxml.exists():
        print("confxml is missing... something went wrong somewhere...")
        return (False, None, None, None, None)

    if options.rerun or not result.exists():
        mcpat_args = []
        mcpat_args.append(str(mcpat))
        mcpat_args.append("-infile")
        mcpat_args.append(str(confxml))
        mcpat_args.append("-print_level")
        mcpat_args.append("5")

        try:
            mcpat_process = Popen(mcpat_args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE)
            mcpat_process.wait()
            stdout, stderr = mcpat_process.communicate()
        except:
            print("{}: running mcpat failed".format(stats_dir.name))
            return (False, None, None, None, None)

        with result.open("wb") as r:
            r.write(stdout)

    if not result.exists():
        print("result is missing... something went wrong somewhere...")
        return (False, None, None, None, None)

    p = parser(str(result))

    area = p.getValue(['Processor:', 'Area'])
    peak = p.getValue(['Processor:', 'Peak Power'])
    leakage = p.getValue(['Processor:', 'Total Leakage'])
    dynamic = p.getValue(['Processor:', 'Runtime Dynamic'])

    area = re.sub(' mm\^2', '', area)
    peak = re.sub(' W', '', peak)
    leakage = re.sub(' W', '', leakage) 
    dynamic = re.sub(' W', '', dynamic) 

    print("{} finished. Area={}, Peak={}, Leakage={}, Dynamic={}".format(stats_dir.name, area, peak, leakage, dynamic))

    return (True, float(area), float(peak), float(leakage), float(dynamic))

def main():
    global options
    parser = OptionParser()
    parser.add_option("-w", "--worker", action="store", type="int", dest="nworkers", metavar="NUM",
                help="number of workers")
    parser.add_option("-c", "--conf", action="store", type="string", dest="config", metavar="FILE",
                help="the configuration file which includes the list of summary files")
    parser.add_option("-p", "--path", action="store", type="string", dest="dir", metavar="DIR",
                help="the directory of summary files")
    parser.add_option("-f", "--force-rerun", action="store_true", dest="rerun", default=False,
                help="force to rerun even file exists")
    parser.add_option("-d", "--dolma", action="store_true", dest="dolma", default=False,
                help="use dolma mode")
    (options, args) = parser.parse_args()

    if options.config is not None and options.dir is not None:
        print("only one of -c and -d is allowed")
        exit(1)

    if options.nworkers is None:
        print("must specify number of workers")

    summary_list = []

    if options.config is not None:
        conf = Path(options.config)
        if not conf.exists() or not conf.is_file():
            print("path error")
            exit(2)
        with conf.open() as f:
            summary_list = f.read().splitlines()
    elif options.dir is not None:
        cdir = Path(options.dir)
        if not cdir.exists() or not cdir.is_dir():
            print("path error")
            exit(3)
        for child in cdir.iterdir():
            if child.is_file() and str(child).endswith(".json"):
                summary_list.append(str(child))

    print("{} summary files".format(len(summary_list)))
    for summary in summary_list:
        with Path(summary).open() as f:
            s = f.read()
        summary_dict = json.loads(s)
        mode = summary_dict['mode']
        bench = summary_dict['bench']
        successful_checkpoints = summary_dict['successful_checkpoints']
        failed_checkpoints = summary_dict['failed_checkpoints']

        checkpoints = []
        for checkpoint in summary_dict['checkpoints']:
            if summary_dict['checkpoints'][checkpoint] == "successful":
                checkpoints.append(checkpoint)

        print("summary file: {}".format(summary))
        print("successful checkpoints: {}".format(successful_checkpoints))
        print("failed checkpoints: {}".format(failed_checkpoints))
        print("benchmark: {}".format(bench))
        print("mode: {}".format(mode))

        result_array = []
        with Pool(options.nworkers) as pool:
            result_array = pool.map(run_mcpat, checkpoints)

        print(result_array)

    return 0

if __name__ == "__main__":
    exit(main())

