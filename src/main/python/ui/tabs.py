"""QtPyHammer Workspace that holds and manages an open .vmf file"""
from enum import Enum
import sys
# Third-party
from PyQt5 import QtCore, QtGui, QtWidgets
# Local
from . import viewport # ui
sys.path.insert(0, "../") # sibling packages
import ops # ops.vmf & ops,timeline
# from utilities import entity
from utilities import render
from utilities import solid
from utilities import vector
from utilities import vmf


class selection_mode(Enum):
    solo = 0
    brush_entitiy = 1
    group = 2
    face = 3


class Workspace(QtWidgets.QWidget):
    """Holds the .vmf data and viewport(s)"""
    def __init__(self, vmf_path, parent):
        super(Workspace, self).__init__(parent)
        self.ctx = parent.ctx
        self.vmf = ops.vmf.interface(self, open(vmf_path))
        self.viewport = viewport.MapViewport3D(self)
        self.viewport.add_brushes(*self.vmf.brushes)
        # self.viewport.render_manager.add_entities(*self.vmf.entities)
        # ^ neither op.vmf.interface or render.manager handle entities. yet
        # self.viewport.setViewMode.connect(...)
        layout = QtWidgets.QVBoxLayout() # holds the viewport
        # ^ QSplitter(s) will be used for quad viewports
        layout.addWidget(self.viewport)
        self.setLayout(layout)
        self.viewport.setFocus() # not working
        self.viewport.raycast.connect(self.raycast) # get 3D ray from viewport
        self.selection_mode = selection_mode.group
        self.selection = {"brushes": set(), "faces": set(), "entities": set()}
        # self.timeline = ops.timeline.edit_history() # also handles multiplayer
        ### EDIT TIMELINE NOTES ###
        # what happens when a user brings "logs in" and pushes all their changes to the shared state?
        # since we're still saving as .vmf, history is saved as it's own file
        # ? branches and reading timelines efficiently (chronological sorting) ?
        # append mode file writing
        ### END EDIT TIMELINE NOTES ###
        # TODO: viewport splitter(s), toolbar (grid controls etc.),
        # selection mode widget, hotkeys (defined in settings)

    def raycast(self, ray_origin, ray_direction):
        """Get the object hit by ray"""
        # test ray against selectable objects
##        print("calcualting raycast")
        ray_end = ray_origin + ray_direction
        for brush in self.vmf.brushes:
            states = set()
            for normal, distance in brush.planes:
                starts_behind = vector.dot(ray_origin, normal) > distance
                ends_behind = vector.dot(ray_end, normal) >= distance
                states.add(starts_behind + ends_behind) # orderless encoding 012
            if (True + False) in states:
##                print(brush.id, sep="\t")
        # modify Workspace.selection based on result
##        if ctrl in self.viewport.keys: # add selection key (defined in settings)
##            self.selection[hit_type].add(hit_object)

    def close(self):
        # release used memory eg. self.viewport.render_manager buffers
        super(Workspace, self).close()
