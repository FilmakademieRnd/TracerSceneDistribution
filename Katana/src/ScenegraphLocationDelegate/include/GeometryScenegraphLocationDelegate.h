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
#ifndef GEOMETRYSCENEGRAPHLOCATIONDELEGATE_H
#define GEOMETRYSCENEGRAPHLOCATIONDELEGATE_H

#include <FnRender/plugin/ScenegraphLocationDelegate.h>

#include "PluginState.h"

class GeometryScenegraphLocationDelegate : public Foundry::Katana::Render::ScenegraphLocationDelegate
{
public:
    static GeometryScenegraphLocationDelegate* create();
    static void flush();

    virtual std::string getSupportedRenderer() const;
    virtual void fillSupportedLocationList(std::vector<std::string>& supportedLocationList) const;
    FnAttribute::Attribute GetAttribute( FnAttribute::GroupAttribute i_attr, std::string i_name );
    bool LoadMap( std::string i_filepath, unsigned char* &o_buffer,  int* o_bufferSize  );
    virtual void* process(FnKat::FnScenegraphIterator sgIterator, void* optionalInput);

private:

    inline bool search_path_textpack( const std::string &key, const Dreamspace::Katana::TexturePackage &texPack) { return ( texPack.path == key ); }


};

#endif

