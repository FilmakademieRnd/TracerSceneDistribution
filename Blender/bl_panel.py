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

from .bl_op import  DoDistribute, StopDistribute, SetupScene, SetupCharacter, InstallZMQ, MakeEditable, ParentToRoot,\
                    InteractionListener, AddPath, AddPointAfter, AddPointBefore, UpdateCurveViz, ToggleAutoUpdate,\
                    ControlPointSelect, EditControlPointHandle, FKIKToggle, EvaluateSpline, AnimationRequest, AnimationSave

## Initialising name and core properties of all panels of the Add-On
# 
class TRACER_Panel:
    bl_category = "TRACER Add-On"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

# Define Layout of the main TRACER Add-On Panel, grouping TRACER communication functionalities
class TRACER_PT_Panel(TRACER_Panel, bpy.types.Panel):
    bl_idname = "TRACER_PT_PANEL"
    bl_label = "TRACER"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.operator(InstallZMQ.bl_idname, text = InstallZMQ.bl_label)
        row.operator(SetupScene.bl_idname, text = SetupScene.bl_label)

        row = layout.row()
        row.operator(SetupCharacter.bl_idname, text = SetupCharacter.bl_label)
        row.operator(MakeEditable.bl_idname, text = MakeEditable.bl_label)
        row.operator(ParentToRoot.bl_idname, text = ParentToRoot.bl_label)
        
        row = layout.row()
        row.operator(DoDistribute.bl_idname, text = DoDistribute.bl_label)
        row.operator(StopDistribute.bl_idname, text = StopDistribute.bl_label)

        row = layout.row()
        row.prop(bpy.context.scene.tracer_properties, 'tracer_collection')
        row = layout.row()
        row.prop(bpy.context.scene.tracer_properties, 'server_ip')

        #? Still needed?
        #row = layout.row()
        #row.prop(bpy.context.scene.tracer_properties, 'humanoid_rig', text="Humanoid Rig?")

        row = layout.row()
        row.operator('object.rpc', text = "RPC CHANGE LATER")

# Define Layout for the Animation Control Path Panel, grouping functionalities related to editing the Control Path for an animation 
class TRACER_PT_Anim_Path_Panel(TRACER_Panel, bpy.types.Panel):
    bl_idname = "TRACER_PT_ANIM_PATH_PANEL"
    bl_label = "Animation Control Path Panel"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(InteractionListener.bl_idname, text=InteractionListener.bl_label)   # Invoke Modal Operaton for automatically update the Animation Path in (almost) real-time
        if bpy.context.mode == 'EDIT_CURVE':
            #if the user is edidting the points of the bezier spline, disable Control Point features and display message
            row = layout.row()
            row.alert = True
            row.label(text="Feature not available in Edit Curve Mode")
        else:
            row = layout.row()
            row.operator(AddPath.bl_idname, text=AddPath.bl_label)
            row.operator(UpdateCurveViz.bl_idname, text=UpdateCurveViz.bl_label)
            row = layout.row()
            row.operator(AddPointAfter.bl_idname, text=AddPointAfter.bl_label)
            row.operator(AddPointBefore.bl_idname, text=AddPointBefore.bl_label)
            if context.active_object and context.active_object.type == 'ARMATURE':
                row = layout.row()
                row.operator(FKIKToggle.bl_idname, text=FKIKToggle.bl_label)
            if AddPath.default_name in bpy.data.objects:
                row = layout.row()
                row.operator(ToggleAutoUpdate.bl_idname, text=ToggleAutoUpdate.bl_label)

