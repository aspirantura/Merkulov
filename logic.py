"""
Логика принятия решения о выборе хирургической тактики
при злокачественных новообразованиях почек у детей.

Основано на данных диссертационного исследования.
Версия 2.0 — с трёхуровневой системой рекомендаций и учётом консилиума.
"""

from dataclasses import dataclass, field
from typing import List


# =============================================================
# Уровни рекомендаций
# =============================================================
LEVEL_STANDARD = "Стандартные показания"
LEVEL_EXTENDED = "Расширенные показания — требуется мультидисциплинарный консилиум"
LEVEL_CONTRAINDICATED = "Противопоказано"


@dataclass
class PatientData:
    """Входные данные пациента и опухоли."""
    # Пациент
    age_months: float
    weight_kg: float
    height_cm: float

    # Опухоль
    tumor_volume: float               # см³, после ПХТ
    localization: str                 # "Полюсная" | "Центральная" | "Смешанная"
    side: str                         # "Правая" | "Левая" | "Билатеральная"
    has_cystic: bool
    hilum_invasion: bool              # инвазия в ворота почки
    vessel_invasion: bool             # инвазия в магистральные сосуды
    tumor_thrombus: bool              # опухолевый тромбоз
    chemo_response: str               # "Хороший" | "Слабый" | "Нет данных"

    # Стадирование
    stage: str                        # "I" | "II" | "III" | "IV" | "V"
    distant_mets: bool
    lymphadenopathy: bool

    # Анатомические условия
    residual_parenchyma_pct: float    # % сохраняемой паренхимы
    margin_5mm_possible: str          # "Да" | "Нет" | "Не оценивалось"


@dataclass
class Decision:
    """Результат принятия решения."""
    operation_type: str = ""          # "Нефрэктомия" | "Резекция почки"
    operation_level: str = ""         # Уровень рекомендации для типа операции
    access: str = ""                  # "Лапароскопический" | "Открытый"
    access_level: str = ""            # Уровень рекомендации для доступа
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    consilium_required: bool = False  # флаг: нужен ли консилиум


# =============================================================
# Пороговые значения (из диссертационного исследования)
# =============================================================
NEPHRECTOMY_LAP_MAX_VOLUME = 200      # см³
RESECTION_LAP_MAX_VOLUME = 100        # см³
MIN_RESIDUAL_PARENCHYMA = 66          # %
MIN_MARGIN_MM = 5                     # мм


def calc_bsa(weight_kg: float, height_cm: float) -> float:
    """Расчёт площади поверхности тела по формуле Мостеллера."""
    if weight_kg <= 0 or height_cm <= 0:
        return 0.0
    return round(((weight_kg * height_cm) / 3600) ** 0.5, 2)


# =============================================================
# ШАГ 1: Определение типа операции (нефрэктомия / резекция)
# =============================================================
def decide_operation_type(pt: PatientData):
    """
    Возвращает: operation_type, level, pros, cons, warnings
    """
    pros, cons, warnings = [], [], []

    # АБСОЛЮТНЫЕ противопоказания к резекции
    if pt.hilum_invasion:
        cons.append("Инвазия в структуры ворот почки — резекция технически невозможна")
        return "Нефрэктомия", LEVEL_STANDARD, pros, cons, warnings

    if pt.tumor_thrombus:
        cons.append("Опухолевый тромбоз — резекция противопоказана")
        return "Нефрэктомия", LEVEL_STANDARD, pros, cons, warnings

    if pt.vessel_invasion:
        cons.append("Инвазия в магистральные сосуды — резекция противопоказана")
        return "Нефрэктомия", LEVEL_STANDARD, pros, cons, warnings

    if pt.residual_parenchyma_pct < MIN_RESIDUAL_PARENCHYMA:
        cons.append(
            f"Сохраняемая паренхима ({pt.residual_parenchyma_pct}%) "
            f"меньше порога {MIN_RESIDUAL_PARENCHYMA}% — резекция нецелесообразна"
        )
        return "Нефрэктомия", LEVEL_STANDARD, pros, cons, warnings

    if pt.margin_5mm_possible == "Нет":
        cons.append(
            f"Невозможен отступ >={MIN_MARGIN_MM} мм от края опухоли — "
            f"резекция не обеспечит онкологической радикальности"
        )
        return "Нефрэктомия", LEVEL_STANDARD, pros, cons, warnings

    # Положительные факторы для резекции
    pros.append(f"Сохраняемая паренхима {pt.residual_parenchyma_pct}% (>={MIN_RESIDUAL_PARENCHYMA}%)")
    if pt.margin_5mm_possible == "Да":
        pros.append(f"Возможен отступ >={MIN_MARGIN_MM} мм от края опухоли")

    # Расширенные показания (требуют консилиума)
    if pt.localization == "Полюсная":
        pros.append("Периферическая (полюсная) локализация — оптимально для резекции")
        return "Резекция почки", LEVEL_STANDARD, pros, cons, warnings

    if pt.localization == "Центральная":
        warnings.append(
            "Центральная локализация опухоли — резекция технически сложна, "
            "но возможна при благоприятных анатомических условиях. "
            "Решение принимается мультидисциплинарным консилиумом."
        )
        return "Резекция почки", LEVEL_EXTENDED, pros, cons, warnings

    if pt.localization == "Смешанная":
        warnings.append(
            "Смешанная локализация (вовлечение полюса и центра) — резекция возможна, "
            "но требует индивидуальной оценки анатомических условий. "
            "Решение принимается мультидисциплинарным консилиумом."
        )
        return "Резекция почки", LEVEL_EXTENDED, pros, cons, warnings

    return "Резекция почки", LEVEL_STANDARD, pros, cons, warnings


