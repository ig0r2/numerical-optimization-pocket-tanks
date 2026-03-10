import numpy as np
from utils import globals
from algorithms import Algorithm, function, calculate_gradient, project, get_x0


class HookeJeeves(Algorithm):
    def __init__(self, delta0=1e-2, shrink_rate=0.4):
        super().__init__()
        self.shrink_rate = shrink_rate
        self.delta_min = globals.stop_criterions["delta_min"]

        self.x_base = get_x0().copy()
        self.f_base = function(self.x_base)
        self.delta = delta0

    @staticmethod
    def params_grid():
        return {
            "delta0": [1e-4, 1e-3, 5e-3, 1e-2, 1e-1, 1, 2],
            "shrink_rate": [0.2, 0.3, 0.4, 0.6, 0.8],
        }

    def _next_base_point(self, x_start):
        x_new = x_start.copy()
        f_current = function(x_start)
        improved = False

        for i in range(len(x_start)):
            # pozitivni korak
            x_test = x_new.copy()
            x_test[i] += self.delta
            x_test[i] = project(x_test[i])

            f_test = function(x_test)
            if f_test < f_current:
                x_new = x_test
                f_current = f_test
                improved = True
                continue

            # negativni korak
            x_test = x_new.copy()
            x_test[i] -= self.delta
            x_test[i] = project(x_test[i])

            f_test = function(x_test)
            if f_test < f_current:
                x_new = x_test
                f_current = f_test
                improved = True

        return x_new, f_current, improved

    def step(self):
        # nadji sledecu bazicnu tacku
        x_new, f_new, improved = self._next_base_point(self.x_base)

        if improved:
            # pokusaj jos jednog pomeraja u istom smeru
            x_new_pattern = x_new + (x_new - self.x_base)
            x_new_pattern = project(x_new_pattern)
            f_pattern = function(x_new_pattern)

            if f_pattern < f_new:
                self.x_base = x_new_pattern
                self.f_base = f_pattern
            else:
                self.x_base = x_new
                self.f_base = f_new
        else:
            # smanjene delte ako nema pobosljanja funkcije
            self.delta *= self.shrink_rate
            self.f_base = f_new

        # provera kriterijuma
        if self.delta <= globals.stop_criterions["delta_min"]:
            return self.x_base.copy(), "delta_min"

        return self.x_base.copy(), False


class SpiralScan(Algorithm):
    """
    Skeniranje po Arhimedovoj spirali
    Jedan poziv step() evaluira jednu tacku spirale
    """

    def __init__(self, delta=0.75, dphi=2.5):
        super().__init__()
        self.delta = delta
        self.dphi = dphi
        self.delta_min = globals.stop_criterions["delta_min"]

        self.x_min = get_x0().copy()
        self.f_min = function(self.x_min)

        self.x_pr = self.x_min.copy()
        self.center = self.x_pr.copy()
        self.phi = self.dphi
        self.steps_per_rotation = int(np.ceil((2.0 * np.pi) / self.dphi))
        self.steps_in_rotation = 0
        self.rotation_improved = False

    @staticmethod
    def params_grid():
        return {
            "delta": [0.1, 0.25, 0.5, 0.75, 1.0],
            "dphi": [0.05, 0.1, 0.2, 0.5, 1, 1.5, 2, 2.5, 3],
        }

    def step(self):
        if self.delta <= self.delta_min:
            return self.x_min.copy(), "delta_min"

        f_prev = self.f_min
        offset = self.delta * self.phi * np.array([np.cos(self.phi), np.sin(self.phi)], dtype=np.float64)
        candidate = project(self.center + offset)
        candidate_f = function(candidate)

        if candidate_f < self.f_min:
            self.x_min = candidate
            self.f_min = candidate_f
            self.rotation_improved = True

        self.phi += self.dphi
        self.steps_in_rotation += 1

        if self.steps_in_rotation >= self.steps_per_rotation:
            if self.rotation_improved:
                # Nastavi spiralu oko istog centra sa vecim phi
                self.x_pr = self.x_min.copy()
            else:
                # Nije bilo poboljsanja u celoj rotaciji: smanji radijus i resetuj spiralu oko novog centra
                self.delta *= 0.5
                self.x_pr = self.x_min.copy()
                self.center = self.x_pr.copy()
                self.phi = self.dphi

                if self.delta <= self.delta_min:
                    return self.x_min.copy(), "delta_min"

            self.steps_in_rotation = 0
            self.rotation_improved = False

        return self.x_min.copy(), False


