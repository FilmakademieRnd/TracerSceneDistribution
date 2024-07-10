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
#pragma once
#include "SceneObjectLight.h"
#include "Engine/SpotLight.h"
#include "Components/SpotLightComponent.h"
#include "SceneObjectSpotLight.generated.h"

/**
 * 
 */
UCLASS()
class VPET_API USceneObjectSpotLight : public USceneObjectLight
{
	GENERATED_BODY()

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	ASpotLight* kSpotLgt;
	USpotLightComponent* spotLgtCmp;
	float rangeFactor = 0.005;
	float angleFactor = 2.0;

	// Light range buffer
	Parameter<float>* Range_Vpet_Param;
	// Light angle buffer
	Parameter<float>* Angle_Vpet_Param;
	
};
