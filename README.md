# Smart Fitness Session Analyzer

Selected option: Option A - Smart Fitness Session Analyzer
Name: Ridouan Boulahyane Essaeh
Student number: riess0465

## Description

This program takes simulated data from a wearable device during a training
session. It checks each reading for missing or impossible values, compares
the good data with the participant's normal heart rate, and decides if the
session was resting, moderate activity, high activity, recovering, or
insufficient data. It also prints a report showing how many readings were
usable and why the session got that classification. No external packages
are used.

## How to run it

```bash
git clone https://github.com/Riddobe/fitness-session-analyzer.git
cd fitness-session-analyzer
python3 main.py
```

To run the tests:

```bash
python3 tests.py
```

## Files

| File | What it contains |
|---|---|
| `main.py` | All the classes, functions, and the program itself |
| `sample_data.py` | Builds the five scenarios using the generator |
| `data_generator.py` | Given by the instructor, not modified |
| `tests.py` | Unit tests |
| `requirements.txt` | Says the project only uses the standard library |

## Class design

ReferenceProfile stores the participant's normal heart rate. The value is
private and can only be set through a property, which checks that it is a
realistic number.

Participant has an id and a ReferenceProfile. This is composition, since a
Participant "has" a ReferenceProfile.

Session has a Participant and a list of readings. This is also
composition. It can return which readings passed validation and which
were rejected.

IntensityClassifier is a base class that decides resting/moderate/high
just from heart rate above the baseline.

SessionClassifier inherits from IntensityClassifier and overrides
classify() to add the insufficient-data and recovery checks first, then
falls back to the base class for normal intensity.

There are also four standalone functions: validate_observation,
check_recovery, analyze_session (which builds the result dictionary), and
print_report.

## Where the OOP requirements are used

Composition: Session has a Participant, and Participant has a
ReferenceProfile.

Encapsulation: the heart rate in ReferenceProfile is stored privately and
can only be changed through a property, which rejects unrealistic values.

Inheritance and overriding: SessionClassifier inherits from
IntensityClassifier and overrides classify(), using super().classify() for
the normal intensity check.

Static method: ReferenceProfile.is_realistic() is a simple check that
doesn't need any data from the object itself.

Class method: Participant.from_profile_dict() builds a Participant
directly from the profile dictionary the generator returns.

## Assumptions and classification rules

A reading is rejected if any value is missing, not a number, or outside
its normal range (heart rate 35-205, skin response 0 to 1000, temperature
25-42, activity level 0-1, signal quality 0-1). Rejected readings are
shown in the report along with the reason.

The session is classified using these rules, checked in this order:

1. Insufficient data - fewer than 4 usable readings.
2. Recovering - heart rate starts at least 20 bpm above baseline, then
   drops by at least 15 bpm, and activity drops by at least 0.20, comparing
   the first third of the session with the last third.
3. High activity - average heart rate is at least 45 bpm above baseline.
4. Moderate activity - average heart rate is at least 15 bpm above
   baseline.
5. Resting - none of the above.

I picked these numbers myself, based on what the generated data looks like.

## Scenarios

The five scenarios all come from the instructor's data generator: resting,
moderate_activity, high_activity, recovery, and poor_quality (which has
missing values, impossible values, and low signal quality).

## Example output

```text
==================================================
Session: recovery   Participant: P004
Classification: RECOVERING
Usable observations: 12 of 12
Why: heart rate and activity dropped near the end of the session

==================================================
Session: poor_quality   Participant: P005
Classification: INSUFFICIENT_DATA
Usable observations: 0 of 12
Why: not enough usable observations to classify
Rejected observations:
 - heart_rate is missing
 - heart_rate is out of range
 - activity_level is out of range
```

## Known limitations

The classification only really uses heart rate; activity level is only
used for the recovery check. Recovery is only checked by comparing the
start and end of the session. The thresholds are fixed and only fit the
simulated data used here.