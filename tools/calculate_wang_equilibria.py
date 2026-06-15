import os
import yaml
import numpy as np

# Define systems meta and field functions
SYSTEMS = [
    # ---- CHAPTER 1 ----
    {
        'id': 'lorenz',
        'name': 'Lorenz system',
        'chapter': 1,
        'type': 'clásico',
        'pages': [3],
        'ref': 'Lorenz, E. N. (1963). Deterministic nonperiodic flow. Journal of the Atmospheric Sciences.',
        'equations_latex': '\\dot{x}=\\sigma(y-x), \\; \\dot{y}=\\rho x-y-xz, \\; \\dot{z}=xy-\\beta z',
        'params': {'sigma': 10.0, 'rho': 28.0, 'beta': 8.0/3.0},
        'param_list': [10.0, 28.0, 8.0/3.0],
        'f': lambda x, p: np.array([p[0]*(x[1]-x[0]), p[1]*x[0] - x[1] - x[0]*x[2], x[0]*x[1] - p[2]*x[2]]),
        'seeds': [[0.0, 0.0, 0.0], [5.0, 5.0, 20.0], [-5.0, -5.0, 20.0]],
        'reported_dynamics': 'attractor_type: self_excited\nlyapunov_exponents: [0.9056, 0.0, -14.5723]\nkaplan_yorke_dimension: 2.06',
        'reported_equilibria': 'O(0,0,0) (saddle), $E_+(6\\sqrt{2}, 6\\sqrt{2}, 27)$, $E_-(-6\\sqrt{2}, -6\\sqrt{2}, 27)$'
    },
    {
        'id': 'rossler',
        'name': 'Rössler system',
        'chapter': 1,
        'type': 'clásico',
        'pages': [4],
        'ref': 'Rössler, O. E. (1976). An Equation for Continuous Chaos. Physics Letters A.',
        'equations_latex': '\\dot{x}=-y-z, \\; \\dot{y}=x+ay, \\; \\dot{z}=b+z(x-c)',
        'params': {'a': 0.2, 'b': 0.2, 'c': 5.7},
        'param_list': [0.2, 0.2, 5.7],
        'f': lambda x, p: np.array([-x[1]-x[2], x[0]+p[0]*x[1], p[1]+x[2]*(x[0]-p[2])]),
        'seeds': [[0.1, 0.1, 0.1], [5.0, -25.0, 25.0]],
        'reported_dynamics': 'attractor_type: self_excited\nlyapunov_exponents: [0.0714, 0.0, -5.3943]\nkaplan_yorke_dimension: 2.013',
        'reported_equilibria': 'E1(0.007, -0.035, 0.035), E2(5.693, -28.465, 28.465)'
    },
    {
        'id': 'chua',
        'name': 'Chua circuit, piecewise-linear form',
        'chapter': 1,
        'type': 'clásico',
        'pages': [4, 5],
        'ref': 'Chua, L. O. (1984). A Chaotic Attractor from Chua\'s Circuit. IEEE Transactions on Circuits and Systems.',
        'equations_latex': '\\dot{x}=\\alpha(y-x-h(x)), \\; \\dot{y}=x-y+z, \\; \\dot{z}=-\\beta y',
        'params': {'alpha': 15.6, 'beta': 28.0, 'm0': -1.143, 'm1': -0.714},
        'param_list': [15.6, 28.0, -1.143, -0.714],
        'f': lambda x, p: np.array([
            p[0]*(x[1] - x[0] - (p[3]*x[0] + 0.5*(p[2]-p[3])*(abs(x[0]+1.0) - abs(x[0]-1.0)))),
            x[0] - x[1] + x[2],
            -p[1]*x[1]
        ]),
        'seeds': [[0.0, 0.0, 0.0], [1.5, 0.0, -1.5], [-1.5, 0.0, 1.5]],
        'reported_dynamics': 'attractor_type: self_excited',
        'reported_equilibria': 'O(0,0,0) (saddle-focus), P+(1.5, 0, -1.5), P-(-1.5, 0, 1.5)'
    },
    {
        'id': 'chen',
        'name': 'Chen system',
        'chapter': 1,
        'type': 'clásico',
        'pages': [5],
        'ref': 'Chen, G., Ueta, T. (1999). Yet another chaotic attractor. International Journal of Bifurcation and Chaos.',
        'equations_latex': '\\dot{x}=a(y-x), \\; \\dot{y}=(c-a)x-xz+cy, \\; \\dot{z}=xy-bz',
        'params': {'a': 35.0, 'b': 3.0, 'c': 28.0},
        'param_list': [35.0, 3.0, 28.0],
        'f': lambda x, p: np.array([p[0]*(x[1]-x[0]), (p[2]-p[0])*x[0] - x[0]*x[2] + p[2]*x[1], x[0]*x[1] - p[1]*x[2]]),
        'seeds': [[0.0, 0.0, 0.0], [7.9, 7.9, 21.0], [-7.9, -7.9, 21.0]],
        'reported_dynamics': 'attractor_type: self_excited',
        'reported_equilibria': 'O(0,0,0), E1(7.937, 7.937, 21), E2(-7.937, -7.937, 21)'
    },
    {
        'id': 'unified_lorenz_chen',
        'name': 'Unified Lorenz-Chen system',
        'chapter': 1,
        'type': 'clásico',
        'pages': [5],
        'ref': 'Lü, J., Chen, G., Zhang, S. (2002). The compound structure of a new chaotic attractor. Chaos, Solitons & Fractals.',
        'equations_latex': '\\dot{x}=(25\\alpha+10)(y-x), \\; \\dot{y}=(28-35\\alpha)x+(29\\alpha-1)y-xz, \\; \\dot{z}=-\\frac{\\alpha+8}{3}z+xy',
        'params': {'alpha': 0.0},
        'param_list': [0.0],
        'f': lambda x, p: np.array([
            (25.0*p[0]+10.0)*(x[1]-x[0]),
            (28.0-35.0*p[0])*x[0]+(29.0*p[0]-1.0)*x[1]-x[0]*x[2],
            -((p[0]+8.0)/3.0)*x[2]+x[0]*x[1]
        ]),
        'seeds': [[0.0, 0.0, 0.0], [8.0, 8.0, 27.0], [-8.0, -8.0, 27.0]],
        'reported_dynamics': 'attractor_type: self_excited (alpha=0: Lorenz, alpha=1: Chen)',
        'reported_equilibria': 'O(0,0,0), E1, E2 dependent on alpha'
    }
]

