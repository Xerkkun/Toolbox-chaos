#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

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

static uint8_t classify_residual_dynamics(int crossing_count, int cluster_count,
                                          double z_min, double z_max,
                                          double x_tail_min, double x_tail_max,
                                          double y_tail_min, double y_tail_max,
                                          double z_tail_min, double z_tail_max,
                                          uint8_t periodic_class) {
    double x_span = x_tail_max - x_tail_min;
    double y_span = y_tail_max - y_tail_min;
    double z_span = z_tail_max - z_tail_min;
    double tail_span = fmax(fmax(x_span, y_span), z_span);
    if (isfinite(tail_span) && tail_span < 0.75) return periodic_class;
    if (crossing_count < 3) return 1;
    if (crossing_count >= 6 && cluster_count <= 2 &&
        isfinite(z_min) && isfinite(z_max) && fabs(z_max - z_min) <= 0.75) {
        return periodic_class;
    }
    return 1;
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
    int tail_start = steps_total / 2;

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
            int crossing_count = 0;
            int cluster_count = 0;
            double clusters[16];
            double z_cross_min = HUGE_VAL;
            double z_cross_max = -HUGE_VAL;
            double x_tail_min = HUGE_VAL, y_tail_min = HUGE_VAL, z_tail_min = HUGE_VAL;
            double x_tail_max = -HUGE_VAL, y_tail_max = -HUGE_VAL, z_tail_max = -HUGE_VAL;

            for (int k = 0; k < steps_total; ++k) {
                double x_prev = x;
                double z_prev = z;
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

                if (k >= tail_start) {
                    if (x < x_tail_min) x_tail_min = x;
                    if (x > x_tail_max) x_tail_max = x;
                    if (y < y_tail_min) y_tail_min = y;
                    if (y > y_tail_max) y_tail_max = y;
                    if (z < z_tail_min) z_tail_min = z;
                    if (z > z_tail_max) z_tail_max = z;

                    if (x_prev > 0.0 && x <= 0.0) {
                        double denom_cross = x_prev - x;
                        double alpha = 0.0;
                        if (fabs(denom_cross) > 1e-15) alpha = x_prev / denom_cross;
                        if (alpha < 0.0) alpha = 0.0;
                        if (alpha > 1.0) alpha = 1.0;

                        double z_cross = z_prev + alpha * (z - z_prev);
                        double tol = 0.05 + 0.01 * fabs(z_cross);
                        int matched = 0;
                        if (z_cross < z_cross_min) z_cross_min = z_cross;
                        if (z_cross > z_cross_max) z_cross_max = z_cross;
                        crossing_count += 1;

                        for (int c = 0; c < cluster_count && c < 16; ++c) {
                            if (fabs(z_cross - clusters[c]) <= tol) {
                                clusters[c] = 0.85 * clusters[c] + 0.15 * z_cross;
                                matched = 1;
                                break;
                            }
                        }
                        if (!matched) {
                            if (cluster_count < 16) {
                                clusters[cluster_count] = z_cross;
                            }
                            cluster_count += 1;
                        }
                    }
                }
            }

            if (basin_class == 1) {
                basin_class = classify_residual_dynamics(
                    crossing_count, cluster_count, z_cross_min, z_cross_max,
                    x_tail_min, x_tail_max, y_tail_min, y_tail_max, z_tail_min, z_tail_max,
                    5
                );
            }

            basin_out[iy * nx + ix] = basin_class;
        }
    }
    return 0;
}

enum {
    SYS_LORENZ = 0,
    SYS_ROSSLER = 1,
    SYS_CHUA = 2,
    SYS_CHEN = 3,
    SYS_LU = 4,
    SYS_HENON = 5,
    SYS_LOGISTIC = 6,
    SYS_IKEDA = 7,
    SYS_MACKEY_GLASS = 8,
    SYS_DUFFING_UEDA = 9,
    SYS_RABINOVICH_FABRIKANT = 10,
    SYS_RIKITAKE = 11,
    SYS_SPROTT_A = 12,
    SYS_THOMAS = 13,
    SYS_HINDMARSH_ROSE = 14,
    SYS_LORENZ96 = 15
};

