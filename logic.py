"""
Логика принятия решения о выборе хирургической тактики
при злокачественных новообразованиях почек у детей.

Основано на данных диссертационного исследования.
"""

from dataclasses import dataclass, field
from typing import List


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
    access: str = ""                  # "Лапароскопический" | "Открытый"
    confidence: str = ""              # "Стандартные показания" | "Расширенные показания" | "Экспертный уровень"
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def calc_bsa(weight_kg: float, height_cm: float) -> float:
    """Расчёт площади поверхности тела по формуле Мостеллера."""
    if weight_kg <= 0 or height_cm <= 0:
        return 0.0
    return round(((weight_kg * height_cm) / 3600) ** 0.5, 2)


# =============================================================
# Пороговые значения (из диссертационного исследования)
# =============================================================
NEPHRECTOMY_LAP_MAX_VOLUME = 200      # см³
RESECTION_LAP_MAX_VOLUME = 100        # см³
MIN_RESIDUAL_PARENCHYMA = 66          # %
MIN_MARGIN_MM = 5                     # мм


def decide_operation_type(pt: PatientData) -> tuple[str, List[str]]:
    """
    ШАГ 1: Определение типа операции (нефрэктомия / резекция).
    """
    reasons = []

    # Абсолютные показания к нефрэктомии
    if pt.hilum_invasion:
        reasons.append("❌ Инвазия в структуры ворот почки")
        return "Нефрэктомия", reasons

    if pt.tumor_thrombus:
        reasons.append("❌ Опухолевый тромбоз")
        return "Нефрэктомия", reasons

    if pt.vessel_invasion:
        reasons.append("❌ Инвазия в магистральные сосуды")
        return "Нефрэктомия", reasons

    # Условия для резекции
    if pt.residual_parenchyma_pct < MIN_RESIDUAL_PARENCHYMA:
        reasons.append(
            f"❌ Сохраняемая паренхима ({pt.residual_parenchyma_pct}%) "
            f"меньше минимального порога {MIN_RESIDUAL_PARENCHYMA}%"
        )
        return "Нефрэктомия", reasons

    if pt.margin_5mm_possible == "Нет":
        reasons.append(f"❌ Невозможен отступ ≥{MIN_MARGIN_MM} мм от края опухоли")
        return "Нефрэктомия", reasons

    # Центральная локализация чаще требует нефрэктомии
    if pt.localization == "Центральная":
        reasons.append("⚠️ Центральная локализация — чаще требует нефрэктомии")
        return "Нефрэктомия", reasons

    # Смешанная локализация — тоже осторожно
    if pt.localization == "Смешанная":
        reasons.append("⚠️ Смешанная локализация (вовлечение центра и полюса)")
        return "Нефрэктомия", reasons

    # Все условия для резекции соблюдены
    reasons.append("✅ Периферическая локализация опухоли")
    reasons.append(f"✅ Сохраняемая паренхима ≥{MIN_RESIDUAL_PARENCHYMA}%")
    if pt.margin_5mm_possible == "Да":
        reasons.append(f"✅ Возможен отступ ≥{MIN_MARGIN_MM} мм")

    return "Резекция почки", reasons