# Define Layout for the Control Points Panel, grouping functionalities related to editing the Points of the Control Path 
class TRACER_PT_Control_Points_Panel(TRACER_Panel, bpy.types.Panel):
    bl_idname = "TRACER_PT_control_points_panel"
    bl_label = "Control Points Panel"

    # By setting TRACER_PT_Anim_Path_Panel as parent of Control_Points_Panel, this panel will be nested into its parent in the UI 
    bl_parent_id = TRACER_PT_Anim_Path_Panel.bl_idname

    def draw(self, context):
        layout = self.layout

        # If the proportional editing is ENABLED, show warning message and disable control points property editing
        if bpy.context.mode == 'EDIT_CURVE':
            #if the user is edidting the points of the bezier spline, disable Control Point features and display message
            row = layout.row()
            row.label(text="Feature not available in Edit Curve Mode")
        elif bpy.context.tool_settings.use_proportional_edit_objects:
            # If the proportional editing is ENABLED, show warning message and disable control points property editing
            row = layout.row()
            row.label(text="To use the Control Point Editing Panel and the Path Auto Update")
            row = layout.row()
            row.label(text="Disable Proportional Editing")
        elif not (AddPath.default_name in bpy.data.objects and bpy.data.objects[AddPath.default_name]["Auto Update"]):
            # If Auto Update editing is DISABLED, disable control points property editing
            row = layout.row()
            row.label(text="To use the Control Point Editing Panel")
            row = layout.row()
            row.label(text="Enable Control Point Editing Panel")
        elif AddPath.default_name in bpy.data.objects:
            # Getting Control Points Properties
            cp_props = bpy.context.scene.control_point_settings
            anim_path = bpy.data.objects[AddPath.default_name]
            grid = layout.grid_flow(row_major=True, columns=5, even_rows=True, even_columns=True, align=True)

            title1 = grid.box(); title1.alert = True; title1.label(text="NAME")
            title2 = grid.box(); title2.alert = True; title2.label(text="POSITION")
            title3 = grid.box(); title3.alert = True; title3.label(text="FRAME")
            title4 = grid.box(); title4.alert = True; title4.label(text="IN")
            title5 = grid.box(); title5.alert = True; title5.label(text="OUT")
            #! Style is not currently used by the framework
            #title6 = grid.box(); title6.alert = True; title6.label(text="STYLE")
                
            # Setting the owner of the data, if it exists
            cp_list_size = len(anim_path["Control Points"])
            for i in range(cp_list_size):
                cp = anim_path["Control Points"][i]
                row = layout.row()

                name_select = grid.box(); name_select.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                name_select.operator(ControlPointSelect.bl_idname, text=cp.name).cp_name = cp.name
                
                # Highlight the selected Control Point by marking the panel entry with a dot
                if (not context.active_object == None) and (context.active_object.name == cp.name):
                    grid.prop(cp_props, property="position", text="", slider=False)
                    grid.prop(cp_props, property="frame", text="", slider=False)
                    grid.prop(cp_props, property="ease_in", text="", slider=True)
                    grid.prop(cp_props, property="ease_out", text="", slider=True)
                    #! Style is not currently used by the framework
                    # grid.prop_menu_enum(data=cp_props, property="style", text=cp["Style"])
                else:
                    postn = grid.box(); postn.alignment = 'CENTER'; postn.label(text=str(i));           # alignment does nothing. Buggy Blender.
                    
                    frame = grid.box()
                    # If a frame value is not valid (smaller than the previous or bigger than the following,
                    # mark it as an alert
                    if (  i > 0             and cp["Frame"] < anim_path["Control Points"][i-1]["Frame"])\
                    or (i+1 < cp_list_size  and cp["Frame"] > anim_path["Control Points"][i+1]["Frame"]):
                        frame.alert = True
                    else:
                        frame.alert = False
                    frame.alignment = 'CENTER'; frame.label(text=str(cp["Frame"]));                         # alignment does nothing. Buggy Blender.
                    
                    e__in = grid.box(); e__in.alignment = 'CENTER'; e__in.label(text=str(cp["Ease In"]));   # alignment does nothing. Buggy Blender.
                    e_out = grid.box(); e_out.alignment = 'CENTER'; e_out.label(text=str(cp["Ease Out"]));  # alignment does nothing. Buggy Blender.
                    #! Style is not currently used by the framework
                    # style = grid.box(); style.alignment = 'CENTER'; style.label(text=cp["Style"]);          # alignment does nothing. Buggy Blender.
            
            row = layout.row()
            row.operator(EditControlPointHandle.bl_idname, text=EditControlPointHandle.bl_label)
            if context.active_object and context.active_object.type == 'ARMATURE':
                row = layout.row()
                row.operator(EvaluateSpline.bl_idname, text=EvaluateSpline.bl_label)
                row = layout.row()
                row.operator_menu_enum(AnimationRequest.bl_idname, property="animation_request_mode", text=AnimationRequest.bl_label)  #(AnimationRequest.bl_idname, text=AnimationRequest.bl_label)
                row.operator(AnimationSave.bl_idname, text=AnimationSave.bl_label)

# Define Layout for the Animation Control Path (sub)menu, to be added to the Add Menu in Blender
# It groups together Operators to add new Control Paths and Points
class TRACER_PT_Anim_Path_Menu(bpy.types.Menu):
    bl_label = "Animation Control Path"
    bl_idname = "OBJECT_MT_custom_spline_menu"

    def draw(self, context):
        if bpy.context.mode == 'OBJECT':
            self.layout.operator(AddPath.bl_idname,
                                 text="Animation Path",
                                 icon='OUTLINER_DATA_CURVE')
            self.layout.operator(AddPointAfter.bl_idname,
                                 text="Path Control Point After Selected",
                                 icon='RESTRICT_SELECT_OFF') # alternative option EMPTY_SINGLE_ARROW
            self.layout.operator(AddPointBefore.bl_idname,
                                 text="Path Control Point Before Selected",
                                 icon='RESTRICT_SELECT_OFF') # alternative option EMPTY_SINGLE_ARROW