class GaussSeidel(Algorithm):
    """
    Gauss-Seidel metod sa metodom zlatnog preseka za 1D optimizaciju
    max_iter_1d - maksimalni broj iteracija zlatnog preseka
    """

    def __init__(self, max_iter_1d=50):
        super().__init__()
        self.max_iter_1d = max_iter_1d
        self.max_iter = globals.stop_criterions["max_iterations"]
        self.x_eps = globals.stop_criterions["x_eps"]
        self.f_eps = globals.stop_criterions["f_eps"]

        self.x = get_x0().copy()
        self.fk = function(self.x)
        self.outer_iters = 0

    @staticmethod
    def params_grid():
        return {
            "max_iter_1d": [1, 2, 5, 10, 20, 50, 100],
        }

    @staticmethod
    def _golden_ratio(a, b, x_full, i_change, max_iter=20):
        def _function1d(x_changed):
            x_f = x_full.copy()
            x_f[i_change] = x_changed
            return function(x_f)

        epsilon = (3 - np.sqrt(5)) / 2
        x1 = a + epsilon * (b - a)
        x2 = b - epsilon * (b - a)

        it = 0
        while (b - a) > globals.stop_criterions["delta_min"] and it < max_iter:
            it += 1
            x1 = np.clip(x1, 0.0, 1.0)
            x2 = np.clip(x2, 0.0, 1.0)
            f1 = _function1d(x1)
            f2 = _function1d(x2)

            if f1 == f2:
                a = x1
                b = x2
                x1 = a + epsilon * (b - a)
                x2 = b - epsilon * (b - a)
            else:
                if f1 < f2:
                    b = x2
                    x2 = x1
                    x1 = a + epsilon * (b - a)
                else:
                    a = x1
                    x1 = x2
                    x2 = b - epsilon * (b - a)

        return (a + b) / 2

    def step(self):
        # spreci da 1D prekoraci globalni limit iteracija
        if self.outer_iters + self.max_iter_1d >= self.max_iter:
            return self.x.copy(), "max_iter"

        x_old = self.x.copy()
        f_prev = self.fk

        for i in range(2):
            # 1D minimizacija po x_i
            self.x[i] = self._golden_ratio(0, 1, x_full=self.x, i_change=i, max_iter=self.max_iter_1d)
            self.x = project(self.x)

        self.outer_iters += 1

        if np.linalg.norm(self.x - x_old) <= self.x_eps:
            return self.x.copy(), "x_eps"
        self.fk = function(self.x)
        if abs(self.fk - f_prev) < self.f_eps:
            return self.x.copy(), "f_eps"

        return self.x.copy(), False


class RandomSearchDensity(Algorithm):
    """
    Metod nasumcinog pretrazivanja sa vecom gustinom
    M - ukupan broj neuspelih pokusaja
    """

    def __init__(self, M=100):
        super().__init__()
        self.M = M

        self.x_min = get_x0()
        self.f_min = function(self.x_min)
        self.k = 1  # broj neuspelih pokusaja

    @staticmethod
    def params_grid():
        return {
            "M": [10, 20, 35, 50, 100, 200]
        }

    def step(self):
        alpha = np.random.uniform(size=2)

        candidate = self.x_min + ((2 * alpha - 1) ** self.k) / self.k
        candidate = project(candidate)
        candidate_f = function(candidate)

        if candidate_f < self.f_min:
            self.x_min = candidate
            self.f_min = candidate_f
        else:
            self.k += 1

        if self.k >= self.M:
            return self.x_min.copy(), "max_failed"

        return self.x_min.copy(), False


