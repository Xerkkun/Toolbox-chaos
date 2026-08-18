#include <math.h>
#include <stdint.h>
#include <stdio.h>

int lorenz_simulate(
    double x0, double y0, double z0,
    double sigma, double rho, double beta,
    double dt, double duration, int method,
    double *times, double *states, int sample_count
);
int chaos_simulate_system(
    int system_id, const double *parameters, int parameter_count,
    double x0, double y0, double z0,
    double dt, double duration, int method,
    double *times, double *states, int sample_count
);
int sprott_simulate_polynomial(
    int kind, int dimension, int order,
    const double *coefficients, int coefficient_count,
    const double *initial, int step_count, double step_size, int method,
    double divergence_threshold, double *times, double *states, int *status
);
int chaos_bifurcation_generic(
    int system_id, const double *parameters, int parameter_count,
    int parameter_index, int observed_index,
    double x0, double y0, double z0,
    double parameter_min, double parameter_max, int parameter_samples,
    double dt, double transient, double keep, int max_points,
    int continuation, int method,
    double *out_parameters, double *out_values, int *out_count
);
int chaos_basin_plane_generic(
    int system_id, const double *parameters, int parameter_count,
    const double *equilibria, int equilibrium_count,
    double z0, double x_min, double x_max, double y_min, double y_max,
    int nx, int ny, int row_start, int row_count,
    double dt, double duration, int method, uint8_t *basin
);

static int close_enough(double left, double right) {
    return fabs(left - right) <= 1.0e-13;
}