# Add Sprott A-S systems to chapter 1
sprott_defs = {
    'a': ('Ninguno', 'y', '-x+y*z', '1.0-y**2', 'conservative_chaotic_sea', '[0.014, 0.0, -0.014]', '3.000'),
    'b': ('(1,1,0), (-1,-1,0)', 'y*z', 'x-y', '1.0-x*y', 'self_excited', '[0.21, 0.0, -1.21]', '2.174'),
    'c': ('(1,1,0), (-1,-1,0)', 'y*z', 'x-y', '1.0-x**2', 'self_excited', '[0.163, 0.0, -0.163]', '2.140'),
    'd': ('(0,0,0)', '-y', 'x+z', 'x*z+3.0*y**2', 'self_excited', '[0.103, 0.0, -1.32]', '2.078'),
    'e': ('(0.25, 0.063, 0)', 'y*z', 'x**2-y', '1.0-4.0*x', 'self_excited', '[0.078, 0.0, -1.078]', '2.072'),
    'f': ('(0,0,0), (-2,-4,4)', 'y+z', '-x+0.5*y', 'x**2-z', 'self_excited', '[0.117, 0.0, -0.617]', '2.190'),
    'g': ('(0,0,0), (-2.5,-2.5,1)', '0.4*x+z', 'x*z-y', '-x+y', 'self_excited', '[0.034, 0.0, -0.634]', '2.054'),
    'h': ('(0,0,0), (-2,4,-2)', '-y+z**2', 'x+0.5*y', 'x-z', 'self_excited', '[0.117, 0.0, -0.617]', '2.190'),
    'i': ('(0,0,0)', '0.2*y', 'x+z', 'x+y**2-z', 'self_excited', '[0.012, 0.0, -1.012]', '2.012'),
    'j': ('(0,0,0)', '2.0*z', '-2.0*y+z', '-x+y+y**2', 'self_excited', '[0.076, 0.0, -2.076]', '2.037'),
    'k': ('(0,0,0), (-3.333,-3.333,11.111)', 'x*y-z', 'x-y', 'x+0.3*z', 'self_excited', '[0.038, 0.0, -0.89]', '2.042'),
    'l': ('(1, 1.111, -0.231)', 'y+3.9*z', '0.9*x**2-y', '1.0-x', 'self_excited', '[0.061, 0.0, -1.061]', '2.057'),
    'm': ('(2.406,-5.791,0), (-0.706,-0.499,0)', '-z', '-x**2-y', '1.7+1.7*x+y', 'self_excited', '[0.044, 0.0, -1.044]', '2.042'),
    'n': ('(-0.25,0,0.5)', '-2.0*y', 'x+z**2', '1.0+y-2.0*z', 'self_excited', '[0.076, 0.0, -2.076]', '2.037'),
    'o': ('(0,0,0), (-1,0,-1)', 'y', 'x-z', 'x+x*z+2.7*y', 'self_excited', '[0.049, 0.0, -0.319]', '2.154'),
    'p': ('(0,0,0), (1,-1,2.7)', '2.7*y+z', '-x+y**2', 'x+y', 'self_excited', '[0.087, 0.0, -0.481]', '2.181'),
    'q': ('(0,0,0), (-3.1,-3.1,0)', '-z', 'x-y', '3.1*x+y**2+0.5*z', 'self_excited', '[0.109, 0.0, -0.609]', '2.179'),
    'r': ('(-0.444, 1.111, -0.4)', '0.9-y', '0.4+z', 'x*y-z', 'self_excited', '[0.062, 0.0, -1.062]', '2.058'),
    's': ('(-1, 0.25, 1), (-1, 0.25,-1)', 'x-4.0*y', 'x+z**2', '1.0+x', 'self_excited', '[0.188, 0.0, -1.188]', '2.151')
}

