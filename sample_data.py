from data_generator import generate_fitness_data


def get_scenarios():
    scenario_names = ["resting", "moderate_activity", "high_activity", "recovery", "poor_quality"]
    scenarios = []


    for i, name in enumerate(scenario_names):
        profile, observations = generate_fitness_data(
            participant_id="P00" + str(i + 1),
            scenario=name,
            seed=i + 1,
            number_of_windows=12,
        )
        scenarios.append({
            "name":name,
            "profile":profile,
            "observation":observations,
        })

    return scenarios