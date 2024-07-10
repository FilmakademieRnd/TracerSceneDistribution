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
#include "PluginState.h"
#include "LightScenegraphLocationDelegate.h"

#include <FnRenderOutputUtils/FnRenderOutputUtils.h>

#include <glm/gtx/string_cast.hpp>

#include <string>


LightScenegraphLocationDelegate* LightScenegraphLocationDelegate::create()
{
    return new LightScenegraphLocationDelegate();
}

void LightScenegraphLocationDelegate::flush()
{
}

std::string LightScenegraphLocationDelegate::getSupportedRenderer() const
{
    return std::string("sceneDistributor");
}

void LightScenegraphLocationDelegate::fillSupportedLocationList(std::vector<std::string>& supportedLocationList) const
{
    supportedLocationList.push_back(std::string("light"));
}

void* LightScenegraphLocationDelegate::process(FnKat::FnScenegraphIterator sgIterator, void* optionalInput)
{
    // get state
    Dreamspace::Katana::SceneDistributorPluginState* sharedState = reinterpret_cast<Dreamspace::Katana::SceneDistributorPluginState*>(optionalInput);

    // create light node
    Dreamspace::Katana::NodeLight* nodeLight =  new Dreamspace::Katana::NodeLight();


    sharedState->nodeTypeList.push_back(Dreamspace::Katana::NodeType::LIGHT);


    // std::cout << "[INFO SceneDistributor.LightScenegraphLocationDelegate] Processing location: " << location << std::endl;

    // Light material
    FnAttribute::GroupAttribute materialAttr = FnKat::RenderOutputUtils::getFlattenedMaterialAttr(sgIterator, sharedState->materialTerminalNamesAttr);

    //std::cout << "[INFO SceneDistributor.LightScenegraphLocationDelegate] Material:" << std::endl;
    //std::cout << materialAttr.getXML() << std::endl;

    // Light attributes
    FnAttribute::GroupAttribute paramsAttr = materialAttr.getChildByName("parameters");
    if ( paramsAttr.isValid() )
    {

          // std::cout << paramsAttr.getXML() << std::endl;

          FnAttribute::StringAttribute  lightTypeAttr = paramsAttr.getChildByName("type");
          std::string lightAreaType = lightTypeAttr.getValue("<default>", false);

          if ( lightAreaType == "sphere" )
          {
              nodeLight->type = Dreamspace::Katana::POINT;
          }
          else if ( lightAreaType == "directional")
          {
              nodeLight->type = Dreamspace::Katana::DIRECTIONAL;
          }
          else if ( lightAreaType == "disk")
          {
              nodeLight->type = Dreamspace::Katana::SPOT;

              // Angle
              FnAttribute::FloatAttribute angleAttr = paramsAttr.getChildByName("coneAngle");
              if ( angleAttr.isValid() )
              {
                  nodeLight->angle = angleAttr.getValue( 120.0, false );
              }

          }
          else if ( lightAreaType == "env")
          {
              // TODO: handle
              nodeLight->type = Dreamspace::Katana::NONE;
          }
          else //rect
          {
              nodeLight->type = Dreamspace::Katana::AREA;
              nodeLight->angle = 180.0;
          }

          // Color
          FnAttribute::FloatAttribute colorAttr = paramsAttr.getChildByName("color");
          if ( colorAttr.isValid() )
          {
              // Get the color value
              FnAttribute::FloatConstVector colorData = colorAttr.getNearestSample(0.0f);

              nodeLight->color[0] = colorData[0];
              nodeLight->color[1] = colorData[1];
              nodeLight->color[2] = colorData[2];
          }

          // Intensity
          FnAttribute::FloatAttribute intensityAttr = paramsAttr.getChildByName("intensity");
          if ( intensityAttr.isValid() )
          {
              nodeLight->intensity = intensityAttr.getValue( 1.0, false );
          }

          // Exposure
          FnAttribute::FloatAttribute exposureAttr = paramsAttr.getChildByName("exposure");
          if ( exposureAttr.isValid() )
          {
              nodeLight->exposure = exposureAttr.getValue( 3.0, false );
          }

          std::cout << "[INFO SceneDistributor.LightScenegraphLocationDelegate] Light color: " << nodeLight->color[0] << " "  << nodeLight->color[1] << " "  << nodeLight->color[2] << " Type: " << lightAreaType << " intensity: " << nodeLight->intensity  << " exposure: " << nodeLight->exposure  << " coneAngle: " << nodeLight->angle << std::endl;

    }
    else
    {
        std::cout << "[INFO SceneDistributor.LightScenegraphLocationDelegate] Common Parameters not found. " << std::endl;
    }

    if ( nodeLight->type != Dreamspace::Katana::NONE )
    {
        // store at sharedState to access it in iterator
        sharedState->node = nodeLight;
        sharedState->numLights++;
    }
    else
    {
        delete nodeLight;
        Dreamspace::Katana::Node* node = new Dreamspace::Katana::Node();
        sharedState->node = node;
        std::cout << "[INFO SceneDistributor.LightScenegraphLocationDelegate] Found unknown Light (add as group)" << std::endl;
    }

    return NULL;

}

