/*
-----------------------------------------------------------------------------
TRACER Scene Distribution Plugin Katana
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Katana is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Katana development.
 
The TRACER Scene Distribution Plugin Katana is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Katana is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Katana may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Katana Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Katana by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Katana in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
-----------------------------------------------------------------------------
*/
#ifndef COMPANYNAMEKATANA_SCENEDISTRIBUTORINFOPLUGIN_H
#define COMPANYNAMEKATANA_SCENEDISTRIBUTORINFOPLUGIN_H

#include "PluginState.h"

#include <FnRender/plugin/RenderBase.h>

#include <string>
#include <queue>

#include <zmq.hpp>

#include <pthread.h>


namespace Dreamspace
{
namespace Katana
{

    /**
     * \ingroup SceneDistributorPlugin
     */

    /**
     * @brief SceneDistributor Render Plugin
     */
    class SceneDistributorPlugin : public FnKat::Render::RenderBase
    {
    public:

        SceneDistributorPlugin(FnKat::FnScenegraphIterator rootIterator,
                             FnKat::GroupAttribute arguments);
        ~SceneDistributorPlugin();

        // Render Control

        int start();

        int pause();

        int resume();

        int stop();

        // Interactive live updates

        int startLiveEditing();

        int stopLiveEditing();

        int processControlCommand(const std::string& command);

        int queueDataUpdates(FnKat::GroupAttribute updateAttribute);

        int applyPendingDataUpdates();

        bool hasPendingDataUpdates() const;

        // Disk Render

        void configureDiskRenderOutputProcess(FnKat::Render::DiskRenderOutputProcess& diskRenderOutputProcess,
                                              const std::string& outputName,
                                              const std::string& outputPath,
                                              const std::string& renderMethodName,
                                              const float& frameTime) const;

        // Plugin Interface

        static Foundry::Katana::Render::RenderBase* create(FnKat::FnScenegraphIterator rootIterator, FnKat::GroupAttribute args)
        {
            return new SceneDistributorPlugin(rootIterator, args);
        }


        static void flush()
        {

        }

    private:
        SceneDistributorPluginState _sharedState;

        // Live render
        struct Update
        {
            std::string type;
            std::string location;
            FnAttribute::GroupAttribute attributesAttr;
            FnAttribute::GroupAttribute xformAttr;
        };
        typedef std::queue<Update> UpdateQueue;

        UpdateQueue _cameraUpdates;
        void updateCamera();

		//zeroMQ context

		//zeroMQ thread
		pthread_t thread;
		
	
    };
    
    static void* server(void* scene);

    /**
     * @}
     */
}
}

#endif
