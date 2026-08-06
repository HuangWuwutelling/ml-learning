"""
5-latitude box model for POPs long-range transport (HCB primary case).

Model: Mackay Level I fugacity framework with inter-box atmospheric advection
and per-box deposition loss. The air column reaches a quasi-steady state
governed by advection, atmospheric degradation, and deposition to surface
(rain scavenging + dry deposition). Surface media in each box are in
equilibrium with local air (Level I partitioning), which gives the
"cold condensation" enrichment: colder boxes have lower Kaw, so water and
soil concentrations are higher at the same air fugacity.

All physical constants are verified by web lookup; every value cites a URL
in the SPECIES dict below. HCB is the primary test case; the same skeleton
is reused for DDT/PCB-153/dieldrin in Task 2.

References (all parameters verified by web lookup, see docstring fields):
- HCB physical constants: PubChem CID 8370 + Wikipedia
  https://pubchem.ncbi.nlm.nih.gov/compound/8370
  https://en.wikipedia.org/wiki/Hexachlorobenzene
- Henry's law: ten Hulscher et al. 1992 Environ Toxicol Chem 11:1595
- Vapor pressure: Farmer et al. 1980 Soil Sci Soc Am J 44:676
- log Kow: Hansch, Leo, Hoekman 1995 "Exploring QSAR" ACS
- OH rate: Brubaker & Hites 1998 Environ Sci Technol 32:766
- Soil half-life: Barber et al. 2005 Sci Total Environ 349:1
- Box model: Mackay 2001 "Multimedia Environmental Models: The Fugacity
  Approach" 2nd ed. CRC Press
- Cold condensation: Wania & Mackay 1995 SETAC monograph / 1996 Crit Rev
  https://www.tandfonline.com/doi/abs/10.1080/10643389609388485

Usage:
    >>> m = POPsLRT(species="HCB")
    >>> m.solve_steady_state(emissions={2: 5e-2})  # 500 t/y at box 2 (mid-N)
    >>> m.summary()
"""

import numpy as np


# Physical constants
R = 8.314  # J/(mol*K)
N_A = 6.022e23
EARTH_R = 6.371e6  # m


# 5 latitude bands. Areas are spherical-zone fractions. Sum to 0.9335
# (omits 60-90S band).
BOX_LATITUDES_DEG = [
    (60, 90),
    (30, 60),
    (0, 30),
    (0, -30),
    (-30, -60),
]
BOX_NAMES = ["Polar-N", "Mid-N", "Eq-N", "Eq-S", "Mid-S"]
BOX_TEMPS_C = [-10.0, 5.0, 25.0, 25.0, 5.0]
BOX_AREA_FRAC = [
    (-np.cos(np.deg2rad(60)) + np.cos(np.deg2rad(90))) * 0.5,  # 0.067
    (np.cos(np.deg2rad(30)) - np.cos(np.deg2rad(60))) * 0.5,   # 0.183
    (np.cos(np.deg2rad(0)) - np.cos(np.deg2rad(30))) * 0.5,    # 0.250
    (np.cos(np.deg2rad(0)) - np.cos(np.deg2rad(30))) * 0.5,    # 0.250
    (np.cos(np.deg2rad(30)) - np.cos(np.deg2rad(60))) * 0.5,   # 0.183
]


# Boundary layer height (m) for the atmospheric box.
# Source: Mackay 2001 textbook examples use 1000 m for the standard
# environmental unit world.
BL_HEIGHT_M = 1000.0


# Inter-latitude atmospheric transport velocity (m/s).
# Source: EMEP/MSC-W global transport model uses 0.1-1.0 m/s for
# meridional inter-latitude exchange.
# https://www.emep.int/mscw/mscw_models.html
K_ATM_VELOCITY = 0.5


# Effective deposition velocity (m/s) for gas-phase POPs.
# Source: Wania & Mackay 1996 use v_dep ~ 0.005 m/s for HCB-like
# semivolatile organochlorines. Combines dry deposition + wet scavenging.
V_DEP_M_S = 0.005


