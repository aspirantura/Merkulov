"""
Алгоритм выбора хирургической тактики при злокачественных
новообразованиях почек у детей.

Streamlit-приложение на основе данных диссертационного исследования.
"""

import streamlit as st
from logic import PatientData, make_decision, calc_bsa
from visuals import draw_kidney

# =============================================================
# Настройки страницы
# =============================================================
st.set_page_config(
    page_title="Алгоритм выбора хирургической тактики",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
# Заголовок
# =============================================================
st.title("Алгоритм выбора хирургической тактики")
st.markdown(
    "### при злокачественных новообразованиях почек у детей"
)
st.markdown(
    "*Электронный алгоритм разработан на основе данных диссертационного исследования "
    "и предназначен для поддержки принятия клинических решений детскими онкохирургами.*"
)
st.divider()

# =============================================================
# Ввод данных (боковая панель)
# =============================================================
with st.sidebar:
    st.header("📝 Ввод клинических данных")

    st.subheader("👶 Пациент")
    age = st.number_input("Возраст, мес", min_value=0.0, max_value=216.0, value=48.0, step=1.0)
    weight = st.number_input("Вес, кг", min_value=1.0, max_value=100.0, value=15.0, step=0.5)
    height = st.number_input("Рост, см", min_value=40.0, max_value=200.0, value=100.0, step=1.0)

    bsa = calc_bsa(weight, height)
    st.info(f"**ППТ (расчётная):** {bsa} м²")

    st.subheader("🎯 Опухоль")
    tumor_volume = st.number_input(
        "Объём опухоли после ПХТ, см³",
        min_value=0.0, max_value=5000.0, value=50.0, step=1.0,
        help="Объём опухоли на момент операции (после неоадъювантной ПХТ)"
    )
    localization = st.selectbox(
        "Локализация в почке",
        ["Полюсная", "Центральная", "Смешанная"]
    )
    side = st.selectbox(
        "Сторона поражения",
        ["Правая", "Левая", "Билатеральная"]
    )
    has_cystic = st.checkbox("Наличие кистозного компонента")
    hilum_invasion = st.checkbox("Инвазия в структуры ворот почки")
    vessel_invasion = st.checkbox("Инвазия в магистральные сосуды")
    tumor_thrombus = st.checkbox("Опухолевый тромбоз")
    chemo_response = st.selectbox(
        "Ответ на неоадъювантную ПХТ",
        ["Хороший", "Слабый", "Нет данных"]
    )

    st.subheader("📊 Стадирование")
    stage = st.selectbox("Стадия (SIOP)", ["I", "II", "III", "IV", "V"])
    distant_mets = st.checkbox("Отдалённые метастазы")
    lymphadenopathy = st.checkbox("Лимфаденопатия")

    st.subheader("🔬 Анатомические условия")
    residual_pct = st.slider(
        "Объём сохраняемой паренхимы, %",
        min_value=0, max_value=100, value=70, step=5,
        help="Оценка по данным волюметрии предоперационной КТ/МРТ"
    )
    margin_5mm = st.selectbox(
        "Возможность отступа ≥5 мм от края опухоли",
        ["Да", "Нет", "Не оценивалось"]
    )

    calculate_btn = st.button("🧮 Рассчитать рекомендацию", type="primary", use_container_width=True)

# =============================================================
# Расчёт и вывод
# =============================================================
if calculate_btn:
    patient = PatientData(
        age_months=age,
        weight_kg=weight,
        height_cm=height,
        tumor_volume=tumor_volume,
        localization=localization,
        side=side,
        has_cystic=has_cystic,
        hilum_invasion=hilum_invasion,
        vessel_invasion=vessel_invasion,
        tumor_thrombus=tumor_thrombus,
        chemo_response=chemo_response,
        stage=stage,
        distant_mets=distant_mets,
        lymphadenopathy=lymphadenopathy,
        residual_parenchyma_pct=residual_pct,
        margin_5mm_possible=margin_5mm,
    )

    decision = make_decision(patient)

    # Основной результат
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📋 Рекомендация")

        # Тип операции
        if decision.operation_type == "Резекция почки":
            st.success(f"**Тип операции:** {decision.operation_type} 🌱")
        else:
            st.warning(f"**Тип операции:** {decision.operation_type}")

        # Доступ
        if decision.access == "Лапароскопический":
            st.success(f"**Доступ:** {decision.access} 🔬")
        else:
            st.warning(f"**Доступ:** {decision.access} ⚕️")

        # Уровень рекомендации
        if decision.confidence:
            st.info(f"**Уровень рекомендации:** {decision.confidence}")

    with col2:
        st.header("🖼️ Схема")
        fig = draw_kidney(localization, side, has_cystic)
        st.pyplot(fig)

    st.divider()

    # Обоснование
    col_pros, col_cons = st.columns(2)

    with col_pros:
        st.subheader("✅ Факторы в пользу выбора")
        if decision.pros:
            for p in decision.pros:
                st.markdown(f"- {p}")
        else:
            st.markdown("*—*")

    with col_cons:
        st.subheader("❌ Противопоказания / ограничения")
        if decision.cons:
            for c in decision.cons:
                st.markdown(f"- {c}")
        else:
            st.markdown("*Противопоказаний не выявлено*")

    # Предостережения
    if decision.warnings:
        st.divider()
        st.subheader("⚠️ Предостережения и требования")
        for w in decision.warnings:
            st.warning(w)

    st.divider()

    # Сводная таблица параметров
    with st.expander("📊 Введённые параметры"):
        st.write(f"**Возраст:** {age} мес | **Вес:** {weight} кг | **Рост:** {height} см | **ППТ:** {bsa} м²")
        st.write(f"**Объём опухоли:** {tumor_volume} см³ | **Локализация:** {localization} | **Сторона:** {side}")
        st.write(f"**Кистозный компонент:** {'Да' if has_cystic else 'Нет'}")
        st.write(f"**Инвазия в ворота:** {'Да' if hilum_invasion else 'Нет'}")
        st.write(f"**Инвазия в сосуды:** {'Да' if vessel_invasion else 'Нет'}")
        st.write(f"**Тромбоз:** {'Да' if tumor_thrombus else 'Нет'}")
        st.write(f"**Ответ на ПХТ:** {chemo_response}")
        st.write(f"**Стадия:** {stage} | **Метастазы:** {'Да' if distant_mets else 'Нет'} | **ЛАП:** {'Да' if lymphadenopathy else 'Нет'}")
        st.write(f"**Сохраняемая паренхима:** {residual_pct}% | **Отступ ≥5 мм:** {margin_5mm}")

else:
    st.info("👈 Введите клинические данные в левой панели и нажмите «Рассчитать рекомендацию»")

    st.divider()

    st.markdown("""
    ### ℹ️ О калькуляторе

    Настоящий алгоритм предназначен для **поддержки принятия клинических решений**
    при выборе хирургической тактики у детей со злокачественными новообразованиями почек.

    **Основные критерии, реализованные в алгоритме:**

    - **Лапароскопическая нефрэктомия** — объём опухоли после ПХТ до 200 см³,
      допустимы периферическая локализация, кистозный компонент, слабый ответ на ПХТ.
    - **Лапароскопическая резекция почки** — периферическая (полюсная) локализация,
      объём опухоли до 100 см³, сохранение ≥66% паренхимы, отступ ≥5 мм.

    **Абсолютные противопоказания к лапароскопии:**
    - опухолевый тромбоз;
    - инвазия в магистральные сосуды;
    - билатеральное поражение (для нефрэктомии).

    ---

    ⚠️ **Внимание:** окончательное решение о выборе хирургической тактики принимается
    врачом на основании комплексной оценки клинической ситуации.
    Данный алгоритм не заменяет клинического суждения специалиста.
    """)

# =============================================================
# Футер
# =============================================================
st.divider()
st.caption(
    "🎓 Алгоритм разработан на основе диссертационного исследования, выполненного "
    "в отделении онкологии и детской хирургии ФГБУ «НМИЦ ДГОИ им. Дмитрия Рогачева» "
    "Минздрава России."
)