# =============================================================
# ШАГ 2а: Определение доступа при нефрэктомии
# =============================================================
def decide_access_nephrectomy(pt: PatientData):
    """
    Возвращает: access, level, pros, cons, warnings
    """
    pros, cons, warnings = [], [], []

    # АБСОЛЮТНЫЕ противопоказания к лапароскопии
    if pt.tumor_thrombus:
        cons.append("Опухолевый тромбоз — абсолютное противопоказание к лапароскопии")
        return "Открытый", LEVEL_STANDARD, pros, cons, warnings

    if pt.vessel_invasion:
        cons.append("Инвазия в магистральные сосуды — противопоказание к лапароскопии")
        return "Открытый", LEVEL_STANDARD, pros, cons, warnings

    # Относительные факторы — требуют консилиума
    extended_flags = []

    if pt.tumor_volume > NEPHRECTOMY_LAP_MAX_VOLUME:
        cons.append(
            f"Объём опухоли ({pt.tumor_volume:.1f} см³) превышает "
            f"рекомендованный порог для лапароскопии ({NEPHRECTOMY_LAP_MAX_VOLUME} см³)"
        )
        return "Открытый", LEVEL_STANDARD, pros, cons, warnings
    else:
        pros.append(
            f"Объём опухоли ({pt.tumor_volume:.1f} см³) — в пределах "
            f"рекомендованного порога (<={NEPHRECTOMY_LAP_MAX_VOLUME} см³)"
        )

    # Проверка расширенных факторов
    if pt.side == "Билатеральная":
        extended_flags.append("билатеральное поражение")
        warnings.append(
            "Билатеральное поражение — лапароскопическая нефрэктомия возможна, "
            "но требует сложной хирургической тактики. Решение принимается консилиумом."
        )

    if pt.localization == "Полюсная":
        extended_flags.append("периферическая локализация")
        pros.append("Периферическая локализация опухоли (расширенные критерии)")

    if pt.has_cystic:
        extended_flags.append("кистозный компонент")
        pros.append("Наличие кистозного компонента (расширенные критерии)")
        warnings.append(
            "Кистозный компонент — требуется особая осторожность при мобилизации "
            "для предотвращения разрыва капсулы опухоли."
        )

    if pt.chemo_response == "Слабый":
        extended_flags.append("слабый ответ на ПХТ")
        pros.append("Слабый ответ на ПХТ (расширенные критерии)")

    if pt.distant_mets:
        extended_flags.append("отдалённые метастазы")
        warnings.append(
            "Наличие отдалённых метастазов — тактика согласовывается с онкологом; "
            "выбор доступа обсуждается на консилиуме."
        )

    # Определение уровня рекомендации
    if extended_flags:
        level = LEVEL_EXTENDED
        warnings.append(
            "Данный пациент отвечает расширенным критериям минимально инвазивного доступа "
            "(за пределами протокола SIOP-RTSG UMBRELLA 2016). Рекомендуется выполнение "
            "в специализированном центре с обязательным решением мультидисциплинарного консилиума."
        )
    else:
        level = LEVEL_STANDARD

    return "Лапароскопический", level, pros, cons, warnings


