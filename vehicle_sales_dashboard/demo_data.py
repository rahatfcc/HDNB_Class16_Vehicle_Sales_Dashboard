"""Synthetic stand-in for the Kaggle "Vehicle Sales Data" file (car_prices.csv).

It mimics the REAL schema and its messiness (mixed-case makes, missing values,
text sale dates, odd odometer values, 1-5 and 10-49 condition scales) so the
dashboard runs even before you have downloaded the real data.

!! The numbers it produces are fake. Never publish insights from it. !!
"""
import numpy as np
import pandas as pd

_MAKES = {
    # make: (weight, base price in $, [models], [body styles])
    "Ford": (14, 21000, ["F-150", "Fusion", "Escape", "Focus", "Explorer"], ["Sedan", "SUV", "Crew Cab"]),
    "Chevrolet": (11, 19000, ["Malibu", "Impala", "Cruze", "Silverado 1500", "Equinox"], ["Sedan", "SUV", "Crew Cab"]),
    "Nissan": (11, 17000, ["Altima", "Sentra", "Rogue", "Versa", "Maxima"], ["Sedan", "SUV"]),
    "Toyota": (8, 20000, ["Camry", "Corolla", "RAV4", "Prius", "Tacoma"], ["Sedan", "SUV", "Hatchback"]),
    "Honda": (6, 19000, ["Accord", "Civic", "CR-V", "Odyssey", "Fit"], ["Sedan", "SUV", "Minivan"]),
    "Hyundai": (5, 16000, ["Sonata", "Elantra", "Santa Fe", "Accent"], ["Sedan", "SUV"]),
    "Dodge": (5, 18000, ["Charger", "Grand Caravan", "Avenger", "Journey"], ["Sedan", "Minivan", "SUV"]),
    "BMW": (4, 38000, ["3 Series", "5 Series", "X5", "X3"], ["Sedan", "SUV", "Coupe"]),
    "Mercedes-Benz": (3, 42000, ["C-Class", "E-Class", "GLK-Class", "M-Class"], ["Sedan", "SUV"]),
    "Kia": (3, 16500, ["Optima", "Sorento", "Soul", "Forte"], ["Sedan", "SUV"]),
    "Jeep": (3, 24000, ["Wrangler", "Grand Cherokee", "Patriot"], ["SUV"]),
    "Lexus": (2, 36000, ["ES 350", "RX 350", "IS 250"], ["Sedan", "SUV"]),
    "Volkswagen": (2, 17000, ["Jetta", "Passat", "Beetle"], ["Sedan", "Hatchback"]),
    "Cadillac": (1, 34000, ["Escalade", "CTS", "SRX"], ["SUV", "Sedan"]),
    "Porsche": (0.4, 70000, ["Cayenne", "911", "Boxster"], ["SUV", "Coupe"]),
}
_STATES = ["ca", "fl", "tx", "pa", "mi", "oh", "ga", "nj", "il", "nc", "az", "tn", "va", "mn", "mo", "wa", "ny", "ma"]
_STATE_W = [16, 14, 8, 8, 6, 6, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 1]
_COLORS = ["black", "white", "silver", "gray", "blue", "red", "green", "gold", "beige", "burgundy", "brown", "—"]


def make_demo_raw(n: int = 40_000, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame shaped like the raw car_prices.csv."""
    rng = np.random.default_rng(seed)
    makes = list(_MAKES)
    w = np.array([_MAKES[m][0] for m in makes], dtype=float)
    mk = rng.choice(makes, size=n, p=w / w.sum())

    model, body, base = [], [], []
    for m in mk:
        _, price, models, bodies = _MAKES[m]
        model.append(rng.choice(models))
        body.append(rng.choice(bodies))
        base.append(price)
    base = np.array(base, dtype=float)

    year = np.clip(2015 - rng.gamma(2.0, 2.6, n).astype(int), 1995, 2015)
    sale = pd.to_datetime("2014-01-02") + pd.to_timedelta(rng.integers(0, 560, n), unit="D")
    sale = sale + pd.to_timedelta(rng.choice([4, 12, 13], n), unit="h") + pd.to_timedelta(30, unit="m")
    age = np.clip(sale.year.to_numpy() - year, 0, None)

    odometer = np.clip(rng.normal(11_000 * age + 6_000, 9_000), 100, None)
    cond_raw = np.clip(rng.normal(3.6 - 0.04 * age, 0.8), 1, 5)
    condition = np.where(rng.random(n) < 0.55, np.round(cond_raw * 10), np.round(cond_raw, 1))  # mixed scales
    mmr = base * 0.88 ** age * (1 - np.clip(odometer / 400_000, 0, 0.4)) * rng.normal(1, 0.06, n)
    mmr = np.clip(mmr, 600, None).round(-2)
    selling = np.clip(mmr * rng.normal(1.0, 0.07, n) + 80 * (condition % 10 - 3), 300, None).round(-2)

    df = pd.DataFrame({
        "year": year,
        "make": mk,
        "model": model,
        "trim": rng.choice(["Base", "LX", "SE", "Limited", "Sport"], n),
        "body": body,
        "transmission": rng.choice(["automatic", "manual", None], n, p=[0.86, 0.04, 0.10]),
        "vin": [f"1xx{i:014d}" for i in range(n)],
        "state": rng.choice(_STATES, n, p=np.array(_STATE_W) / sum(_STATE_W)),
        "condition": condition,
        "odometer": odometer.round(),
        "color": rng.choice(_COLORS, n, p=[.2, .19, .16, .15, .09, .07, .04, .03, .02, .02, .02, .01]),
        "interior": rng.choice(["black", "gray", "beige", "tan", "brown", "—"], n),
        "seller": rng.choice([f"seller {i}" for i in range(300)], n),
        "mmr": mmr,
        "sellingprice": selling,
        "saledate": sale.strftime("%a %b %d %Y %H:%M:%S") + " GMT-0800 (PST)",
    })

    # --- inject the kinds of mess the real file has ---
    messy = rng.random(n)
    df.loc[messy < 0.06, "make"] = df["make"].str.lower()                 # 'ford'
    df.loc[(messy >= 0.06) & (messy < 0.08), "make"] = df["make"] + " "   # trailing space
    df.loc[(df["make"].str.strip() == "Volkswagen") & (rng.random(n) < 0.3), "make"] = "vw"
    df.loc[rng.random(n) < 0.02, "make"] = None
    df.loc[rng.random(n) < 0.03, "body"] = df["body"].str.lower()
    df.loc[rng.random(n) < 0.01, "odometer"] = 999_999
    df.loc[rng.random(n) < 0.002, "odometer"] = None
    df.loc[rng.random(n) < 0.02, "condition"] = None
    df.loc[rng.random(n) < 0.0005, "sellingprice"] = 1
    df.loc[rng.random(n) < 0.0003, "sellingprice"] = None
    df.loc[rng.random(n) < 0.0003, "state"] = "3vwd17aj4fm258472"           # junk leaking into state
    df.loc[rng.random(n) < 0.0003, "saledate"] = None
    df.loc[rng.random(n) < 0.05, "transmission"] = "Sedan"                  # value in the wrong column
    return df
