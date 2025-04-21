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

