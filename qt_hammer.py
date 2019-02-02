import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np # for vertex buffers
from OpenGL.GL import * # Installed via pip (PyOpenGl 3.1.0)
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import *
import viewports

sys.path.insert(0, 'utilities')
import vmf_tool
import solid_tool

def except_hook(cls, exception, traceback): # for debugging python called by Qt
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

def print_methods(obj, filter_lambda=lambda x: True, joiner='\n'):
    methods = [a for a in dir(obj) if hasattr(getattr(obj, a), '__call__')]
    print(joiner.join([m for m in methods if filter_lambda(m) == True]))

# TODOS:
# context menu (set shortcut)
# clearly log & report crashes!
# especially those that occur in slots (sys.excepthook)
# vmf manager
# edit vmf as text (text editor)
# IDE (colours, auto-complete) preserve solids
# use IDE tools to attempt recovery of corrupt vmfs
# recovery tools in general

new_file_count = 0

# disable menu items when they cannot be used

# need a QSettings to store: LOAD HERE!
#  recent files
#  OpenGL settings
#  game configurations
#  default filepaths
#  keybinds
#  ...
# .ini should be straightforward enough

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()
window.setWindowTitle('QtPyHammer')
window.setGeometry(640, 400, 640, 480)
window.setTabPosition(QtCore.Qt.TopDockWidgetArea, QtWidgets.QTabWidget.North)

# read .fgd(s) for entity_data
# prepare .vpks (grab directories)
# mount custom data (tf/custom etc)

### MAIN MENU ###
menu = QtWidgets.QMenuBar()

file_menu = menu.addMenu('&File')
new_file = file_menu.addAction('&New')
new_file.setShortcut('Ctrl+N')

##tabs = []
##def new_tab(vmf=None): # add a new viewport
##    global new_file_count, window, tabs
##    new_file_count += 1
##    map_dock = viewports.QuadViewportDock(f'untitled {new_file_count}') # feed in vmf here
##    tabs.append(map_dock)
##    window.addDockWidget(QtCore.Qt.TopDockWidgetArea, map_dock)
##    # add dock as tab if already have one dock ?
##    map_dock.widget().layout().itemAt(2).widget().sharedGLsetup() # too soon
    
##new_file.triggered.connect(new_tab) # also need to load .vmf into the manager

open_file = file_menu.addAction('&Open')
open_file.setShortcut('Ctrl+O')
open_browser = QtWidgets.QFileDialog()
open_browser.setDirectory('F:/Modding/tf2 maps/') # default map directory
open_browser.setDefaultSuffix('vmf') # for saving, doesn't filter
# set to open file and filter for .vmf

def load_vmf():
    vmf_name = QtWidgets.QFileDialog.getOpenFileName(filter='Valve Map Format (*.vmf)')[0]
    # load on a seoerate thread from ui
    # progress bar
    #   how do we measure progress when we don't have a value for 100% ?
    # reuse new_tab
    print(vmf_name)

open_file.triggered.connect(load_vmf)

file_menu.addAction('&Save').setShortcut('Ctrl+S')
file_menu.addAction('Save &As').setShortcut('Ctrl+Shift+S')
file_menu.addSeparator()
import_menu = file_menu.addMenu('Import')
import_menu.addAction('.obj')
import_menu.addAction('.blend')
export_menu = file_menu.addMenu('Export')
export_menu.addAction('.obj')
export_menu.addAction('.blend')
file_menu.addSeparator()
file_menu.addAction('&Options')
file_menu.addSeparator()
file_menu.addAction('Compile').setShortcut('F9')
file_menu.addSeparator()
file_menu.addAction('Exit')

edit_menu = menu.addMenu('&Edit')
edit_menu.addAction('Undo').setShortcut('Ctrl+Z')
edit_menu.addAction('Redo').setShortcut('Ctrl+Y')
edit_menu.addMenu('&History...')
edit_menu.addSeparator()
edit_menu.addAction('Find &Entites').setShortcut('Ctrl+Shift+F')
edit_menu.addAction('&Replace').setShortcut('Ctrl+Shift+R')
edit_menu.addSeparator()
edit_menu.addAction('Cu&t').setShortcut('Ctrl+X')
edit_menu.addAction('&Copy').setShortcut('Ctrl+C')
edit_menu.addAction('&Paste').setShortcut('Ctrl+V')
edit_menu.addAction('Paste &Special').setShortcut('Ctrl+Shift+V')
edit_menu.addAction('&Delete').setShortcut('Del')
edit_menu.addSeparator()
edit_menu.addAction('P&roperties').setShortcut('Alt+Enter')

