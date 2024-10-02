/*
TRACER Scene Distribution Plugin Unreal Engine
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Unreal Engine is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Unreal Engine development.
 
The TRACER Scene Distribution Plugin Unreal Engine is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Unreal Engine is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Unreal Engine may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Unreal Engine Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Unreal Engine by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Unreal Engine in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/


using System.IO;
using UnrealBuildTool;

public class libzmq : ModuleRules
{
    public libzmq(ReadOnlyTargetRules Target) : base(Target)
    {
        //Type = ModuleType.External;
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            // Include
            // Include files from former plugin - needed a minor adjustment at include files 
            PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "..", "..", "ThirdParty", "libzmq_4.3.1", "include"));
            // Most recent include files - will lead to some deprecated methods warnings, but builds correctly
            //PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "..", "..", "ThirdParty", "libzmq_432", "include"));

            // Library
            PublicAdditionalLibraries.Add(Path.Combine(ModuleDirectory, "..", "..", "ThirdParty", "libzmq_4.3.1", "Windows", "x64", "libzmq-v141-mt-s-4_3_2.lib"));
            // Fresh release lib - doesn't work for the build
            //PublicAdditionalLibraries.Add(Path.Combine(ModuleDirectory, "..", "..", "ThirdParty", "libzmq_432", "win_x64", "libzmq-v141-mt-s-4_3_2.lib"));

            // Add definition for zmq library
            PublicDefinitions.Add("ZMQ_STATIC");
        }

        // Basic core functionality
        PublicDependencyModuleNames.AddRange(new string[] { "Core", });


    }
}