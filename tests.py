import unittest

from main import (
    ReferenceProfile,
    Participant,
    Session,
    SessionClassifier,
    validate_observation,
    check_recovery,
    analyze_session,
)

# one good observation used in several tests
GOOD_OBS = {
    "heart_rate": 100,
    "skin_response": 2.0,
    "temperature": 32.5,
    "activity_level": 0.5,
    "signal_quality": 0.9,
}


class TestValidation(unittest.TestCase):
    def test_valid_observation_has_no_problems(self):
        self.assertEqual(validate_observation(GOOD_OBS), [])

    def test_missing_value_is_flagged(self):
        bad = dict(GOOD_OBS)
        bad["heart_rate"] = None
        self.assertTrue(validate_observation(bad))

    def test_impossible_value_is_flagged(self):
        bad = dict(GOOD_OBS)
        bad["heart_rate"] = 300
        self.assertTrue(validate_observation(bad))

    def test_wrong_type_is_flagged(self):
        bad = dict(GOOD_OBS)
        bad["heart_rate"] = "fast"
        self.assertTrue(validate_observation(bad))


class TestReferenceProfile(unittest.TestCase):
    def test_valid_heart_rate_is_accepted(self):
        ref = ReferenceProfile(70)
        self.assertEqual(ref.heart_rate, 70)

    def test_invalid_heart_rate_raises_error(self):
        with self.assertRaises(ValueError):
            ReferenceProfile(500)


class TestSession(unittest.TestCase):
    def test_usable_observations_skips_bad_ones(self):
        bad_obs = dict(GOOD_OBS)
        bad_obs["heart_rate"] = None
        participant = Participant("P1", ReferenceProfile(70))
        session = Session("test", participant, [GOOD_OBS, bad_obs])

        self.assertEqual(len(session.usable_observations()), 1)
        self.assertEqual(len(session.rejected_observations()), 1)


class TestRecovery(unittest.TestCase):
    def test_recovery_detected_when_heart_rate_and_activity_drop(self):
        obs = []
        heart_rates = [130, 125, 120, 100, 85, 78, 75, 74, 73]
        activities = [0.8, 0.8, 0.7, 0.5, 0.3, 0.2, 0.1, 0.1, 0.1]
        for hr, act in zip(heart_rates, activities):
            obs.append({"heart_rate": hr, "activity_level": act})
        self.assertTrue(check_recovery(obs, 70))

    def test_no_recovery_when_activity_stays_high(self):
        obs = []
        heart_rates = [130, 125, 120, 100, 85, 78, 75, 74, 73]
        for hr in heart_rates:
            obs.append({"heart_rate": hr, "activity_level": 0.8})
        self.assertFalse(check_recovery(obs, 70))


class TestClassification(unittest.TestCase):
    def test_resting_session(self):
        participant = Participant("P1", ReferenceProfile(70))
        obs = [dict(GOOD_OBS, heart_rate=72) for _ in range(6)]
        session = Session("test", participant, obs)
        result = analyze_session(session, SessionClassifier())
        self.assertEqual(result["classification"], "resting")

    def test_high_activity_session(self):
        participant = Participant("P1", ReferenceProfile(70))
        obs = [dict(GOOD_OBS, heart_rate=140) for _ in range(6)]
        session = Session("test", participant, obs)
        result = analyze_session(session, SessionClassifier())
        self.assertEqual(result["classification"], "high_activity")

    def test_insufficient_data_when_too_few_usable(self):
        bad_obs = dict(GOOD_OBS)
        bad_obs["heart_rate"] = None
        participant = Participant("P1", ReferenceProfile(70))
        session = Session("test", participant, [bad_obs] * 6)
        result = analyze_session(session, SessionClassifier())
        self.assertEqual(result["classification"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()