# =============================================================
# ШАГ 2б: Определение доступа при резекции
# =============================================================
def decide_access_resection(pt: PatientData):
    """
    Возвращает: access, level, pros, cons, warnings
    """
    pros, cons, warnings = [], [], []
    extended_flags = []

    # Проверка объёма
    if pt.tumor_volume > RESECTION_LAP_MAX_VOLUME:
        cons.append(
            f"Объём опухоли ({pt.tumor_volume:.1f} см³) превышает "
            f"рекомендованный порог для лапароскопической резекции "
            f"({RESECTION_LAP_MAX_VOLUME} см³)"
        )
        if pt.tumor_volume > 317:  # выше максимума в серии
            return "Открытый", LEVEL_STANDARD, pros, cons, warnings
        else:
            extended_flags.append("превышение порога объёма опухоли")
            warnings.append(
                f"Объём опухоли превышает стандартный порог, но находится в пределах "
                f"максимального опыта серии (до 317 см³). Возможно выполнение "
                f"в специализированном центре по решению консилиума."
            )
    else:
        pros.append(
            f"Объём опухоли ({pt.tumor_volume:.1f} см³) — в пределах "
            f"рекомендованного порога (<={RESECTION_LAP_MAX_VOLUME} см³)"
        )

    # Локализация
    if pt.localization == "Полюсная":
        pros.append("Периферическая (полюсная) локализация опухоли")
    else:
        extended_flags.append(f"{pt.localization.lower()} локализация")
        warnings.append(
            f"{pt.localization} локализация опухоли — лапароскопическая резекция "
            f"технически сложна. Решение принимается мультидисциплинарным консилиумом "
            f"с учётом опыта хирургической бригады."
        )

    # Билатеральное поражение
    if pt.side == "Билатеральная":
        extended_flags.append("билатеральное поражение")
        warnings.append(
            "Билатеральное поражение — лапароскопическая резекция возможна "
            "по решению консилиума с учётом опыта центра."
        )

    # Метастазы и лимфаденопатия
    if pt.distant_mets:
        extended_flags.append("отдалённые метастазы")
        warnings.append(
            "Наличие отдалённых метастазов — вопрос выбора доступа "
            "решается индивидуально на консилиуме."
        )

    if pt.lymphadenopathy:
        extended_flags.append("лимфаденопатия")
        warnings.append(
            "Лимфаденопатия — требуется адекватная лимфаденэктомия, "
            "выполнимость лапароскопически обсуждается на консилиуме."
        )

    # Положительные факторы
    pros.append(f"Сохраняемая паренхима — {pt.residual_parenchyma_pct}% (>={MIN_RESIDUAL_PARENCHYMA}%)")
    if pt.margin_5mm_possible == "Да":
        pros.append(f"Возможность отступа >={MIN_MARGIN_MM} мм от края опухоли")

    # Обязательные предостережения
    warnings.append(
        "При невозможности интраоперационного определения границ резекции "
        "(в том числе при интраоперационном УЗИ) показана конверсия в открытый доступ."
    )
    warnings.append(
        "Рекомендуется срочное гистологическое исследование краёв резекции "
        "при сомнительном макроскопическом статусе."
    )

    # Определение уровня рекомендации
    if extended_flags:
        level = LEVEL_EXTENDED
        warnings.insert(0,
            "Данный пациент отвечает расширенным показаниям к лапароскопической резекции. "
            "Обязательно решение мультидисциплинарного консилиума."
        )
    else:
        level = LEVEL_STANDARD

    return "Лапароскопический", level, pros, cons, warnings


# =============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# =============================================================
def make_decision(pt: PatientData) -> Decision:
    """Главная функция принятия решения."""
    decision = Decision()

    # Шаг 1: тип операции
    operation, op_level, op_pros, op_cons, op_warnings = decide_operation_type(pt)
    decision.operation_type = operation
    decision.operation_level = op_level

    # Шаг 2: доступ
    if operation == "Нефрэктомия":
        access, acc_level, acc_pros, acc_cons, acc_warnings = decide_access_nephrectomy(pt)
    else:
        access, acc_level, acc_pros, acc_cons, acc_warnings = decide_access_resection(pt)

    decision.access = access
    decision.access_level = acc_level
    decision.pros = op_pros + acc_pros
    decision.cons = op_cons + acc_cons
    decision.warnings = op_warnings + acc_warnings

    # Флаг консилиума
    decision.consilium_required = (
        op_level == LEVEL_EXTENDED or acc_level == LEVEL_EXTENDED
    )

    return decision