map_menu = menu.addMenu('&Map')
snap_to_grid = map_menu.addAction('&Snap to Grid')
snap_to_grid.setShortcut('Shift+W')
snap_to_grid.setCheckable(True)
snap_to_grid.setChecked(True)
show_grid = map_menu.addAction('Sho&w Grid')
show_grid.setShortcut('Shift+R')
show_grid.setCheckable(True)
show_grid.setChecked(True)
grid_settings = map_menu.addMenu('&Grid Settings')
map_menu.addSeparator()
map_menu.addAction('&Entity Report')
map_menu.addAction('&Zooify') # make an asset zoo / texture pallets
map_menu.addAction('&Check for Problems').setShortcut('Alt+P')
map_menu.addAction('&Diff Map File')
map_menu.addSeparator()
map_menu.addAction('Find Leak (.lin)')
map_menu.addAction('Portalfile (.prt)')
map_menu.addSeparator()
map_menu.addAction('Show &Information')
map_menu.addAction('&Map Properties') # skybox / detail file

search_menu = menu.addMenu('&Search') # connect to active editor.find()
search_menu.addAction('Find Entity')
search_menu.addAction('Find IO')
search_menu.addAction('Find + Replace IO')
search_menu.addSeparator()
search_menu.addAction('Go to Coordinates')
search_menu.addAction('Go to Brush Number')

view_menu = menu.addMenu('&View')
view_menu.addAction('Center 2D Views on selection').setShortcut('Ctrl+E')
view_menu.addAction('Center 3D Views on selection').setShortcut('Ctrl+Shift+E')
view_menu.addAction('Go To &Coordinates')
view_menu.addSeparator()
io_links = view_menu.addAction('Show IO &Links')
io_links.setCheckable(True)
show_2d_models = view_menu.addAction('Show &Models in 2D')
show_2d_models.setCheckable(True)
show_2d_models.setChecked(True)
ent_names = view_menu.addAction('Entity &Names')
ent_names.setCheckable(True)
ent_names.setChecked(True)
radius_culling = view_menu.addAction('Radius &Culling')
radius_culling.setShortcut('C')
radius_culling.setCheckable(True)
radius_culling.setChecked(True)
view_menu.addSeparator()
view_menu.addAction('&Hide').setShortcut('H')
view_menu.addAction('Hide Unselected').setShortcut('Ctrl+H')
view_menu.addAction('&Unhide').setShortcut('U')
view_menu.addSeparator()
view_menu.addAction('Selection to Visgroup')
view_menu.addSeparator()
view_menu.addAction('&OpenGL Settings')

tools_menu = menu.addMenu('&Tools')
tools_menu.addAction('&Group').setShortcut('Ctrl+G')
tools_menu.addAction('&Ungroup').setShortcut('Ctrl+U')
tools_menu.addSeparator()
tools_menu.addAction('&Tie to Entitiy').setShortcut('Ctrl+T')
tools_menu.addAction('&Move to World').setShortcut('Ctrl+Shift+W')
tools_menu.addSeparator()
tools_menu.addAction('&Apply Texture').setShortcut('Shift+A')
tools_menu.addAction('&Replace Textures')
tools_menu.addAction('Texture &Lock').setShortcut('Shift+L')
tools_menu.addSeparator()
tools_menu.addAction('&Sound Browser').setShortcut('Alt+S')
tools_menu.addSeparator()
tools_menu.addAction('Transform').setShortcut('Crtl+M')
tools_menu.addAction('Snap Selection to Grid').setShortcut('Crtl+B')
tools_menu.addAction('Snap Selection to Grid Individually').setShortcut('Crtl+Shift+B')
tools_menu.addSeparator()
tools_menu.addAction('Flip Horizontally').setShortcut('Ctrl+L')
tools_menu.addAction('Flip Vertically').setShortcut('Ctrl+I')
tools_menu.addSeparator()
tools_menu.addAction('&Create Prefab').setShortcut('Ctrl+R')

help_menu = menu.addMenu('&Help')
help_menu.addAction('Offline Help').setShortcut('F1')
help_menu.addSeparator()
help_menu.addAction('About QtPyHammer')
help_menu.addAction('About Qt')
help_menu.addAction('License')
help_menu.addSeparator()
help_menu.addAction('Valve Developer Community')
help_menu.addAction('TF2Maps.net')

