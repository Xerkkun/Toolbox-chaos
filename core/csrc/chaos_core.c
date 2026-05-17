#include <math.h>
#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) || defined(__CYGWIN__)
  #define CHAOS_API __declspec(dllexport)
#else
  #define CHAOS_API __attribute__((visibility("default")))
#endif

static void lorenz_rhs(double x, double y, double z, double sigma, double rho, double beta,
                       double *dx, double *dy, double *dz) {
    *dx = sigma * (y - x);
    *dy = x * (rho - z) - y;
    *dz = x * y - beta * z;
}

static void step_lorenz(double *x, double *y, double *z,
                        double sigma, double rho, double beta,
                        double dt, int method) {
    double dx1, dy1, dz1;
    double dx2, dy2, dz2;
    double dx3, dy3, dz3;
    double dx4, dy4, dz4;
    double xn, yn, zn;

    if (method == 0) { /* Euler */
        lorenz_rhs(*x, *y, *z, sigma, rho, beta, &dx1, &dy1, &dz1);
        *x += dt * dx1;
        *y += dt * dy1;
        *z += dt * dz1;
        return;
    }

    if (method == 1) { /* Heun / improved Euler */
        lorenz_rhs(*x, *y, *z, sigma, rho, beta, &dx1, &dy1, &dz1);
        xn = *x + dt * dx1;
        yn = *y + dt * dy1;
        zn = *z + dt * dz1;
        lorenz_rhs(xn, yn, zn, sigma, rho, beta, &dx2, &dy2, &dz2);
        *x += 0.5 * dt * (dx1 + dx2);
        *y += 0.5 * dt * (dy1 + dy2);
        *z += 0.5 * dt * (dz1 + dz2);
        return;
    }

    /* RK4 default */
    lorenz_rhs(*x, *y, *z, sigma, rho, beta, &dx1, &dy1, &dz1);
    lorenz_rhs(*x + 0.5 * dt * dx1, *y + 0.5 * dt * dy1, *z + 0.5 * dt * dz1,
               sigma, rho, beta, &dx2, &dy2, &dz2);
    lorenz_rhs(*x + 0.5 * dt * dx2, *y + 0.5 * dt * dy2, *z + 0.5 * dt * dz2,
               sigma, rho, beta, &dx3, &dy3, &dz3);
    lorenz_rhs(*x + dt * dx3, *y + dt * dy3, *z + dt * dz3,
               sigma, rho, beta, &dx4, &dy4, &dz4);

    *x += (dt / 6.0) * (dx1 + 2.0 * dx2 + 2.0 * dx3 + dx4);
    *y += (dt / 6.0) * (dy1 + 2.0 * dy2 + 2.0 * dy3 + dy4);
    *z += (dt / 6.0) * (dz1 + 2.0 * dz2 + 2.0 * dz3 + dz4);
}

static int state_invalid(double x, double y, double z, double esc_radius) {
    if (!isfinite(x) || !isfinite(y) || !isfinite(z)) return 1;
    if (fabs(x) > esc_radius || fabs(y) > esc_radius || fabs(z) > esc_radius) return 1;
    return 0;
}

CHAOS_API int lorenz_simulate(
    double x0, double y0, double z0,
    double sigma, double rho, double beta,
    double dt, double T,
    int method,
    double *t_out,
    double *X_out,
    int n
) {
    if (dt <= 0.0 || T <= 0.0 || n < 2 || t_out == NULL || X_out == NULL) {
        return -1;
    }

    double x = x0, y = y0, z = z0;
    double t = 0.0;
    t_out[0] = t;
    X_out[0] = x;
    X_out[1] = y;
    X_out[2] = z;

    for (int i = 1; i < n; ++i) {
        step_lorenz(&x, &y, &z, sigma, rho, beta, dt, method);
        t += dt;
        t_out[i] = t;
        X_out[3 * i + 0] = x;
        X_out[3 * i + 1] = y;
        X_out[3 * i + 2] = z;
    }
    return 0;
}

