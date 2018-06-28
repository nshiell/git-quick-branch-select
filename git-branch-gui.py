#! /usr/bin/python3
# Character Encoding: UTF-8

import sys
import os

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import subprocess

os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"

app = QApplication(sys.argv)

class Window(QWidget):
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            sys.exit()

win = Window()

layout = QGridLayout(win)

list_branches_widget = QListWidget(win)
list_branches_widget.show()

def exec_cli(cmd, line_callback=None, exit_status_callback=None):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if line_callback:
        for line in p.stdout.readlines():
            line_callback(line.decode("utf-8").replace('\n', ''))

    if exit_status_callback:
        exit_status_callback(p.wait())

def sanity_check():
    if len(sys.argv) > 1 and sys.argv[1] == '--open':
        dir1 = str(box.getExistingDirectory(win, "Select You Local checkout"))

        
        
        print(dir1)
        if not os.path.isdir(dir1):
            QMessageBox.critical(win, 'Invalid directory', dir1 + ' is an invalid directory path', QMessageBox.Ok)
            sys.exit()
        os.chdir(dir1)
    elif len(sys.argv) > 1:
        if not os.path.isdir(sys.argv[1]):
            QMessageBox.critical(win, 'Invalid directory', sys.argv[1] + ' is an invalid directory path', QMessageBox.Ok)
            sys.exit()
        os.chdir(sys.argv[1])

    git_installed = False
    def git_found(l):
        nonlocal git_installed
        git_installed = True

    exec_cli('which git', git_found)
    
    if not git_installed:
        QMessageBox.critical(win, 'Git not installed', 'Please install git', QMessageBox.Ok)
        sys.exit()

    git_dir_found = False
    def git_dir(l):
        nonlocal git_dir_found
        git_dir_found = True

    exec_cli('ls -a . | grep -wF .git', git_dir)

    if not git_dir_found:
        QMessageBox.critical(win, 'Invalid direcory', os.getcwd() + ' is not a git repository clone', QMessageBox.Ok)
        sys.exit()

sanity_check()


def list_branches_widget_change(model_index):
    def checkout_line(branch_name_raw):
        branch_name = branch_name_raw.strip()
        if not '* ' in branch_name:
            question = QMessageBox.question(win, 'Checkout ' + branch_name + '?', "Do you want to checkout branch:<div style='margin-top: 20px; font-size: 18px'>" + branch_name + "</div>", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            def checkout_current_line():
                result_lines = ''
                result_status_code = None
                def checkout_result(line):
                    nonlocal result_lines
                    result_lines = result_lines + line + '\n'

                def result_status_code_set(code):
                    nonlocal result_status_code
                    result_status_code = code

                cmd_checkout = 'git checkout $(git branch | head -n LINE | tail -n 1)'.replace('LINE', str(model_index.row() + 1))
                exec_cli(cmd_checkout, checkout_result, result_status_code_set)
                if result_status_code == 0:
                    #QMessageBox.information(win, 'StatusCode: ' + str(result_status_code),
                    #    'Command:\n' + cmd_checkout + '\n' + result_lines, QMessageBox.Ok)
                    exec_cli('notify-send -i stock_text_left "Checked out ' + branch_name + '" "' + result_lines + '"')
                    sys.exit()
                else:
                    QMessageBox.critical(win, 'StatusCode: ' + str(result_status_code),
                        'Command:\n' + cmd_checkout + '\n' + result_lines, QMessageBox.Ok)

            if question == QMessageBox.Yes:
                return checkout_current_line()

    exec_cli('git branch | head -n LINE | tail -n 1'.replace('LINE', str(model_index.row() + 1)), checkout_line)

list_branches_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
list_branches_widget.activated.connect(list_branches_widget_change)
layout.addWidget(list_branches_widget, 0, 0)

line_count = 0
current_branch = ''

def add_branch_to_list(branch_name):
    global line_count
    global current_branch

    line_count = line_count + 1
    list_branches_widget.addItem(branch_name)
    if '* ' in branch_name:
        current_branch = branch_name.replace('*', '').strip()
    
    
exec_cli('git branch', add_branch_to_list)

win.resize(520, line_count * 25)
win.setWindowTitle('Git ' + os.getcwd() + ' [' + current_branch + ']')

win.show()
sys.exit(app.exec_())
    
