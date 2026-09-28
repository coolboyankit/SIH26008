import json
import os
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_SCALES = [0.25, 0.50, 1.00, 2.00]

# Higher = more tolerant of small changes
TOLERANCE_MULTIPLIER = 3.5

# Minimum score above which a pattern can be considered abnormal
MIN_ERROR_SCORE = 3.0


# ============================================================
# REFERENCE FILE
# ============================================================

def load_reference(filename="bandsaw_normal_reference.json"):
    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Reference file not found: {filename}"
        )

    with open(filename, "r") as f:
        return json.load(f)


def save_reference(reference, filename="bandsaw_normal_reference.json"):
    with open(filename, "w") as f:
        json.dump(reference, f, indent=4)


# ============================================================
# BASIC SIGNAL FEATURES
# ============================================================

def extract_features(samples, sample_rate):
    """
    Extract features from one signal window.
    """

    x = np.asarray(samples, dtype=float)

    if len(x) < 5:
        return None

    # Remove DC/bias
    x = x - np.mean(x)

    rms = float(np.sqrt(np.mean(x ** 2)))
    std = float(np.std(x))
    peak = float(np.max(np.abs(x)))
    peak_to_peak = float(np.ptp(x))

    # Frequency features
    fft = np.fft.rfft(x)
    magnitude = np.abs(fft)

    frequencies = np.fft.rfftfreq(
        len(x),
        d=1.0 / sample_rate
    )

    # Ignore DC
    if len(magnitude) > 1:
        magnitude[0] = 0

    total_energy = float(np.sum(magnitude ** 2)) + 1e-12

    bands = [
        (0, 20),
        (20, 40),
        (40, 60),
        (60, 80),
        (80, 100),
        (100, 150),
        (150, 200),
        (200, 250)
    ]

    band_energy = []

    for low, high in bands:

        mask = (
            (frequencies >= low) &
            (frequencies < high)
        )

        energy = float(
            np.sum(magnitude[mask] ** 2)
            / total_energy
        )

        band_energy.append(energy)

    return np.array(
        [
            rms,
            std,
            peak,
            peak_to_peak,
            *band_energy
        ],
        dtype=float
    )


# ============================================================
# NORMAL DATA EXTRACTION
# ============================================================

def get_normal_samples(reference):

    segments = reference.get("normal_segments", [])

    all_samples = []

    for segment in segments:

        samples = segment.get("samples", [])

        if samples:
            all_samples.extend(samples)

    return np.asarray(all_samples, dtype=float)


# ============================================================
# NORMAL MODEL
# ============================================================

def build_normal_model(
    reference,
    scales=DEFAULT_SCALES
):

    sample_rate = float(
        reference.get("sample_rate_hz", 500)
    )

    normal_segments = reference.get(
        "normal_segments",
        []
    )

    feature_vectors = []

    for segment in normal_segments:

        samples = np.asarray(
            segment.get("samples", []),
            dtype=float
        )

        if len(samples) < 10:
            continue

        for scale in scales:

            window_size = int(
                scale * sample_rate
            )

            if window_size < 10:
                continue

            if len(samples) < window_size:
                continue

            step = max(
                1,
                window_size // 4
            )

            for start in range(
                0,
                len(samples) - window_size + 1,
                step
            ):

                window = samples[
                    start:start + window_size
                ]

                features = extract_features(
                    window,
                    sample_rate
                )

                if features is not None:
                    feature_vectors.append(features)

    if not feature_vectors:
        raise ValueError(
            "Not enough normal data to build model."
        )

    features = np.asarray(
        feature_vectors,
        dtype=float
    )

    # Robust statistics
    median = np.median(
        features,
        axis=0
    )

    mad = np.median(
        np.abs(features - median),
        axis=0
    )

    # Prevent zero tolerance
    mad[mad < 1e-9] = 1e-9

    # Convert MAD into usable tolerance
    tolerance = mad * TOLERANCE_MULTIPLIER

    model = {
        "median": median.tolist(),
        "mad": mad.tolist(),
        "tolerance": tolerance.tolist(),
        "feature_count": int(features.shape[1]),
        "training_windows": int(len(features))
    }

    reference["normal_model"] = model

    return reference


