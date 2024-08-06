import click

@click.command()
@click.pass_context
def help_command(ctx):
    """Shows the usage of the application."""
    click.echo("\nDockyman CLI\n")
    click.echo("Commands:")
    for command in ctx.parent.command.commands.values():
        click.echo(f"  {command.name} - {command.help}")
