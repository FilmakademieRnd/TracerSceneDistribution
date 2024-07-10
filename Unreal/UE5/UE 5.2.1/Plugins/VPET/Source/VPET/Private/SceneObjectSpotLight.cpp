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
#include "SceneObjectSpotLight.h"

// Message parsing pre-declarations
void UpdateRange(std::vector<uint8_t> kMsg, AActor* actor);
void UpdateAngle(std::vector<uint8_t> kMsg, AActor* actor);

// Called when the game starts
void USceneObjectSpotLight::BeginPlay()
{
	Super::BeginPlay();

	kSpotLgt = Cast<ASpotLight>(kLit);
	if (kSpotLgt)
		spotLgtCmp = kSpotLgt->SpotLightComponent;
	if (spotLgtCmp)
	{
		float range = spotLgtCmp->AttenuationRadius * rangeFactor;
		float angle = spotLgtCmp->OuterConeAngle * angleFactor;

		Range_Vpet_Param = new Parameter<float>(range, thisActor, "range", &UpdateRange, this);
		Angle_Vpet_Param = new Parameter<float>(angle, thisActor, "spot angle", &UpdateAngle, this);
	}
}

// Using the update loop to check for local parameter changes
void USceneObjectSpotLight::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (_lock)
		return;
	if (spotLgtCmp)
	{
		float range = spotLgtCmp->AttenuationRadius * rangeFactor;
		float angle = spotLgtCmp->OuterConeAngle * angleFactor;

		if (range != Range_Vpet_Param->getValue())
		{
			UE_LOG(LogTemp, Warning, TEXT("RANGE CHANGE"));
			ParameterObject_HasChanged.Broadcast(Range_Vpet_Param);
			Range_Vpet_Param->setValue(range);
		}
		if (angle != Angle_Vpet_Param->getValue())
		{
			UE_LOG(LogTemp, Warning, TEXT("ANGLE CHANGE"));
			ParameterObject_HasChanged.Broadcast(Angle_Vpet_Param);
			Angle_Vpet_Param->setValue(angle);
		}
	}
}

// Parses a message for range change
void UpdateRange(std::vector<uint8_t> kMsg, AActor* actor)
{
	UE_LOG(LogTemp, Warning, TEXT("[SYNC Parse] Try Type RANGE"));
	ASpotLight* kSpotLgt = Cast<ASpotLight>(actor);
	USpotLightComponent* spotLgtCmp = NULL;
	if(kSpotLgt)
		spotLgtCmp = kSpotLgt->SpotLightComponent;
	if (spotLgtCmp)
	{
		float rangeFactor = 0.005;

		float lK = *reinterpret_cast<float*>(&kMsg[0]);
		UE_LOG(LogTemp, Warning, TEXT("[SYNC Parse] Type RANGE: %f"), lK);

		spotLgtCmp->AttenuationRadius = lK / rangeFactor;
	}
}

// Parses a message for angle change
void UpdateAngle(std::vector<uint8_t> kMsg, AActor* actor)
{
	UE_LOG(LogTemp, Warning, TEXT("[SYNC Parse] Try Type SPOT ANGLE"));
	ASpotLight* kSpotLgt = Cast<ASpotLight>(actor);
	USpotLightComponent* spotLgtCmp = NULL;
	if(kSpotLgt)
		spotLgtCmp = kSpotLgt->SpotLightComponent;
	if (spotLgtCmp)
	{
		float angleFactor = 2.0;

		float lK = *reinterpret_cast<float*>(&kMsg[0]);
		UE_LOG(LogTemp, Warning, TEXT("[SYNC Parse] Type SPOT ANGLE: %f"), lK);

		spotLgtCmp->OuterConeAngle = lK / angleFactor;
	}
}
