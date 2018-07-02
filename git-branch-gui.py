#! /usr/bin/python3
# Character Encoding: UTF-8

import sys
import os

import json

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import subprocess

class Cli:
    def exec(self, cmd, line_callback=None, exit_status_callback=None):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if line_callback:
            for line in p.stdout.readlines():
                line_callback(line.decode("utf-8").replace('\n', ''))

        if exit_status_callback:
            exit_status_callback(p.wait())

    def get_git_installed(self):
        git_installed = False
        def git_found(l):
            nonlocal git_installed
            git_installed = True

        self.exec('which git', git_found)
        return git_installed

class Toast_Notification:
    cli = None
    def __init__(self, cli):
        self.cli = cli

    def send(self, icon, summary, body):
        self.cli.exec('notify-send -i '
            + json.dumps(icon)
            + ' ' + json.dumps(summary)
            + ' ' + json.dumps(body))

class Checkout:
    cli = None
    return_code = None
    std_out = ''

    def __init__(self, cli):
        self.cli = cli

    def add_to_std_out_string(self, line):
        self.std_out = self.std_out + line + '\n'

    def get_return_code(self, return_code):
        self.return_code = return_code

    def exec(self, branch_name):
        cmd_checkout = 'git checkout "branch_name"'.replace('branch_name', branch_name)
        self.cli.exec(cmd_checkout, self.add_to_std_out_string, self.get_return_code)
        return self.return_code == 0

class Checkout_Factory:
    def __init__(self, cli):
        self.cli = cli

    def create_instance(self):
        return Checkout(self.cli)

class Dir_Fetcher:
    win = None
    def __init__(self, win):
        self.win = win

    def __validate_git_dir_or_exit(self, model):
        if not model.checkout_dir or not os.path.isdir(model.checkout_dir):
            self.win.critical_invalid_dir()
            sys.exit()

        if not os.path.isdir(model.checkout_dir + '/.git'):
            self.win.critical_not_git_dir()
            sys.exit()

    def set_dir_in_model(self, model):
        if model.get_should_ask_for_path():
            model.checkout_dir = self.win.get_path_from_dialog()
        elif model.get_dir_from_cli():
            model.checkout_dir = model.get_dir_from_cli()

        self.__validate_git_dir_or_exit(model)
        os.chdir(model.checkout_dir)

class Model:
    cli = None
    argv = None
    branch_count = 0
    current_branch = None
    checkout_dir = None
    checkout_factory = None

    def __init__(self, cli, checkout_factory, argv):
        self.cli = cli
        self.argv = argv
        self.checkout_factory = checkout_factory

    def get_should_ask_for_path(self):
        return True if len(self.argv) < 2 else False
        #return True if len(self.argv) > 1 and self.argv[1] == '--open' else False
        
    def get_branch_names(self, ui_adder):
        def add_branch_to_list(branch_name):
            nonlocal ui_adder

            self.branch_count = self.branch_count + 1
            ui_adder(branch_name.strip())
            if '* ' in branch_name:
                self.current_branch = branch_name.replace('*', '').strip()

        self.cli.exec('git branch', add_branch_to_list)

    def get_dir_from_cli(self):
        if len(self.argv) > 1:
            return self.argv[1]

    def create_end_exec_checkout(self, branch_name):
        checkout = self.checkout_factory.create_instance()
        checkout.exec(branch_name)
        return checkout

    def get_is_branch_checoutable(self, branch_name):
        return False if '* ' in branch_name else True

class Window(QWidget):
    list_branches_widget = None
    model = None
    toast_notification = None

    def __init__(self, toast_notification):
        self.toast_notification = toast_notification
        super(Window, self).__init__()
        self.set_ui()

    def set_ui(self):
        layout = QGridLayout(self)
        self.list_branches_widget = QListWidget(self)
        self.list_branches_widget.show()
        self.list_branches_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.list_branches_widget, 0, 0)

        self.list_branches_widget.activated.connect(self.event_branch_change)

    def event_branch_change(self, model_index):
        branch_name = self.list_branches_widget.selectedItems()[0].text()
        if self.model.get_is_branch_checoutable(branch_name):
            if self.confirm_checkout(branch_name) == QMessageBox.Yes:
                checkout = self.model.create_end_exec_checkout(branch_name)
                if not checkout.return_code:
                    self.toast_notification.send('stock_text_left', 'Checked out ' + branch_name, checkout.std_out)
                    sys.exit()
                else:
                    self.critical_checkout_failled(branch_name, checkout.std_out)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            sys.exit()

    def populate_branch_list_and_style(self):
        self.model.get_branch_names(self.list_branches_widget.addItem)
        self.resize(520, self.model.branch_count * 25)
        self.setWindowTitle('Git ' + os.getcwd() + ' [' + self.model.current_branch + ']')

    def set_model(self, model):
        self.model = model

    def get_path_from_dialog(self):
        return str(QFileDialog.getExistingDirectory(self, "Select You Local checkout"))

    def confirm_checkout(self, branch_name):
        return QMessageBox.question(self,
            'Checkout ' + branch_name + '?',
            "Do you want to checkout branch:<div style='margin-top: 20px; font-size: 18px'>" + branch_name + "</div>", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    def critical_invalid_dir(self):
        if not self.model.checkout_dir:
            return QMessageBox.critical(self, 'Invalid directory', 'No directory selected', QMessageBox.Ok)
        return QMessageBox.critical(self, 'Invalid directory', self.model.checkout_dir + ' is an invalid directory path', QMessageBox.Ok)

    def critical_checkout_failled(self, branch_name, reason):
        return QMessageBox.critical(win, 'Checkout failled', 'Unable to checkout branch' + branch_name + '\n' + reason, QMessageBox.Ok)

    def critical_not_git_dir(self):
        return QMessageBox.critical(win, 'Invalid direcory', self.model.checkout_dir + ' is not a git repository clone', QMessageBox.Ok)

    def critical_git_not_installed(self):
        return QMessageBox.critical(win, 'Git not installed', 'Please install git', QMessageBox.Ok)


class Git_branch_gui:
    def go(self):
        os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"
        app = QApplication(sys.argv)
        cli = Cli()
        toast_notification = Toast_Notification(cli)
        checkout_factory = Checkout_Factory(cli)
        model = Model(cli, checkout_factory, sys.argv)
    
        win = Window(toast_notification)

        if not cli.get_git_installed():
            win.critical_git_not_installed()

        win.set_model(model)
    
        dir_fetcher = Dir_Fetcher(win)
        dir_fetcher.set_dir_in_model(model)
    
        win.populate_branch_list_and_style()
    
        win.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    Git_branch_gui().go()