static double param_at(const double *params, int n_params, int idx, double fallback) {
    if (params == NULL || idx < 0 || idx >= n_params) return fallback;
    return params[idx];
}

static int is_map_system(int system_id) {
    return system_id == SYS_HENON || system_id == SYS_LOGISTIC || system_id == SYS_IKEDA;
}

static int is_dde_system(int system_id) {
    return system_id == SYS_MACKEY_GLASS;
}

static int is_lorenz96_system(int system_id) {
    return system_id == SYS_LORENZ96;
}

static void rhs3_generic(int system_id, double x, double y, double z,
                         const double *p, int n_params,
                         double *dx, double *dy, double *dz) {
    if (system_id == SYS_LORENZ) {
        double sigma = param_at(p, n_params, 0, 10.0);
        double rho = param_at(p, n_params, 1, 28.0);
        double beta = param_at(p, n_params, 2, 8.0 / 3.0);
        *dx = sigma * (y - x);
        *dy = x * (rho - z) - y;
        *dz = x * y - beta * z;
        return;
    }
    if (system_id == SYS_ROSSLER) {
        double a = param_at(p, n_params, 0, 0.2);
        double b = param_at(p, n_params, 1, 0.2);
        double c = param_at(p, n_params, 2, 5.7);
        *dx = -y - z;
        *dy = x + a * y;
        *dz = b + z * (x - c);
        return;
    }
    if (system_id == SYS_CHUA) {
        double alpha = param_at(p, n_params, 0, 15.6);
        double beta = param_at(p, n_params, 1, 28.0);
        double m0 = param_at(p, n_params, 2, -1.143);
        double m1 = param_at(p, n_params, 3, -0.714);
        double fx = m1 * x + 0.5 * (m0 - m1) * (fabs(x + 1.0) - fabs(x - 1.0));
        *dx = alpha * (y - x - fx);
        *dy = x - y + z;
        *dz = -beta * y;
        return;
    }
    if (system_id == SYS_CHEN) {
        double a = param_at(p, n_params, 0, 35.0);
        double b = param_at(p, n_params, 1, 3.0);
        double c = param_at(p, n_params, 2, 28.0);
        *dx = a * (y - x);
        *dy = (c - a) * x - x * z + c * y;
        *dz = x * y - b * z;
        return;
    }
    if (system_id == SYS_LU) {
        double a = param_at(p, n_params, 0, 36.0);
        double b = param_at(p, n_params, 1, 3.0);
        double c = param_at(p, n_params, 2, 20.0);
        *dx = a * (y - x);
        *dy = -x * z + c * y;
        *dz = x * y - b * z;
        return;
    }
    if (system_id == SYS_DUFFING_UEDA) {
        double delta = param_at(p, n_params, 0, 0.2);
        double alpha = param_at(p, n_params, 1, -1.0);
        double beta = param_at(p, n_params, 2, 1.0);
        double gamma = param_at(p, n_params, 3, 0.3);
        double omega = param_at(p, n_params, 4, 1.2);
        *dx = y;
        *dy = -delta * y - alpha * x - beta * x * x * x + gamma * cos(z);
        *dz = omega;
        return;
    }
    if (system_id == SYS_RABINOVICH_FABRIKANT) {
        double alpha = param_at(p, n_params, 0, 1.1);
        double gamma = param_at(p, n_params, 1, 0.87);
        *dx = y * (z - 1.0 + x * x) + gamma * x;
        *dy = x * (3.0 * z + 1.0 - x * x) + gamma * y;
        *dz = -2.0 * z * (alpha + x * y);
        return;
    }
    if (system_id == SYS_RIKITAKE) {
        double mu = param_at(p, n_params, 0, 2.0);
        double a = param_at(p, n_params, 1, 5.0);
        *dx = -mu * x + y * z;
        *dy = -mu * y + x * (z - a);
        *dz = 1.0 - x * y;
        return;
    }
    if (system_id == SYS_SPROTT_A) {
        *dx = y;
        *dy = -x + y * z;
        *dz = 1.0 - y * y;
        return;
    }
    if (system_id == SYS_THOMAS) {
        double b = param_at(p, n_params, 0, 0.18);
        *dx = sin(y) - b * x;
        *dy = sin(z) - b * y;
        *dz = sin(x) - b * z;
        return;
    }
    if (system_id == SYS_HINDMARSH_ROSE) {
        double a = param_at(p, n_params, 0, 1.0);
        double b = param_at(p, n_params, 1, 3.0);
        double c = param_at(p, n_params, 2, 1.0);
        double d = param_at(p, n_params, 3, 5.0);
        double r = param_at(p, n_params, 4, 0.006);
        double s = param_at(p, n_params, 5, 4.0);
        double current = param_at(p, n_params, 6, 3.25);
        double xr = -1.6;
        *dx = y - a * x * x * x + b * x * x - z + current;
        *dy = c - d * x * x - y;
        *dz = r * (s * (x - xr) - z);
        return;
    }
    *dx = 0.0;
    *dy = 0.0;
    *dz = 0.0;
}

