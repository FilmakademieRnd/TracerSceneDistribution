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

//#include "Parameter.h"

#include "CoreMinimal.h"

#include "Components/ActorComponent.h"

#include "ParameterObject.generated.h"

class AbstractParameter;
//class AbstractParameter;
typedef TMulticastDelegate<void(AbstractParameter*)> FVpet_ParameterObject_Delegate;

//DECLARE_DELEGATE_OneParam(FParameterModifiedSignature, AbstractParameter);
//DECLARE_DELEGATE_OneParam(FVpet_ParameterObject_Delegate, AbstractParameter, param);

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class VPET_API UParameterObject : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UParameterObject();
	FVpet_ParameterObject_Delegate ParameterObject_HasChanged;

	int ID;
	
protected:
	// Called when the game starts
	 void BeginPlay() override;

public:	
	// Called every frame
	 void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	TArray<AbstractParameter*> _parameterList;

public:

	//FParameterModifiedSignature OnParameterModified;
	
	void AddParameter(AbstractParameter* param)
	{
		_parameterList.Add(param);
	}

	TArray<AbstractParameter*>* GetParameterList()
	{
		return &_parameterList;
	}

	void PrintParams();
		
};
