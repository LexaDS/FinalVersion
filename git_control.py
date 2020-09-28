import subprocess

class git_control:

    def run(self,*args):
        return subprocess.check_call(['git'] + list(args))

    def clone(self,gitpath,local_path):

        subprocess.Popen(['git', 'clone', gitpath, local_path])

    def commit(self):
        message = input("\nType in your commit message: ")
        commit_message = f'{message}'

        git_control.run("commit", "-am", commit_message)
        git_control.run("push", "-u", "origin", "master")

    def branch(self):

        branch = input("\nType in the name of the branch you want to make: ")
        br = f'{branch}'

        git_control.run("checkout", "-b", br)

        choice = input("\nDo you want to push the branch right now to GitHub? (y/n): ")
        choice = choice.lower()

        if choice == "y":
            git_control.run("push", "-u", "origin", br)

        elif choice == "n":
            print("\nOkay, goodbye!\n")

        else:
            print("\nInvalid command! Use y or n.\n")