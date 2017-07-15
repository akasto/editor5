import click
from editor5.editor import Editor

@click.command()
@click.argument('filepath')
def cli(filepath):
    Editor(filepath).run()

if __name__ == '__main__':
    cli()