static void step3_generic(int system_id, double *x, double *y, double *z,
                          const double *p, int n_params, double dt, int method) {
    double dx1, dy1, dz1, dx2, dy2, dz2, dx3, dy3, dz3, dx4, dy4, dz4;
    if (method == 0) {
        rhs3_generic(system_id, *x, *y, *z, p, n_params, &dx1, &dy1, &dz1);
        *x += dt * dx1;
        *y += dt * dy1;
        *z += dt * dz1;
        return;
    }
    if (method == 1) {
        rhs3_generic(system_id, *x, *y, *z, p, n_params, &dx1, &dy1, &dz1);
        rhs3_generic(system_id, *x + dt * dx1, *y + dt * dy1, *z + dt * dz1, p, n_params, &dx2, &dy2, &dz2);
        *x += 0.5 * dt * (dx1 + dx2);
        *y += 0.5 * dt * (dy1 + dy2);
        *z += 0.5 * dt * (dz1 + dz2);
        return;
    }
    rhs3_generic(system_id, *x, *y, *z, p, n_params, &dx1, &dy1, &dz1);
    rhs3_generic(system_id, *x + 0.5 * dt * dx1, *y + 0.5 * dt * dy1, *z + 0.5 * dt * dz1, p, n_params, &dx2, &dy2, &dz2);
    rhs3_generic(system_id, *x + 0.5 * dt * dx2, *y + 0.5 * dt * dy2, *z + 0.5 * dt * dz2, p, n_params, &dx3, &dy3, &dz3);
    rhs3_generic(system_id, *x + dt * dx3, *y + dt * dy3, *z + dt * dz3, p, n_params, &dx4, &dy4, &dz4);
    *x += (dt / 6.0) * (dx1 + 2.0 * dx2 + 2.0 * dx3 + dx4);
    *y += (dt / 6.0) * (dy1 + 2.0 * dy2 + 2.0 * dy3 + dy4);
    *z += (dt / 6.0) * (dz1 + 2.0 * dz2 + 2.0 * dz3 + dz4);
}

static void map_step_generic(int system_id, double *x, double *y, double *z,
                             const double *p, int n_params) {
    if (system_id == SYS_LOGISTIC) {
        double r = param_at(p, n_params, 0, 3.9);
        *x = r * (*x) * (1.0 - *x);
        *y = 0.0;
        *z = 0.0;
        return;
    }
    if (system_id == SYS_HENON) {
        double a = param_at(p, n_params, 0, 1.4);
        double b = param_at(p, n_params, 1, 0.3);
        double xn = 1.0 - a * (*x) * (*x) + *y;
        double yn = b * (*x);
        *x = xn;
        *y = yn;
        *z = 0.0;
        return;
    }
    if (system_id == SYS_IKEDA) {
        double u = param_at(p, n_params, 0, 0.918);
        double theta = 0.4 - 6.0 / (1.0 + (*x) * (*x) + (*y) * (*y));
        double xn = 1.0 + u * ((*x) * cos(theta) - (*y) * sin(theta));
        double yn = u * ((*x) * sin(theta) + (*y) * cos(theta));
        *x = xn;
        *y = yn;
        *z = 0.0;
    }
}