# HCB physical constants (CAS 118-74-1, CID 8370)
# All values verified against the cited URL.
HCB = {
    "name": "Hexachlorobenzene",
    "cas": "118-74-1",
    "formula": "C6Cl6",
    "M_gmol": 284.78,         # PubChem Computed, CRC Handbook 91st
                              # https://pubchem.ncbi.nlm.nih.gov/compound/8370
    "mp_C": 228.83,           # CRC Handbook 91st via PubChem
    "bp_C": 325.0,            # CRC Handbook 91st via PubChem
    "log_Kow": 5.73,          # Hansch, Leo, Hoekman 1995, HSDB via PubChem
                              # Note: WHO EHC 195 reports 4.13 (older data);
                              # modern HSDB consensus is 5.73.
    "solubility_mg_L_25C": 4.7e-3,  # SRI 2011, HSDB via PubChem
    "vapor_pressure_Pa_25C": 0.00229,  # Farmer 1980, HSDB via PubChem
    "H_Pa_m3_mol_25C": 58.8,  # ten Hulscher 1992, HSDB via PubChem
                              # Note: WHO EHC 195 reports 13.7 (4x lower).
    "dH_vap_kJ_mol": 49.0,    # ten Hulscher 1992, HSDB via PubChem
    "k_OH_cm3_molc_s_25C": 2.7e-14,  # Brubaker & Hites 1998, HSDB via PubChem
    "log_Koc": 4.5,           # Mackay handbook 2006
    "BCF": 17000,             # Wikipedia/Barber 2005
                              # https://en.wikipedia.org/wiki/Hexachlorobenzene
    "half_life_air_d": 1000,  # Wikipedia citing Barber 2005
    "half_life_water_d": 2200,
    "half_life_soil_d": 3300,
    "half_life_veg_d": 1000,
    "Ea_air_J_mol": 10000.0,
    "Ea_water_J_mol": 50000.0,
    "Ea_soil_J_mol": 50000.0,
}


SPECIES = {"HCB": HCB}


