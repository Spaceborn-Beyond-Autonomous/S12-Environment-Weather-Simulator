from .emi_model import EMIModel


def main():

    print("==============================")
    print(" EMI Simulator")
    print("==============================")


    emi = EMIModel()


    intensity = emi.calculate_intensity(
        drone_x=10,
        drone_y=10,
        drone_z=5
    )


    print("EMI Intensity:", intensity)


    noisy_mag = emi.inject_magnetometer_noise(
        original_mag_value=50.0,
        emi_intensity=intensity
    )


    print("Magnetometer value:", noisy_mag)


    covariance = emi.inject_gps_covariance_noise(
        base_covariance=1.0,
        emi_intensity=intensity
    )


    print("GPS covariance:", covariance)


    print("EMI Simulation OK")


if __name__ == "__main__":
    main()