file_act = QtWidgets.QAction()
menu.addAction(file_act) # ???

window.setMenuBar(menu)

# TOOLBARS
key_tools = QtWidgets.QToolBar('Tools 1')
key_tools.setMovable(False)
button_1 = QtWidgets.QToolButton() # need icons (.png)
button_1.setToolTip('Toggle 2D grid visibility')
key_tools.addWidget(button_1)
button_2 = QtWidgets.QToolButton()
button_2.setToolTip('Toggle 3D grid visibility')
key_tools.addWidget(button_2)
button_3 = QtWidgets.QToolButton()
button_3.setToolTip('Grid scale -  [')
key_tools.addWidget(button_3)
button_3 = QtWidgets.QToolButton()
button_3.setToolTip('Grid scale +  ]')
key_tools.addWidget(button_3)
key_tools.addSeparator()
# undo redo | carve | group ungroup ignore | hide unhide alt-hide |
# cut copy paste | cordon radius | TL <TL> | DD 3D DW DA |
# compile helpers 2D_models fade CM detail NO_DRAW
window.addToolBar(QtCore.Qt.TopToolBarArea, key_tools)

# right-click "split view" anywhere? (blender style)
# viewport type / mode selector

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None): # parent is the document highlighted
        super(Highlighter, self).__init__(parent)
        self.text_formats = []
        f1 = QtGui.QTextCharFormat()
        f1.setBackground(QtCore.Qt.yellow)
        self.text_formats.append(f1)
        f2 = QtGui.QTextCharFormat()
        f2.setFontWeight(QtGui.QFont.Bold)
        f2.setBackground(QtCore.Qt.yellow)
        self.text_formats.append(f2)
        
        self.expressions = []
        f1_exp = QtCore.QRegularExpression("\".*\"") # catches quotes
        self.expressions.append(f1_exp)
        f2_exp = QtCore.QRegularExpression("\[.*\]|\(.*\)|[0-9]")
        self.expressions.append(f2_exp)


        self.rules = {0: 0, 1: 1}

        # match with a dict

    def highlightBlock(self, text):
        for text_format, expression in self.rules.items():
            text_format = self.text_formats[text_format]
            expression = self.expressions[expression]
            matcher = expression.globalMatch(text)
            while matcher.hasNext():
                match = matcher.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, text_format)

# can we make diff higlighting?
# need lots of stats on lines
# can we jump straight into the undo-redo stack?
# apply / preview updates (changes)

# this is where the magic happens
vmf = open('tests/vmfs/test.vmf') # QFile may load with less errors
window.setWindowTitle(f'QtPyHammer - [{vmf.name}]')
vmf_text = vmf.read()
vmf_object = vmf_tool.namespace_from(vmf_text) # interacts
# solids -> iterable
if hasattr(vmf_object.world, 'solid'):
    vmf_object.world.solids = [vmf_object.world.solid]
    del vmf_object.world.solid
if not hasattr(vmf_object.world, 'solids'):
    vmf_object.world['solids'] = []
# entities -> iterable
if hasattr(vmf_object, 'entity'):
    vmf_object.entities = [vmf_object.entity]
    del vmf_object.entity
if not hasattr(vmf_object, 'entities'):
    vmf_object['entities'] = []

# map brushes into a buffer
# when editing a brush
# keep old
# make new from start line to terminator
# remove from draw calls
# add new to buffer

# defrag buffer & maps function(s)
        
workspace = QtWidgets.QSplitter(QtCore.Qt.Vertical)
viewport = viewports.Viewport3D(30)

# load vmf into viewport