def decide_access_nephrectomy(pt: PatientData) -> tuple[str, str, List[str], List[str], List[str]]:
    """
    ШАГ 2 (для нефрэктомии): Определение доступа.
    Возвращает: access, confidence, pros, cons, warnings
    """
    pros, cons, warnings = [], [], []

    # Абсолютные противопоказания к лапароскопии
    if pt.tumor_thrombus:
        cons.append("❌ Опухолевый тромбоз — противопоказание к лапароскопии")
        return "Открытый", "", pros, cons, warnings

    if pt.vessel_invasion:
        cons.append("❌ Инвазия в магистральные сосуды")
        return "Открытый", "", pros, cons, warnings

    if pt.side == "Билатеральная":
        cons.append("❌ Билатеральное поражение")
        return "Открытый", "", pros, cons, warnings

    # Оценка объёма
    if pt.tumor_volume > NEPHRECTOMY_LAP_MAX_VOLUME:
        cons.append(
            f"❌ Объём опухоли ({pt.tumor_volume:.1f} см³) превышает "
            f"рекомендованный порог для лапароскопии ({NEPHRECTOMY_LAP_MAX_VOLUME} см³)"
        )
        return "Открытый", "", pros, cons, warnings
    else:
        pros.append(
            f"✅ Объём опухоли ({pt.tumor_volume:.1f} см³) — в пределах "
            f"рекомендованного порога (≤{NEPHRECTOMY_LAP_MAX_VOLUME} см³)"
        )

    # Дополнительные положительные факторы
    if pt.localization == "Полюсная":
        pros.append("✅ Периферическая локализация (благоприятно)")
    if pt.has_cystic:
        pros.append("✅ Наличие кистозного компонента (допустимо в расширенных критериях)")
        warnings.append(
            "⚠️ При кистозном компоненте требуется особая осторожность "
            "при мобилизации для предотвращения разрыва капсулы"
        )
    if pt.chemo_response == "Слабый":
        pros.append("✅ Слабый ответ на ПХТ — допустимо в расширенных критериях")

    # Определение уровня рекомендации
    is_extended = (
        pt.has_cystic
        or pt.localization == "Полюсная"
        or pt.chemo_response == "Слабый"
    )

    if is_extended:
        confidence = "Расширенные критерии (за пределами протокола SIOP-RTSG UMBRELLA 2016)"
        warnings.append(
            "⚠️ Данный пациент отвечает расширенным критериям минимально инвазивного "
            "доступа — рекомендуется выполнение в специализированном центре."
        )
    else:
        confidence = "Стандартные показания (в соответствии с протоколом SIOP-RTSG UMBRELLA 2016)"

    return "Лапароскопический", confidence, pros, cons, warnings


def decide_access_resection(pt: PatientData) -> tuple[str, str, List[str], List[str], List[str]]:
    """
    ШАГ 2 (для резекции): Определение доступа.
    """
    pros, cons, warnings = [], [], []

    # Абсолютные противопоказания
    if pt.distant_mets:
        cons.append("❌ Наличие отдалённых метастазов")
    if pt.lymphadenopathy:
        cons.append("❌ Наличие лимфаденопатии")
    if pt.localization != "Полюсная":
        cons.append(f"❌ Локализация «{pt.localization}» — требуется полюсная")

    # Оценка объёма
    if pt.tumor_volume > RESECTION_LAP_MAX_VOLUME:
        cons.append(
            f"❌ Объём опухоли ({pt.tumor_volume:.1f} см³) превышает "
            f"рекомендованный порог для лапароскопической резекции "
            f"({RESECTION_LAP_MAX_VOLUME} см³)"
        )
    else:
        pros.append(
            f"✅ Объём опухоли ({pt.tumor_volume:.1f} см³) — в пределах "
            f"рекомендованного порога (≤{RESECTION_LAP_MAX_VOLUME} см³)"
        )

    # Если есть противопоказания
    if cons:
        return "Открытый", "", pros, cons, warnings

    # Положительные факторы
    pros.append("✅ Периферическая (полюсная) локализация опухоли")
    pros.append(f"✅ Сохраняемая паренхима — {pt.residual_parenchyma_pct}% (≥{MIN_RESIDUAL_PARENCHYMA}%)")
    if pt.margin_5mm_possible == "Да":
        pros.append(f"✅ Возможность отступа ≥{MIN_MARGIN_MM} мм от края опухоли")

    warnings.append(
        "⚠️ При невозможности интраоперационного определения границ резекции "
        "(в том числе при интраоперационном УЗИ) показана конверсия в открытый доступ."
    )
    warnings.append(
        "⚠️ Требуется срочное гистологическое исследование краёв резекции при "
        "сомнительном макроскопическом статусе."
    )

    confidence = "Показания к лапароскопической резекции почки"

    return "Лапароскопический", confidence, pros, cons, warnings


def make_decision(pt: PatientData) -> Decision:
    """Главная функция принятия решения."""
    decision = Decision()

    # Шаг 1: тип операции
    operation, op_reasons = decide_operation_type(pt)
    decision.operation_type = operation

    # Шаг 2: доступ
    if operation == "Нефрэктомия":
        access, confidence, pros, cons, warnings = decide_access_nephrectomy(pt)
    else:
        access, confidence, pros, cons, warnings = decide_access_resection(pt)

    decision.access = access
    decision.confidence = confidence
    decision.pros = op_reasons + pros
    decision.cons = cons
    decision.warnings = warnings

    return decision
