#include <math.h>
#include <float.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#if defined(_WIN32) || defined(__CYGWIN__)
  #define CHAOS_API __declspec(dllexport)
#else
  #define CHAOS_API __attribute__((visibility("default")))
#endif

#define CHAOS_CORE_ABI_VERSION 2

CHAOS_API int chaos_core_abi_version(void) {
    return CHAOS_CORE_ABI_VERSION;
}

typedef enum {
    CHAOS_METHOD_EULER = 0,
    CHAOS_METHOD_HEUN = 1,
    CHAOS_METHOD_RK4 = 2
} ChaosMethod;

static int valid_method(int method) {
    return method >= CHAOS_METHOD_EULER && method <= CHAOS_METHOD_RK4;
}

static int fixed_step_count(double duration, double dt, int allow_zero, int *steps_out) {
    if (steps_out == NULL || !isfinite(duration) || !isfinite(dt) || dt <= 0.0) return -1;
    if (duration < 0.0 || (!allow_zero && duration == 0.0)) return -1;
    double ratio = duration / dt;
    if (!isfinite(ratio) || ratio > (double)(INT_MAX - 2)) return -1;
    double nearest = nearbyint(ratio);
    double reconstructed = nearest * dt;
    double scale = fmax(fabs(duration), fmax(fabs(reconstructed), fabs(dt)));
    double duration_ulp = fabs(nextafter(duration, INFINITY) - duration);
    double reconstructed_ulp = fabs(nextafter(reconstructed, INFINITY) - reconstructed);
    double tolerance = fmax(
        64.0 * DBL_EPSILON * scale,
        fmax(8.0 * duration_ulp, 8.0 * reconstructed_ulp)
    );
    if (fabs(reconstructed - duration) > tolerance || nearest < 0.0) return -1;
    if (!allow_zero && nearest < 1.0) return -1;
    *steps_out = (int)nearest;
    return 0;
}

static int bounded_integer(double value, int minimum, int maximum, int *result) {
    if (result == NULL || !isfinite(value)) return -1;
    double nearest = nearbyint(value);
    double scale = fmax(1.0, fabs(value));
    double tolerance = fmax(
        64.0 * DBL_EPSILON * scale,
        8.0 * fabs(nextafter(value, INFINITY) - value)
    );
    if (fabs(value - nearest) > tolerance || nearest < (double)minimum ||
        nearest > (double)maximum) return -1;
    *result = (int)nearest;
    return 0;
}

static int checked_mul_size(size_t left, size_t right, size_t *result) {
    if (result == NULL || (right != 0 && left > SIZE_MAX / right)) return -1;
    *result = left * right;
    return 0;
}

static int checked_add_size(size_t left, size_t right, size_t *result) {
    if (result == NULL || left > SIZE_MAX - right) return -1;
    *result = left + right;
    return 0;
}

static int finite_array(const double *values, int count) {
    if (count < 0 || (count > 0 && values == NULL)) return 0;
    for (int index = 0; index < count; ++index) {
        if (!isfinite(values[index])) return 0;
    }
    return 1;
}