static int simulate_final3(int system_id, const double *p, int n_params,
                           double x0, double y0, double z0,
                           double dt, double T, int method,
                           double *xf, double *yf, double *zf) {
    int n = (int)(T / dt) + 1;
    if (n < 2) n = 2;
    double x = x0, y = y0, z = z0;
    if (is_map_system(system_id)) {
        for (int i = 1; i < n; ++i) map_step_generic(system_id, &x, &y, &z, p, n_params);
    } else if (!is_dde_system(system_id) && !is_lorenz96_system(system_id)) {
        for (int i = 1; i < n; ++i) {
            step3_generic(system_id, &x, &y, &z, p, n_params, dt, method);
            if (state_invalid(x, y, z, 1e6)) break;
        }
    } else {
        return -1;
    }
    *xf = x;
    *yf = y;
    *zf = z;
    return 0;
}

CHAOS_API int chaos_simulate_system(
    int system_id,
    const double *params,
    int n_params,
    double x0, double y0, double z0,
    double dt, double T,
    int method,
    double *t_out,
    double *X_out,
    int n
) {
    if (dt <= 0.0 || T <= 0.0 || n < 2 || t_out == NULL || X_out == NULL) return -1;

    double x = x0, y = y0, z = z0;
    double t = 0.0;
    t_out[0] = t;
    X_out[0] = x;
    X_out[1] = y;
    X_out[2] = z;

    if (is_map_system(system_id)) {
        for (int i = 1; i < n; ++i) {
            map_step_generic(system_id, &x, &y, &z, params, n_params);
            t += dt;
            t_out[i] = t;
            X_out[3 * i + 0] = x;
            X_out[3 * i + 1] = y;
            X_out[3 * i + 2] = z;
        }
        return 0;
    }

    if (is_dde_system(system_id)) {
        double beta = param_at(params, n_params, 0, 0.2);
        double gamma = param_at(params, n_params, 1, 0.1);
        double exponent = param_at(params, n_params, 2, 10.0);
        double tau = param_at(params, n_params, 3, 17.0);
        int delay_steps = (int)round(tau / dt);
        if (delay_steps < 1) delay_steps = 1;
        double *history = (double *)malloc((size_t)(n + delay_steps + 1) * sizeof(double));
        if (history == NULL) return -2;
        for (int i = 0; i < n + delay_steps + 1; ++i) history[i] = x0;
        for (int i = 0; i < n; ++i) {
            double x_tau = history[i];
            double x_now = history[i + delay_steps];
            double dx = beta * x_tau / (1.0 + pow(fabs(x_tau), exponent)) - gamma * x_now;
            history[i + delay_steps + 1] = x_now + dt * dx;
            t_out[i] = i * dt;
            X_out[3 * i + 0] = x_now;
            X_out[3 * i + 1] = x_tau;
            X_out[3 * i + 2] = dx;
        }
        free(history);
        return 0;
    }

    if (is_lorenz96_system(system_id)) {
        double forcing = param_at(params, n_params, 0, 8.0);
        int dim = (int)round(param_at(params, n_params, 1, 8.0));
        if (dim < 4) dim = 4;
        if (dim > 256) dim = 256;
        double *state = (double *)malloc((size_t)dim * sizeof(double));
        double *next = (double *)malloc((size_t)dim * sizeof(double));
        if (state == NULL || next == NULL) {
            free(state);
            free(next);
            return -2;
        }
        for (int j = 0; j < dim; ++j) state[j] = forcing;
        state[0] = x0;
        state[1] = y0;
        state[2] = z0;
        for (int i = 1; i < n; ++i) {
            for (int j = 0; j < dim; ++j) {
                double rhs = (state[(j + 1) % dim] - state[(j - 2 + dim) % dim]) * state[(j - 1 + dim) % dim] - state[j] + forcing;
                next[j] = state[j] + dt * rhs;
            }
            for (int j = 0; j < dim; ++j) state[j] = next[j];
            t += dt;
            t_out[i] = t;
            X_out[3 * i + 0] = state[0];
            X_out[3 * i + 1] = state[1];
            X_out[3 * i + 2] = state[2];
        }
        free(state);
        free(next);
        return 0;
    }

    for (int i = 1; i < n; ++i) {
        step3_generic(system_id, &x, &y, &z, params, n_params, dt, method);
        t += dt;
        t_out[i] = t;
        X_out[3 * i + 0] = x;
        X_out[3 * i + 1] = y;
        X_out[3 * i + 2] = z;
        if (state_invalid(x, y, z, 1e12)) {
            for (int j = i + 1; j < n; ++j) {
                t += dt;
                t_out[j] = t;
                X_out[3 * j + 0] = NAN;
                X_out[3 * j + 1] = NAN;
                X_out[3 * j + 2] = NAN;
            }
            break;
        }
    }
    return 0;
}

