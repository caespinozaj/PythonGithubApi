import subprocess as sp
import os
import shutil
import stat
from dataclasses import dataclass
import pathlib

@dataclass
class ResponseObject:
    returncode: int
    stdout: str
    stderr: str


def change_permissions(folder):
    """
    Given a folder, changes permissions of all files
    and directories recursively to read, write and execute.
    """
    for root, directories, files in os.walk(folder):
        for directory in directories:
            os.chmod(os.path.join(root, directory), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)


def change_dirs(fn, *args, **kwargs):
    """
    wrapper function that, given a class with 'directory'
    attribute, executes functions in said directory and
    then exits to previous directory.
    """
    def wrapped(self=None, *args, **kwargs):
        cwd = os.path.abspath(os.getcwd())
        os.chdir(self.directory)
        result = fn(self, *args, **kwargs)
        os.chdir(cwd)
        return result
    return wrapped


def run_command(command):
    """
    Given a command in str (e.g. "ls -l") or list form (e.g. ["ls, "-l"]), it
    executes it. Return ResponseObject that has returncode, stdout and stderr.
    """
    if type(command) == str:
        command = command.split(" ")
    p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
    result = p.communicate()
    result = ResponseObject(p.returncode, result[0].decode(), result[1].decode())
    p.terminate()
    return result


class Issue:
    def __init__(self, link, directory, id_):
        self.link = link
        self.id = id_
        self.directory = directory

    @change_dirs
    def comment(self, comment):
        return run_command(["gh", "issue", "comment", self.id, "-b", comment])


class Repository:

    def __init__(self, link=None, directory=None):
        """
        Initializes repository. link must be in the format 'github.com/<repository>'
        """
        if link is None and directory is None:
            raise ValueError('Empty link and directory not allowed')
        self.link = link
        self.directory = directory
        if directory is not None:
            if not os.path.exists(directory):
                os.mkdir(directory)
            self.directory = os.path.abspath(directory)
            if link is None:
                self.link = self._get_remote()
        self.repo = self.link[self.link.find("/") + 1:]

    def clone(self, folder):
        if self.directory is None:
            self.directory = os.path.abspath(folder)
        return run_command(f"gh repo clone {self.repo} {folder}")

    @change_dirs
    def add(self, add_string):
        return run_command(["git", "add", add_string])

    @change_dirs
    def remove(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

    @change_dirs
    def delete_git(self):
        change_permissions(".git")
        shutil.rmtree(".git")

    def delete(self):
        self.delete_git()
        shutil.rmtree(self.directory)

    @change_dirs
    def commit(self, message):
        run_command(["git", "commit", "-m", message])

    @change_dirs
    def push(self):
        result = run_command(f"git push")
        if result.returncode == 128:
            run_command(f"git push --set-upstream origin master")

    @change_dirs
    def status(self):
        result = run_command(f"git status")
        return result.stdout

    @change_dirs
    def checkout(self, commit):
        run_command(f"git checkout {commit}")

    def copy_file(self, src, dest):
        """
        copies the file from src path into dest path.
        src: relative path to root
        dest: relative path to repository
        """
        dest = os.path.join(self.directory, dest)
        dirname = os.path.dirname(dest)
        pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)

    def copy_directory(self, src, dest):
        """
        copies the directory from src path into dest path.
        src: relative path to root
        dest: relative path to repository
        """
        shutil.copytree(src, os.path.join(self.directory, dest))

    def copy_root(self, src):
        """
        copies the contents of one folder into this repository.
        Useful for starting new repositories. Does not copy empty
        directories.
        """
        for root, _, files in os.walk(src):
            for file in files:
                src_ = os.path.join(root,file)
                dest = os.path.join(os.path.relpath(root, src),file)
                self.copy_file(src_, dest)

    @change_dirs
    def create_issue(self, title, body):
        """
        Creates an issue on the repository. Returns said issue.
        """
        result = run_command(["gh", "issue", "create", "-t", title, "-b", body])
        id_ = result.stdout[result.stdout.rfind("/") + 1:].strip()
        return Issue(self.link, self.directory, id_)

    def add_collaborator(self, user):
        command = f"gh api -XPUT repos/{self.repo}/collaborators/{user} -f permission=push"
        return run_command(command)

    @change_dirs
    def get_last_commit(self, start_date, end_date):
        """
        Returns last commit (and its date) between start_date and end_date (strings).
        Returns None, None if not found.
        start_date and end_date format: yyyy-mm-dd HH:MM:SS (e.g. "2000-11-20 13:59:00")
        """
        command = ["git", "log", "--since", f"\"{start_date}\"", "--until", f"\"{end_date}\"", "-1", "--date=iso", "--pretty=format:\"%H %ad\""]
        result = run_command(command)
        output = result.stdout
        if len(output.strip()) == 0:
            return None, None
        output = output.split(" ")
        commit, date_time = output[0][1:], f"{output[1]} {output[2]}"
        return commit, date_time

    @change_dirs
    def _get_remote(self):
        """
        given a local repository, returns the remote
        repository (link) associated with it.
        """
        result = run_command("git remote get-url origin").stdout
        result = result[result.find("github.com/"):].strip().strip(".git")
        return result

class Github:

    def repository(self, link=None, directory=None):
        return Repository(link, directory)

    def create_repository(self, repository, directory=None, public=False):
        reach = "private"
        if public:
            reach = "public"
        run_command(f"gh repo create {repository} --{reach} -y")
        repository_name = repository[repository.rfind("/")+1:]
        if directory is not None:
            os.rename(repository_name, directory)
            return Repository(directory=directory)
        return Repository(directory=repository_name)
