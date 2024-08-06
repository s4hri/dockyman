import click
from dockyman.commands import init, help, setup, build

@click.group()
def cli():
    pass

cli.add_command(init.init_command, 'init')
cli.add_command(setup.setup_command, 'setup')
cli.add_command(build.build_command, 'build')
cli.add_command(help.help_command, 'help')


def main():
    cli()

if __name__ == '__main__':
    main()