CHAOS_API int chaos_bifurcation_generic(
    int system_id,
    const double *params,
    int n_params,
    int param_idx,
    double x0, double y0, double z0,
    double param_min, double param_max,
    int n_param,
    double dt, double T_trans, double T_keep,
    int max_points,
    int continuation,
    int method,
    double *out_param,
    double *out_value,
    int *out_count
) {
    if (params == NULL || n_params < 0 || param_idx < 0 || n_param < 1 || dt <= 0.0 ||
        T_keep <= 0.0 || max_points < 1 || out_param == NULL || out_value == NULL || out_count == NULL) {
        return -1;
    }
    if (param_idx >= n_params) return -1;

    int steps_trans = (int)(T_trans / dt);
    int steps_keep = (int)(T_keep / dt);
    if (steps_keep < 2) steps_keep = 2;
    int denom = (n_param == 1) ? 1 : (n_param - 1);
    int count = 0;

    double seed_x = x0, seed_y = y0, seed_z = z0;
    double *p = (double *)malloc((size_t)n_params * sizeof(double));
    double *fallback = (double *)malloc((size_t)max_points * sizeof(double));
    double *maxima = (double *)malloc((size_t)max_points * sizeof(double));
    if (p == NULL || fallback == NULL || maxima == NULL) {
        free(p);
        free(fallback);
        free(maxima);
        return -2;
    }

    for (int j = 0; j < n_param; ++j) {
        for (int k = 0; k < n_params; ++k) p[k] = params[k];
        double param_value = param_min + (param_max - param_min) * ((double)j) / ((double)denom);
        p[param_idx] = param_value;

        double x = seed_x, y = seed_y, z = seed_z;
        int valid = 1;

        if (is_map_system(system_id)) {
            for (int i = 0; i < steps_trans; ++i) {
                map_step_generic(system_id, &x, &y, &z, p, n_params);
                if (state_invalid(x, y, z, 1e12)) {
                    valid = 0;
                    break;
                }
            }
            int kept = 0;
            for (int i = 0; valid && i < steps_keep; ++i) {
                fallback[kept % max_points] = x;
                kept += 1;
                map_step_generic(system_id, &x, &y, &z, p, n_params);
                if (state_invalid(x, y, z, 1e12)) valid = 0;
            }
            int emit = kept < max_points ? kept : max_points;
            int start = kept < max_points ? 0 : (kept % max_points);
            for (int i = 0; valid && i < emit; ++i) {
                out_param[count] = param_value;
                out_value[count] = fallback[(start + i) % max_points];
                count += 1;
            }
        } else if (!is_dde_system(system_id) && !is_lorenz96_system(system_id)) {
            for (int i = 0; i < steps_trans; ++i) {
                step3_generic(system_id, &x, &y, &z, p, n_params, dt, method);
                if (state_invalid(x, y, z, 1e8)) {
                    valid = 0;
                    break;
                }
            }
            double zm2 = z, zm1 = z;
            int maxima_count = 0;
            int fallback_count = 0;
            for (int i = 0; valid && i < steps_keep; ++i) {
                double xnew = x, ynew = y, znew = z;
                step3_generic(system_id, &xnew, &ynew, &znew, p, n_params, dt, method);
                if (state_invalid(xnew, ynew, znew, 1e8)) {
                    valid = 0;
                    break;
                }
                if (i >= 1 && zm1 > zm2 && zm1 >= znew) {
                    maxima[maxima_count % max_points] = zm1;
                    maxima_count += 1;
                }
                fallback[fallback_count % max_points] = znew;
                fallback_count += 1;
                zm2 = zm1;
                zm1 = znew;
                x = xnew;
                y = ynew;
                z = znew;
            }
            if (valid) {
                double *source = maxima_count > 0 ? maxima : fallback;
                int source_count = maxima_count > 0 ? maxima_count : fallback_count;
                int emit = source_count < max_points ? source_count : max_points;
                int start = source_count < max_points ? 0 : (source_count % max_points);
                for (int i = 0; i < emit; ++i) {
                    out_param[count] = param_value;
                    out_value[count] = source[(start + i) % max_points];
                    count += 1;
                }
            }
        } else {
            double *t_tmp = (double *)malloc((size_t)(steps_trans + steps_keep + 2) * sizeof(double));
            double *x_tmp = (double *)malloc((size_t)(steps_trans + steps_keep + 2) * 3 * sizeof(double));
            if (t_tmp == NULL || x_tmp == NULL) {
                free(t_tmp);
                free(x_tmp);
                free(p);
                free(fallback);
                free(maxima);
                return -2;
            }
            int n_tmp = steps_trans + steps_keep + 1;
            int rc = chaos_simulate_system(system_id, p, n_params, x, y, z, dt, dt * (n_tmp - 1), method, t_tmp, x_tmp, n_tmp);
            if (rc == 0) {
                int kept = 0;
                for (int i = steps_trans; i < n_tmp; ++i) {
                    double value = x_tmp[3 * i + 0];
                    if (isfinite(value)) {
                        fallback[kept % max_points] = value;
                        kept += 1;
                    }
                }
                int emit = kept < max_points ? kept : max_points;
                int start = kept < max_points ? 0 : (kept % max_points);
                for (int i = 0; i < emit; ++i) {
                    out_param[count] = param_value;
                    out_value[count] = fallback[(start + i) % max_points];
                    count += 1;
                }
                x = x_tmp[3 * (n_tmp - 1) + 0];
                y = x_tmp[3 * (n_tmp - 1) + 1];
                z = x_tmp[3 * (n_tmp - 1) + 2];
            }
            free(t_tmp);
            free(x_tmp);
        }

        if (continuation && valid && isfinite(x) && isfinite(y) && isfinite(z)) {
            seed_x = x;
            seed_y = y;
            seed_z = z;
        } else if (continuation && !valid) {
            seed_x = x0;
            seed_y = y0;
            seed_z = z0;
        }
    }

    free(p);
    free(fallback);
    free(maxima);
    *out_count = count;
    return 0;
}

