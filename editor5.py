import urwid
from urwid.widget import BOX
from urwid.container import WidgetContainerMixin

import logging
import pygments
from pygments import highlight
from pygments.style import Style
from pygments.token import Token
from pygments.lexers import Python3Lexer
from pygments.formatters import Terminal256Formatter, TerminalFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler('mywidget.log')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

palette = [
    ('body','default', 'default'),
    ('footer','dark cyan', 'dark blue', 'bold'),
    ('key','dark blue', 'white', 'underline'),
    ('reversed','light cyan', 'dark blue', 'underline'),
    (pygments.token.Comment, urwid.LIGHT_GRAY, urwid.DEFAULT),
    (pygments.token.Comment.Single, urwid.LIGHT_GRAY, urwid.DEFAULT),
    (pygments.token.Literal.String.Doc, urwid.LIGHT_RED, urwid.DEFAULT),
    (pygments.token.Name.Namespace, urwid.LIGHT_BLUE, urwid.DEFAULT),
    (pygments.token.Name.Builtin, urwid.DARK_CYAN, urwid.DEFAULT),
    (pygments.token.Text, urwid.WHITE, urwid.DEFAULT),
    (pygments.token.Operator.Word, urwid.DARK_GREEN, urwid.DEFAULT),
    (pygments.token.Name, urwid.WHITE, urwid.DEFAULT),
    (pygments.token.Punctuation, urwid.WHITE, urwid.DEFAULT),
    (pygments.token.Keyword, urwid.DARK_GREEN, urwid.DEFAULT),
    (pygments.token.Name.Function, urwid.LIGHT_BLUE, urwid.DEFAULT),
    (pygments.token.Name.Class, urwid.LIGHT_BLUE, urwid.DEFAULT),
    (pygments.token.Keyword.Namespace, urwid.DARK_GREEN, urwid.DEFAULT),
    (pygments.token.Name.Builtin.Pseudo, urwid.DARK_CYAN, urwid.DEFAULT),
    (pygments.token.Name.Builtin, urwid.DARK_CYAN, urwid.DEFAULT),
    (pygments.token.Operator, urwid.WHITE, urwid.DEFAULT),
    (pygments.token.Literal.Number.Integer, urwid.DARK_RED, urwid.DEFAULT),
    (pygments.token.Literal.String, urwid.LIGHT_RED, urwid.DEFAULT),
    (pygments.token.Literal.String.Double, urwid.LIGHT_RED, urwid.DEFAULT),
    (pygments.token.Literal.String.Single, urwid.LIGHT_RED, urwid.DEFAULT),
    ]


class SourceLine(urwid.Widget):
    """ SourceLine holds information about a single line """
    _sizing = frozenset(['flow'])
    _selectable = True

    def __init__(self, text):
        self._text = text
        self.tokens = Python3Lexer().get_tokens(self.text)
        self._cursor_col = 0

    def __str__(self):
        return 'col:' + str(self.cursor_col) + ' ' + self.text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self._invalidate()

    @property
    def cursor_col(self):
        return self._cursor_col

    @cursor_col.setter
    def cursor_col(self, value):
        self._cursor_col = value
        self._invalidate()

    def rows(self, size, focus=False): #What dis do
        return 1

    def get_cursor_coords(self, size):
        (maxcol,) = size
        col = min(self.cursor_col, maxcol - 1)
        return col, 0

    def color_attribute(self, tokens):
        """
        Takes in tokens list from pygments [(token, word),] and convert it to a list of
        attributes urwid likes [(color, length),].
        """
        v = []
        for t in tokens:
            v.append((t[0], len(t[1])))
        return v

    def render(self, size, focus=False):
        (maxcol,) = size
        #num_pudding = maxcol / len(self.text.encode('utf-8'))
        cursor = None
        if focus:
            cursor = self.get_cursor_coords(size)
        tokens = Python3Lexer().get_tokens(self.text.encode('utf-8'))
        logger.info(tokens)
        color_attribute = self.color_attribute(tokens)
        logger.info(color_attribute)
        #import rpdb; rpdb.Rpdb().set_trace()
        logger.info(self.text.encode('utf-8'))
        return urwid.TextCanvas([self.text.encode('utf-8')], attr=[color_attribute], cursor=cursor, maxcol=maxcol)

    def keypress(self, size, key):
        (maxcol, ) = size
        if len(key) == 1:
            self.text = self.text[:self.cursor_col]+key+self.text[self.cursor_col:]
            self.cursor_col += 1
        elif key == 'backspace':
            if self.cursor_col != 0:
                self.text = self.text[:self.cursor_col-1]+self.text[self.cursor_col:]
                self.cursor_col -= 1
        elif key == 'left':
            if self.cursor_col > 0:
                self.cursor_col -= 1
        elif key == 'right':
            if len(self.text) > self.cursor_col:
                self.cursor_col += 1
        return key