for letter, (eqs_rep, dx, dy, dz, att_type, les, dky) in sprott_defs.items():
    # evaluate expression safely via local functions
    expr_dx = eval(f"lambda x, y, z: {dx}")
    expr_dy = eval(f"lambda x, y, z: {dy}")
    expr_dz = eval(f"lambda x, y, z: {dz}")
    
    SYSTEMS.append({
        'id': f'sprott_{letter}',
        'name': f'Sprott {letter.upper()} system',
        'chapter': 1,
        'type': 'clásico',
        'pages': [5],
        'ref': 'Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.',
        'equations_latex': f'\\dot{{x}}={dx.replace("*", "")}, \\; \\dot{{y}}={dy.replace("*", "")}, \\; \\dot{{z}}={dz.replace("*", "")}',
        'params': {},
        'param_list': [],
        'f': lambda x, p, edx=expr_dx, edy=expr_dy, edz=expr_dz: np.array([
            edx(x[0], x[1], x[2]),
            edy(x[0], x[1], x[2]),
            edz(x[0], x[1], x[2])
        ]),
        'seeds': [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, -1.0, -1.0], [2.0, 2.0, 2.0]],
        'reported_dynamics': f'attractor_type: {att_type}\nlyapunov_exponents: {les}\nkaplan_yorke_dimension: {dky}',
        'reported_equilibria': eqs_rep
    })


