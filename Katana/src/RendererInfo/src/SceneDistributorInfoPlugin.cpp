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
#include "SceneDistributorInfoPlugin.h"
#include <algorithm>

namespace Dreamspace
{
namespace Katana
{

SceneDistributorInfoPlugin::SceneDistributorInfoPlugin()
{
}

SceneDistributorInfoPlugin::~SceneDistributorInfoPlugin()
{
}

void SceneDistributorInfoPlugin::fillRenderMethods(
    std::vector<Foundry::Katana::RendererInfo::RenderMethod*>& renderMethods) const
{
    renderMethods.clear();

    // e.g.
    // Support Preview, Disk and Live Render Methods:

    FnKat::RendererInfo::RenderMethod *diskRenderMethod;
    FnKat::RendererInfo::RenderMethod *previewRenderMethod;
    FnKat::RendererInfo::RenderMethod *liveRenderMethod;

    diskRenderMethod = new FnKat::RendererInfo::DiskRenderMethod();
    previewRenderMethod = new FnKat::RendererInfo::PreviewRenderMethod();
    liveRenderMethod = new FnKat::RendererInfo::LiveRenderMethod();

    renderMethods.push_back(diskRenderMethod);
    renderMethods.push_back(previewRenderMethod);
    renderMethods.push_back(liveRenderMethod);
}

void SceneDistributorInfoPlugin::fillRendererObjectNames(
    std::vector<std::string>& rendererObjectNames,
    const std::string& type,
    const std::vector<std::string>& typeTags) const
{
    rendererObjectNames.clear();

    // TODO: Fill out the names of objects (e.g. shaders) that exist
    // for each of the tags in typeTags.

    // e.g.
    // if (type == kFnRendererObjectTypeShader)
    // {
    //     if (std::find(typeTags.begin(), typeTags.end(), "surface") != typeTags.end())
    //     {
    //         rendererObjectNames.push_back("myWoodShader");
    //     }
    // }
}

void SceneDistributorInfoPlugin::fillRendererObjectTypes(
    std::vector<std::string>& renderObjectTypes,
    const std::string& type) const
{
    renderObjectTypes.clear();

    // TODO: Fill out the full list of object types your renderer
    // supports, of the specified parent 'type'.

    // e.g.
    // if (type == kFnRendererObjectTypeShader)
    // {
    //     renderObjectTypes.push_back("surface");
    //     renderObjectTypes.push_back("light");
    // }
    // else if (type == kFnRendererObjectTypeRenderOutput)
    // {
    //     renderObjectTypes.push_back(kFnRendererOutputTypeColor);
    //     renderObjectTypes.push_back(kFnRendererOutputTypeRaw);
    // }
    // else if (type == kFnRendererObjectTypeOutputChannelCustomParam)
    // {
    //     renderObjectTypes.push_back("opacity");
    // }
}

void SceneDistributorInfoPlugin::configureBatchRenderMethod(
    Foundry::Katana::RendererInfo::DiskRenderMethod& batchRenderMethod) const
{
    // e.g.
    // batchRenderMethod.setDebugOutputFileType("txt");
}

std::string SceneDistributorInfoPlugin::getRegisteredRendererName() const
{
    return "sceneDistributor";
}

std::string SceneDistributorInfoPlugin::getRegisteredRendererVersion() const
{
    return "0.0v0";
}

std::string SceneDistributorInfoPlugin::getRendererObjectDefaultType(
    const std::string& type) const
{
    // e.g.
    // if (type == kFnRendererObjectTypeRenderOutput)
    // {
    //     return kFnRendererOutputTypeColor;
    // }

    // Default:
    return FnKat::RendererInfo::RendererInfoBase::getRendererObjectDefaultType(type);
}

bool SceneDistributorInfoPlugin::isPresetLocalFileNeeded(
    const std::string &outputType) const
{
    // e.g.
    // if (outputType == kSomeOutputTypeWhichRequiresPresetLocalFile)
    // {
    //     return true;
    // }

    // Default:
    return FnKat::RendererInfo::RendererInfoBase::isPresetLocalFileNeeded(outputType);
}

bool SceneDistributorInfoPlugin::isNodeTypeSupported(
    const std::string &nodeType) const
{
    // e.g.
    // if (nodeType == "ShadingNode" || nodeType == "OutputChannelDefine")
    // {
    //     return true;
    // }

    // Default:
    return FnKat::RendererInfo::RendererInfoBase::isNodeTypeSupported(nodeType);
}

bool SceneDistributorInfoPlugin::isPolymeshFacesetSplittingEnabled() const
{
    // If true is returned, Katana will split geometry automatically before
    // calling the Render plug-in.

    return FnKat::RendererInfo::RendererInfoBase::isPolymeshFacesetSplittingEnabled();
}

void SceneDistributorInfoPlugin::fillShaderInputNames(
    std::vector<std::string>& shaderInputNames,
    const std::string& shaderName) const
{
    shaderInputNames.clear();

    // TODO: Fill out the names of inputs supported by the
    // shader specified in 'shaderName'. These are used to
    // connect shading nodes.

    // e.g.
    // if (shaderName == "myWoodShader")
    // {
    //     shaderInputNames.push_back("colour");
    // }
}

void SceneDistributorInfoPlugin::fillShaderInputTags(
    std::vector<std::string>& shaderInputTags,
    const std::string& shaderName,
    const std::string& inputName) const
{
    shaderInputTags.clear();

    // TODO: Fill out the type tags of inputs supported by the
    // shader specified in 'shaderName'. These are used to
    // constrain connections between shading nodes.
    //
    // Type tags are specified using a simple Python-like syntax
    // that supports boolean operations.

    // e.g.
    // if (shaderName == "myWoodShader")
    // {
    //     shaderInputTags.push_back("rgba or float");
    // }
}

void SceneDistributorInfoPlugin::fillShaderOutputNames(
    std::vector<std::string>& shaderOutputNames,
    const std::string& shaderName) const
{
    shaderOutputNames.clear();

    // TODO: Fill out the names of inputs supported by the
    // shader specified in 'shaderName'. These are used to
    // connect shading nodes.

    // e.g.
    // if (shaderName == "myWoodShader")
    // {
    //     shaderOutputNames.push_back("out");
    // }
}

void SceneDistributorInfoPlugin::fillShaderOutputTags(
    std::vector<std::string>& shaderOutputTags,
    const std::string& shaderName,
    const std::string& outputName) const
{
    shaderOutputTags.clear();

    // TODO: Fill out the type tags of outputs supported by the
    // shader specified in 'shaderName'. These are used to
    // constrain connections between shading nodes.
    //
    // Type tags are specified using a simple Python-like syntax
    // that supports boolean operations.

    // e.g.
    // if (shaderName == "myWoodShader")
    // {
    //     shaderOutputTags.push_back("rgba or float");
    // }
}

void SceneDistributorInfoPlugin::fillRendererShaderTypeTags(
    std::vector<std::string>& shaderTypeTags,
    const std::string& shaderType) const
{
    shaderTypeTags.clear();

    // TODO: Fill out any type tags that are compatible with the
    // shader specified in 'shaderType'.  These are used to
    // constrain the connection of shading nodes to Network
    // Material node input terminals.

    // e.g.
    // Allowing only float and rgba to connect to a surface
    // terminal on a NetworkMaterial node:
    //
    // if (shaderType == "surface")
    // {
    //     shaderTypeTags.push_back("float or rgba");
    // }
}

std::string SceneDistributorInfoPlugin::getRendererCoshaderType() const
{
    // e.g.
    // return "class";

    // Default:
    return FnKat::RendererInfo::RendererInfoBase::getRendererCoshaderType();
}

bool SceneDistributorInfoPlugin::buildRendererObjectInfo(
    FnKat::GroupBuilder& rendererObjectInfo,
    const std::string& name,
    const std::string& type,
    const FnKat::GroupAttribute inputAttr /*= 0x0*/) const
{
    // Provide attribute data for objects that are advertised in
    // fillRendererObjectNames/fillRendererObjectTypes.

    // e.g.
    //
    // if(type == kFnRendererObjectTypeShader)
    // {
    //     if (name == "myWoodShader")
    //     {
    //         _buildAttributesForWoodShader(rendererObjectInfo, inputAttr);
    //     }
    // }
    // else if(type == kFnRendererObjectTypeRenderOutput)
    // {
    //     if (name == kFnRendererOutputTypeColor)
    //     {
    //         _buildAttributesForColorOutput(rendererObjectInfo, inputAttr);
    //     }
    // }
    // etc

    return false;
}

void SceneDistributorInfoPlugin::fillLiveRenderTerminalOps(
    FnKat::RendererInfo::RendererInfoBase::OpDefinitionQueue& terminalOps,
    const FnAttribute::GroupAttribute& stateArgs) const
{
    // Define the terminal ops to be added during live rendering
    {
        // Observe camera changes
        FnAttribute::GroupBuilder opArgs;
        opArgs.set("type", FnAttribute::StringAttribute("camera"));
        opArgs.set("location", FnAttribute::StringAttribute("/root/world"));

        std::string attributes[] = {"xform", "geometry"};
        opArgs.set("attributeNames", FnAttribute::StringAttribute(attributes, 2, 1));

        terminalOps.push_back(std::make_pair("LiveRenderFilter", opArgs.build()));
    }
}

void SceneDistributorInfoPlugin::initialiseCaches()
{

}

void SceneDistributorInfoPlugin::flushCaches()
{

}

DEFINE_RENDERERINFO_PLUGIN(SceneDistributorInfoPlugin)

}
}

void registerPlugins()
{
    REGISTER_PLUGIN(Dreamspace::Katana::SceneDistributorInfoPlugin, "sceneDistributorInfoPlugin", 0, 1);
}
