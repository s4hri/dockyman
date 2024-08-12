import click
import colorama
from dockyman.commands import init, help, setup, build, clean, status
from dockyman.utils import get_dockyman_version

# Initialize colorama
colorama.init(autoreset=True)

@click.group()
def cli():
    pass


cli.add_command(status.status_command, 'status')
cli.add_command(init.init_command, 'init')
cli.add_command(setup.setup_command, 'setup')
cli.add_command(build.build_command, 'build')
cli.add_command(clean.clean_command, 'clean')
cli.add_command(help.help_command, 'help')


def main():
    cli()

if __name__ == '__main__':
    version = get_dockyman_version()
    click.echo(f'{colorama.Fore.YELLOW}Dockyman CLI - Docker Management Tool (Version: {version})')
    main()

