<<<<<<< HEAD
# Budget Traveller with Coupons

A Python + Streamlit application that finds the minimum-cost directed flight route from city `1` to city `N`, subject to a maximum number of intermediate stops and a limited number of discount coupons.

## Features

- Manual flight input (Option 1)
- Upload a CSV flight graph (Option 2)
- Generate a random directed graph with user-selected `N`, `K`, and `C` (Option 3)
- Dynamic programming over flights taken and coupons used
- Each coupon discounts one flight to `floor(price / 2)`
- Output `-1` if the destination cannot be reached within the stop limit
- Export a CSV with chosen-path markers, coupon markers, charged price, and path order
- Interactive directed graph visualization and journey-step animation

## Requirements

- Python 3.10 or newer

## Run locally

```bash
python -m venv .venv
```

Activate the environment:

**Windows**
```bash
.venv\Scripts\activate
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install dependencies and launch:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser, usually at `http://localhost:8501`.

## CSV input format

Create a CSV named `flights.csv` with these columns:

```csv
u,v,p
1,2,200
1,3,300
2,4,250
4,5,150
```

- `u`: source city
- `v`: destination city
- `p`: non-negative ticket price

Cities must be numbered from `1` through `N`. The destination is always city `N`.

## Algorithm

At most `K` intermediate stops means at most `K + 1` flights. The dynamic program tracks states `(city, flights_taken, coupons_used)`. For each flight, it considers both paying the full fare and, when a coupon remains, paying `price // 2`. The cheapest destination state within `K + 1` flights is returned.

Approximate time complexity: `O((K + 1) * C * M)` transitions in the straightforward implementation, with state storage bounded by `O(N * (K + 1) * (C + 1))` plus parent pointers.

## CSV output

The output file contains:

- `u`, `v`, `p`: original flight
- `chosen_path`: `x` when the flight is part of the selected route
- `coupon_used`: `x` when a coupon was used on that flight
- `charged_price`: price paid for a selected flight
- `path_order`: position in the chosen journey

## Colour legend

- Green: start city
- Red: destination
- Orange: cities on the chosen route
- Blue: selected route flights
- Gold: selected route flights discounted with a coupon

## Notes

The graph generator guarantees a direct chain from city `1` to city `N` before adding random flights. Depending on `K`, that guaranteed chain may still be too long; the solver correctly reports `-1` if no valid route is available within the stop limit.
=======
# budget-traveller-with-coupons
A Python application that finds the minimum-cost flight route using stop limits and discount coupons, with graph visualization and CSV export.
>>>>>>> 4ebb43d91914b0025259a168566bffdd0b1291f5