# ============================================================
# FEATURE DEVIATION
# ============================================================

def calculate_deviation(
    features,
    model
):

    median = np.asarray(
        model["median"],
        dtype=float
    )

    tolerance = np.asarray(
        model["tolerance"],
        dtype=float
    )

    tolerance[
        tolerance < 1e-9
    ] = 1e-9

    difference = np.abs(
        features - median
    )

    normalized = (
        difference / tolerance
    )

    # RMS-like overall deviation
    score = float(
        np.sqrt(
            np.mean(normalized ** 2)
        )
    )

    return score


# ============================================================
# ACCEPTED VARIATION MATCHING
# ============================================================

def compare_accepted_variations(
    features,
    reference
):

    variations = reference.get(
        "accepted_variations",
        []
    )

    if not variations:
        return None

    best_id = None
    best_distance = float("inf")

    for variation in variations:

        saved_features = np.asarray(
            variation.get("features", []),
            dtype=float
        )

        tolerance = float(
            variation.get(
                "tolerance",
                1.0
            )
        )

        if len(saved_features) != len(features):
            continue

        distance = float(
            np.sqrt(
                np.mean(
                    (features - saved_features) ** 2
                )
            )
        )

        if distance < best_distance:

            best_distance = distance
            best_id = variation.get(
                "pattern_id"
            )

    if best_id is not None:

        variation = next(
            v for v in variations
            if v.get("pattern_id") == best_id
        )

        if best_distance <= variation.get(
            "tolerance",
            1.0
        ):
            return {
                "matched": True,
                "pattern_id": best_id,
                "distance": best_distance
            }

    return {
        "matched": False,
        "pattern_id": None,
        "distance": best_distance
    }


# ============================================================
# ANALYZE ONE WINDOW
# ============================================================

def analyze_window(
    samples,
    sample_rate,
    reference
):

    features = extract_features(
        samples,
        sample_rate
    )

    if features is None:
        return {
            "status": "NORMAL",
            "score": 0.0,
            "features": []
        }

    # Make model if not already available
    if "normal_model" not in reference:
        build_normal_model(reference)

    model = reference["normal_model"]

    score = calculate_deviation(
        features,
        model
    )

    # First check patterns that user already accepted
    accepted = compare_accepted_variations(
        features,
        reference
    )

    if accepted and accepted["matched"]:

        return {
            "status": "NORMAL",
            "reason": "ACCEPTED_VARIATION",
            "accepted_pattern": accepted["pattern_id"],
            "score": score,
            "accepted_distance": accepted["distance"],
            "features": features.tolist()
        }

    # Normal variation
    if score < MIN_ERROR_SCORE:

        return {
            "status": "NORMAL",
            "reason": "NORMAL_REFERENCE",
            "score": score,
            "features": features.tolist()
        }

    # Abnormal
    return {
        "status": "ERROR",
        "reason": "PATTERN_DEVIATION",
        "score": score,
        "features": features.tolist()
    }


# ============================================================
# ACCEPT A DETECTED PATTERN
# ============================================================

def add_accepted_variation(
    reference,
    features,
    duration,
    tolerance=1.5
):

    if "accepted_variations" not in reference:
        reference["accepted_variations"] = []

    existing = reference[
        "accepted_variations"
    ]

    number = len(existing) + 1

    pattern_id = f"AV{number:03d}"

    variation = {
        "pattern_id": pattern_id,
        "duration": float(duration),
        "features": list(
            map(float, features)
        ),
        "tolerance": float(tolerance)
    }

    existing.append(variation)

    return pattern_id


# ============================================================
# BUILD MODEL AND SAVE
# ============================================================

def prepare_reference(
    filename="bandsaw_normal_reference.json"
):

    reference = load_reference(filename)

    reference = build_normal_model(
        reference
    )

    save_reference(
        reference,
        filename
    )

    return reference


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("Loading normal reference...")

    reference = prepare_reference()

    print(
        "Normal model created successfully."
    )

    print(
        "Training windows:",
        reference["normal_model"]
        ["training_windows"]
    )

    print("Algorithm ready.")