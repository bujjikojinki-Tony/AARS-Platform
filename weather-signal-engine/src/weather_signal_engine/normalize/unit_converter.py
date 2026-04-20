class UnitConverter:
    @staticmethod
    def c_to_f(value_c: float) -> float:
        return (value_c * 9 / 5) + 32

    @staticmethod
    def f_to_c(value_f: float) -> float:
        return (value_f - 32) * 5 / 9