class MADS(Algorithm):
    """
    Mesh Adaptive Direct Search (MADS)
    """

    def __init__(self, delta0=0.1, tau=6.0):
        super().__init__()
        if tau <= 1.0:
            raise ValueError("tau mora biti > 1")
        self.delta_poll = delta0
        self.tau = tau
        self.delta_min = globals.stop_criterions["delta_min"]
        self.x_eps = globals.stop_criterions["x_eps"]
        self.f_eps = globals.stop_criterions["f_eps"]

        self.x_min = get_x0().copy()
        self.f_min = function(self.x_min)

        self.delta_mesh = min(self.delta_poll, self.delta_poll ** 2)  # mreza
        # mreza sluzi za kontrolisanje gustine okoline

    @staticmethod
    def params_grid():
        return {
            "delta0": [0.001, 0.05, 0.1, 0.2, 0.5, 1, 2, 5],
            "tau": [1.25, 1.5, 2, 5, 6, 10, 20, 50, 100],
        }

    def _snap_to_mesh(self, x):
        mesh_step = max(self.delta_mesh, 1e-12)
        snapped = np.round(np.asarray(x, dtype=np.float64) / mesh_step) * mesh_step
        return project(snapped)

    @staticmethod
    def _poll_directions():
        # smerovi za pretragu. 4 smera, po 90stepeni medjusobno, ali svi rotirani za random ugao theta
        theta = np.random.uniform(0.0, 2.0 * np.pi)
        c = np.cos(theta)
        s = np.sin(theta)
        u = np.array([c, s], dtype=np.float64)
        v = np.array([-s, c], dtype=np.float64)
        return u, -u, v, -v

    def step(self):
        x_prev = self.x_min.copy()
        f_prev = self.f_min
        improved = False

        # Poll korak: isprobavanje tacaka u 4 smera
        for direction in self._poll_directions():
            candidate = self._snap_to_mesh(self.x_min + self.delta_poll * direction)
            candidate_f = function(candidate)

            # ako je kandidat vrlo blizu x, ne biraj
            if np.linalg.norm(candidate - self.x_min) < self.x_eps:
                continue
            # ako je kandidat vrlo blizu fx, ne biraj
            if abs(candidate_f - self.f_min) <= self.f_eps:
                continue

            if candidate_f < self.f_min:
                self.x_min = candidate
                self.f_min = candidate_f
                improved = True
                break

        if improved:
            self.delta_poll = min(1.0, self.delta_poll * self.tau)
        else:
            self.delta_poll /= self.tau

        # updejtuj mrezu
        self.delta_mesh = min(self.delta_poll, self.delta_poll ** 2)

        if self.delta_poll < self.delta_min:
            return self.x_min.copy(), "delta_min"
        if improved and abs(self.f_min - f_prev) < self.f_eps:
            return self.x_min.copy(), "f_eps"
        if np.linalg.norm(self.x_min - x_prev) < self.x_eps and self.delta_poll <= max(self.delta_min, self.x_eps):
            return self.x_min.copy(), "x_eps"

        return self.x_min.copy(), False


class GradientDescentAutoLR(Algorithm):
    """
    Gradijentni spust sa automatskom korekcijom koraka
    korak se povecava za grow_rate ako se funkcija smanjivala prethodne 2 itreacije
    korak se smanjuje za shrink_rate ako se funkcija nije smanjila u trenutnoj itreaciji
    """

    def __init__(self, start_tk=1e-3, grow_rate=1.2, shrink_rate=0.4):
        super().__init__()
        self.start_tk = start_tk
        self.grow_rate = grow_rate
        self.shrink_rate = shrink_rate
        self.grad_eps = globals.stop_criterions["gradient_eps"]
        self.x_eps = globals.stop_criterions["x_eps"]
        self.f_eps = globals.stop_criterions["f_eps"]

        self.x = get_x0().copy()
        self.fk = function(self.x)
        self.f_prev = None
        self.f_prev_2 = None
        self.tk = self.start_tk

    @staticmethod
    def params_grid():
        return {
            "start_tk": [1e-4, 1e-3, 1e-2, 0.1],
            "shrink_rate": [0.1, 0.2, 0.4, 0.6, 0.8],
            "grow_rate": [1.05, 1.5],
        }

    def step(self):
        grad = calculate_gradient(self.x)

        # provera kriterijuma - mali gradijent
        if np.linalg.norm(grad) < self.grad_eps:
            return self.x.copy(), "grad_eps"

        self.f_prev_2 = self.f_prev
        self.f_prev = self.fk
        x_prev = self.x.copy()

        # update
        self.x -= self.tk * grad
        self.x = project(self.x)
        self.fk = function(self.x)

        # update koraka
        if self.f_prev is not None and self.fk >= self.f_prev:
            self.tk *= self.shrink_rate
        elif self.f_prev_2 is not None and self.fk < self.f_prev < self.f_prev_2:
            self.tk *= self.grow_rate

        # provera kriterijuma - razlika x
        if np.linalg.norm(self.x - x_prev) < self.x_eps:
            return self.x.copy(), "x_eps"
        # provera kriterijuma - razlika f
        if self.f_prev_2 is not None:
            if abs(self.fk - self.f_prev) < self.f_eps:
                return self.x.copy(), "f_eps"

        return self.x.copy(), False