int main(void) {
    double times[4] = {0.0};
    double states[12] = {0.0};
    if (lorenz_simulate(
            0.1, 0.1, 0.1, 10.0, 28.0, 8.0 / 3.0,
            0.3, 0.9, 2, times, states, 4) != 0) {
        fputs("exact fixed-step trajectory was rejected\n", stderr);
        return 1;
    }
    if (!close_enough(times[3], 0.9)) {
        fputs("fixed-step trajectory has an incorrect final time\n", stderr);
        return 2;
    }
    if (lorenz_simulate(
            0.1, 0.1, 0.1, 10.0, 28.0, 8.0 / 3.0,
            0.3, 1.0, 2, times, states, 4) == 0) {
        fputs("partial final step was accepted\n", stderr);
        return 3;
    }

    const double dde_parameters[4] = {0.2, 0.1, 10.0, 1.0e308};
    if (chaos_simulate_system(
            8, dde_parameters, 4, 1.2, 0.0, 0.0,
            0.1, 0.1, 2, times, states, 2) == 0) {
        fputs("unrepresentable delay was accepted\n", stderr);
        return 4;
    }
    const double nonintegral_delay[4] = {0.2, 0.1, 10.0, 0.25};
    for (int method = 0; method <= 2; ++method) {
        if (chaos_simulate_system(
                8, nonintegral_delay, 4, 1.2, 0.0, 0.0,
                0.1, 0.1, method, times, states, 2) != 0 ||
            !isfinite(states[3]) || !isfinite(states[4]) || !isfinite(states[5])) {
            fputs("valid non-integral DDE delay or method was rejected\n", stderr);
            return 7;
        }
    }
    const double invalid_short_delay[4] = {0.2, 0.1, 10.0, 0.05};
    if (chaos_simulate_system(
            8, invalid_short_delay, 4, 1.2, 0.0, 0.0,
            0.1, 0.1, 2, times, states, 2) == 0) {
        fputs("DDE delay shorter than the explicit step was accepted\n", stderr);
        return 8;
    }
    const double valid_delay[4] = {0.2, 0.1, 10.0, 0.2};
    const double fractional_lorenz96[2] = {8.0, 7.2};
    if (chaos_simulate_system(
            15, fractional_lorenz96, 2, 8.01, 8.0, 8.0,
            0.1, 0.1, 2, times, states, 2) == 0) {
        fputs("fractional Lorenz-96 dimension was accepted\n", stderr);
        return 9;
    }
    const double invalid_parameters[3] = {10.0, NAN, 8.0 / 3.0};
    if (chaos_simulate_system(
            0, invalid_parameters, 3, 0.1, 0.1, 0.1,
            0.1, 0.1, 2, times, states, 2) == 0 ||
        chaos_simulate_system(
            0, valid_delay, 3, NAN, 0.1, 0.1,
            0.1, 0.1, 2, times, states, 2) == 0 ||
        chaos_simulate_system(
            999, valid_delay, 3, 0.1, 0.1, 0.1,
            0.1, 0.1, 2, times, states, 2) == 0 ||
        chaos_simulate_system(
            0, valid_delay, 3, 0.1, 0.1, 0.1,
            0.1, 0.1, 99, times, states, 2) == 0 ||
        chaos_simulate_system(
            0, valid_delay, 3, 0.1, 0.1, 0.1,
            0.1, 0.1, 2, times, states, 1) == 0) {
        fputs("invalid generic simulation boundary was accepted\n", stderr);
        return 10;
    }

    double out_parameters[4] = {0.0};
    double out_values[4] = {0.0};
    int out_count = -1;
    const double lorenz_parameters[3] = {10.0, 28.0, 8.0 / 3.0};
    if (chaos_bifurcation_generic(
            0, lorenz_parameters, 3, 1, 2, 0.1, 0.1, 0.1,
            20.0, 30.0, 1, 0.1, 0.0, 0.1, 1, 2, 2,
            out_parameters, out_values, &out_count) == 0 ||
        chaos_bifurcation_generic(
            0, lorenz_parameters, 3, 1, 2, 0.1, 0.1, 0.1,
            20.0, 30.0, 1, 0.1, 0.0, 0.1, 1, 0, 99,
            out_parameters, out_values, &out_count) == 0) {
        fputs("invalid bifurcation boundary was accepted\n", stderr);
        return 11;
    }
    const double l96_parameters[2] = {8.0, 7.0};
    for (int method = 0; method <= 2; ++method) {
        out_count = -1;
        if (chaos_bifurcation_generic(
                8, nonintegral_delay, 4, 3, 0, 1.2, 0.0, 0.0,
                0.23, 0.37, 2, 0.05, 0.05, 0.10, 2, 1, method,
                out_parameters, out_values, &out_count) != 0 ||
            out_count < 1 || out_count > 4) {
            fputs("valid Mackey-Glass bifurcation failed\n", stderr);
            return 14;
        }
        for (int index = 0; index < out_count; ++index) {
            if (!isfinite(out_parameters[index]) || !isfinite(out_values[index])) {
                fputs("Mackey-Glass bifurcation emitted a nonfinite value\n", stderr);
                return 15;
            }
        }
        out_count = -1;
        if (chaos_bifurcation_generic(
                15, l96_parameters, 2, 0, 0, 8.01, 8.0, 8.0,
                7.9, 8.1, 2, 0.01, 0.01, 0.02, 2, 1, method,
                out_parameters, out_values, &out_count) != 0 ||
            out_count < 1 || out_count > 4) {
            fputs("valid Lorenz-96 bifurcation failed\n", stderr);
            return 16;
        }
        for (int index = 0; index < out_count; ++index) {
            if (!isfinite(out_parameters[index]) || !isfinite(out_values[index])) {
                fputs("Lorenz-96 bifurcation emitted a nonfinite value\n", stderr);
                return 17;
            }
        }
    }

    uint8_t basin[4] = {0};
    const double equilibrium[3] = {0.0, 0.0, 0.0};
    if (chaos_basin_plane_generic(
            0, lorenz_parameters, 3, equilibrium, 240,
            0.0, -1.0, 1.0, -1.0, 1.0,
            2, 2, 0, 2, 0.1, 0.1, 2, basin) == 0 ||
        chaos_basin_plane_generic(
            0, lorenz_parameters, 3, equilibrium, 1,
            0.0, -1.0, 1.0, -1.0, 1.0,
            2, 2, 1, 2, 0.1, 0.1, 2, basin) == 0 ||
        chaos_basin_plane_generic(
            0, lorenz_parameters, 3, equilibrium, 1,
            0.0, -1.0, 1.0, -1.0, 1.0,
            2, 2, 0, 2, 0.1, 0.1, 2, NULL) == 0) {
        fputs("invalid basin boundary was accepted\n", stderr);
        return 12;
    }

    const double coefficients[3] = {0.0, 1.0, 0.0};
    const double initial[1] = {0.1};
    double sprott_times[2] = {0.0};
    double sprott_states[2] = {0.0};
    int status = -1;
    if (sprott_simulate_polynomial(
            1, 1, 2, coefficients, 3, initial, 1, 0.2, 1,
            1.0e6, sprott_times, sprott_states, &status) != 0 ||
        status != 0 || !close_enough(sprott_states[1], 0.122)) {
        fputs("Heun polynomial-flow contract failed\n", stderr);
        return 5;
    }
    if (sprott_simulate_polynomial(
            1, 1, 2, coefficients, 3, initial, 1, 0.2, 99,
            1.0e6, sprott_times, sprott_states, &status) == 0) {
        fputs("invalid method enum was accepted\n", stderr);
        return 6;
    }
    const double nonfinite_coefficients[3] = {0.0, NAN, 0.0};
    const double nonfinite_initial[1] = {NAN};
    if (sprott_simulate_polynomial(
            1, 1, 2, nonfinite_coefficients, 3, initial, 1, 0.2, 1,
            1.0e6, sprott_times, sprott_states, &status) == 0 ||
        sprott_simulate_polynomial(
            1, 1, 2, coefficients, 3, nonfinite_initial, 1, 0.2, 1,
            1.0e6, sprott_times, sprott_states, &status) == 0) {
        fputs("nonfinite Sprott input was accepted\n", stderr);
        return 13;
    }

    puts("NATIVE_SANITIZER_OK");
    return 0;
}
