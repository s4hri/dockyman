# MIT License
#
# Copyright (c) 2025 Istituto Italiano di Tecnologia (IIT)
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import click
import config

from colorama import Fore
from dockyman.commands import init, help, setup, build, clean, status, pull, push, run, stop
from dockyman.utils import get_dockyman_version

@click.group()
def cli():
    pass


cli.add_command(status.status_command, 'status')
cli.add_command(init.init_command, 'init')
cli.add_command(setup.setup_command, 'setup')
cli.add_command(build.build_command, 'build')
cli.add_command(clean.clean_command, 'clean')
cli.add_command(push.push_command, 'push')
cli.add_command(pull.pull_command, 'pull')
cli.add_command(run.run_command, 'run')
cli.add_command(stop.stop_command, 'stop')
cli.add_command(help.help_command, 'help')


def main():
    cli()

if __name__ == '__main__':
    version = get_dockyman_version()
    click.echo(f'\n{Fore.YELLOW}Dockyman CLI - Docker Management Tool (Version: {version})\n')
    main()