class GradientDescentBacktracking(Algorithm):
    """
    Gradijentni spust sa Armijo backtracking line search
    """

    def __init__(self, start_t=0.001, armijo_rho=1e-3, armijo_beta=0.2):
        super().__init__()
        self.start_t = start_t
        self.armijo_rho = armijo_rho
        self.armijo_beta = armijo_beta
        self.min_step = globals.stop_criterions["delta_min"]
        self.grad_eps = globals.stop_criterions["gradient_eps"]
        self.x_eps = globals.stop_criterions["x_eps"]
        self.f_eps = globals.stop_criterions["f_eps"]

        self.x = get_x0().copy()
        self.fk = function(self.x)

    @staticmethod
    def params_grid():
        return {
            "start_t": [0.001, 0.01, 0.1, 0.2, 0.3, 0.5, 0.75],
            "armijo_rho": [1e-2, 1e-3, 1e-4, 1e-5],
            "armijo_beta": [0.2, 0.4, 0.6, 0.8],
        }

    def step(self):
        grad = calculate_gradient(self.x)

        if np.linalg.norm(grad) < self.grad_eps:
            return self.x.copy(), "grad_eps"

        d_k = -grad
        gkdk = np.dot(grad, d_k)
        x_prev = self.x.copy()
        f_prev = self.fk
        t = self.start_t

        while t >= self.min_step:
            candidate = self.x + t * d_k
            candidate = project(candidate)
            if np.linalg.norm(candidate - self.x) < self.x_eps:
                t *= self.armijo_beta
                continue

            candidate_f = function(candidate)
            if candidate_f <= self.fk + self.armijo_rho * t * gkdk:
                self.x = candidate
                self.fk = candidate_f
                break

            t *= self.armijo_beta
        else:
            return self.x.copy(), "min_step"

        if np.linalg.norm(self.x - x_prev) < self.x_eps:
            return self.x.copy(), "x_eps"
        if abs(self.fk - f_prev) < self.f_eps:
            return self.x.copy(), "f_eps"

        return self.x.copy(), False


class BFGS(Algorithm):
    """
    BFGS sa Armijo backtracking line search
    """

    def __init__(self, start_t=0.001, armijo_rho=1e-3, armijo_beta=0.2):
        super().__init__()
        self.armijo_rho = armijo_rho
        self.armijo_beta = armijo_beta
        self.start_t = start_t
        self.min_step = globals.stop_criterions["delta_min"]
        self.grad_eps = globals.stop_criterions["gradient_eps"]
        self.x_eps = globals.stop_criterions["x_eps"]
        self.f_eps = globals.stop_criterions["f_eps"]

        self.x_k = get_x0().copy()
        self.g_k = calculate_gradient(self.x_k)
        self.H_k = np.eye(2, dtype=np.float64)

    @staticmethod
    def params_grid():
        return {
            "start_t": [0.001, 0.01, 0.1, 0.2, 0.3, 0.5, 0.75],
            "armijo_rho": [1e-2, 1e-3, 1e-4, 1e-5, 1e-6],
            "armijo_beta": [0.2, 0.4, 0.6, 0.8],
        }

    def step(self):
        if np.linalg.norm(self.g_k) < self.grad_eps:
            return self.x_k.copy(), "grad_eps"

        # pravac pretrage: dk = -Hk*gk
        d_k = -self.H_k @ self.g_k

        # ako pravac nije descent direction, resetuj Hk
        if np.dot(d_k, self.g_k) >= 0.0:
            d_k = -self.g_k
            self.H_k = np.eye(2, dtype=np.float64)

        # linijsko trazenje - backtracking
        t = self.start_t
        fk = function(self.x_k)
        f_prev = fk
        gkdk = np.dot(self.g_k, d_k)

        while t >= self.min_step:
            candidate = self.x_k + t * d_k
            candidate = project(candidate)
            candidate_f = function(candidate)

            if candidate_f <= fk + self.armijo_rho * t * gkdk:
                x_new = candidate
                fk = candidate_f
                break

            t *= self.armijo_beta
        else:
            return self.x_k.copy(), "min_step"

        # BFGS
        I = np.eye(2, dtype=np.float64)

        s_k = x_new - self.x_k
        g_new = calculate_gradient(x_new)
        y_k = g_new - self.g_k

        # provera kriterijuma
        if np.linalg.norm(g_new) < self.grad_eps:
            return self.x_k.copy(), "grad_eps"
        if np.linalg.norm(s_k) < self.x_eps:
            return self.x_k.copy(), "x_eps"
        if abs(fk - f_prev) < self.f_eps:
            return self.x_k.copy(), "f_eps"

        # Azuriranje aproksimacije inverza
        ys = np.dot(y_k, s_k)
        if ys > 1e-12:
            part1 = I - np.outer(s_k, y_k) / ys  # (I - s*y^T / s^T*y)
            part2 = I - np.outer(y_k, s_k) / ys  # (I - y*s^T / s^T*y)
            part3 = np.outer(s_k, s_k) / ys  # s*s^T / s^T*y

            # Hk+1 = (I - s*y^T / s^T*y) * H * (I - y*s^T / s^T*y) + s*s^T / s^T*y
            self.H_k = part1 @ self.H_k @ part2 + part3

        self.x_k = project(x_new)
        self.g_k = g_new

        return self.x_k.copy(), False