CHAOS_API int lorenz_bifurcation_poincare(
    double x0, double y0, double z0,
    double sigma, double beta,
    double rho_min, double rho_max,
    int n_rho,
    double dt, double T_trans, double T_keep,
    int max_crossings_per_rho,
    int continuation,
    int method,
    double *out_rho,
    double *out_z,
    int *out_count
) {
    if (n_rho < 1 || max_crossings_per_rho < 1 || dt <= 0.0 || T_keep <= 0.0 ||
        out_rho == NULL || out_z == NULL || out_count == NULL) {
        return -1;
    }

    int steps_trans = (int)(T_trans / dt);
    int steps_keep = (int)(T_keep / dt);
    if (steps_keep < 2) steps_keep = 2;

    int count = 0;
    int denom = (n_rho == 1) ? 1 : (n_rho - 1);

    double x_seed = x0, y_seed = y0, z_seed = z0;

    for (int j = 0; j < n_rho; ++j) {
        double rho = rho_min + (rho_max - rho_min) * ((double)j) / ((double)denom);
        double x = x_seed, y = y_seed, z = z_seed;
        int valid = 1;

        for (int i = 0; i < steps_trans; ++i) {
            step_lorenz(&x, &y, &z, sigma, rho, beta, dt, method);
            if (state_invalid(x, y, z, 1e6)) {
                valid = 0;
                break;
            }
        }

        if (!valid) {
            if (continuation) {
                x_seed = x0;
                y_seed = y0;
                z_seed = z0;
            }
            continue;
        }

        int crossings_this_rho = 0;
        double x_prev = x, y_prev = y, z_prev = z;

        for (int i = 0; i < steps_keep; ++i) {
            double x_new = x_prev, y_new = y_prev, z_new = z_prev;
            step_lorenz(&x_new, &y_new, &z_new, sigma, rho, beta, dt, method);

            if (state_invalid(x_new, y_new, z_new, 1e6)) {
                valid = 0;
                break;
            }

            if (x_prev > 0.0 && x_new <= 0.0) {
                double denom_cross = x_prev - x_new;
                double alpha = 0.0;
                if (fabs(denom_cross) > 1e-15) {
                    alpha = x_prev / denom_cross;
                }
                if (alpha < 0.0) alpha = 0.0;
                if (alpha > 1.0) alpha = 1.0;

                double z_cross = z_prev + alpha * (z_new - z_prev);
                if (crossings_this_rho < max_crossings_per_rho) {
                    out_rho[count] = rho;
                    out_z[count] = z_cross;
                    count += 1;
                    crossings_this_rho += 1;
                }
            }

            x_prev = x_new;
            y_prev = y_new;
            z_prev = z_new;
        }

        if (continuation && valid) {
            x_seed = x_prev;
            y_seed = y_prev;
            z_seed = z_prev;
        } else if (continuation && !valid) {
            x_seed = x0;
            y_seed = y0;
            z_seed = z0;
        }
    }

    *out_count = count;
    return 0;
}

CHAOS_API int lorenz_basin_plane(
    double sigma, double rho, double beta,
    double z0_fixed,
    double x_min, double x_max,
    double y_min, double y_max,
    int nx, int ny,
    double dt, double T_total,
    double hit_radius, double esc_radius,
    int method,
    uint8_t *basin_out
) {
    if (nx < 2 || ny < 2 || dt <= 0.0 || T_total <= 0.0 || basin_out == NULL) {
        return -1;
    }

    int steps_total = (int)(T_total / dt);
    if (steps_total < 2) steps_total = 2;

    int denom_x = (nx == 1) ? 1 : (nx - 1);
    int denom_y = (ny == 1) ? 1 : (ny - 1);
    int has_pair = (rho > 1.0) ? 1 : 0;

    double s = 0.0, z_eq = 0.0;
    if (has_pair) {
        s = sqrt(beta * (rho - 1.0));
        z_eq = rho - 1.0;
    }

    for (int iy = 0; iy < ny; ++iy) {
        double y0 = y_min + (y_max - y_min) * ((double)iy) / ((double)denom_y);
        for (int ix = 0; ix < nx; ++ix) {
            double x0 = x_min + (x_max - x_min) * ((double)ix) / ((double)denom_x);
            double x = x0, y = y0, z = z0_fixed;
            uint8_t basin_class = 1;

            for (int k = 0; k < steps_total; ++k) {
                step_lorenz(&x, &y, &z, sigma, rho, beta, dt, method);

                if (state_invalid(x, y, z, esc_radius)) {
                    basin_class = 0;
                    break;
                }

                if (has_pair) {
                    double dp = sqrt((x - s) * (x - s) + (y - s) * (y - s) + (z - z_eq) * (z - z_eq));
                    double dm = sqrt((x + s) * (x + s) + (y + s) * (y + s) + (z - z_eq) * (z - z_eq));
                    if (dp < hit_radius) {
                        basin_class = 2;
                        break;
                    }
                    if (dm < hit_radius) {
                        basin_class = 3;
                        break;
                    }
                } else {
                    double d0 = sqrt(x * x + y * y + z * z);
                    if (d0 < hit_radius) {
                        basin_class = 4;
                        break;
                    }
                }
            }

            basin_out[iy * nx + ix] = basin_class;
        }
    }
    return 0;
}
