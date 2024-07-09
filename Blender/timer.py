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
import time  # Ensure time module is imported

class TimerClass:
    s_timestepsBase = 128

    def __init__(self, framerate=60):
        self.framerate = framerate
        self.m_timesteps = (TimerClass.s_timestepsBase // self.framerate) * self.framerate
        self.last_update_time = time.time()
        self.start_time = time.time()  # Initialize start_time for continuous measurement
        self.time_60_start_time = None  # To measure time from 60 to 119
        self.accumulated_increments = 0.0  # To accumulate fractional increments

    def update_time(self):
        global vpet
        current_time = time.time()
        elapsed = current_time - self.last_update_time  # Elapsed time since last update
        increments = elapsed * self.framerate  # Calculate potential fractional increments
        
        # Accumulate increments (including fractional parts)
        self.accumulated_increments += increments
        
        # Determine how many whole increments to apply
        whole_increments = int(self.accumulated_increments)
        
        # Adjust accumulated increments to keep only the fractional part
        self.accumulated_increments -= whole_increments
        
        # Update vpet.time with whole increments
        new_time = vpet.time + whole_increments     

        # Handle cycle reset and ensure vpet.time remains an integer
        if new_time >= self.m_timesteps - 1:
            vpet.time = int(new_time % self.m_timesteps)  # Loop back if exceeding m_timesteps
            self.start_time = current_time  # Reset start time for the new cycle
            self.time_60_start_time = None  # Reset to measure next span from 60 to 119 again
        else:
            vpet.time = int(new_time)
        
        self.last_update_time = current_time  # Update the last_update_time for the next cycle

class TimerModalOperator(bpy.types.Operator):
    """Operator to run a timer at specified framerate"""
    bl_idname = "wm.timer_modal_operator"
    bl_label = "Timer Modal Operator"

    _timer = None
    my_instance = TimerClass(framerate=60)  # Create an instance of TimerClass

    def modal(self, context, event):
        if event.type == 'TIMER':
            self.my_instance.update_time()
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        global vpet
        vpet = bpy.context.window_manager.vpet_data
        self._timer = wm.event_timer_add(1.0 / self.my_instance.framerate, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