static double convex_interpolate(double left, double right, int numerator, int denominator) {
    if (denominator <= 0 || numerator <= 0) return left;
    if (numerator >= denominator) return right;
    double alpha = (double)numerator / (double)denominator;
    if (signbit(left) == signbit(right)) {
        return left + (right - left) * alpha;
    }
    return (1.0 - alpha) * left + alpha * right;
}

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

    if (method == CHAOS_METHOD_EULER) {
        lorenz_rhs(*x, *y, *z, sigma, rho, beta, &dx1, &dy1, &dz1);
        *x += dt * dx1;
        *y += dt * dy1;
        *z += dt * dz1;
        return;
    }

    if (method == CHAOS_METHOD_HEUN) {
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
    int steps = 0;
    if (fixed_step_count(T, dt, 0, &steps) != 0 || n != steps + 1 ||
        !valid_method(method) ||
        !isfinite(x0) || !isfinite(y0) || !isfinite(z0) ||
        !isfinite(sigma) || !isfinite(rho) || !isfinite(beta) ||
        t_out == NULL || X_out == NULL) {
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
        size_t offset = (size_t)3 * (size_t)i;
        X_out[offset + 0U] = x;
        X_out[offset + 1U] = y;
        X_out[offset + 2U] = z;
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
    int steps_trans = 0;
    int steps_keep = 0;
    if (n_rho < 1 || max_crossings_per_rho < 1 ||
        n_rho > INT_MAX / max_crossings_per_rho ||
        fixed_step_count(T_trans, dt, 1, &steps_trans) != 0 ||
        fixed_step_count(T_keep, dt, 0, &steps_keep) != 0 ||
        !valid_method(method) ||
        !isfinite(x0) || !isfinite(y0) || !isfinite(z0) ||
        !isfinite(sigma) || !isfinite(beta) ||
        !isfinite(rho_min) || !isfinite(rho_max) || rho_min > rho_max ||
        (continuation != 0 && continuation != 1) ||
        out_rho == NULL || out_z == NULL || out_count == NULL) {
        return -1;
    }

    int count = 0;
    int denom = (n_rho == 1) ? 1 : (n_rho - 1);

    double x_seed = x0, y_seed = y0, z_seed = z0;

    for (int j = 0; j < n_rho; ++j) {
        double rho = convex_interpolate(rho_min, rho_max, j, denom);
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
    int steps_total = 0;
    size_t basin_count = 0;
    if (nx < 2 || ny < 2 ||
        checked_mul_size((size_t)nx, (size_t)ny, &basin_count) != 0 ||
        fixed_step_count(T_total, dt, 0, &steps_total) != 0 ||
        !isfinite(sigma) || !isfinite(rho) || !isfinite(beta) ||
        !isfinite(z0_fixed) || !isfinite(x_min) || !isfinite(x_max) ||
        !isfinite(y_min) || !isfinite(y_max) || x_min >= x_max || y_min >= y_max ||
        !isfinite(hit_radius) || hit_radius <= 0.0 ||
        !isfinite(esc_radius) || esc_radius <= 0.0 ||
        !valid_method(method) || basin_out == NULL) {
        return -1;
    }

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
        double y0 = convex_interpolate(y_min, y_max, iy, denom_y);
        for (int ix = 0; ix < nx; ++ix) {
            double x0 = convex_interpolate(x_min, x_max, ix, denom_x);
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

            basin_out[(size_t)iy * (size_t)nx + (size_t)ix] = basin_class;
        }
    }
    return 0;
}

typedef enum {
    #define CHAOS_SYSTEM(py_key, c_symbol, numeric_id) c_symbol = numeric_id,
    #include "system_ids.def"
    #undef CHAOS_SYSTEM
    SYS_COUNT
} ChaosSystem;

static int valid_system(int system_id) {
    return system_id >= SYS_LORENZ && system_id < SYS_COUNT;
}

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

static void lorenz96_rhs(const double *state, double *derivative, int dimension,
                         double forcing) {
    for (int j = 0; j < dimension; ++j) {
        derivative[j] =
            (state[(j + 1) % dimension] - state[(j - 2 + dimension) % dimension])
            * state[(j - 1 + dimension) % dimension]
            - state[j] + forcing;
    }
}

static void step_lorenz96(double *state, double *next, double *workspace,
                          int dimension, double forcing, double dt, int method) {
    double *k1 = workspace;
    double *k2 = workspace + dimension;
    double *k3 = workspace + 2 * dimension;
    double *k4 = workspace + 3 * dimension;
    double *temporary = workspace + 4 * dimension;
    lorenz96_rhs(state, k1, dimension, forcing);
    if (method == CHAOS_METHOD_EULER) {
        for (int j = 0; j < dimension; ++j) next[j] = state[j] + dt * k1[j];
        return;
    }
    if (method == CHAOS_METHOD_HEUN) {
        for (int j = 0; j < dimension; ++j) temporary[j] = state[j] + dt * k1[j];
        lorenz96_rhs(temporary, k2, dimension, forcing);
        for (int j = 0; j < dimension; ++j) {
            next[j] = state[j] + 0.5 * dt * (k1[j] + k2[j]);
        }
        return;
    }
    for (int j = 0; j < dimension; ++j) temporary[j] = state[j] + 0.5 * dt * k1[j];
    lorenz96_rhs(temporary, k2, dimension, forcing);
    for (int j = 0; j < dimension; ++j) temporary[j] = state[j] + 0.5 * dt * k2[j];
    lorenz96_rhs(temporary, k3, dimension, forcing);
    for (int j = 0; j < dimension; ++j) temporary[j] = state[j] + dt * k3[j];
    lorenz96_rhs(temporary, k4, dimension, forcing);
    for (int j = 0; j < dimension; ++j) {
        next[j] = state[j] + (dt / 6.0) * (
            k1[j] + 2.0 * k2[j] + 2.0 * k3[j] + k4[j]
        );
    }
}

static int vector_invalid(const double *state, int dimension, double escape_radius) {
    if (state == NULL || dimension < 1) return 1;
    for (int index = 0; index < dimension; ++index) {
        if (!isfinite(state[index]) || fabs(state[index]) > escape_radius) return 1;
    }
    return 0;
}

static int mackey_delay_layout(double tau, double dt, int *delay_ceiling,
                               double *delay_ratio) {
    if (delay_ceiling == NULL || delay_ratio == NULL ||
        !isfinite(tau) || !isfinite(dt) || dt <= 0.0 || tau < dt) return -1;
    double ratio = tau / dt;
    if (!isfinite(ratio) || ratio > (double)(INT_MAX - 2)) return -1;
    double ceiling = ceil(ratio);
    if (!isfinite(ceiling) || ceiling < 1.0 || ceiling > (double)(INT_MAX - 2)) return -1;
    *delay_ceiling = (int)ceiling;
    *delay_ratio = ratio;
    return 0;
}

static double mackey_delayed_value(const double *history, size_t current_index,
                                   double delay_ratio, double stage_fraction,
                                   int cubic, size_t origin_index,
                                   int constant_before_origin) {
    double position = (double)current_index + stage_fraction - delay_ratio;
    if (position < 0.0) position = 0.0;
    if (position > (double)current_index) position = (double)current_index;
    size_t lower = (size_t)floor(position);
    if (lower >= current_index) return history[current_index];
    double fraction = position - (double)lower;
    if (!cubic || current_index < 3U || fraction <= 8.0 * DBL_EPSILON) {
        return (1.0 - fraction) * history[lower] + fraction * history[lower + 1U];
    }

    size_t stencil_min = 0U;
    size_t stencil_max = current_index;
    double relative = position - (double)origin_index;
    double tolerance = 64.0 * DBL_EPSILON * fmax(1.0, fabs(position));
    if (constant_before_origin && relative <= tolerance) return history[origin_index];
    if (relative >= -tolerance) {
        double segment_value = floor(fmax(0.0, relative) / delay_ratio);
        double left_boundary = (double)origin_index + segment_value * delay_ratio;
        double right_boundary = left_boundary + delay_ratio;
        double minimum_value = ceil(left_boundary - tolerance);
        double maximum_value = floor(right_boundary + tolerance);
        if (minimum_value > 0.0) stencil_min = (size_t)minimum_value;
        if (maximum_value < (double)current_index) {
            stencil_max = maximum_value < 0.0 ? 0U : (size_t)maximum_value;
        }
    }

    size_t available = stencil_max >= stencil_min
        ? stencil_max - stencil_min + 1U : 0U;
    size_t degree_count = available < 4U ? available : 4U;
    if (degree_count < 2U) {
        double nearest_value = nearbyint(position);
        if (nearest_value < 0.0) nearest_value = 0.0;
        if (nearest_value > (double)current_index) nearest_value = (double)current_index;
        return history[(size_t)nearest_value];
    }
    size_t start = lower > 0U ? lower - 1U : 0U;
    if (start < stencil_min) start = stencil_min;
    size_t latest_start = stencil_max - degree_count + 1U;
    if (start > latest_start) start = latest_start;
    double result = 0.0;
    for (size_t node_offset = 0U; node_offset < degree_count; ++node_offset) {
        size_t node = start + node_offset;
        double weight = 1.0;
        for (size_t other_offset = 0U; other_offset < degree_count; ++other_offset) {
            if (other_offset != node_offset) {
                size_t other = start + other_offset;
                weight *= (position - (double)other) / ((double)node - (double)other);
            }
        }
        result += weight * history[node];
    }
    return result;
}

static double mackey_rhs(double current, double delayed, double beta,
                         double gamma, double exponent) {
    double power = pow(fabs(delayed), exponent);
    double feedback = isinf(power) ? 0.0 : beta * delayed / (1.0 + power);
    return feedback - gamma * current;
}

static double step_mackey(const double *history, size_t current_index,
                          double delay_ratio, double beta, double gamma,
                          double exponent, double dt, int method,
                          size_t origin_index, int constant_before_origin) {
    double current = history[current_index];
    int cubic = method == CHAOS_METHOD_RK4;
    double delayed_1 = mackey_delayed_value(
        history, current_index, delay_ratio, 0.0, cubic,
        origin_index, constant_before_origin
    );
    double k1 = mackey_rhs(current, delayed_1, beta, gamma, exponent);
    if (method == CHAOS_METHOD_EULER) return current + dt * k1;
    if (method == CHAOS_METHOD_HEUN) {
        double delayed_2 = mackey_delayed_value(
            history, current_index, delay_ratio, 1.0, 0,
            origin_index, constant_before_origin
        );
        double k2 = mackey_rhs(current + dt * k1, delayed_2, beta, gamma, exponent);
        return current + 0.5 * dt * (k1 + k2);
    }
    double delayed_half = mackey_delayed_value(
        history, current_index, delay_ratio, 0.5, 1,
        origin_index, constant_before_origin
    );
    double k2 = mackey_rhs(current + 0.5 * dt * k1, delayed_half, beta, gamma, exponent);
    double k3 = mackey_rhs(current + 0.5 * dt * k2, delayed_half, beta, gamma, exponent);
    double delayed_4 = mackey_delayed_value(
        history, current_index, delay_ratio, 1.0, 1,
        origin_index, constant_before_origin
    );
    double k4 = mackey_rhs(current + dt * k3, delayed_4, beta, gamma, exponent);
    return current + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4);
}

