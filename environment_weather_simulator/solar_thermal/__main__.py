from .solar_model import SolarModel
from .thermal_model import ThermalModel


def main():

    print("==============================")
    print(" Solar Thermal Simulator")
    print("==============================")

    solar = SolarModel()

    irradiance = solar.calculate_irradiance(
        time_of_day_hours=12.0,
        cloud_cover_percent=0.2
    )

    print("Solar Irradiance:", irradiance, "W/m2")


    thermal = ThermalModel()

    temp = thermal.calculate_surface_temperature(
        ambient_temp_c=30.0,
        solar_irradiance=irradiance,
        wind_speed_m_s=5.0
    )


    print("Surface Temperature:", temp, "C")


    noise = thermal.calculate_camera_thermal_noise(temp)

    print("Thermal Noise:", noise)

    print("Solar Thermal Simulation OK")


if __name__ == "__main__":
    main()