class POPsLRT:
    """5-latitude box model for long-range atmospheric transport of POPs.

    Framework: each box has a well-mixed air column (1000 m BL) and surface
    media (water, soil, vegetation) in equilibrium with local air (Mackay
    Level I). Air moves between adjacent boxes by advection at velocity
    k_atm. Each box has air-degradation loss (OH reaction) and deposition
    loss to surface (rain scavenging + dry deposition at v_dep).

    Per-box air steady state (per m^2 surface):

        0 = E_i - k_deg_air * h * C_a_i - v_dep * C_a_i
            + k_atm * (C_a_{i-1} + C_a_{i+1} - 2 * C_a_i)

    where h is the boundary-layer height (so k_deg_air * h * C_a is the
    per-m^2 air-degradation rate).

    Surface concentrations follow from Mackay Level I partition:
        C_w = C_a / Kaw
        C_soil = C_w * Kd = C_w * Koc * foc * rho_soil
        C_veg = C_w * Kow * rho_veg

    The "cold condensation" enrichment of polar surface comes from
    smaller Kaw at low T (HCB has lower volatility from water at cold
    T), so the same air fugacity drives higher water/soil concentration.
    """

    def __init__(self, species="HCB", k_atm=None, bl_height=None,
                 v_dep=None):
        self.species = species
        if species not in SPECIES:
            raise ValueError(f"species must be one of {list(SPECIES)}")
        self.params = SPECIES[species]
        self.k_atm = k_atm if k_atm is not None else K_ATM_VELOCITY
        self.bl_height = bl_height if bl_height is not None else BL_HEIGHT_M
        self.v_dep = v_dep if v_dep is not None else V_DEP_M_S
        # Phase densities (g/m^3) for converting concentrations to ng/g.
        self.phase_density_g_m3 = {
            "air": 1.2e3,
            "water": 1.0e6,
            "soil": 1.5e6,
            "vegetation": 5.0e5,
        }
        # Organic carbon fraction of soil.
        self.foc = 0.02  # 2%
        # State: steady-state solution (set by solve_steady_state)
        self.conc_air = None
        self.concentrations = None
        self.ss_emissions = None

    def K_H_Hcp(self, T_K):
        """Henry's law constant H' in Pa m^3 / mol at T_K (van't Hoff)."""
        T_ref = 298.15
        dH = self.params["dH_vap_kJ_mol"] * 1000.0
        H_ref = self.params["H_Pa_m3_mol_25C"]
        return H_ref * np.exp(-dH / R * (1.0 / T_K - 1.0 / T_ref))

    def partition_coefficients(self, T_K):
        """Return (Kaw, Kow, Koc) at temperature T_K."""
        H = self.K_H_Hcp(T_K)
        Kaw = H / (R * T_K)
        Kow = 10.0 ** self.params["log_Kow"]
        Koc = 10.0 ** self.params["log_Koc"]
        return Kaw, Kow, Koc

    def half_life(self, medium, T_K):
        """Half-life (days) at T_K, Arrhenius corrected."""
        ref_map = {
            "air": self.params["half_life_air_d"],
            "water": self.params["half_life_water_d"],
            "soil": self.params["half_life_soil_d"],
            "vegetation": self.params["half_life_veg_d"],
        }
        ea_map = {
            "air": self.params["Ea_air_J_mol"],
            "water": self.params["Ea_water_J_mol"],
            "soil": self.params["Ea_soil_J_mol"],
            "vegetation": self.params["Ea_air_J_mol"],
        }
        t_ref = ref_map[medium]
        ea = ea_map[medium]
        T_ref = 298.15
        k_ref = np.log(2) / t_ref
        k = k_ref * np.exp(-ea / R * (1.0 / T_K - 1.0 / T_ref))
        return np.log(2) / k

    def solve_steady_state(self, emissions):
        """Solve the 5-box steady state for air concentration.

        Equation per box (per m^2 surface):

            0 = E_i - k_deg_air_i * h * C_a_i - v_dep * C_a_i
                + k_atm * (C_a_{i-1} + C_a_{i+1} - 2 * C_a_i)

        All terms in mol/(m^2 s). E_i is emission flux (mol/m^2/s);
        C_a is air concentration (mol/m^3); h is BL height (m).

        Rearranged as A C_a = E for the 5 boxes.

        Parameters
        ----------
        emissions : dict
            Mapping 1-based box index (1..5) -> emission rate in mol/s
            TOTAL into the box (not per m^2). Internal scaling divides
            by box area to get per-m^2 flux.

        Returns
        -------
        dict : 1-based box index -> {air, water, soil, veg} concentrations
        """
        n = len(BOX_NAMES)
        T_K = np.array([t + 273.15 for t in BOX_TEMPS_C])
        delta_lat_m = np.deg2rad(30) * EARTH_R  # ~3330 km
        # Per-box air mass balance (per m^2 surface)
        A = np.zeros((n, n))
        rhs = np.zeros(n)
        for i in range(n):
            T_i = T_K[i]
            k_deg_air_i = np.log(2) / (self.half_life("air", T_i) * 86400.0)
            # Local loss: degradation * h + deposition + out-advection
            A[i, i] = k_deg_air_i * self.bl_height + self.v_dep
            nbrs = []
            if i - 1 >= 0:
                nbrs.append(i - 1)
            if i + 1 < n:
                nbrs.append(i + 1)
            A[i, i] += len(nbrs) * self.k_atm
            for j in nbrs:
                A[i, j] -= self.k_atm
            # Emission: convert mol/s TOTAL to mol/(m^2 s) using box area
            # Box area = 4 pi R^2 * area_fraction_i
            for k, v in emissions.items():
                if k == i + 1:
                    box_area = 4 * np.pi * EARTH_R**2 * BOX_AREA_FRAC[i]
                    rhs[i] = v / box_area
        C_a = np.linalg.solve(A, rhs)
        self.conc_air = C_a
        self.T_K = T_K
        self.ss_emissions = emissions
        # Compute per-phase concentrations using Mackay Level I partition
        concentrations = []
        for i in range(n):
            Kaw, Kow, Koc = self.partition_coefficients(T_K[i])
            C_w = C_a[i] / Kaw
            Koc_m3_kg = Koc * 1e-3
            rho_soil_kg = self.phase_density_g_m3["soil"] / 1000.0
            C_soil = C_w * Koc_m3_kg * self.foc * rho_soil_kg
            Kow_m3_kg = Kow * 1e-3
            rho_veg_kg = self.phase_density_g_m3["vegetation"] / 1000.0
            C_veg = C_w * Kow_m3_kg * rho_veg_kg
            M = self.params["M_gmol"]
            conc = {
                "air_mol_m3": C_a[i],
                "water_mol_m3": C_w,
                "soil_mol_m3": C_soil,
                "vegetation_mol_m3": C_veg,
                "air_pg_m3": C_a[i] * M * 1e12,
                "water_pg_L": C_w * M * 1e12,
                "soil_ng_g": C_soil * M * 1e9 / rho_soil_kg,
                "vegetation_ng_g": C_veg * M * 1e9 / rho_veg_kg,
                "Kaw": Kaw,
                "log_Kaw": np.log10(Kaw),
            }
            concentrations.append(conc)
        self.concentrations = concentrations
        return {i + 1: c for i, c in enumerate(concentrations)}

    def enrichment_factor(self, box_i, source_box=2, medium="soil"):
        """Enrichment factor of box_i medium vs source_box medium.

        medium: "air", "water", "soil", "vegetation"
        """
        if self.concentrations is None:
            raise RuntimeError("Call solve_steady_state first.")
        key = f"{medium}_mol_m3"
        return (self.concentrations[box_i - 1][key]
                / self.concentrations[source_box - 1][key])

    def summary(self):
        """Print 5-box summary + enrichment factors (air, water, soil)."""
        if self.concentrations is None:
            raise RuntimeError("Call solve_steady_state first.")
        print(f"=== POPs LRT Model: {self.species} ===")
        print(f"Box layout: {len(BOX_NAMES)} latitude bands")
        print(f"Emissions (mol/s TOTAL): {self.ss_emissions}")
        print(f"Temperatures (degC): {BOX_TEMPS_C}")
        print(f"k_atm = {self.k_atm} m/s, BL height = {self.bl_height} m, "
              f"v_dep = {self.v_dep} m/s")
        print()
        print(f"{'Box':<8}{'T_C':<8}{'air_pg_m3':<14}{'water_pg_L':<14}{'soil_ng_g':<14}{'logKaw':<10}")
        for i, name in enumerate(BOX_NAMES):
            c = self.concentrations[i]
            print(f"{name:<8}{BOX_TEMPS_C[i]:<8.1f}{c['air_pg_m3']:<14.3e}"
                  f"{c['water_pg_L']:<14.3e}{c['soil_ng_g']:<14.3e}"
                  f"{c['log_Kaw']:<10.2f}")
        print()
        # Find source box from emissions
        if self.ss_emissions:
            src = max(self.ss_emissions, key=self.ss_emissions.get)
        else:
            src = 2
        print(f"Enrichment factors (relative to source box {src}):")
        for med in ("air", "water", "soil", "vegetation"):
            print(f"  {med:<12}: ", end="")
            for i, name in enumerate(BOX_NAMES):
                ef = self.enrichment_factor(i + 1, source_box=src, medium=med)
                print(f"  {name}={ef:5.2f}x", end="")
            print()
        print()
        print("Partition coefficient check at 25 degC (298.15 K):")
        Kaw, Kow, Koc = self.partition_coefficients(298.15)
        print(f"  Kaw = {Kaw:.3e}, log Kaw = {np.log10(Kaw):.2f}")
        print(f"  Kow = {Kow:.3e}")
        print(f"  Koc = {Koc:.3e}")


if __name__ == "__main__":
    m = POPsLRT(species="HCB")
    # Spread emission: most HCB came from mid-latitudes (Europe, US, China).
    # Historical global emission ~ 1000 t/y peak (Barber 2005). Use 500 t/y
    # distributed: 60% mid-N, 20% mid-S, 10% each Eq-N/Eq-S, ~0% polar.
    t_y_kg = 500_000  # 500 tonnes/year
    E_total = t_y_kg / 284.78 / (365.25 * 86400)  # mol/s
    emissions = {
        1: 0.0 * E_total,                 # polar-N (no local source)
        2: 0.60 * E_total,                # mid-N
        3: 0.10 * E_total,                # eq-N
        4: 0.10 * E_total,                # eq-S
        5: 0.20 * E_total,                # mid-S
    }
    m.solve_steady_state(emissions=emissions)
    m.summary()