static double mackey_observed(const double *history, size_t current_index,
                              double delay_ratio, double beta, double gamma,
                              double exponent, int observed_var_idx, int method,
                              size_t origin_index, int constant_before_origin) {
    double current = history[current_index];
    double delayed = mackey_delayed_value(
        history, current_index, delay_ratio, 0.0,
        method == CHAOS_METHOD_RK4, origin_index, constant_before_origin
    );
    if (observed_var_idx == 0) return current;
    if (observed_var_idx == 1) return delayed;
    return mackey_rhs(current, delayed, beta, gamma, exponent);
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
    if (system_id == SYS_WANG_CHEN_NO_EQUILIBRIUM) {
        double a = param_at(p, n_params, 0, 0.218);
        *dx = y;
        *dy = z;
        *dz = -y + 3.0 * y * y - x * x - x * z + a;
        return;
    }
    if (system_id == SYS_NAZARIMEHR_LINE_EQUILIBRIUM) {
        double k = param_at(p, n_params, 0, -0.2);
        *dx = y;
        *dy = 0.4 * x * z;
        *dz = 0.3 * y - 0.1 * z - 1.4 * y * y + k * x * y;
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
    if (system_id == SYS_UNIFIED_LORENZ_CHEN) {
        double alpha = param_at(p, n_params, 0, 0.0);
        *dx = (25.0 * alpha + 10.0) * (y - x);
        *dy = (28.0 - 35.0 * alpha) * x + (29.0 * alpha - 1.0) * y - x * z;
        *dz = -((alpha + 8.0) / 3.0) * z + x * y;
        return;
    }
    if (system_id == SYS_SPROTT_B) {
        *dx = y * z;
        *dy = x - y;
        *dz = 1.0 - x * y;
        return;
    }
    if (system_id == SYS_SPROTT_C) {
        *dx = y * z;
        *dy = x - y;
        *dz = 1.0 - x * x;
        return;
    }
    if (system_id == SYS_SPROTT_D) {
        *dx = -y;
        *dy = x + z;
        *dz = x * z + 3.0 * y * y;
        return;
    }
    if (system_id == SYS_SPROTT_E) {
        *dx = y * z;
        *dy = x * x - y;
        *dz = 1.0 - 4.0 * x;
        return;
    }
    if (system_id == SYS_SPROTT_F) {
        *dx = y + z;
        *dy = -x + 0.5 * y;
        *dz = x * x - z;
        return;
    }
    if (system_id == SYS_SPROTT_G) {
        *dx = 0.4 * x + z;
        *dy = x * z - y;
        *dz = -x + y;
        return;
    }
    if (system_id == SYS_SPROTT_H) {
        *dx = -y + z * z;
        *dy = x + 0.5 * y;
        *dz = x - z;
        return;
    }
    if (system_id == SYS_SPROTT_I) {
        *dx = 0.2 * y;
        *dy = x + z;
        *dz = x + y * y - z;
        return;
    }
    if (system_id == SYS_SPROTT_J) {
        *dx = 2.0 * z;
        *dy = -2.0 * y + z;
        *dz = -x + y + y * y;
        return;
    }
    if (system_id == SYS_SPROTT_K) {
        *dx = x * y - z;
        *dy = x - y;
        *dz = x + 0.3 * z;
        return;
    }
    if (system_id == SYS_SPROTT_L) {
        *dx = y + 3.9 * z;
        *dy = 0.9 * x * x - y;
        *dz = 1.0 - x;
        return;
    }
    if (system_id == SYS_SPROTT_M) {
        *dx = -z;
        *dy = -x * x - y;
        *dz = 1.7 + 1.7 * x + y;
        return;
    }
    if (system_id == SYS_SPROTT_N) {
        *dx = -2.0 * y;
        *dy = x + z * z;
        *dz = 1.0 + y - 2.0 * z;
        return;
    }
    if (system_id == SYS_SPROTT_O) {
        *dx = y;
        *dy = x - z;
        *dz = x + x * z + 2.7 * y;
        return;
    }
    if (system_id == SYS_SPROTT_P) {
        *dx = 2.7 * y + z;
        *dy = -x + y * y;
        *dz = x + y;
        return;
    }
    if (system_id == SYS_SPROTT_Q) {
        *dx = -z;
        *dy = x - y;
        *dz = 3.1 * x + y * y + 0.5 * z;
        return;
    }
    if (system_id == SYS_SPROTT_R) {
        *dx = 0.9 - y;
        *dy = 0.4 + z;
        *dz = x * y - z;
        return;
    }
    if (system_id == SYS_SPROTT_S) {
        *dx = x - 4.0 * y;
        *dy = x + z * z;
        *dz = 1.0 + x;
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
    if (method == CHAOS_METHOD_EULER) {
        rhs3_generic(system_id, *x, *y, *z, p, n_params, &dx1, &dy1, &dz1);
        *x += dt * dx1;
        *y += dt * dy1;
        *z += dt * dz1;
        return;
    }
    if (method == CHAOS_METHOD_HEUN) {
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
    int steps = 0;
    if (!valid_system(system_id) || !valid_method(method) || n_params < 0 ||
        (n_params > 0 && params == NULL) ||
        !finite_array(params, n_params) ||
        !isfinite(x0) || !isfinite(y0) || !isfinite(z0) ||
        fixed_step_count(T, dt, 0, &steps) != 0 || n != steps + 1 ||
        t_out == NULL || X_out == NULL) return -1;

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
            size_t offset = (size_t)3 * (size_t)i;
            X_out[offset + 0U] = x;
            X_out[offset + 1U] = y;
            X_out[offset + 2U] = z;
        }
        return 0;
    }

    if (is_dde_system(system_id)) {
        double beta = param_at(params, n_params, 0, 0.2);
        double gamma = param_at(params, n_params, 1, 0.1);
        double exponent = param_at(params, n_params, 2, 10.0);
        double tau = param_at(params, n_params, 3, 17.0);
        int delay_ceiling = 0;
        double delay_ratio = 0.0;
        if (exponent <= 0.0 ||
            mackey_delay_layout(tau, dt, &delay_ceiling, &delay_ratio) != 0 ||
            delay_ceiling > INT_MAX - n - 2) return -1;
        size_t prefix_count = (size_t)delay_ceiling + 3U;
        size_t history_count = 0;
        size_t history_bytes = 0;
        if (checked_add_size(prefix_count, (size_t)n - 1U, &history_count) != 0 ||
            checked_mul_size(history_count, sizeof(double), &history_bytes) != 0) return -2;
        double *history = (double *)malloc(history_bytes);
        if (history == NULL) return -2;
        for (size_t i = 0; i < history_count; ++i) history[i] = x0;
        size_t origin_index = prefix_count - 1U;
        for (int i = 0; i < n; ++i) {
            size_t current_index = origin_index + (size_t)i;
            double x_now = history[current_index];
            double x_tau = mackey_delayed_value(
                history, current_index, delay_ratio, 0.0,
                method == CHAOS_METHOD_RK4, origin_index, 1
            );
            double dx = mackey_rhs(x_now, x_tau, beta, gamma, exponent);
            t_out[i] = i * dt;
            size_t offset = (size_t)3 * (size_t)i;
            X_out[offset + 0U] = x_now;
            X_out[offset + 1U] = x_tau;
            X_out[offset + 2U] = dx;
            if (i + 1 < n) {
                double next_value = step_mackey(
                    history, current_index, delay_ratio,
                    beta, gamma, exponent, dt, method, origin_index, 1
                );
                if (!isfinite(next_value)) {
                    free(history);
                    return -3;
                }
                history[current_index + 1U] = next_value;
            }
        }
        free(history);
        return 0;
    }

    if (is_lorenz96_system(system_id)) {
        double forcing = param_at(params, n_params, 0, 8.0);
        double dimension_value = param_at(params, n_params, 1, 8.0);
        int dim = 0;
        if (!isfinite(forcing) ||
            bounded_integer(dimension_value, 4, 256, &dim) != 0) return -1;
        size_t state_bytes = 0;
        size_t workspace_count = 0;
        size_t workspace_bytes = 0;
        if (checked_mul_size((size_t)dim, sizeof(double), &state_bytes) != 0 ||
            checked_mul_size((size_t)dim, 5U, &workspace_count) != 0 ||
            checked_mul_size(workspace_count, sizeof(double), &workspace_bytes) != 0) return -2;
        double *state = (double *)malloc(state_bytes);
        double *next = (double *)malloc(state_bytes);
        double *workspace = (double *)malloc(workspace_bytes);
        if (state == NULL || next == NULL || workspace == NULL) {
            free(state);
            free(next);
            free(workspace);
            return -2;
        }
        for (int j = 0; j < dim; ++j) state[j] = forcing;
        state[0] = x0;
        state[1] = y0;
        state[2] = z0;
        for (int i = 1; i < n; ++i) {
            step_lorenz96(state, next, workspace, dim, forcing, dt, method);
            for (int j = 0; j < dim; ++j) state[j] = next[j];
            t += dt;
            t_out[i] = t;
            size_t offset = (size_t)3 * (size_t)i;
            X_out[offset + 0U] = state[0];
            X_out[offset + 1U] = state[1];
            X_out[offset + 2U] = state[2];
        }
        free(state);
        free(next);
        free(workspace);
        return 0;
    }

    for (int i = 1; i < n; ++i) {
        step3_generic(system_id, &x, &y, &z, params, n_params, dt, method);
        t += dt;
        t_out[i] = t;
        size_t offset = (size_t)3 * (size_t)i;
        X_out[offset + 0U] = x;
        X_out[offset + 1U] = y;
        X_out[offset + 2U] = z;
        if (state_invalid(x, y, z, 1e12)) {
            for (int j = i + 1; j < n; ++j) {
                t += dt;
                t_out[j] = t;
                size_t tail_offset = (size_t)3 * (size_t)j;
                X_out[tail_offset + 0U] = NAN;
                X_out[tail_offset + 1U] = NAN;
                X_out[tail_offset + 2U] = NAN;
            }
            break;
        }
    }
    return 0;
}

static void emit_bifurcation_ring(
    double parameter,
    const double *maxima, int maxima_count,
    const double *fallback, int fallback_count,
    int max_points,
    double *out_param, double *out_value, int *count
) {
    const double *source = maxima_count > 0 ? maxima : fallback;
    int source_count = maxima_count > 0 ? maxima_count : fallback_count;
    int emit = source_count < max_points ? source_count : max_points;
    int start = source_count < max_points ? 0 : (source_count % max_points);
    for (int index = 0; index < emit; ++index) {
        out_param[*count] = parameter;
        out_value[*count] = source[(start + index) % max_points];
        *count += 1;
    }
}

static int bifurcation_mackey_glass(
    const double *params, int n_params, int param_idx, int observed_var_idx,
    double x0, double param_min, double param_max, int n_param,
    double dt, int steps_trans, int steps_keep, int max_points,
    int continuation, int method,
    double *out_param, double *out_value, int *out_count
) {
    if (n_params < 4 || param_idx >= n_params || steps_trans > INT_MAX - steps_keep) {
        return -1;
    }
    double exponent_min = param_idx == 2 ? param_min : params[2];
    double tau_min = param_idx == 3 ? param_min : params[3];
    double tau_max = param_idx == 3 ? param_max : params[3];
    if (exponent_min <= 0.0) return -1;
    int delay_ceiling = 0;
    int minimum_delay_ceiling = 0;
    double maximum_delay_ratio = 0.0;
    double minimum_delay_ratio = 0.0;
    if (mackey_delay_layout(tau_min, dt, &minimum_delay_ceiling,
                            &minimum_delay_ratio) != 0 ||
        mackey_delay_layout(tau_max, dt, &delay_ceiling,
                            &maximum_delay_ratio) != 0) return -1;
    (void)minimum_delay_ceiling;
    (void)minimum_delay_ratio;
    (void)maximum_delay_ratio;

    int steps_total = steps_trans + steps_keep;
    if (steps_total > INT_MAX - 3 ||
        delay_ceiling > INT_MAX - steps_total - 3) return -1;
    size_t prefix_count = (size_t)delay_ceiling + 3U;
    size_t history_count = 0;
    size_t params_bytes = 0;
    size_t prefix_bytes = 0;
    size_t history_bytes = 0;
    size_t points_bytes = 0;
    if (checked_add_size(prefix_count, (size_t)steps_total, &history_count) != 0 ||
        checked_mul_size((size_t)n_params, sizeof(double), &params_bytes) != 0 ||
        checked_mul_size(prefix_count, sizeof(double), &prefix_bytes) != 0 ||
        checked_mul_size(history_count, sizeof(double), &history_bytes) != 0 ||
        checked_mul_size((size_t)max_points, sizeof(double), &points_bytes) != 0) {
        return -2;
    }
    double *p = (double *)malloc(params_bytes);
    double *seed_history = (double *)malloc(prefix_bytes);
    double *history = (double *)malloc(history_bytes);
    double *fallback = (double *)malloc(points_bytes);
    double *maxima = (double *)malloc(points_bytes);
    if (p == NULL || seed_history == NULL || history == NULL ||
        fallback == NULL || maxima == NULL) {
        free(p); free(seed_history); free(history); free(fallback); free(maxima);
        return -2;
    }
    for (size_t index = 0; index < prefix_count; ++index) seed_history[index] = x0;

    int count = 0;
    int seed_is_constant = 1;
    int denominator = n_param == 1 ? 1 : n_param - 1;
    for (int parameter_index = 0; parameter_index < n_param; ++parameter_index) {
        for (int index = 0; index < n_params; ++index) p[index] = params[index];
        double parameter = convex_interpolate(
            param_min, param_max, parameter_index, denominator
        );
        p[param_idx] = parameter;
        double beta = p[0];
        double gamma = p[1];
        double exponent = p[2];
        double tau = p[3];
        int actual_delay_ceiling = 0;
        double delay_ratio = 0.0;
        if (exponent <= 0.0 ||
            mackey_delay_layout(tau, dt, &actual_delay_ceiling, &delay_ratio) != 0 ||
            actual_delay_ceiling > delay_ceiling) {
            free(p); free(seed_history); free(history); free(fallback); free(maxima);
            return -1;
        }
        for (size_t index = 0; index < prefix_count; ++index) {
            history[index] = continuation ? seed_history[index] : x0;
        }
        size_t current_index = prefix_count - 1U;
        size_t origin_index = current_index;
        int constant_before_origin = !continuation || seed_is_constant;
        int valid = 1;
        for (int step = 0; step < steps_trans; ++step) {
            double next_value = step_mackey(
                history, current_index, delay_ratio,
                beta, gamma, exponent, dt, method,
                origin_index, constant_before_origin
            );
            if (!isfinite(next_value) || fabs(next_value) > 1e8) {
                valid = 0;
                break;
            }
            current_index += 1U;
            history[current_index] = next_value;
        }

        int maxima_count = 0;
        int fallback_count = 0;
        if (valid) {
            double previous_previous = mackey_observed(
                history, current_index, delay_ratio,
                beta, gamma, exponent, observed_var_idx, method,
                origin_index, constant_before_origin
            );
            double previous = previous_previous;
            for (int step = 0; step < steps_keep; ++step) {
                double next_value = step_mackey(
                    history, current_index, delay_ratio,
                    beta, gamma, exponent, dt, method,
                    origin_index, constant_before_origin
                );
                if (!isfinite(next_value) || fabs(next_value) > 1e8) {
                    valid = 0;
                    break;
                }
                current_index += 1U;
                history[current_index] = next_value;
                double value = mackey_observed(
                    history, current_index, delay_ratio,
                    beta, gamma, exponent, observed_var_idx, method,
                    origin_index, constant_before_origin
                );
                if (!isfinite(value)) {
                    valid = 0;
                    break;
                }
                if (step >= 1 && previous > previous_previous && previous >= value) {
                    maxima[maxima_count % max_points] = previous;
                    maxima_count += 1;
                }
                fallback[fallback_count % max_points] = value;
                fallback_count += 1;
                previous_previous = previous;
                previous = value;
            }
        }
        if (valid) {
            emit_bifurcation_ring(
                parameter, maxima, maxima_count, fallback, fallback_count,
                max_points, out_param, out_value, &count
            );
            if (continuation) {
                size_t start = current_index - prefix_count + 1U;
                for (size_t index = 0; index < prefix_count; ++index) {
                    seed_history[index] = history[start + index];
                }
                seed_is_constant = 0;
            }
        } else if (continuation) {
            for (size_t index = 0; index < prefix_count; ++index) seed_history[index] = x0;
            seed_is_constant = 1;
        }
    }

    free(p); free(seed_history); free(history); free(fallback); free(maxima);
    *out_count = count;
    return 0;
}

static int bifurcation_lorenz96(
    const double *params, int n_params, int param_idx, int observed_var_idx,
    double x0, double y0, double z0,
    double param_min, double param_max, int n_param,
    double dt, int steps_trans, int steps_keep, int max_points,
    int continuation, int method,
    double *out_param, double *out_value, int *out_count
) {
    if (n_params < 2 || param_idx >= n_params || steps_trans > INT_MAX - steps_keep ||
        (param_idx == 1 && (n_param != 1 || param_min != param_max))) return -1;
    double dimension_value = param_idx == 1 ? param_min : params[1];
    int dimension = 0;
    if (bounded_integer(dimension_value, 4, 256, &dimension) != 0) return -1;

    size_t params_bytes = 0;
    size_t state_bytes = 0;
    size_t workspace_count = 0;
    size_t workspace_bytes = 0;
    size_t points_bytes = 0;
    if (checked_mul_size((size_t)n_params, sizeof(double), &params_bytes) != 0 ||
        checked_mul_size((size_t)dimension, sizeof(double), &state_bytes) != 0 ||
        checked_mul_size((size_t)dimension, 5U, &workspace_count) != 0 ||
        checked_mul_size(workspace_count, sizeof(double), &workspace_bytes) != 0 ||
        checked_mul_size((size_t)max_points, sizeof(double), &points_bytes) != 0) return -2;
    double *p = (double *)malloc(params_bytes);
    double *state = (double *)malloc(state_bytes);
    double *next = (double *)malloc(state_bytes);
    double *seed_state = (double *)malloc(state_bytes);
    double *workspace = (double *)malloc(workspace_bytes);
    double *fallback = (double *)malloc(points_bytes);
    double *maxima = (double *)malloc(points_bytes);
    if (p == NULL || state == NULL || next == NULL || seed_state == NULL ||
        workspace == NULL || fallback == NULL || maxima == NULL) {
        free(p); free(state); free(next); free(seed_state); free(workspace);
        free(fallback); free(maxima);
        return -2;
    }

    int count = 0;
    int have_seed = 0;
    int denominator = n_param == 1 ? 1 : n_param - 1;
    for (int parameter_index = 0; parameter_index < n_param; ++parameter_index) {
        for (int index = 0; index < n_params; ++index) p[index] = params[index];
        double parameter = convex_interpolate(
            param_min, param_max, parameter_index, denominator
        );
        p[param_idx] = parameter;
        int actual_dimension = 0;
        if (bounded_integer(p[1], 4, 256, &actual_dimension) != 0 ||
            actual_dimension != dimension || !isfinite(p[0])) {
            free(p); free(state); free(next); free(seed_state); free(workspace);
            free(fallback); free(maxima);
            return -1;
        }
        if (continuation && have_seed) {
            for (int index = 0; index < dimension; ++index) state[index] = seed_state[index];
        } else {
            for (int index = 0; index < dimension; ++index) state[index] = p[0];
            state[0] = x0;
            state[1] = y0;
            state[2] = z0;
        }
        int valid = 1;
        for (int step = 0; step < steps_trans; ++step) {
            step_lorenz96(state, next, workspace, dimension, p[0], dt, method);
            if (vector_invalid(next, dimension, 1e8)) {
                valid = 0;
                break;
            }
            for (int index = 0; index < dimension; ++index) state[index] = next[index];
        }

        int maxima_count = 0;
        int fallback_count = 0;
        if (valid) {
            double previous_previous = state[observed_var_idx];
            double previous = previous_previous;
            for (int step = 0; step < steps_keep; ++step) {
                step_lorenz96(state, next, workspace, dimension, p[0], dt, method);
                if (vector_invalid(next, dimension, 1e8)) {
                    valid = 0;
                    break;
                }
                for (int index = 0; index < dimension; ++index) state[index] = next[index];
                double value = state[observed_var_idx];
                if (step >= 1 && previous > previous_previous && previous >= value) {
                    maxima[maxima_count % max_points] = previous;
                    maxima_count += 1;
                }
                fallback[fallback_count % max_points] = value;
                fallback_count += 1;
                previous_previous = previous;
                previous = value;
            }
        }
        if (valid) {
            emit_bifurcation_ring(
                parameter, maxima, maxima_count, fallback, fallback_count,
                max_points, out_param, out_value, &count
            );
            if (continuation) {
                for (int index = 0; index < dimension; ++index) seed_state[index] = state[index];
                have_seed = 1;
            }
        } else if (continuation) {
            have_seed = 0;
        }
    }

    free(p); free(state); free(next); free(seed_state); free(workspace);
    free(fallback); free(maxima);
    *out_count = count;
    return 0;
}

CHAOS_API int chaos_bifurcation_generic(
    int system_id,
    const double *params,
    int n_params,
    int param_idx,
    int observed_var_idx,
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
    int steps_trans = 0;
    int steps_keep = 0;
    if (!valid_system(system_id) || !valid_method(method) || params == NULL ||
        n_params < 0 || param_idx < 0 || observed_var_idx < 0 ||
        observed_var_idx > 2 || n_param < 1 ||
        fixed_step_count(T_trans, dt, 1, &steps_trans) != 0 ||
        fixed_step_count(T_keep, dt, 0, &steps_keep) != 0 ||
        max_points < 1 || n_param > INT_MAX / max_points ||
        !finite_array(params, n_params) ||
        !isfinite(x0) || !isfinite(y0) || !isfinite(z0) ||
        !isfinite(param_min) || !isfinite(param_max) || param_min > param_max ||
        (continuation != 0 && continuation != 1) ||
        out_param == NULL || out_value == NULL || out_count == NULL) {
        return -1;
    }
    if (param_idx >= n_params) return -1;
    if (is_dde_system(system_id)) {
        return bifurcation_mackey_glass(
            params, n_params, param_idx, observed_var_idx,
            x0, param_min, param_max, n_param,
            dt, steps_trans, steps_keep, max_points,
            continuation, method, out_param, out_value, out_count
        );
    }
    if (is_lorenz96_system(system_id)) {
        return bifurcation_lorenz96(
            params, n_params, param_idx, observed_var_idx,
            x0, y0, z0, param_min, param_max, n_param,
            dt, steps_trans, steps_keep, max_points,
            continuation, method, out_param, out_value, out_count
        );
    }
    int denom = (n_param == 1) ? 1 : (n_param - 1);
    int count = 0;

    double seed_x = x0, seed_y = y0, seed_z = z0;
    size_t params_bytes = 0;
    size_t points_bytes = 0;
    if (checked_mul_size((size_t)n_params, sizeof(double), &params_bytes) != 0 ||
        checked_mul_size((size_t)max_points, sizeof(double), &points_bytes) != 0) return -2;
    double *p = (double *)malloc(params_bytes);
    double *fallback = (double *)malloc(points_bytes);
    double *maxima = (double *)malloc(points_bytes);
    if (p == NULL || fallback == NULL || maxima == NULL) {
        free(p);
        free(fallback);
        free(maxima);
        return -2;
    }

    for (int j = 0; j < n_param; ++j) {
        for (int k = 0; k < n_params; ++k) p[k] = params[k];
        double param_value = convex_interpolate(param_min, param_max, j, denom);
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
                double val = (observed_var_idx == 0) ? x : ((observed_var_idx == 1) ? y : z);
                fallback[kept % max_points] = val;
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
            double initial_val = (observed_var_idx == 0) ? x : ((observed_var_idx == 1) ? y : z);
            double val_m2 = initial_val, val_m1 = initial_val;
            int maxima_count = 0;
            int fallback_count = 0;
            for (int i = 0; valid && i < steps_keep; ++i) {
                double xnew = x, ynew = y, znew = z;
                step3_generic(system_id, &xnew, &ynew, &znew, p, n_params, dt, method);
                if (state_invalid(xnew, ynew, znew, 1e8)) {
                    valid = 0;
                    break;
                }
                double val_new = (observed_var_idx == 0) ? xnew : ((observed_var_idx == 1) ? ynew : znew);
                if (i >= 1 && val_m1 > val_m2 && val_m1 >= val_new) {
                    maxima[maxima_count % max_points] = val_m1;
                    maxima_count += 1;
                }
                fallback[fallback_count % max_points] = val_new;
                fallback_count += 1;
                val_m2 = val_m1;
                val_m1 = val_new;
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
            size_t temporary_count = 0;
            size_t temporary_time_bytes = 0;
            size_t temporary_state_count = 0;
            size_t temporary_state_bytes = 0;
            if (steps_trans > INT_MAX - steps_keep - 2 ||
                checked_add_size((size_t)steps_trans, (size_t)steps_keep + 2U, &temporary_count) != 0 ||
                checked_mul_size(temporary_count, sizeof(double), &temporary_time_bytes) != 0 ||
                checked_mul_size(temporary_count, 3U, &temporary_state_count) != 0 ||
                checked_mul_size(temporary_state_count, sizeof(double), &temporary_state_bytes) != 0) {
                free(p); free(fallback); free(maxima); return -2;
            }
            double *t_tmp = (double *)malloc(temporary_time_bytes);
            double *x_tmp = (double *)malloc(temporary_state_bytes);
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
    int steps_total = 0;
    size_t output_count = 0;
    if (!valid_system(system_id) || !valid_method(method) ||
        n_params < 0 || !finite_array(params, n_params) ||
        n_eq < 0 || n_eq >= 240 || !finite_array(eq_points, 3 * n_eq) ||
        !isfinite(z0_fixed) || !isfinite(x_min) || !isfinite(x_max) ||
        !isfinite(y_min) || !isfinite(y_max) || x_min >= x_max || y_min >= y_max ||
        nx < 2 || ny < 2 || row_start < 0 || row_count < 1 ||
        row_start > ny - row_count ||
        checked_mul_size((size_t)row_count, (size_t)nx, &output_count) != 0 ||
        fixed_step_count(T_total, dt, 0, &steps_total) != 0 || basin_out == NULL) {
        return -1;
    }
    if (is_map_system(system_id) || is_dde_system(system_id) || is_lorenz96_system(system_id)) return -1;

    int denom_x = nx - 1;
    int denom_y = ny - 1;
    int tail_start = steps_total / 2;
    uint8_t periodic_class = (uint8_t)((n_eq >= 0 && n_eq < 240) ? (2 + n_eq) : 250);

    for (int local_y = 0; local_y < row_count; ++local_y) {
        int iy = row_start + local_y;
        double y0 = convex_interpolate(y_min, y_max, iy, denom_y);
        for (int ix = 0; ix < nx; ++ix) {
            double x0 = convex_interpolate(x_min, x_max, ix, denom_x);
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
                double y_prev = y;
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

                    int wang_chen_crossing =
                        system_id == SYS_WANG_CHEN_NO_EQUILIBRIUM &&
                        y_prev > 0.0 && y <= 0.0;
                    int generic_crossing =
                        system_id != SYS_WANG_CHEN_NO_EQUILIBRIUM &&
                        x_prev > 0.0 && x <= 0.0;
                    if (wang_chen_crossing || generic_crossing) {
                        double left_value = wang_chen_crossing ? y_prev : x_prev;
                        double right_value = wang_chen_crossing ? y : x;
                        double denom_cross = left_value - right_value;
                        double alpha = 0.0;
                        if (fabs(denom_cross) > 1e-15) {
                            alpha = left_value / denom_cross;
                        }
                        if (alpha < 0.0) alpha = 0.0;
                        if (alpha > 1.0) alpha = 1.0;

                        double z_cross = wang_chen_crossing
                            ? x_prev + alpha * (x - x_prev)
                            : z_prev + alpha * (z - z_prev);
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

            if (basin_class == 1 &&
                system_id == SYS_NAZARIMEHR_LINE_EQUILIBRIUM) {
                /*
                 * E* is the complete x axis, not a finite collection of
                 * points.  Classify convergence by the orthogonal distance
                 * to that invariant line.
                 */
                double line_tail_radius = fmax(
                    fmax(fabs(y_tail_min), fabs(y_tail_max)),
                    fmax(fabs(z_tail_min), fabs(z_tail_max))
                );
                if (isfinite(line_tail_radius) &&
                    line_tail_radius <= 0.05) {
                    basin_class = 2;
                }
            }

            /*
             * The two equilibria of the Wang-Chen reference case a=0.218
             * are repellers.  Passing close to either one at the terminal
             * instant must not be reported as convergence.
             */
            if (basin_class == 1 &&
                system_id != SYS_WANG_CHEN_NO_EQUILIBRIUM &&
                system_id != SYS_NAZARIMEHR_LINE_EQUILIBRIUM &&
                n_eq > 0 && eq_points != NULL) {
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

            if (basin_class == 1 &&
                system_id == SYS_WANG_CHEN_NO_EQUILIBRIUM &&
                crossing_count >= 6 && cluster_count <= 4) {
                /*
                 * For this jerk system, y=0 downward crossings are maxima of
                 * x.  Its published limit cycle alternates between two
                 * maxima separated by more than the generic amplitude
                 * threshold, so the number of return-map clusters is the
                 * relevant discriminator.
                 */
                basin_class = periodic_class;
            }

            if (basin_class == 1 &&
                system_id != SYS_NAZARIMEHR_LINE_EQUILIBRIUM) {
                basin_class = classify_residual_dynamics(
                    crossing_count, cluster_count, z_cross_min, z_cross_max,
                    x_tail_min, x_tail_max, y_tail_min, y_tail_max, z_tail_min, z_tail_max,
                    periodic_class
                );
            }
            basin_out[(size_t)local_y * (size_t)nx + (size_t)ix] = basin_class;
        }
    }
    return 0;
}

static int sprott_monomial_count(int dimension, int order) {
    int n = dimension + order;
    int k = order;
    if (k > n - k) k = n - k;
    int result = 1;
    for (int i = 1; i <= k; ++i) {
        result = (result * (n - k + i)) / i;
    }
    return result;
}

static double pow_int_nonnegative(double x, int power) {
    double out = 1.0;
    for (int i = 0; i < power; ++i) out *= x;
    return out;
}

static void sprott_fill_degree_terms_rec(
    int dimension,
    int position,
    int remaining_degree,
    const double *state,
    int *powers,
    double *terms,
    int *term_index
) {
    if (position == dimension - 1) {
        powers[position] = remaining_degree;
        double value = 1.0;
        for (int j = 0; j < dimension; ++j) {
            value *= pow_int_nonnegative(state[j], powers[j]);
        }
        terms[*term_index] = value;
        *term_index += 1;
        return;
    }

    for (int power = remaining_degree; power >= 0; --power) {
        powers[position] = power;
        sprott_fill_degree_terms_rec(
            dimension,
            position + 1,
            remaining_degree - power,
            state,
            powers,
            terms,
            term_index
        );
    }
}

static int sprott_fill_monomials(int dimension, int order, const double *state, double *terms, int max_terms) {
    int powers[4] = {0, 0, 0, 0};
    int term_index = 0;
    for (int degree = 0; degree <= order; ++degree) {
        sprott_fill_degree_terms_rec(dimension, 0, degree, state, powers, terms, &term_index);
        if (term_index > max_terms) return -1;
    }
    return term_index;
}

static int sprott_eval_polynomial(
    int dimension,
    int order,
    const double *coefficients,
    int n_coefficients,
    const double *state,
    double *out
) {
    double terms[126];
    if (dimension < 1 || dimension > 4 || order < 0 || order > 5 ||
        coefficients == NULL || state == NULL || out == NULL) return -1;
    int monomial_count = sprott_monomial_count(dimension, order);
    int expected = dimension * monomial_count;
    if (n_coefficients != expected) return -1;
    if (monomial_count > 126) return -1;
    if (sprott_fill_monomials(dimension, order, state, terms, monomial_count) != monomial_count) return -1;

    for (int row = 0; row < dimension; ++row) {
        double sum = 0.0;
        for (int col = 0; col < monomial_count; ++col) {
            int coeff_idx = row * monomial_count + col;
            double coeff = coefficients[coeff_idx];
            sum += coeff * terms[col];
        }
        out[row] = sum;
    }
    return 0;
}

static int sprott_state_invalid(const double *state, int dimension, double threshold) {
    double norm2 = 0.0;
    for (int i = 0; i < dimension; ++i) {
        if (!isfinite(state[i])) return 1;
        norm2 += state[i] * state[i];
    }
    return sqrt(norm2) >= threshold;
}

static int sprott_flow_step(
    int dimension,
    int order,
    const double *coefficients,
    int n_coefficients,
    double h,
    int method,
    const double *state,
    double *next
) {
    double k1[4], k2[4], k3[4], k4[4], tmp[4];
    if (method == CHAOS_METHOD_EULER) {
        if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, state, k1) != 0) return -1;
        for (int i = 0; i < dimension; ++i) next[i] = state[i] + h * k1[i];
        return 0;
    }

    if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, state, k1) != 0) return -1;
    if (method == CHAOS_METHOD_HEUN) {
        for (int i = 0; i < dimension; ++i) tmp[i] = state[i] + h * k1[i];
        if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, tmp, k2) != 0) return -1;
        for (int i = 0; i < dimension; ++i) {
            next[i] = state[i] + 0.5 * h * (k1[i] + k2[i]);
        }
        return 0;
    }
    for (int i = 0; i < dimension; ++i) tmp[i] = state[i] + 0.5 * h * k1[i];
    if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, tmp, k2) != 0) return -1;
    for (int i = 0; i < dimension; ++i) tmp[i] = state[i] + 0.5 * h * k2[i];
    if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, tmp, k3) != 0) return -1;
    for (int i = 0; i < dimension; ++i) tmp[i] = state[i] + h * k3[i];
    if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, tmp, k4) != 0) return -1;
    for (int i = 0; i < dimension; ++i) {
        next[i] = state[i] + (h / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
    }
    return 0;
}

