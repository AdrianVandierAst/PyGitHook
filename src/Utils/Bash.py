"""
Bash is a placeholder for the execute_command function

execute_command is a wrapper around subprocess.check_output.

AUTHOR:
    Gael Magnan de bornier
    Adrian Vandier Ast
"""

from __future__ import print_function
from subprocess import check_output, CalledProcessError, STDOUT, PIPE, Popen


def execute_command_rawoutput(command, shell=False):
    """Execute a bash command,
    returns a return code 0 for success the error code otherwise
    and the output as a string"""
    try:
        ret_code = 0
        try:
            output = check_output(command.split(), stderr=STDOUT, shell=shell)
        except CalledProcessError, error:
            output = error.output
            ret_code = error.returncode
        return ret_code, output
    except StandardError, error:
        print("The command: {0} failed.".format(command))
        print("Please transmit the following message to your administrator")
        print(error)
    return 1, ""


def execute_command(command, shell=False):
    """Execute a bash command,
    returns a return code 0 for success the error code otherwise
    and the output as a array of string (1 element = 1 line) without empty lines"""
    error, output_string = execute_command_rawoutput(command, shell)
    return error, [s for s in output_string.split('\n') if s != ""]


def execute_piped_command(command1, command2):
    """Execute two bash commands, the stdout of the first one is piped
    to the stdin of the second.
    returns a return code 0 for success the error code otherwise
    and the output of the commands"""

    try:
        p1 = Popen(command1.split(), stdout=PIPE)
    except CalledProcessError, error:
        return error.returncode, error.output
    else:
        try:
            p2 = Popen(command2.split(), stdin=p1.stdout, stderr=PIPE )
        except CalledProcessError, error:
            return error.returncode, error.output
        else:
            try:
                p1.stdout.close()
                output = p2.communicate()[0]
                return 0, output
            except StandardError, error:
                print("The commands: {0} failed.\n".format((command1, command2)))
                print("Please transmit the following message to your administrator:")
                print(error)
    return 1, []
    
