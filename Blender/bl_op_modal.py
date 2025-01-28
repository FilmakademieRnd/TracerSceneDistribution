"""
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
"""

import bpy
from mathutils import Vector
from .bl_op import EditControlPointHandle, EvaluateSpline, AnimationRequest, ToggleAutoUpdate
from .Core.tools import update_curve
from .Core.ServerAdapter import send_lock_msg, send_unlock_msg
from .settings import TracerData

### MODAL Operator. It is called every 0.1 seconds checking for any changes to the editable objects in the scene
# Called at DoDistribute Operator in bl_op.py
class UpdateSender(bpy.types.Operator):
    bl_idname = "wm.real_time_updater"
    bl_label = "Real-Time Updater"

    _timer = None
    
    def modal(self, context, event):
        if not context.window_manager.scene_manager.is_distributed:
            return {'PASS_THROUGH'}

        if event.type == 'TIMER':
            context.window_manager.scene_manager.check_for_updates()
        
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm: bpy.types.WindowManager = context.window_manager
        tracer_collection: bpy.types.Collection = bpy.data.collections.get("TRACER_Collection")

        if not tracer_collection:
            return {'CANCELLED'}

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
class SingleSelect(bpy.types.Operator):
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
                    for scene_obj in self.tracer_data.scene_objects:
                        if obj == scene_obj.blender_object:
                            send_unlock_msg(scene_obj)

                # Check for new selection
                newly_selected_objects = current_selected_objects - self.last_selected_objects
                for obj in newly_selected_objects:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.blender_object:
                            send_lock_msg(scene_obj)

                # Update the last selected objects set
                self.last_selected_objects = current_selected_objects

            if not self.scene_manager.is_distributed:
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.tracer_data = context.window_manager.tracer_data
        self.scene_manager = context.window_manager.scene_manager
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)


