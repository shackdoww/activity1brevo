class Grade:
    def __init__(self, code, subject, units, grade):
        self.code = str(code).strip()
        self.subject = str(subject).strip()
        self.units = float(units)
        self.grade = float(grade)

    def weighted_points(self):
        return self.units * self.grade

    def to_list(self):
        return [
            self.code,
            self.subject,
            f"{self.units:g}",
            f"{self.grade:.2f}",
        ]


class Student:
    def __init__(self, name, program_year, academic_period="", grades=None):
        self.name = str(name).strip()
        self.program_year = str(program_year).strip()
        self.academic_period = str(academic_period).strip()
        self.grades = grades if grades else []

    def add_grade(self, grade):
        if not isinstance(grade, Grade):
            raise TypeError("grade must be a Grade object")
        self.grades.append(grade)

    def total_units(self):
        return sum(grade.units for grade in self.grades)

    def weighted_average(self):
        total_units = self.total_units()
        if total_units == 0:
            return None
        total_points = sum(grade.weighted_points() for grade in self.grades)
        return total_points / total_units

    def to_dict(self):
        return {
            "name": self.name,
            "program_year": self.program_year,
            "academic_period": self.academic_period,
            "grades": [grade.to_list() for grade in self.grades],
        }
