'''
TRACER Scene Distribution Plugin Blender
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Blender is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Blender development.
 
The TRACER Scene Distribution Plugin Blender is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Blender is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Blender may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Blender Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Blender by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Blender in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''

import bpy
from .settings import TracerData
from .bl_op import DoDistribute
from .serverAdapter import send_lock_msg, send_unlock_msg;


class OBJECT_OT_single_select(bpy.types.Operator):
    bl_idname = "object.single_select"
    bl_label = "Single Object Selection and Print"
    bl_options = {'REGISTER'}

    _timer = None
    tracer_data: TracerData = None
    last_selected_objects = set()  # Variable to store the last selected object
    running = False

    def modal(self, context, event):
        if event.type == 'TIMER':
            current_selected_objects = set(context.selected_objects)

            # Check if multiple objects are selected
            if len(current_selected_objects) > 1:
                # Check if there was a previously selected object before multiple selection attempt
                previously_selected = self.last_selected_objects

                # Deselect all objects
                for obj in current_selected_objects:
                    obj.select_set(False)

                # Clear the last selected objects set
                self.last_selected_objects = set()

            else:
                # Check for deselection
                deselected_objects = self.last_selected_objects - current_selected_objects
                for obj in deselected_objects:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.editable_object:
                            send_unlock_msg(scene_obj)

                # Check for new selection
                newly_selected_objects = current_selected_objects - self.last_selected_objects
                for obj in newly_selected_objects:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.editable_object:
                            send_lock_msg(scene_obj)

                # Update the last selected objects set
                self.last_selected_objects = current_selected_objects

            if not DoDistribute.is_distributed:
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.tracer_data = bpy.context.window_manager.tracer_data
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)

