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

from .bl_op import AddPath, AddPointAfter, AddPointBefore, EvalCurve, ToggleAutoEval, ControlPointSelect

## Interface
# 
class VPET_Panel:
    bl_category = "VPET Addon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

class VPET_PT_Panel(VPET_Panel, bpy.types.Panel):
    bl_idname = "VPET_PT_PANEL"
    bl_label = "VPET"
    
    def draw(self, context):
        layout = self.layout
        #scene = context.scene
        
        row = layout.row()
        row.operator('object.zmq_install', text = 'Pip Install ZMQ')
        row.operator('object.setup_vpet', text='Setup Scene for VPET')

        row = layout.row()
        row.operator('object.setup_character', text='Setup Character for VPET')
        row.operator('object.make_obj_editable', text='Make selected Editable')
        row.operator('object.parent_to_root', text='Parent TO Root')
        
        row = layout.row()
        row.operator('object.zmq_distribute', text = "Do Distribute")
        row.operator('object.zmq_stopdistribute', text = "Stop Distribute")

        row = layout.row()
        row.prop(bpy.context.scene.vpet_properties, 'vpet_collection')
        row = layout.row()
        #row.prop(bpy.context.scene.vpet_properties, 'edit_collection')
        #row = layout.row()
        row.prop(bpy.context.scene.vpet_properties, 'server_ip')

        row = layout.row()
        row.prop(bpy.context.scene.vpet_properties, 'mixamo_humanoid', text="Mixamo Humanoid?")

        row = layout.row()
        row.operator('object.rpc', text = "RPC CHANGE LATER")

class VPET_PT_Anim_Path_Panel(VPET_Panel, bpy.types.Panel):
    bl_idname = "VPET_PT_ANIM_PATH_PANEL"
    bl_label = "Animation Path"

    def draw(self, context):
        layout = self.layout

        if bpy.context.mode == 'EDIT_CURVE':
            #if the user is edidting the points of the bezier spline, disable Control Point features and display message
            row = layout.row()
            row.label(text="Feature not available in Edit Curve Mode")
        else:
            row = layout.row()
            row.operator(AddPath.bl_idname, text='Add Control Path')
            row.operator(EvalCurve.bl_idname, text='Evaluate Curve')
            row = layout.row()
            row.operator(AddPointAfter.bl_idname, text='New Point After')
            row.operator(AddPointBefore.bl_idname, text='New Point Before')
            if AddPath.default_name in bpy.data.objects:
                row = layout.row()
                row.operator(ToggleAutoEval.bl_idname, text=ToggleAutoEval.bl_label)

class VPET_PT_Control_Points_Panel(VPET_Panel, bpy.types.Panel):
    bl_idname = "VPET_PT_control_points_panel"
    bl_label = "Control Points"

    # By setting VPET_PT_Anim_Path_Panel as parent of Control_Points_Panel, this panel will be nested into its parent in the UI 
    bl_parent_id = VPET_PT_Anim_Path_Panel.bl_idname

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
            row.label(text="To use the Control Point Property Panel and the Path Auto Update")
            row = layout.row()
            row.label(text="Disable Proportional Editing")
        elif AddPath.default_name in bpy.data.objects:
            # Getting Control Points Properties
            cp_props = bpy.context.scene.control_point_settings
            anim_path = bpy.data.objects[AddPath.default_name]
            grid = layout.grid_flow(row_major=True, columns=6, even_rows=True, even_columns=True, align=True)

            title1 = grid.box(); title1.alert = True; title1.label(text="NAME")
            title2 = grid.box(); title2.alert = True; title2.label(text="POSITION")
            title3 = grid.box(); title3.alert = True; title3.label(text="FRAME")
            title4 = grid.box(); title4.alert = True; title4.label(text="IN")
            title5 = grid.box(); title5.alert = True; title5.label(text="OUT")
            title6 = grid.box(); title6.alert = True; title6.label(text="STYLE")
                
            # Setting the owner of the data, if it exists
            cp_list_size = len(anim_path["Control Points"])
            for i in range(cp_list_size):
                cp = anim_path["Control Points"][i]
                row = layout.row()

                name_select = grid.box(); name_select.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                name_select.operator(ControlPointSelect.bl_idname, text=cp.name).cp_name = cp.name
                # TODO: try to make the name a button for selecting the contol point to edit
                # Highlight the selected Control Point by marking the panel entry with a dot
                if (not context.active_object == None) and (context.active_object.name == cp.name):
                    grid.prop(cp_props, property="position", text="", slider=False)
                    grid.prop(cp_props, property="frame", text="", slider=False)
                    grid.prop(cp_props, property="ease_in", text="", slider=True)
                    grid.prop(cp_props, property="ease_out", text="", slider=True)
                    grid.prop_menu_enum(data=cp_props, property="style", text=cp["Style"])
                else:
                    postn = grid.box(); postn.label(text=str(i));           postn.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                    frame = grid.box(); frame.label(text=str(cp["Frame"])); frame.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                    # If a frame value is not valid (smaller than the previous or bigger than the following,
                    # mark it as an alert
                    if (  i > 0             and cp["Frame"] < anim_path["Control Points"][i-1]["Frame"])\
                    or (i+1 < cp_list_size  and cp["Frame"] > anim_path["Control Points"][i+1]["Frame"]):
                        frame.alert = True
                    else:
                        frame.alert = False
                    e__in = grid.box(); e__in.label(text=str(cp["Ease In"]));   e__in.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                    e_out = grid.box(); e_out.label(text=str(cp["Ease Out"]));  e_out.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                    style = grid.box(); style.label(text=cp["Style"]);          style.alignment = 'CENTER' # alignment does nothing. Buggy Blender.
                

class VPET_PT_Anim_Path_Menu(bpy.types.Menu):
    bl_label = "Animation Path"	   
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