### MODAL Operator. It is called every frame by default.
#   It executes specific functions when certain conditions are met:
#   - When DEL or X are pressed (a Control Point could have been deleted), it checks that the Animation Path is up to date. Eventually, it updates it and cleans up the data left over by the deleted point
#   - When Enter or the LMB are relesed (usually indicating that some modification has been confirmed) and Auto Update is enabled, the Path gets updated
#   - When + or shift+= are released while a Control Point Object is selected, add a new point after the selected one
#   - When ctrl+shift++ are released while a Control Point Object is selected, add a new point before the selected one
#   - When the user gets into Edit Mode while selcting a Control Point, trigger the Edit Mode on the corresponding Bezier Point of the spline
#   - When the user is into Edit Mode while selecting the Spline, record the various edits the user makes in order to be applied to later versions of the Control Path 
class InteractionListener(bpy.types.Operator):
    bl_idname = "path.interaction_listener"
    bl_label = "Start Path Operator"
    bl_description = "Listening to Interaction Events on the Animation Path Object and Sub-Objects"

    is_running = False

    def __init__(self):
        print("Start")

    def __del__(self):
        InteractionListener.is_running = False
        print("End")

    def edit_handles(self, context):
        self.layout.operator(EditControlPointHandle.bl_idname, text="Edit Handles", icon='HANDLE_ALIGNED')

    def modal(self, context, event):

        if not bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            return {'PASS_THROUGH'}
        elif self.anim_path == None:
            self.anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
        
        # If the active mode is *changing to* Object
        if self.mode != 'OBJECT' and context.mode == 'OBJECT':
            # If the active object is the control path, check which Bezier Point was being edited (if one)
            if context.active_object and context.active_object.name == "Control Path":
                active_cp_idx = EditControlPointHandle.last_selected_point_index
                EditControlPointHandle.last_selected_point_index = -1
            else:
                active_cp_idx = -1

            for cp in self.anim_path["Control Points"]:                 # For every Pointer Object
                bpy.context.view_layer.objects.active = cp              # Set it as the Active Object
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)    # Set its mode to Object
                cp.select_set(False)                                    # Deselect it, so that the operation is transparent to the user
            
            # If one of the Bezier Points of the Control Path was being edited, select the corresponding Control Point Object
            if active_cp_idx >= 0:
                self.anim_path["Control Points"][active_cp_idx].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Control Points"][active_cp_idx]
        
        # Update the current saved mode
        self.mode = context.mode

        # If the Enter or the Left Mouse Button are released (so a changed has been confirmed) and the Auto Update option is active, update the animation curve
        if  (event.type == 'LEFTMOUSE' or event.type == 'RET' or event.type == 'NUMPAD_ENTER') and event.value == 'RELEASE' and \
            (not context.object == None and (context.object.name == bpy.context.scene.tracer_properties.control_path_name or ((not context.object.parent == None) and\
                 context.object.parent.name == bpy.context.scene.tracer_properties.control_path_name))) and\
            bpy.data.objects[self.tracer_props.control_path_name] != None and bpy.data.objects[self.tracer_props.control_path_name]["Auto Update"]:
            update_curve(bpy.data.objects[self.tracer_props.control_path_name])
            # If an Animation Preview object is in the scene update also its animation
            if EvaluateSpline.anim_preview_obj_name in bpy.context.scene.objects:
                if not AnimationRequest.valid_frames:
                    self.report({'ERROR'}, "Invalid frame values for the Control Points")
                else:
                    bpy.ops.curve.evaluate_spline() # Executing EvaluateSpline operator
        
        # If the active object is one of the children of the Control Path, listen to 'Shift + =' or 'Ctrl + +' Release events,
        # this will trigger the addition of a new point to the animation path, right after the currently selected points
        if  (context.active_object in bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name].children) and \
            ((event.type == 'PLUS'and not event.ctrl and not event.shift) or (event.type == 'NUMPAD_PLUS' and event.ctrl and not event.shift) or (event.type == 'EQUAL' and event.shift and not event.ctrl)) and \
            event.value == 'RELEASE':
            bpy.ops.object.add_control_point_after()

        # If the active object is one of the children of the Control Path, listen to 'Ctrl + Shift + =' or 'Ctrl + Shift + +' Release events,
        # this will trigger the addition of a new point to the animation path, right before the currently selected points
        if  (context.active_object in bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name].children) and \
            ((event.type == 'PLUS' and event.ctrl and event.shift) or (event.type == 'NUMPAD_PLUS' and event.ctrl and event.shift) or (event.type == 'EQUAL' and event.shift and event.ctrl)) and \
            event.value == 'RELEASE':
            bpy.ops.object.add_control_point_before()

        # If new_cp_location.w >= 0, it means that there is one point in the Bezier Spline that has been moved (i.e. it has a new location)
        #  - therefore, we need to updater the location of the corresponding Control Point!
        #  - The index of the affected Control Point is "saved" in the w component of new_cp_location, while xyz represent the location vector to be applied to the Control Point
        #  - The update should take place when the editing of the Bezier Point is done (=> context.mode != 'EDIT')
        if context.mode != 'EDIT':
            for i, cp in enumerate(self.anim_path["Control Points"]):
                if i < len(self.new_cp_locations) and self.new_cp_locations[i].w == 1:
                    cp.location = self.new_cp_locations[i].xyz
                    self.new_cp_locations[i].w = 0     # Setting the w to -1 in order to avoid overwriting the location multiple times

        if (context.active_object) and (context.active_object.mode == 'OBJECT') and (context.active_object in self.anim_path["Control Points"]) and bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"]:
            # If the User is selecting a Control Point, the Object Menu will also display the possibility of jumping directly into Handles Editing
            #  - removing the entry before adding it (again) avoids duplicates
            bpy.types.VIEW3D_MT_object.remove(InteractionListener.edit_handles) # Checking whether the element is in the menu before removal takes time and does not improve the code operations
            bpy.types.VIEW3D_MT_object.append(InteractionListener.edit_handles)
        else:
            bpy.types.VIEW3D_MT_object.remove(InteractionListener.edit_handles)
            
        if context.active_object and (context.active_object.mode == 'EDIT') and (context.active_object in self.anim_path["Control Points"]):
            # If the User is trying to get into edit mode while selecting a pointer object redirect them to EDIT_CURVE mode while selecting the corresponding Curve Point
            #  - while in EDIT mode, blender will update the Left Handle and Right Handle properties od the Control Point object according to the User interactions with the Control Point
            if not ("Control Path" in bpy.data.objects and self.anim_path["Auto Update"]):
                # If the condition to enter handles edit mode are not met, switch back to object mode and emit warning
                self.report({"ERROR"}, "To edit the tangents of the path, first create one and enable Auto Update")
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            else:
                bpy.ops.curve.edit_control_point_handle()    
            
        if context.active_object and context.active_object.mode == 'EDIT' and context.active_object.name == "Control Path":
            # If the User is editing the Control Path Bezier Spline, save their moifications in the Properties of the various Control Points

            path = context.active_object.data.splines[0]
            self.new_cp_locations = []
            # Get the index of the (first) control point that is currently being edited
            for i in range(len(path.bezier_points)):
                if i >= len(self.new_cp_locations):
                    self.new_cp_locations.append(Vector((0, 0, 0, 0)))

                if  path.bezier_points[i].select_control_point  or\
                    path.bezier_points[i].select_left_handle    or\
                    path.bezier_points[i].select_right_handle:

                    #selected_cp_idx = i

                    selected_curve_cp = path.bezier_points[i]
                    cp_list = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Control Points"]
                    selected_cp = cp_list[i]

                    selected_cp["Left Handle Type"]  = selected_curve_cp.handle_left_type
                    selected_cp["Right Handle Type"] = selected_curve_cp.handle_right_type
                    selected_cp["Left Handle"]  = Vector(selected_curve_cp.handle_left - selected_curve_cp.co)
                    selected_cp["Right Handle"] = Vector(selected_curve_cp.handle_right - selected_curve_cp.co)

                    self.new_cp_locations[i].xyz = selected_curve_cp.co
                    self.new_cp_locations[i].w = 1

        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        if not InteractionListener.is_running:
            # Add the modal listener to the list of called handlers and save the Animation Path object
            context.window_manager.modal_handler_add(self)
            self.tracer_props = bpy.context.scene.tracer_properties
            self.anim_path = None
            self.new_cp_locations = []
            self.mode = 'OBJECT'

            # Check for inconsistency in Panel UI w.r.t. Auto Update property
            if (bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects) and\
                bool(bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"]) != bool(ToggleAutoUpdate.bl_label == "Disable Path Auto Update"):

                ToggleAutoUpdate.bl_label = "Disable Path Auto Update" if bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"] else "Enable Path Auto Update"
                self.anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            InteractionListener.is_running = True
        return {'RUNNING_MODAL'}