CHAOS_API int sprott_simulate_polynomial(
    int kind,
    int dimension,
    int order,
    const double *coefficients,
    int n_coefficients,
    const double *initial,
    int n_steps,
    double h,
    int method,
    double divergence_threshold,
    double *t_out,
    double *x_out,
    int *status_out
) {
    int expected_coefficients = 0;
    if (dimension >= 1 && dimension <= 4 && order >= 2 && order <= 5) {
        expected_coefficients = dimension * sprott_monomial_count(dimension, order);
    }
    if (dimension < 1 || dimension > 4 || order < 2 || order > 5 ||
        coefficients == NULL || initial == NULL || n_steps < 1 ||
        n_steps > INT_MAX - 1 || h <= 0.0 ||
        n_coefficients != expected_coefficients ||
        !finite_array(coefficients, n_coefficients) ||
        !finite_array(initial, dimension) ||
        !isfinite(h) || !isfinite(divergence_threshold) || divergence_threshold <= 0.0 ||
        (kind != 0 && kind != 1) || !valid_method(method) ||
        t_out == NULL || x_out == NULL || status_out == NULL) {
        return -1;
    }

    double state[4] = {0.0, 0.0, 0.0, 0.0};
    double next[4] = {0.0, 0.0, 0.0, 0.0};
    *status_out = 0;
    for (int j = 0; j < dimension; ++j) {
        state[j] = initial[j];
        x_out[j] = state[j];
    }
    t_out[0] = 0.0;

    for (int step = 1; step <= n_steps; ++step) {
        if (kind == 0) {
            if (sprott_eval_polynomial(dimension, order, coefficients, n_coefficients, state, next) != 0) {
                return -2;
            }
        } else if (kind == 1) {
            if (sprott_flow_step(dimension, order, coefficients, n_coefficients, h, method, state, next) != 0) {
                return -2;
            }
        } else {
            return -1;
        }

        t_out[step] = ((double)step) * h;
        for (int j = 0; j < dimension; ++j) {
            state[j] = next[j];
            x_out[(size_t)step * (size_t)dimension + (size_t)j] = state[j];
        }

        if (sprott_state_invalid(state, dimension, divergence_threshold)) {
            *status_out = 1;
            for (int k = step + 1; k <= n_steps; ++k) {
                t_out[k] = ((double)k) * h;
                for (int j = 0; j < dimension; ++j) {
                    x_out[(size_t)k * (size_t)dimension + (size_t)j] = NAN;
                }
            }
            return 0;
        }
    }
    return 0;
}
