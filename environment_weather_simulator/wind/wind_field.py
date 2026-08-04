from typing import Tuple, List
import math
from environment_weather_simulator.api import WindFieldSample
from environment_weather_simulator.wind.gust_shear import GustShearModel
from environment_weather_simulator.wind.turbulence import TurbulenceModel

class WindFieldGrid:
    """
    Generates a 3D spatial wind grid and combines spatial interpolation,
    altitude shear, discrete gusting, and stochastic turbulence.
    """
    def __init__(
        self,
        bounds: Tuple[float, float, float, float, float, float] = (-100.0, 100.0, -100.0, 100.0, 0.0, 50.0),
        resolution: float = 10.0,
        base_wind: Tuple[float, float, float] = (5.0, 2.0, 0.0),
        enable_shear: bool = True,
        enable_turbulence: bool = True
    ):
        self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax = bounds
        self.resolution = resolution
        self.base_wind = base_wind

        # Grid cell dimensions
        self.nx = max(2, int(math.ceil((self.xmax - self.xmin) / resolution)) + 1)
        self.ny = max(2, int(math.ceil((self.ymax - self.ymin) / resolution)) + 1)
        self.nz = max(2, int(math.ceil((self.zmax - self.zmin) / resolution)) + 1)

        self.grid = self._generate_grid()

        # Internal sub-models
        self.shear_model = GustShearModel(reference_speed=math.sqrt(base_wind[0]**2 + base_wind[1]**2)) if enable_shear else None
        self.turbulence_model = TurbulenceModel() if enable_turbulence else None
        self._last_timestamp = 0.0

    def _generate_grid(self) -> List[List[List[Tuple[float, float, float]]]]:
        grid = []
        for ix in range(self.nx):
            plane = []
            for iy in range(self.ny):
                line = []
                for iz in range(self.nz):
                    line.append(self.base_wind)
                plane.append(line)
            grid.append(plane)
        return grid

    def sample_at(self, position_xyz: Tuple[float, float, float], timestamp: float = 0.0) -> WindFieldSample:
        """
        Queries the combined wind vector at (x, y, z, t).
        """
        x, y, z = position_xyz

        # 1. Clamp inside bounding box
        x_c = max(self.xmin, min(self.xmax, x))
        y_c = max(self.ymin, min(self.ymax, y))
        z_c = max(self.zmin, min(self.zmax, z))

        # 2. Normalized grid coordinates
        gx = (x_c - self.xmin) / self.resolution
        gy = (y_c - self.ymin) / self.resolution
        gz = (z_c - self.zmin) / self.resolution

        x0 = min(int(math.floor(gx)), self.nx - 2)
        y0 = min(int(math.floor(gy)), self.ny - 2)
        z0 = min(int(math.floor(gz)), self.nz - 2)

        x1, y1, z1 = x0 + 1, y0 + 1, z0 + 1

        xd, yd, zd = gx - x0, gy - y0, gz - z0

        # 3. Trilinear spatial interpolation of base wind
        c000 = self.grid[x0][y0][z0]
        c100 = self.grid[x1][y0][z0]
        c010 = self.grid[x0][y1][z0]
        c110 = self.grid[x1][y1][z0]
        c001 = self.grid[x0][y0][z1]
        c101 = self.grid[x1][y0][z1]
        c011 = self.grid[x0][y1][z1]
        c111 = self.grid[x1][y1][z1]

        base_v = []
        for i in range(3):
            c00 = c000[i] * (1 - xd) + c100[i] * xd
            c01 = c001[i] * (1 - xd) + c101[i] * xd
            c10 = c010[i] * (1 - xd) + c110[i] * xd
            c11 = c011[i] * (1 - xd) + c111[i] * xd

            c0 = c00 * (1 - yd) + c10 * yd
            c1 = c01 * (1 - yd) + c11 * yd

            c = c0 * (1 - zd) + c1 * zd
            base_v.append(c)

        vx, vy, vz = base_v[0], base_v[1], base_v[2]
        mean_speed = math.sqrt(vx**2 + vy**2 + vz**2)

        # 4. Apply altitude shear & gusting
        gust_mag = 0.0
        shear_grad = 0.0
        if self.shear_model:
            shear_factor = self.shear_model.get_shear_velocity(z_c) / max(self.shear_model.ref_speed, 1e-3)
            vx *= shear_factor
            vy *= shear_factor
            shear_grad = self.shear_model.get_shear_gradient(z_c)
            gust_mag = self.shear_model.get_gust_magnitude(timestamp)

            if mean_speed > 0:
                vx += (vx / mean_speed) * gust_mag
                vy += (vy / mean_speed) * gust_mag

        # 5. Apply stochastic turbulence
        dt = max(0.0, timestamp - self._last_timestamp)
        self._last_timestamp = timestamp

        u_t, v_t, w_t = 0.0, 0.0, 0.0
        turb_intensity = 0.0
        if self.turbulence_model and dt > 0.0:
            u_t, v_t, w_t = self.turbulence_model.step(dt, max(mean_speed, 1.0), z_c)
            turb_intensity = self.turbulence_model.get_turbulence_intensity(max(mean_speed, 1.0))

        
        final_vx = vx + u_t
        final_vy = vy + v_t
        final_vz = vz + w_t

        # Create WindFieldSample using class-based API
        sample = WindFieldSample()

        sample.velocity_vector = (final_vx, final_vy, final_vz)
        sample.gust_magnitude = gust_mag
        sample.shear_gradient = shear_grad
        sample.turbulence_intensity = turb_intensity

        return sample