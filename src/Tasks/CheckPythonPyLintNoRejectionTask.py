"""
Task to check the PyLint grade of a file and informs commiter about his grade.

AUTHORS:
    Abdelhalim Kadi
    Adrian Vandier Ast
"""

from __future__ import print_function
import os
import re
from tempfile import NamedTemporaryFile
from src.Tasks.CheckSyntaxTask import CheckSyntaxTask
from src.Tasks.HookTask import HookNewOrModifiedFileTask
from src.Utils import Bash


class CheckPythonPyLintNoRejectionTask(CheckSyntaxTask, HookNewOrModifiedFileTask):
    """
    Task to check the PyLint grade of a file and inform commiter about his grade.
    """
    EVALUATION = re.compile(r"Your code has been rated at (-\d+\.\d\d)/10|Your code has been rated at (\d+\.\d\d)/10")
    ERRORS = re.compile(r"(^E:.*\d+:.*$)", re.MULTILINE)
    MINIMUM_GRADE = 5.0
    AVERAGE_GRADE = 7.5
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    def check_syntax(self, file_desc, filename=""):
        """
        Execute PyLint and parse the result, inform commiter about his grade.
        Pylint report is saved to a temporary file.
        """
        if filename[-3:] != ".py":
            print("{0} doesn't end with .py we ignore it".format(filename))
            return True

        conf_filename = os.path.join(self.conf_location, "pylint.conf")
        pylint_cmd = "pylint --rcfile={0} {1}".format(conf_filename, file_desc.name)
        _, data = Bash.execute_command_rawoutput(command=pylint_cmd)

        report_filename = ""
        base_filename = filename.split("/")[-1].split(".")[0]
        with NamedTemporaryFile(mode="w", delete=False, prefix="pylint_report_", suffix="_{0}".format(base_filename)) \
                as report_file:
            report_file.write(data)
            report_filename = report_file.name

        error = self.ERRORS.findall(data)
        if error:
            print(self.RED + ">>> " + "\n>>> ".join(error) + self.ENDC)

        evaluation = self.EVALUATION.search(data)
        if evaluation:
            value_str = evaluation.group(1) or evaluation.group(2)
            value = float(value_str)
            color = self.RED
            if value >= self.AVERAGE_GRADE:
                color = self.GREEN
            elif value >= self.MINIMUM_GRADE:
                color = self.YELLOW
            print(color + ">> \"%s\" graded %s/10 \033[0m" % (filename, value_str) + self.ENDC)
            if value < self.MINIMUM_GRADE:
                print(">> /!\\ You shouldn't push this /!\\")

        print(">> Pylint report file: %s" % report_filename)

        return True
