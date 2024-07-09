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

// Do note: VPETWindow - or VPET Helper - was redone from scratch for VPET2 modifications
// New plugin template derives from UE4.27
// It might not be backwards compatible
// For prior versions compatibility, check former source code (relative to original VPET, prior to 2022)

#pragma once

// FSelectionIterator
#include "Engine/Selection.h"
// TActorIterator
#include "EngineUtils.h"
// UEditorLevelLibrary
#include "EditorLevelLibrary.h"
// UEditorAssetLibrary
#include "EditorAssetLibrary.h"
// USceneCaptureComponent2D
#include "Components/SceneCaptureComponent2D.h"
// ASceneCapture2D
#include "Engine/SceneCapture2D.h"
// AStaticMeshActor
#include "Engine/StaticMeshActor.h"
// ADirectionalLight
#include "Engine/DirectionalLight.h"
// UTextureRenderTarget2D
#include "Engine/TextureRenderTarget2D.h"
// IAssetTools::CreateAsset
//#include "IAssetTools.h"
// UTextureRenderTargetFactoryNew
#include "Factories/TextureRenderTargetFactoryNew.h"
// FImageUtils::ExportRenderTarget2DAsPNG
#include "ImageUtils.h"
// FMessageDialog
#include "Misc/MessageDialog.h"
// GameSourceDir
#include "Misc/Paths.h"


#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FToolBarBuilder;
class FMenuBuilder;

class FVPETWindowModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	
	/** This function will be bound to Command. */
	void PluginButtonClicked();
	
private:

	void RegisterMenus();

	TSharedRef<class SDockTab> OnSpawnPluginTab(const class FSpawnTabArgs& SpawnTabArgs);


private:
	TSharedPtr<class FUICommandList> PluginCommands;
};
