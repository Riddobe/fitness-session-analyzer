from sample_data import get_scenarios

# valid ranges for each field
LIMITS = {
    "heart_rate": (35, 205),
    "skin_response": (0, 1000),
    "temperature": (25, 42),
    "activity_level": (0, 1),
    "signal_quality": (0, 1),
}


def validate_observation(obs):
    # checks one observation, returns list of problems (empty = ok)
    problems = []
    for field, (low, high) in LIMITS.items():
        value = obs.get(field)
        if value is None:
            problems.append(f"{field} is missing")
        elif type(value) != int and type(value) != float:
            problems.append(f"{field} is not a number")
        elif value < low or value > high:
            problems.append(f"{field} is out of range")
    return problems


class ReferenceProfile:
    # stores the participant's baseline heart rate
    # heart rate is kept private and checked through a property
    def __init__(self, heart_rate):
        self.heart_rate = heart_rate  # goes through the setter below

    @staticmethod
    def is_realistic(value):
        # simple check used by the setter, doesn't need self
        if type(value) != int and type(value) != float:
            return False
        return 30 <= value <= 120

    @property
    def heart_rate(self):
        return self._heart_rate

    @heart_rate.setter
    def heart_rate(self, value):
        if not self.is_realistic(value):
            raise ValueError("baseline heart rate must be between 30 and 120")
        self._heart_rate = value


class Participant:
    # a participant has a reference profile (composition)
    def __init__(self, participant_id, reference):
        self.participant_id = participant_id
        self.reference = reference

    @classmethod
    def from_profile_dict(cls, profile):
        # builds a Participant straight from the generator's profile dict
        reference = ReferenceProfile(profile["baseline_heart_rate"])
        return cls(profile["participant_id"], reference)


class Session:
    # one training session: a participant + their observations
    def __init__(self, name, participant, observations):
        self.name = name
        self.participant = participant
        self.observations = observations

    def usable_observations(self):
        # only keep observations that passed validation
        usable = []
        for obs in self.observations:
            if not validate_observation(obs):
                usable.append(obs)
        return usable

    def rejected_observations(self):
        # observations that failed validation, with the reasons
        rejected = []
        for obs in self.observations:
            problems = validate_observation(obs)
            if problems:
                rejected.append({"observation": obs, "problems": problems})
        return rejected


def check_recovery(usable_observations, baseline_heart_rate):
    # checks if heart rate and activity go down near the end
    if len(usable_observations) < 6:
        return False

    third = len(usable_observations) // 3
    early = usable_observations[:third]
    late = usable_observations[-third:]

    early_hr_total = 0
    for obs in early:
        early_hr_total += obs["heart_rate"]
    early_hr = early_hr_total / len(early)

    late_hr_total = 0
    for obs in late:
        late_hr_total += obs["heart_rate"]
    late_hr = late_hr_total / len(late)

    early_activity_total = 0
    for obs in early:
        early_activity_total += obs["activity_level"]
    early_activity = early_activity_total / len(early)

    late_activity_total = 0
    for obs in late:
        late_activity_total += obs["activity_level"]
    late_activity = late_activity_total / len(late)

    started_elevated = early_hr - baseline_heart_rate >= 20
    heart_rate_dropped = (early_hr - late_hr) >= 15
    activity_dropped = (early_activity - late_activity) >= 0.20

    return started_elevated and heart_rate_dropped and activity_dropped


class IntensityClassifier:
    # base class: decides resting / moderate / high from heart rate alone
    HIGH_CUTOFF = 45
    MODERATE_CUTOFF = 15

    def classify(self, usable, baseline_heart_rate):
        total = 0
        for obs in usable:
            total += obs["heart_rate"]
        average_hr = total / len(usable)
        elevation = average_hr - baseline_heart_rate

        if elevation >= self.HIGH_CUTOFF:
            label = "high_activity"
        elif elevation >= self.MODERATE_CUTOFF:
            label = "moderate_activity"
        else:
            label = "resting"

        rounded_elevation = round(elevation, 1)
        explanation = f"average heart rate was {rounded_elevation} bpm above baseline"
        return label, explanation


class SessionClassifier(IntensityClassifier):
    # adds the insufficient-data and recovery checks on top of the base class
    MIN_USABLE = 4

    def classify(self, usable, baseline_heart_rate):
        if len(usable) < self.MIN_USABLE:
            return "insufficient_data", "not enough usable observations to classify"

        if check_recovery(usable, baseline_heart_rate):
            return "recovering", "heart rate and activity dropped near the end of the session"

        # fall back to the base class for plain intensity
        return super().classify(usable, baseline_heart_rate)


def analyze_session(session, classifier):
    # runs the full analysis and returns everything as one dictionary
    usable = session.usable_observations()
    rejected = session.rejected_observations()
    label, explanation = classifier.classify(usable, session.participant.reference.heart_rate)

    return {
        "session_name": session.name,
        "participant_id": session.participant.participant_id,
        "classification": label,
        "explanation": explanation,
        "usable_count": len(usable),
        "total_count": len(session.observations),
        "rejected": rejected,
    }


def print_report(result):
    # prints a short report from the result dictionary
    print("=" * 50)
    print(f"Session: {result['session_name']}   Participant: {result['participant_id']}")
    print(f"Classification: {result['classification'].upper()}")
    print(f"Usable observations: {result['usable_count']} of {result['total_count']}")
    print(f"Why: {result['explanation']}")
    if result["rejected"]:
        print("Rejected observations:")
        for item in result["rejected"]:
            problem_text = ""
            for i, problem in enumerate(item["problems"]):
                if i > 0:
                    problem_text += ", "
                problem_text += problem
            print(f" - {problem_text}")
    print()


def main():
    classifier = SessionClassifier()
    for scenario in get_scenarios():
        participant = Participant.from_profile_dict(scenario["profile"])
        session = Session(scenario["name"], participant, scenario["observation"])
        result = analyze_session(session, classifier)
        print_report(result)


if __name__ == "__main__":
    main()