class LBFGS(Algorithm):
    """
    L-BFGS sa Armijo backtracking line search
    """

    def __init__(self, memory=5, start_t=0.001, armijo_rho=1e-3, armijo_beta=0.2):
        super().__init__()
        self.memory = int(memory)
        self.armijo_rho = armijo_rho
        self.armijo_beta = armijo_beta
        self.start_t = start_t
        self.min_step = globals.stop_criterions["delta_min"]
        self.grad_eps = globals.stop_criterions["gradient_eps"]
        self.x_eps = globals.stop_criterions["x_eps"]
        self.f_eps = globals.stop_criterions["f_eps"]

        self.x_k = get_x0().copy()
        self.g_k = calculate_gradient(self.x_k)
        self.s_history = []
        self.y_history = []

    @staticmethod
    def params_grid():
        return {
            "memory": [3, 5, 10],
            "start_t": [0.001, 0.01, 0.1, 0.2, 0.3, 0.5, 0.75],
            "armijo_rho": [1e-2, 1e-3, 1e-4, 1e-5, 1e-6],
            "armijo_beta": [0.2, 0.4, 0.6, 0.8],
        }

    def _two_loop_direction(self):
        if not self.s_history:
            return -self.g_k.copy()

        q = self.g_k.copy()
        alpha_list = []

        for s, y in zip(reversed(self.s_history), reversed(self.y_history)):
            ys = np.dot(y, s)
            if ys <= 1e-12:
                alpha_list.append(0.0)
                continue
            alpha = np.dot(s, q) / ys
            alpha_list.append(alpha)
            q -= alpha * y

        # skalarna aproksimacija
        s = self.s_history[-1]
        y = self.y_history[-1]
        yy = np.dot(y, y)
        if yy > 1e-12:
            gamma = np.dot(s, y) / yy
        else:
            gamma = 1.0

        r = gamma * q

        for idx, (s, y) in enumerate(zip(self.s_history, self.y_history)):
            ys = np.dot(y, s)
            if ys <= 1e-12:
                continue
            beta = np.dot(y, r) / ys
            alpha = alpha_list[len(self.s_history) - 1 - idx]
            r += s * (alpha - beta)

        return -r

    def step(self):
        if np.linalg.norm(self.g_k) < self.grad_eps:
            return self.x_k.copy(), "grad_eps"

        # pravac pretrage preko two-loop rekurzije
        d_k = self._two_loop_direction()

        # ako pravac nije descent direction resetuj istoriju
        if np.dot(d_k, self.g_k) >= 0.0:
            d_k = -self.g_k
            self.s_history.clear()
            self.y_history.clear()

        # linijsko trazenje - backtracking
        t = self.start_t
        fk = function(self.x_k)
        f_prev = fk
        gkdk = np.dot(self.g_k, d_k)

        while t >= self.min_step:
            candidate = self.x_k + t * d_k
            candidate = project(candidate)
            candidate_f = function(candidate)

            if candidate_f <= fk + self.armijo_rho * t * gkdk:
                x_new = candidate
                fk = candidate_f
                break

            t *= self.armijo_beta
        else:
            return self.x_k.copy(), "min_step"

        s_k = x_new - self.x_k
        g_new = calculate_gradient(x_new)
        y_k = g_new - self.g_k

        # provera kriterijuma
        if np.linalg.norm(g_new) < self.grad_eps:
            return self.x_k.copy(), "grad_eps"
        if np.linalg.norm(s_k) < self.x_eps:
            return self.x_k.copy(), "x_eps"
        if abs(fk - f_prev) < self.f_eps:
            return self.x_k.copy(), "f_eps"

        ys = np.dot(y_k, s_k)
        if ys > 1e-12:
            self.s_history.append(s_k)
            self.y_history.append(y_k)
            if len(self.s_history) > self.memory:
                self.s_history.pop(0)
                self.y_history.pop(0)

        self.x_k = project(x_new)
        self.g_k = g_new

        return self.x_k.copy(), False
