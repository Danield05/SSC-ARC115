import pytest

from app.modules.patients.bmi import bmi, bmi_category


@pytest.mark.parametrize(
    "weight,height,expected,category",
    [
        (70, 170, 24.2, "Normal"),
        (50, 170, 17.3, "Bajo peso"),
        (80, 170, 27.7, "Sobrepeso"),
        (90, 170, 31.1, "Obesidad grado I"),
        (105, 170, 36.3, "Obesidad grado II"),
        (125, 170, 43.3, "Obesidad grado III"),
    ],
)
def test_bmi_and_category_for_adults(weight, height, expected, category):
    value = bmi(weight, height)
    assert value == expected
    assert bmi_category(value, 40) == category


@pytest.mark.parametrize(
    "value,category", [(18.5, "Normal"), (25.0, "Sobrepeso"), (30.0, "Obesidad grado I")]
)
def test_category_limits_belong_to_upper_range(value, category):
    assert bmi_category(value, 30) == category


def test_adult_limit_is_18():
    assert bmi_category(24.2, 18) == "Normal"
    assert bmi_category(24.2, None) is None


@pytest.mark.parametrize(
    "value,age,sex,category",
    [
        (15.0, 10, "M", "Normal"),  # entre -2 y +1 DE
        (21.0, 10, "M", "Sobrepeso"),  # +1 DE = 19.429, +2 DE = 23.134
        (24.0, 10, "M", "Obesidad"),
        (13.0, 10, "M", "Delgadez"),  # -3 DE = 12.542, -2 DE = 13.666
        (12.0, 10, "M", "Delgadez severa"),
        (24.2, 17, "M", "Normal"),  # +1 DE a los 17 años: 24.649 (niños) y 24.603 (niñas)
        (24.7, 17, "M", "Sobrepeso"),
        (24.7, 17, "F", "Sobrepeso"),
    ],
)
def test_children_use_who_zscore_cutoffs(value, age, sex, category):
    assert bmi_category(value, age, sex) == category


def test_same_value_is_classified_by_age_not_adult_cutoffs():
    # Con el corte de adultos 24.0 sería «Normal»; a los 9 años es obesidad.
    assert bmi_category(24.0, 9, "M") == "Obesidad"
    assert bmi_category(24.0, 30, "M") == "Normal"


def test_no_category_without_sex_or_under_5():
    assert bmi_category(15.0, 10, None) is None
    assert bmi_category(15.0, 10, "") is None
    assert bmi_category(15.0, 4, "F") is None
    assert bmi_category(15.0, 0, "M") is None


def test_no_height_gives_none():
    assert bmi(70, None) is None
    assert bmi(70, 0) is None
    assert bmi_category(None, 40) is None
