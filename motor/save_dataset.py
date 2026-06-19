import csv
from motor.run_timeseries import simulate_motor

def save_to_csv(filename="motor_dataset.csv", steps=100, dt=0.1):
    history = simulate_motor(steps=steps, dt=dt)

    if not history:
        return

    fieldnames = list(history[0].keys())

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history)

    print(f"Saved {len(history)} rows to {filename}")

if __name__ == "__main__":
    save_to_csv("motor_dataset.csv", steps=100, dt=0.1)