class CursorLocation:
    def __init__(self, widgets):
        self.widgets = widgets
        self.cursor_col = 0

    def move_left(self):
        widget, line = self.widgets.get_focus()
        self.cursor_col = widget.cursor_col-1

    def move_right(self):
        widget, line = self.widgets.get_focus()
        self.cursor_col = widget.cursor_col+1

    def move_up(self):
        widget, line = self.widgets.get_focus()
        if len(self.widgets[line-1].text) < self.cursor_col:
            self.widgets[line-1].cursor_col = len(self.widgets[line-1].text)
        else:
            self.widgets[line-1].cursor_col = self.cursor_col

    def move_down(self):
        widget, line = self.widgets.get_focus()
        if len(self.widgets) <= line+1:
            return
        elif len(self.widgets[line+1].text) < self.cursor_col: # if next line is shorter then the cursor col we go to end of text
            self.widgets[line+1].cursor_col = len(self.widgets[line+1].text)
        else:
            self.widgets[line+1].cursor_col = self.cursor_col


class TextArea(urwid.Widget):
    """ TextArea has many SourceLines and manages their relationship. """
    _selectable = True

    def __init__(self):
        # SimpleFocusListWalker is a child of a list
        self.list = urwid.SimpleFocusListWalker([])
        logger.info(self.list)
        self.listbox = urwid.ListBox(self.list)
        self.cursor_location = CursorLocation(self.list)

    def __getattr__(self, name):
        return getattr(self.listbox, name)

    def keypress(self, size, key):
        if key == 'backspace':
            widget, line = self.list.get_focus()
            if widget.cursor_col == 0 and widget.text == '': # do not propgate this keypress
                self.list.remove(widget)
                self.list.set_focus(line-1)
                return key
            elif widget.cursor_col == 0 and widget.text != '':
                self.list[line-1].text += widget.text
                self.list.set_focus(line-1)
                self.list.remove(widget)
        elif key == 'enter':
            self.change_line()
        elif key == 'left':
            self.cursor_location.move_left()
        elif key == 'right':
            self.cursor_location.move_right()
        elif key == 'down':
            self.cursor_location.move_down()
        elif key == 'up':
            self.cursor_location.move_up()
        logger.info(self.cursor_location.cursor_col)
        self.listbox.keypress(size, key)
        return key

    def get_listbox(self):
        return self.listbox

    def change_line(self):
        """ Splits line into lines """
        logger.info('change line')
        logger.info(self.list.get_focus())
        widget, line = self.list.get_focus()
        cursor_pos = widget.cursor_col
        self.list.insert(line, SourceLine(widget.text[:cursor_pos]))
        widget.text = widget.text[cursor_pos:]
        self.list.set_focus(line+1)
        widget.cursor_col = 0

    def open_file(self, path):
        logger.info('open file')
        del self.list[:]
        f = open(path)
        for num, line in enumerate(f):
            # rstrip to get rid of ? mark for each \n
            edit = SourceLine(line.rstrip())
            self.list.append(edit)

    def save_file(self):
        with open('workfile', 'w') as f:
            for line in self.list:
                f.write(line.text+'\n')

registry = []

class CommandPrompt(urwid.Widget):
    _selectable = True

    def __init__(self, textarea, plugins):
        self.textarea = textarea
        self.plugins = plugins
        self.edit = urwid.Edit('', '')

    def rows(self, size, focus=False): #What dis do
        return 1

    def __getattr__(self, name):
        return getattr(self.edit, name)

    def keypress(self, size, key):
        logger.info('keypress')
        if key == 'enter':
            # check for matching command
            cmd = self.plugins.get_plugin(self.edit.edit_text)
            if cmd:
                logger.info('match')
        self.edit.keypress(size, key)
        return key


class RegistryMeta(type):
    def __init__(cls, name, bases, attrs, **kwargs):
        registry.append((name, cls))
        print("clsname: ", name)
        print("superclasses: ", bases)
        print("attributedict: ", attrs)
        print(registry)
        return super().__init__(name, bases, attrs)

class Plugin:
    def __init__(self, textarea):
        self.textarea = textarea

    def get_plugin(self, command):
        for class_name, cls_obj in registry:
            if cls_obj.command.startswith(command.split()[0]):
                return cls_obj(command, self.textarea)

class Command(object, metaclass=RegistryMeta):
    command = 'none'

class OpenFile(Command):
    command = 'open'
    def __init__(self, command, textarea):
        logger.info('Hello From OPENFILE plugin')
        logger.info(command)
        textarea.open_file(command.split()[1])

class SaveFile(Command):
    command = 'save'
    def __init__(self, command, textarea):
        logger.info('save file')
        textarea.save_file()


class Editor:
    def __init__(self):
        self.textarea = TextArea()
        self.textarea.open_file('../projects/colors.py')
        listbox = self.textarea.get_listbox()
        plugins = Plugin(self.textarea)
        self.footer = CommandPrompt(self.textarea, plugins)
        self.top = urwid.Frame(self.textarea, footer=self.footer, focus_part='body')

    def run(self):
        self.loop = urwid.MainLoop(
            self.top, palette, input_filter=self.input_filter,
        )
        self.loop.run()

    def input_filter(self, key, raw):
        if key == ['meta c']:
            self.top.focus_position = 'footer'
        if key == ['f5']:
            logger.info('save')
        if key == ['f1']:
            self.open('editor.py')
        return key


if __name__ == "__main__":
    Editor().run()