def vmf_setup(viewport, vmf_object):
    string_solids = [] # need starting line number of each for snappy updates
    for brush in vmf_object.world.solids:
        string_solids.append(brush)
    for entity in vmf_object.entities: # do these cases ever occur?
        if hasattr(entity, 'solid'):
            if isinstance(entity.solid, vmf_tool.namespace):
                string_solids.append(entity.solid)
        if hasattr(entity, 'solids'):
            if isinstance(entity.solids[0], vmf_tool.namespace):
                string_solids += entity.solids
    brushes = []
    for brush in string_solids:
        try:
            brushes.append(solid_tool.solid(brush))
        except Exception as exc:
            print(f"Invalid solid! (id {brush.id})")
            print(exc, '\n')

    vertices = []
    indices = []
    buffer_map = dict() # brush.id: (start, len) # start and len in index buffer
    for solid in brushes: # build buffer
        buffer_map[solid.string_solid.id] = (len(indices), len(solid.indices))
        vertices += solid.vertices
        indices += solid.indices

    try: # GLSL 450
        # Vertex Shaders
        vert_shader_brush = compileShader(open('shaders/GLSL_450/verts_brush.v', 'rb'), GL_VERTEX_SHADER)
        vert_shader_displacement = compileShader(open('shaders/GLSL_450/verts_displacement.v', 'rb'), GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_shader_brush_flat = compileShader(open('shaders/GLSL_450/brush_flat.f', 'rb'), GL_FRAGMENT_SHADER)
        frag_shader_displacement_flat = compileShader(open('shaders/GLSL_450/displacement_flat.f', 'rb'), GL_FRAGMENT_SHADER)
    except RuntimeError as exc: # GLES 3.00
        # Vertex Shaders
        vert_shader_brush = compileShader(open('shaders/GLES_300/verts_brush.v', 'rb'), GL_VERTEX_SHADER)
        vert_shader_displacement = compileShader(open('shaders/GLES_300/verts_displacement.v', 'rb'), GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_shader_brush_flat = compileShader(open('shaders/GLES_300/brush_flat.f', 'rb'), GL_FRAGMENT_SHADER)
        frag_shader_displacement_flat = compileShader(open('shaders/GLES_300/displacement_flat.f', 'rb'), GL_FRAGMENT_SHADER)
    # Programs
    program_flat_brush = compileProgram(vert_shader_brush, frag_shader_brush_flat)
    program_flat_displacement = compileProgram(vert_shader_displacement, frag_shader_displacement_flat)
    glLinkProgram(program_flat_brush)
    glLinkProgram(program_flat_displacement)

    # Vertex Buffer
    VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
    glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, np.array(vertices, dtype=np.float32), GL_STATIC_DRAW)
    # Index Buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, np.array(indices, dtype=np.uint32), GL_STATIC_DRAW)
    # Vertex Format
    glEnableVertexAttribArray(0) # vertex_position
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
    glEnableVertexAttribArray(1) # vertex_normal
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
    glEnableVertexAttribArray(2) # vertex_uv
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
    glEnableVertexAttribArray(4) # editor_colour
    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))
    # glEnableVertexAttribArray(5) # blend_alpha (displacements, overrides 1)
    glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))

    viewport.buffers = [VERTEX_BUFFER, INDEX_BUFFER]
    viewport.programs = [program_flat_brush, program_flat_displacement]
    viewport.draw_calls[viewport.programs[0]] = (0, len(indices))

workspace.addWidget(viewport)
editor = QtWidgets.QPlainTextEdit()
font = QtGui.QFont()
font.setFamily("Courier")
font.setFixedPitch(True) # fullwidth
font.setPointSize(8)
editor.setFont(font)
editor.insertPlainText(vmf_text)
editor.document().clearUndoRedoStacks(QtGui.QTextDocument.UndoStack)
# document switcher & some options in a layout? (font, font size etc)
# top bar of things
editor.setDocumentTitle('test.vmf')
# cursor pos getter (line:character)
# if A < line_no < B:
#     solid = X
# keep diffs (utilise undo / redo)
# undo history
# wireframe preview
# enter to apply
# string to solid
# tris to solid (OBJ LOAD / MODEL EDITING)
# solid to string (VMF FILE)
# solid to tris (RENDERER)
editor.setTabStopWidth(20) # approx~ 4 spaces
# more r-click options
# contract segment (model-view ?)
# show limited attributes per solid.side (simplified view)
# line numbers
# live diff
# update viewport & vmf_object
syntax_highlighter = Highlighter(editor.document())
##syntax_highlighter.setDocument(editor.document()) # doesn't update automatically?
workspace.addWidget(editor)

window.setCentralWidget(workspace)

##window.showMaximized() # start with maximised window
window.show()

viewport.executeGL(vmf_setup, vmf_object) # need active gl context
# use surfaces & QGLWindow?
# http://doc.qt.io/qt-5/qtgui-index.html#opengl-and-opengl-es-integration

workspace.widget(0).sharedGLsetup()

app.exec_() # loop?




