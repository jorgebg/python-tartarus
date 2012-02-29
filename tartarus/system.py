import subprocess
import os

def execute(commands, quiet=False):
    fulloutput=''
    if isinstance(commands, str):
        commands = [commands]
    for cmd in commands:
        if not quiet: print cmd
        output,error = subprocess.Popen([cmd],stdout = subprocess.PIPE, stderr= subprocess.PIPE, shell=True).communicate()
        if not quiet:
            print output
        fulloutput=fulloutput+output
    return fulloutput

def abspath(*x):
    return os.path.join(os.path.abspath(os.getcwd()), *x)