CHAOS_API int chaos_basin_plane_generic(
    int system_id,
    const double *params,
    int n_params,
    const double *eq_points,
    int n_eq,
    double z0_fixed,
    double x_min, double x_max,
    double y_min, double y_max,
    int nx, int ny,
    int row_start, int row_count,
    double dt, double T_total,
    int method,
    uint8_t *basin_out
) {
    if (params == NULL || nx < 2 || ny < 2 || row_start < 0 || row_count < 1 ||
        row_start + row_count > ny || dt <= 0.0 || T_total <= 0.0 || basin_out == NULL) {
        return -1;
    }
    if (is_map_system(system_id) || is_dde_system(system_id) || is_lorenz96_system(system_id)) return -1;

    int denom_x = nx - 1;
    int denom_y = ny - 1;
    int steps_total = (int)(T_total / dt);
    if (steps_total < 2) steps_total = 2;
    int tail_start = steps_total / 2;
    uint8_t periodic_class = (uint8_t)((n_eq >= 0 && n_eq < 240) ? (2 + n_eq) : 250);

    for (int local_y = 0; local_y < row_count; ++local_y) {
        int iy = row_start + local_y;
        double y0 = y_min + (y_max - y_min) * ((double)iy) / ((double)denom_y);
        for (int ix = 0; ix < nx; ++ix) {
            double x0 = x_min + (x_max - x_min) * ((double)ix) / ((double)denom_x);
            double x = x0, y = y0, z = z0_fixed;
            uint8_t basin_class = 1;

            int crossing_count = 0;
            int cluster_count = 0;
            double clusters[16];
            double z_cross_min = HUGE_VAL;
            double z_cross_max = -HUGE_VAL;
            double x_tail_min = HUGE_VAL, y_tail_min = HUGE_VAL, z_tail_min = HUGE_VAL;
            double x_tail_max = -HUGE_VAL, y_tail_max = -HUGE_VAL, z_tail_max = -HUGE_VAL;

            for (int k = 0; k < steps_total; ++k) {
                double x_prev = x;
                double z_prev = z;
                step3_generic(system_id, &x, &y, &z, params, n_params, dt, method);
                if (state_invalid(x, y, z, 1e4)) {
                    basin_class = 0;
                    break;
                }

                if (k >= tail_start) {
                    if (x < x_tail_min) x_tail_min = x;
                    if (x > x_tail_max) x_tail_max = x;
                    if (y < y_tail_min) y_tail_min = y;
                    if (y > y_tail_max) y_tail_max = y;
                    if (z < z_tail_min) z_tail_min = z;
                    if (z > z_tail_max) z_tail_max = z;

                    if (x_prev > 0.0 && x <= 0.0) {
                        double denom_cross = x_prev - x;
                        double alpha = 0.0;
                        if (fabs(denom_cross) > 1e-15) alpha = x_prev / denom_cross;
                        if (alpha < 0.0) alpha = 0.0;
                        if (alpha > 1.0) alpha = 1.0;

                        double z_cross = z_prev + alpha * (z - z_prev);
                        double tol = 0.05 + 0.01 * fabs(z_cross);
                        int matched = 0;
                        if (z_cross < z_cross_min) z_cross_min = z_cross;
                        if (z_cross > z_cross_max) z_cross_max = z_cross;
                        crossing_count += 1;

                        for (int c = 0; c < cluster_count && c < 16; ++c) {
                            if (fabs(z_cross - clusters[c]) <= tol) {
                                clusters[c] = 0.85 * clusters[c] + 0.15 * z_cross;
                                matched = 1;
                                break;
                            }
                        }
                        if (!matched) {
                            if (cluster_count < 16) {
                                clusters[cluster_count] = z_cross;
                            }
                            cluster_count += 1;
                        }
                    }
                }
            }

            if (basin_class == 1 && n_eq > 0 && eq_points != NULL) {
                double best = HUGE_VAL;
                int best_idx = 0;
                for (int k = 0; k < n_eq; ++k) {
                    double ex = eq_points[3 * k + 0];
                    double ey = eq_points[3 * k + 1];
                    double ez = eq_points[3 * k + 2];
                    double d = (x - ex) * (x - ex) + (y - ey) * (y - ey) + (z - ez) * (z - ez);
                    if (d < best) {
                        best = d;
                        best_idx = k;
                    }
                }
                double ex = eq_points[3 * best_idx + 0];
                double ey = eq_points[3 * best_idx + 1];
                double ez = eq_points[3 * best_idx + 2];
                double eq_norm = sqrt(ex * ex + ey * ey + ez * ez);
                double conv_radius = fmax(0.75, 0.03 * fmax(1.0, eq_norm));
                if (best <= conv_radius * conv_radius) {
                    basin_class = (uint8_t)(2 + best_idx);
                }
            }

            if (basin_class == 1) {
                basin_class = classify_residual_dynamics(
                    crossing_count, cluster_count, z_cross_min, z_cross_max,
                    x_tail_min, x_tail_max, y_tail_min, y_tail_max, z_tail_min, z_tail_max,
                    periodic_class
                );
            }
            basin_out[local_y * nx + ix] = basin_class;
        }
    }
    return 0;
}