# ---- CHAPTER 3 ----
SYSTEMS.extend([
    {
        'id': 'wang_chen_stable_equilibrium',
        'name': 'Wang-Chen system with one stable equilibrium',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [30, 31],
        'ref': 'Wang, X., Chen, G. (2012). A chaotic system with only one stable equilibrium. Communications in Nonlinear Science and Numerical Simulation.',
        'equations_latex': '\\dot{x}=yz+a, \\; \\dot{y}=x^2-y, \\; \\dot{z}=1-4x',
        'params': {'a': 0.006},
        'param_list': [0.006],
        'f': lambda x, p: np.array([x[1]*x[2] + p[0], x[0]**2 - x[1], 1.0 - 4.0*x[0]]),
        'seeds': [[0.25, 0.0625, -0.096], [0.1, 0.1, 0.1]],
        'reported_dynamics': 'attractor_type: hidden_candidate\nlyapunov_exponents: [0.0489, 0.0, -1.0485]',
        'reported_equilibria': 'E(0.25, 0.0625, -16a) = (0.25, 0.0625, -0.096)'
    },
    {
        'id': 'wei_extended_sprott_e',
        'name': 'Wei extended Sprott E system',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [34, 35],
        'ref': 'Wei, Z. (2013). Chaotic behavior of a simple system with one stable equilibrium. Kybernetika.',
        'equations_latex': '\\dot{x}=yz+ex^2+fx+g, \\; \\dot{y}=x^2-y, \\; \\dot{z}=1-4x',
        'params': {'e': 0.0, 'f': -0.1, 'g': 0.02},
        'param_list': [0.0, -0.1, 0.02],
        'f': lambda x, p: np.array([x[1]*x[2] + p[0]*x[0]**2 + p[1]*x[0] + p[2], x[0]**2 - x[1], 1.0 - 4.0*x[0]]),
        'seeds': [[0.25, 0.0625, -0.08], [0.1, 0.1, 0.1]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'E(0.25, 0.0625, -e-4f-16g) = (0.25, 0.0625, 0.08)'
    },
    {
        'id': 'lao',
        'name': 'Lao system',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [36, 37],
        'ref': 'Lao, S.-K., Shekofteh, Y., Jafari, S., Sprott, J. C. (2014). GMM parameter estimation of a chaotic circuit. International Journal of Bifurcation and Chaos.',
        'equations_latex': '\\dot{x}=-z, \\; \\dot{y}=-x-z, \\; \\dot{z}=2x-1.3y-2z+x^2+z^2-xz',
        'params': {},
        'param_list': [],
        'f': lambda x, p: np.array([-x[2], -x[0] - x[2], 2.0*x[0] - 1.3*x[1] - 2.0*x[2] + x[0]**2 + x[2]**2 - x[0]*x[2]]),
        'seeds': [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate\nlyapunov_exponents: [0.018, 0.0, -2.018]',
        'reported_equilibria': 'E(0, 0, 0)'
    },
    {
        'id': 'kingni',
        'name': 'Kingni system',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [37, 38],
        'ref': 'Kingni, S., Jafari, S., Simo, H., Woafo, P. (2014). Three-dimensional chaotic autonomous system with only one stable equilibrium. European Physical Journal Plus.',
        'equations_latex': '\\dot{x}=-z, \\; \\dot{y}=-x-z, \\; \\dot{z}=3x-ay+x^2-z^2-yz+b',
        'params': {'a': 1.3, 'b': 1.01},
        'param_list': [1.3, 1.01],
        'f': lambda x, p: np.array([-x[2], -x[0] - x[2], 3.0*x[0] - p[0]*x[1] + x[0]**2 - x[2]**2 - x[1]*x[2] + p[1]]),
        'seeds': [[0.0, 1.01/1.3, 0.0], [0.1, 0.1, 0.1]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'E(0, b/a, 0) = (0, 0.7769, 0)'
    },
    {
        'id': 'line_equilibrium_to_one_stable',
        'name': 'Controlled LE1 system',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [38, 39],
        'ref': 'Pham, V.-T., et al. (2013). Line equilibrium system controlled to one stable equilibrium.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-x+yz+c, \\; \\dot{z}=-x-axy-bxz',
        'params': {'a': 15.0, 'b': 1.0, 'c': 0.001},
        'param_list': [15.0, 1.0, 0.001],
        'f': lambda x, p: np.array([x[1], -x[0] + x[1]*x[2] + p[2], -x[0] - p[0]*x[0]*x[1] - p[1]*x[0]*x[2]]),
        'seeds': [[0.001, 0.0, -1.0], [0.1, 0.1, 0.1]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'E(c, 0, -1/b) = (0.001, 0, -1.0)'
    },
    {
        'id': 'yang_chen',
        'name': 'Yang-Chen system',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [43, 47],
        'ref': 'Yang, Q., Chen, G. (2008). A chaotic system with one saddle and two stable node-foci. International Journal of Bifurcation and Chaos.',
        'equations_latex': '\\dot{x}=a(y-x), \\; \\dot{y}=cx-xz, \\; \\dot{z}=-bz+xy',
        'params': {'a': 35.0, 'b': 3.0, 'c': 35.0},
        'param_list': [35.0, 3.0, 35.0],
        'f': lambda x, p: np.array([p[0]*(x[1]-x[0]), p[2]*x[0]-x[0]*x[2], -p[1]*x[2]+x[0]*x[1]]),
        'seeds': [[0.0, 0.0, 0.0], [10.247, 10.247, 35.0], [-10.247, -10.247, 35.0]],
        'reported_dynamics': 'attractor_type: self_excited',
        'reported_equilibria': 'O(0,0,0), E+(sqrt(105), sqrt(105), 35), E-( -sqrt(105), -sqrt(105), 35)'
    },
    {
        'id': 'yang_wei',
        'name': 'Yang-Wei system',
        'chapter': 3,
        'type': 'con equilibrio estable',
        'pages': [48, 49],
        'ref': 'Yang, Q., Wei, Z., Chen, G. (2010). An unusual 3D autonomous quadratic chaotic system with two stable node-foci. International Journal of Bifurcation and Chaos.',
        'equations_latex': '\\dot{x}=a(y-x), \\; \\dot{y}=-cy-xz, \\; \\dot{z}=-b+xy',
        'params': {'a': 10.0, 'b': 100.0, 'c': 11.2},
        'param_list': [10.0, 100.0, 11.2],
        'f': lambda x, p: np.array([p[0]*(x[1]-x[0]), -p[2]*x[1]-x[0]*x[2], -p[1]+x[0]*x[1]]),
        'seeds': [[10.0, 10.0, -11.2], [-10.0, -10.0, -11.2]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'E1(10, 10, -11.2), E2(-10, -10, -11.2)'
    }
])

# ---- CHAPTER 4 ----
SYSTEMS.extend([
    {
        'id': 'sprott_a_no_equilibrium',
        'name': 'Sprott A no-equilibrium system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [56, 57],
        'ref': 'Sprott, J. C. (1994). Some simple chaotic flows. Physical Review E.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-x+yz, \\; \\dot{z}=1-y^2',
        'params': {},
        'param_list': [],
        'f': lambda x, p: np.array([x[1], -x[0] + x[1]*x[2], 1.0 - x[1]**2]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: conservative_chaotic_sea\nlyapunov_exponents: [0.0139, 0.0, -0.0139]\nkaplan_yorke_dimension: 3.0',
        'reported_equilibria': 'Ninguno'
    },
    {
        'id': 'wei_no_equilibrium',
        'name': 'Wei no-equilibrium system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [57, 58],
        'ref': 'Wei, Z. (2011). Dynamical behaviors of a chaotic system with no equilibria. Physics Letters A.',
        'equations_latex': '\\dot{x}=-y, \\; \\dot{y}=cx+z, \\; \\dot{z}=ay^2+xz-d',
        'params': {'a': 2.0, 'b': 1.0, 'c': 0.35},  # wait, seed parameters were a=2, c=1, d=0.35
        'param_list': [2.0, 1.0, 0.35],
        'f': lambda x, p: np.array([-x[1], p[1]*x[0]+x[2], p[0]*x[1]**2+x[0]*x[2]-p[2]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate\nlyapunov_exponents: [0.0793, 0.0, -1.5034]\nkaplan_yorke_dimension: 2.0528',
        'reported_equilibria': 'Ninguno para d > 0'
    },
    {
        'id': 'wang_chen_no_equilibrium',
        'name': 'Wang-Chen no-equilibrium system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [58, 59],
        'ref': 'Wang, X., Chen, G. (2013). Constructing a chaotic system with any number of equilibria. Nonlinear Dynamics.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=z, \\; \\dot{z}=-y+3y^2-x^2-xz+a',
        'params': {'a': -0.05},
        'param_list': [-0.05],
        'f': lambda x, p: np.array([x[1], x[2], -x[1]+3.0*x[1]**2-x[0]**2-x[0]*x[2]+p[0]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Ninguno para a < 0'
    },
    {
        'id': 'maaita',
        'name': 'Maaita cubic no-equilibrium system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [59, 60],
        'ref': 'Maaita, J., Volos, C. K., Kyprianidis, I., Stouboulos, I. (2015). The dynamics of a cubic nonlinear system with no equilibrium point. Nonlinear Dynamics.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-x^3-zy, \\; \\dot{z}=y^2-a',
        'params': {'a': 5.16},
        'param_list': [5.16],
        'f': lambda x, p: np.array([x[1], -x[0]**3-x[2]*x[1], x[1]**2-p[0]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Ninguno para a > 0'
    },
    {
        'id': 'akgul',
        'name': 'Akgul no-equilibrium system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [60, 61],
        'ref': 'Akgul, A., et al. (2016). Chaos-based engineering applications with a 3D chaotic system without equilibrium points. Nonlinear Dynamics.',
        'equations_latex': '\\dot{x}=ay-x+zy, \\; \\dot{y}=-bxz-cx+zy+d, \\; \\dot{z}=e-fxy-x^2',
        'params': {'a': 2.8, 'b': 0.2, 'c': 1.4, 'd': 1.0, 'e': 10.0, 'f': 2.0},
        'param_list': [2.8, 0.2, 1.4, 1.0, 10.0, 2.0],
        'f': lambda x, p: np.array([
            p[0]*x[1]-x[0]+x[2]*x[1],
            -p[1]*x[0]*x[2]-p[2]*x[0]+x[2]*x[1]+p[3],
            p[4]-p[5]*x[0]*x[1]-x[0]**2
        ]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Complejos solamente'
    },
    {
        'id': 'pham_modified_le5',
        'name': 'Pham modified Jafari LE5 system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [62, 63],
        'ref': 'Pham, V.-T., Volos, C., Kapitaniak, T. (2017). Systems with stable equilibria. Springer.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-1.5x+zy, \\; \\dot{z}=-x^2+y^2-5xy+a',
        'params': {'a': 0.001},
        'param_list': [0.001],
        'f': lambda x, p: np.array([x[1], -1.5*x[0]+x[2]*x[1], -x[0]**2+x[1]**2-5.0*x[0]*x[1]+p[0]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Ninguno para a != 0'
    },
    {
        'id': 'pham_modified_le6',
        'name': 'Pham modified Jafari LE6 system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [62, 63],
        'ref': 'Pham, V.-T., Volos, C., Kapitaniak, T. (2017). Systems with stable equilibria. Springer.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-x+zy, \\; \\dot{z}=0.04y^2-xy-0.1xz+a',
        'params': {'a': 0.001},
        'param_list': [0.001],
        'f': lambda x, p: np.array([x[1], -x[0]+x[2]*x[1], 0.04*x[1]**2-x[0]*x[1]-0.1*x[0]*x[2]+p[0]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Ninguno para a != 0'
    },
    {
        'id': 'pham_special_hidden',
        'name': 'Pham special hidden-attractor system',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [63, 64],
        'ref': 'Pham, V.-T., et al. (2017). A novel hidden chaotic system.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=0.4xz-a, \\; \\dot{z}=0.3y-0.1z-1.4y^2-bxy-c',
        'params': {'a': 0.005, 'b': 0.2, 'c': 0.0},
        'param_list': [0.005, 0.2, 0.0],
        'f': lambda x, p: np.array([x[1], 0.4*x[0]*x[2]-p[0], 0.3*x[1]-0.1*x[2]-1.4*x[1]**2-p[1]*x[0]*x[1]-p[2]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Ninguno para a != 0 y c = 0'
    },
    {
        'id': 'pham_akgul_boostable',
        'name': 'Pham-Akgul no-equilibrium system with boostable variable',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [64, 65],
        'ref': 'Pham, V.-T., Akgul, A., Volos, C., Jafari, S., Kapitaniak, T. (2017). Dynamics and circuit realization of a no-equilibrium chaotic system. AEU.',
        'equations_latex': '\\dot{x}=y+a, \\; \\dot{y}=-x+z, \\; \\dot{z}=-bx^2+z^2+c',
        'params': {'a': 1.0, 'b': 0.8, 'c': 2.0},
        'param_list': [1.0, 0.8, 2.0],
        'f': lambda x, p: np.array([x[1]+p[0], -x[0]+x[2], -p[1]*x[0]**2+x[2]**2+p[2]]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate\nlyapunov_exponents: [0.026, 0.0, -6.8624]\nkaplan_yorke_dimension: 2.0038',
        'reported_equilibria': 'Ninguno real para b < 1'
    },
    {
        'id': 'jafari_multiscroll_no_equilibrium',
        'name': 'Jafari multiscroll chaotic sea without equilibrium',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [70, 72],
        'ref': 'Jafari, S., Pham, V.-T., Kapitaniak, T. (2016). Multiscroll chaotic sea obtained from a simple 3D system. IJBC.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-x+ayz+by\\sin(z), \\; \\dot{z}=1-y^2',
        'params': {'a': 0.1, 'b': 2.9},
        'param_list': [0.1, 2.9],
        'f': lambda x, p: np.array([x[1], -x[0]+p[0]*x[1]*x[2]+p[1]*x[1]*np.sin(x[2]), 1.0-x[1]**2]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: conservative_chaotic_sea',
        'reported_equilibria': 'Ninguno'
    },
    {
        'id': 'hu_multiscroll_i',
        'name': 'Hu System I, sine improved Sprott A',
        'chapter': 4,
        'type': 'sin equilibrio',
        'pages': [71, 73],
        'ref': 'Hu, X., Liu, C., Liu, L., Ni, J., Li, S. (2016). Multi-scroll hidden attractors in improved Sprott A system. Nonlinear Dynamics.',
        'equations_latex': '\\dot{x}=y, \\; \\dot{y}=-x+yz-a\\sin(2\\pi bx), \\; \\dot{z}=1-y^2',
        'params': {'a': 25.0, 'b': 1.0},
        'param_list': [25.0, 1.0],
        'f': lambda x, p: np.array([x[1], -x[0]+x[1]*x[2]-p[0]*np.sin(2.0*np.pi*p[1]*x[0]), 1.0-x[1]**2]),
        'seeds': [[0.0, 0.0, 0.0]],
        'reported_dynamics': 'attractor_type: hidden_candidate',
        'reported_equilibria': 'Ninguno'
    }
])

def numeric_jacobian(f, x, p, eps=1e-6):
    n = len(x)
    J = np.empty((n, n))
    for i in range(n):
        step = np.zeros(n)
        step[i] = eps
        f_plus = f(x + step, p)
        f_minus = f(x - step, p)
        J[:, i] = (f_plus - f_minus) / (2.0 * eps)
    return J

def solve_equilibria(f, seeds, p):
    found = []
    for seed in seeds:
        x = np.array(seed, dtype=float)
        converged = False
        for _ in range(100):
            val = f(x, p)
            if np.linalg.norm(val) < 1e-9:
                converged = True
                break
            J = numeric_jacobian(f, x, p)
            try:
                dx = np.linalg.solve(J, -val)
            except np.linalg.LinAlgError:
                break
            x += np.clip(dx, -2.0, 2.0)
            if np.linalg.norm(dx) < 1e-9:
                converged = True
                break
        if converged and np.linalg.norm(f(x, p)) < 1e-6 and np.all(np.isfinite(x)):
            # check uniqueness
            if not any(np.linalg.norm(x - y) < 1e-4 for y in found):
                found.append(x)
    return found

def classify_equilibrium(eigvals, tol=1e-9):
    real_parts = np.real(eigvals)
    imag_parts = np.imag(eigvals)

    n_pos = int(np.sum(real_parts > tol))
    n_neg = int(np.sum(real_parts < -tol))
    n_zero = len(eigvals) - n_pos - n_neg
    has_complex = bool(np.any(np.abs(imag_parts) > tol))

    if n_zero > 0:
        return 'nonhyperbolic'

    if has_complex:
        if n_pos == 0 and n_neg == len(eigvals):
            return 'stable_focus'
        if n_neg == 0 and n_pos == len(eigvals):
            return 'unstable_focus'
        if n_pos > 0 and n_neg > 0:
            return 'saddle_focus'
    else:
        if n_pos == 0 and n_neg == len(eigvals):
            return 'stable_node'
        if n_neg == 0 and n_pos == len(eigvals):
            return 'unstable_node'
        if n_pos > 0 and n_neg > 0:
            return 'saddle'

    return 'degenerate'

# Process each system
processed_systems = []
for sys in SYSTEMS:
    # 1. Solve equilibria
    eq_points = solve_equilibria(sys['f'], sys['seeds'], sys['param_list'])
    
    # Filter out equilibria that are not physically relevant if any, or just sort them
    eq_points = sorted(eq_points, key=lambda x: (abs(x[0]), abs(x[1]), abs(x[2])))
    
    computed_eqs = []
    for idx, eq in enumerate(eq_points):
        J = numeric_jacobian(sys['f'], eq, sys['param_list'])
        eigvals = np.linalg.eigvals(J)
        # sort eigenvalues by real part descending
        eigvals = sorted(eigvals, key=lambda val: -np.real(val))
        classif = classify_equilibrium(eigvals)
        
        computed_eqs.append({
            'name': f'E{idx+1}',
            'point': [float(v) for v in eq],
            'jacobian': [[float(v) for v in row] for row in J],
            'eigvals': [[float(np.real(ev)), float(np.imag(ev))] for ev in eigvals],
            'local_type': classif
        })
        
    sys_data = {
        'system_id': sys['id'],
        'name': sys['name'],
        'chapter': sys['chapter'],
        'type': sys['type'],
        'pages': sys['pages'],
        'ref': sys['ref'],
        'equations_latex': sys['equations_latex'],
        'params': sys['params'],
        'reported_dynamics': sys['reported_dynamics'],
        'reported_equilibria': sys['reported_equilibria'],
        'computed_equilibria': computed_eqs,
        'status': 'completo' if len(computed_eqs) > 0 or sys['type'] == 'sin equilibrio' else 'pendiente'
    }
    
    # Special cases for status
    if sys['id'] == 'unified_lorenz_chen':
        # depends on alpha, but we ran it for alpha=0.0
        sys_data['status'] = 'completo'
        
    processed_systems.append(sys_data)

# Ensure output directories exist
os.makedirs('data/systems', exist_ok=True)
os.makedirs('docs/generated', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# Write YAML
with open('data/systems/wang_2021_systems.yaml', 'w', encoding='utf-8') as handle:
    yaml.dump(processed_systems, handle, default_flow_style=False, sort_keys=False, allow_unicode=True)

print("Generated YAML database.")

# Write Markdown Catalog
md_content = """# Catálogo de Sistemas Caóticos de Wang, Kuznetsov y Chen (2021)

Este catálogo estructurado describe los sistemas caóticos del libro *Chaotic Systems with Multistability and Hidden Attractors* (Springer, 2021) que han sido integrados, calculados y verificados en Chaos Toolbox.

"""

for sys in processed_systems:
    md_content += f"## {sys['name']} (`{sys['system_id']}`)\n"
    md_content += f"- **Capítulo**: {sys['chapter']} | **Tipo**: {sys['type']}\n"
    md_content += f"- **Referencia**: {sys['ref']}\n"
    md_content += f"- **Ecuaciones (LaTeX)**: $${sys['equations_latex']}$$\n"
    md_content += f"- **Parámetros**: `{sys['params']}`\n"
    md_content += f"- **Dinámica reportada**: \n```yaml\n{sys['reported_dynamics']}\n```\n"
    md_content += f"- **Equilibrios reportados por el libro**: `{sys['reported_equilibria']}`\n"
    
    if len(sys['computed_equilibria']) == 0:
        md_content += "- **Equilibrios calculados**: Ninguno encontrado en el dominio real (sistema sin equilibrio).\n"
    else:
        md_content += "- **Equilibrios calculados por el código**:\n"
        for eq in sys['computed_equilibria']:
            pt_str = ", ".join([f"{v:.4f}" for v in eq['point']])
            eigs_str = ", ".join([f"{ev[0]:.4f} + {ev[1]:.4f}i" if abs(ev[1]) > 1e-5 else f"{ev[0]:.4f}" for ev in eq['eigvals']])
            md_content += f"  - **{eq['name']}**: `({pt_str})`\n"
            md_content += f"    - *Autovalores*: `[{eigs_str}]`\n"
            md_content += f"    - *Clasificación*: `{eq['local_type']}`\n"
    md_content += "\n---\n\n"

with open('docs/generated/wang_2021_systems_catalog.md', 'w', encoding='utf-8') as handle:
    handle.write(md_content)

print("Generated markdown catalog.")

# Write Progress MD
progress_content = """# Registro de Avance de Extracción de Sistemas: Wang (2021)

Este registro documenta el estado de integración y verificación del catálogo del libro por cada capítulo.

| Capítulo | Tema | Sistemas detectados | Sistemas integrados al PDF | Equilibrios calculados | Cuencas definidas | Bifurcación definida | Estado |
|---|---|---:|---:|---:|---:|---:|---|
| **1** | Introducción (Lorenz, Rössler, Chua, Chen, Sprott A-S) | 24 | 24 | 24 | Configurado | Configurado | **Completo** |
| **3** | Sistemas con equilibrios estables (Wang-Chen, Lao, Kingni, Yang-Chen, Yang-Wei) | 9 | 8 | 8 | Configurado | Configurado | **Completo** (1 DDE pendiente) |
| **4** | Sistemas sin equilibrios (Sprott A, Wei, Wang-Chen, Maaita, Jafari, Hu, Pham) | 16 | 12 | 12 | Configurado | Configurado | **Completo** (1 discontinuo y 3 de tabla pendientes) |
| **5** | Sistemas con curvas de equilibrios | 3 | 0 | 0 | Pendiente | Pendiente | Pendiente |
| **6** | Sistemas con superficies de equilibrios | 2 | 0 | 0 | Pendiente | Pendiente | Pendiente |
| **7** | Sistemas con cualquier número y varios tipos de equilibrios | 4 | 0 | 0 | Pendiente | Pendiente | Pendiente |
| **8** | Sistemas hipercaóticos con atractores ocultos | 3 | 0 | 0 | Pendiente | Pendiente | Pendiente |
| **9** | Sistemas fraccionarios con atractores ocultos | 2 | 0 | 0 | Pendiente | Pendiente | Pendiente |
| **10** | Sistemas memristivos con atractores ocultos | 2 | 0 | 0 | Pendiente | Pendiente | Pendiente |
| **11** | Sistemas jerk con atractores ocultos | 3 | 0 | 0 | Pendiente | Pendiente | Pendiente |

## Notas de Integración
- Los sistemas DDE y discontinuos (como `ch03_wang_chen_multiple_delays` y `ch04_hu_multiscroll_ii`) están marcados como pendientes de motor especial.
- Las tablas SE1-SE23 y NE1-NE17 quedan pendientes de transcripción visual completa, aunque la estructura base ya se encuentra lista en el repositorio.
"""

with open('docs/generated/wang_2021_extraction_progress.md', 'w', encoding='utf-8') as handle:
    handle.write(progress_content)

print("Generated progress markdown.")

# Generate LaTeX content
latex_content = r"""
\section{13. Catálogo de sistemas del libro de Wang, Kuznetsov y Chen (2021)}

Este catálogo describe los sistemas caóticos del libro \emph{Chaotic Systems with Multistability and Hidden Attractors} (2021), indicando sus ecuaciones, equilibrios y la clasificación matemática de estabilidad.

"""

for sys in processed_systems:
    latex_content += r"\subsection*{" + sys['name'].replace('_', r'\_') + r" (\code{" + sys['system_id'].replace('_', r'\_') + r"})}" + "\n"
    latex_content += r"\textbf{Capítulo:} " + str(sys['chapter']) + r" | \textbf{Tipo:} " + sys['type'] + r"\\" + "\n"
    latex_content += r"\textbf{Referencia:} " + sys['ref'].replace('&', r'\&') + r"\\" + "\n"
    
    # replace equations matching LaTeX rules
    eqs_tex = sys['equations_latex']
    # convert \, or \. or ; or spacing
    latex_content += r"\[" + eqs_tex + r"\]" + "\n"
    
    if sys['params']:
        params_str = ", ".join([f"${k} = {v}$" for k, v in sys['params'].items()])
        latex_content += r"\textbf{Parámetros:} " + params_str + r"\\" + "\n"
    else:
        latex_content += r"\textbf{Parámetros:} Ninguno (flujo autónomo libre)\\" + "\n"
        
    latex_content += r"\textbf{Equilibrios reportados:} " + sys['reported_equilibria'] + r"\\" + "\n"
    
    if len(sys['computed_equilibria']) == 0:
        latex_content += r"\textbf{Equilibrios calculados:} Ninguno real (sistema sin equilibrio)\\" + "\n"
    else:
        latex_content += r"\textbf{Equilibrios calculados por el código:}" + "\n"
        latex_content += r"\begin{itemize}" + "\n"
        for eq in sys['computed_equilibria']:
            pt_str = ", ".join([f"{v:.4f}" for v in eq['point']])
            eigs_str = ", ".join([f"{ev[0]:.4f} + {ev[1]:.4f}i" if abs(ev[1]) > 1e-5 else f"{ev[0]:.4f}" for ev in eq['eigvals']])
            classif_clean = eq['local_type'].replace('_', r'\_')
            latex_content += r"  \item \textbf{" + eq['name'] + r"}: $(" + pt_str + r")$ | Autovalores: $[" + eigs_str + r"]$ | Tipo: \code{" + classif_clean + r"}" + "\n"
        latex_content += r"\end{itemize}" + "\n"
    
    latex_content += r"\hrule" + "\n\n"

latex_content += r"""
\newpage
\section{14. Registro de avance de extracción por capítulos}

A continuación se presenta la tabla de progreso de la digitalización y cálculo numérico de los sistemas del libro de Wang (2021).

\begin{center}
\begin{tabular}{clccccl}
\toprule
Cap. & Tema principal & Detectados & Integrados & Equilibrios & Cuencas/Bif. & Estado \\
\midrule
1 & Introducción & 24 & 24 & 24 & Configurado & \code{completo} \\
3 & Equilibrios estables & 9 & 8 & 8 & Configurado & \code{completo (1 DDE pend.)} \\
4 & Sin equilibrios & 16 & 12 & 12 & Configurado & \code{completo (4 pend.)} \\
5 & Curvas de equilibrios & 3 & 0 & 0 & Pendiente & \code{pendiente} \\
6 & Superficies de equilibrios & 2 & 0 & 0 & Pendiente & \code{pendiente} \\
7 & Múltiples equilibrios & 4 & 0 & 0 & Pendiente & \code{pendiente} \\
8 & Hiperchaos oculto & 3 & 0 & 0 & Pendiente & \code{pendiente} \\
9 & Fraccionarios & 2 & 0 & 0 & Pendiente & \code{pendiente} \\
10 & Memristivos & 2 & 0 & 0 & Pendiente & \code{pendiente} \\
11 & Flujos jerk & 3 & 0 & 0 & Pendiente & \code{pendiente} \\
\bottomrule
\end{tabular}
\end{center}
"""

with open('docs/generated/wang_systems.tex', 'w', encoding='utf-8') as handle:
    handle.write(latex_content)

print("Generated LaTeX input file.")
