"""
Git Hook. The Simple python way to code Hooks

Hook is the base class for every Hook.

AUTHOR:
    Gael Magnan de bornier
"""

import sys
import os
import re
from tempfile import NamedTemporaryFile
from contextlib import contextmanager

from src.Utils import Bash
from src.Tasks import HookTask

class Hook(object):

    def __init__(self, tasks=None, conf_location="", exclude=None):
        if tasks is None:
            tasks = []
        if exclude is None:
            exclude = []
        self.exclude = exclude
        self.tasks = tasks
        self.conf_location = conf_location


    def main_process(self):
        """Main function"""
        kwargs = self.get_exec_params()
        result = self.process(**kwargs)

        if result:
            sys.exit(0)
        sys.exit(1)


    def get_script_params(self, **kwargs):
        return {'${0}'.format(i): arg for i, arg in enumerate(sys.argv)}

    def get_line_params(self, **kwargs):
        return {}

    def get_files_params(self, **kwargs):
        return self.get_files_grouped_by_change(**kwargs)

    def get_exec_params(self):
        """Reads the inputs to get execution parameters"""
        params = {'conf_location': self.conf_location}
        params.update(self.get_script_params(**params))
        params.update(self.get_line_params(**params))
        params.update(self.get_files_params(**params))
        return params


    def process(self, **kwargs):
        """Main treatment, execute the tasks return False if any task fails,
        true otherwise"""
        try:
            tasks = self.get_tasks_group_by_type()
            return self.execute_tasks_group_by_type(*tasks, **kwargs)
        except Exception as e:
            print("An error occured during the runing of the script, "
                  "please report this following message to you administrator.")
            print(e)
            return False


    def get_tasks_group_by_type(self):
        """ This method return the tasks group by execution context,
        the groups should be the ones used by execute_tasks_group_by_type"""
        general_tasks = []
        new_file_task = []
        modified_file_task = []
        deleted_file_task = []
        for task in self.tasks:
            if issubclass(task, HookTask.HookNewOrModifiedFileTask):
                new_file_task.append(task)
                modified_file_task.append(task)
            elif issubclass(task, HookTask.HookNewFileTask):
                new_file_task.append(task)
            elif issubclass(task, HookTask.HookModifiedFileTask):
                modified_file_task.append(task)
            elif issubclass(task, HookTask.HookDeletedFileTask):
                deleted_file_task.append(task)
            elif issubclass(task, HookTask.HookFileTask):
                new_file_task.append(task)
                modified_file_task.append(task)
                deleted_file_task.append(task)
            else:
                general_tasks.append(task)
        return (general_tasks, new_file_task, modified_file_task,
                deleted_file_task)


    def execute_tasks_group_by_type(self, general_tasks, new_file_task,
                                    modified_file_task, deleted_file_task,
                                    **kwargs):
        """The tasks are executed with different context depending on their type
        The HookFileTasks are executed on specific files depending on the
        changes the file encountered
        Other tasks are executing as general statements"""
        for task in general_tasks:
            if not task().execute(**kwargs):
                return False

        if new_file_task or modified_file_task or deleted_file_task:
            for file_type in ['new_files', 'modified_files', 'deleted_files']:
                files_to_check = kwargs[file_type]
                for filename in files_to_check:
                    exclusion_matchs = [ x for x in self.exclude if re.match(x, filename)]
                    if exclusion_matchs:
                        print( "{0} ignored because it matches: {1}".format( filename, exclusion_matchs ) )
                        continue
                    if(file_type != "deleted_files" and
                       len(new_file_task) + len(modified_file_task) > 0):
                        try:
                            file_val = self.get_file(filename, **kwargs)
                        except:
                            print("Could not read %s" % filename)
                            return False
                        with self.get_temp_file() as tmp:
                            try:
                                self.write_file_value_in_file(file_val, tmp)
                            except:
                                print("Could not write %s " % filename)
                                return False

                            if file_type == "new_files":
                                for task in new_file_task:
                                    if not task().execute(file_desc=tmp,
                                                          filename=filename,
                                                          file_value=file_val,
                                                          **kwargs):
                                        return False

                            elif file_type == "modified_files":
                                for task in modified_file_task:
                                    if not task().execute(file_desc=tmp,
                                                          filename=filename,
                                                          file_value=file_val,
                                                          **kwargs):
                                        return False

                    else:
                        for task in deleted_file_task:
                            if not task().execute(filename=filename, **kwargs):
                                return False

        return True


    def get_file(self, filename, **kwargs):
        pass


    def get_file_diffs(self, **kwargs):
        pass

    @contextmanager
    def get_temp_file(self, mode="r+"):
        f = NamedTemporaryFile(mode=mode, delete=False)
        try:
            yield f
        finally:
            try:
                os.unlink(f.name)
            except OSError:
                pass


    def write_file_value_in_file(self, file_value, file_desc):
        if file_value:
            file_desc.write("\n".join(file_value))
            file_desc.flush()
        else:
            raise Exception()


    def get_files_grouped_by_change(self, **kwargs):
        added = []
        modified = []
        deleted = []
        file_diffs = self.get_file_diffs(**kwargs)
        for line in file_diffs:
            if len(line) < 3:
                continue
            mode, filename = self.get_mode_and_filname(line)
            if mode == "A":
                added.append(filename)
            elif mode == "M":
                modified.append(filename)
            elif mode == "D":
                deleted.append(filename)
        return {'new_files': added,
                'modified_files': modified,
                'deleted_files': deleted}


    def get_mode_and_filname(self, line):
        try:
            mode, filename = line.split()
            return mode, filename
        except:
            line_splited = line.split()
            if len(line_splited) > 2:
                mode = line_splited[0]
                filename = line.replace(mode, "", 1)
                return mode, filename
            else:
                print("An error occured while trying to split:{0}"
                      " Please warn and adminitrator ".format(line))


def main(_klass, tasks=None, conf_location="", exclude=None):
    if issubclass(_klass, Hook):
        hook = _klass(tasks, conf_location, exclude)
        hook.main_process()
    else:
        print("Not a valid class, should inherit from Hook")
        sys.exit(1)

    sys.exit(0)
