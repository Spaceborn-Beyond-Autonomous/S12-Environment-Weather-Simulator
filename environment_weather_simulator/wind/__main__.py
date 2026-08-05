#!/usr/bin/env python3

from environment_weather_simulator.wind import WindFieldGrid


def main():

    print("=" * 50)
    print(" Environment Weather Simulator - Wind Module")
    print("=" * 50)

    wind = WindFieldGrid()

    positions = [
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 10.0),
        (0.0, 0.0, 50.0),
    ]

    for pos in positions:

        sample = wind.sample_at(
            position_xyz=pos,
            timestamp=1.0
        )

        print("\nPosition:", pos)
        print("Velocity:", sample.velocity_vector)
        print("Gust:", sample.gust_magnitude)
        print("Shear:", sample.shear_gradient)
        print("Turbulence:", sample.turbulence_intensity)


    print("\nWind simulation completed successfully.")


if __name__ == "__main__":
    main()