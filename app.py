import streamlit as st
import pandas as pd
import datetime
from math import pow

# Настройка страницы
st.set_page_config(
    page_title="Кредитный калькулятор",
    layout="wide"
)

# Заголовок приложения
st.title("Кредитный калькулятор")
st.markdown("---")

# Инициализация состояния сеанса для истории расчётов
if "calculation_history" not in st.session_state:
    st.session_state.calculation_history = []


# Функция для расчёта аннуитетного платежа
def calculate_annuity_payment(amount, rate, months):
    """
    Расчёт аннуитетного платежа
    amount: сумма кредита
    rate: годовая процентная ставка (в %)
    months: срок кредита в месяцах
    """
    monthly_rate = rate / 100 / 12
    if monthly_rate == 0:
        return amount / months
    annuity_coef = monthly_rate * pow(1 + monthly_rate, months) / (pow(1 + monthly_rate, months) - 1)
    return amount * annuity_coef


# Функция для расчёта графика аннуитетных платежей
def calculate_annuity_schedule(amount, rate, months, start_date=None):
    """
    Расчёт графика аннуитетных платежей
    """
    monthly_payment = calculate_annuity_payment(amount, rate, months)
    monthly_rate = rate / 100 / 12

    schedule = []
    remaining_balance = amount

    for month in range(1, months + 1):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment

        if month == months:
            principal_payment = remaining_balance
            monthly_payment = remaining_balance + interest_payment

        schedule.append({
            "Номер платежа": month,
            "Остаток долга на начало": remaining_balance,
            "Ежемесячный платёж": monthly_payment,
            "Процентная часть": interest_payment,
            "Долговая часть": principal_payment,
            "Остаток долга на конец": remaining_balance - principal_payment
        })

        remaining_balance -= principal_payment

        # Округление для избежания погрешностей
        if remaining_balance < 0:
            remaining_balance = 0

    return pd.DataFrame(schedule), monthly_payment


# Функция для расчёта графика дифференцированных платежей
def calculate_differentiated_schedule(amount, rate, months, start_date=None):
    """
    Расчёт графика дифференцированных платежей
    """
    monthly_rate = rate / 100 / 12
    principal_payment_fixed = amount / months

    schedule = []
    remaining_balance = amount

    for month in range(1, months + 1):
        interest_payment = remaining_balance * monthly_rate
        monthly_payment = principal_payment_fixed + interest_payment

        schedule.append({
            "Номер платежа": month,
            "Остаток долга на начало": remaining_balance,
            "Ежемесячный платёж": monthly_payment,
            "Процентная часть": interest_payment,
            "Долговая часть": principal_payment_fixed,
            "Остаток долга на конец": remaining_balance - principal_payment_fixed
        })

        remaining_balance -= principal_payment_fixed

        if remaining_balance < 0:
            remaining_balance = 0

    return pd.DataFrame(schedule), principal_payment_fixed


# Боковая панель для ввода данных
with st.sidebar:
    st.header("Параметры кредита")

    # Считывание суммы кредита
    loan_amount = st.number_input(
        "Сумма кредита (руб)",
        min_value=1000.0,
        max_value=100000000.0,
        value=1000000.0,
        step=10000.0,
        format="%.2f",
        help="Введите сумму кредита в рублях"
    )

    # Считывание процентной ставки
    interest_rate = st.number_input(
        "Процентная ставка (% годовых)",
        min_value=0.0,
        max_value=100.0,
        value=12.0,
        step=0.1,
        format="%.2f",
        help="Введите годовую процентную ставку"
    )

    # Считывание срока кредита
    col1, col2 = st.columns(2)
    with col1:
        loan_term_years = st.number_input(
            "Срок (лет)",
            min_value=0,
            max_value=50,
            value=5,
            step=1,
            help="Срок кредита в годах"
        )
    with col2:
        loan_term_months = st.number_input(
            "Срок (мес)",
            min_value=0,
            max_value=600,
            value=0,
            step=1,
            help="Дополнительные месяцы"
        )

    total_months = loan_term_years * 12 + loan_term_months

    if total_months <= 0:
        st.error("Срок кредита должен быть больше 0")

    # Считывание типа платежа
    payment_type = st.radio(
        "Тип платежа",
        ["Аннуитетный", "Дифференцированный"],
        help="Аннуитетный - равные платежи, Дифференцированный - уменьшающиеся"
    )

    # Дополнительный функционал: дата первого платежа
    use_date = st.checkbox("Указать дату первого платежа")
    start_date = None
    if use_date:
        start_date = st.date_input(
            "Дата первого платежа",
            value=datetime.date.today(),
            format="DD.MM.YYYY"
        )

    # Кнопка для расчёта
    calculate_button = st.button("Рассчитать кредит", type="primary", use_container_width=True)

    st.markdown("---")

    # Информационная панель
    with st.expander("Информация о типах платежей"):
        st.markdown("""
        **Аннуитетный платёж:**
        - Ежемесячный платёж одинаковый
        - В начале срока больше процентов
        - Удобно для планирования бюджета

        **Дифференцированный платёж:**
        - Платежи постепенно уменьшаются
        - Переплата по кредиту меньше
        - Первые платежи больше по сумме
        """)

# Основная область приложения
if calculate_button and total_months > 0:
    try:
        # Выполнение расчёта
        if payment_type == "Аннуитетный":
            schedule_df, monthly_payment = calculate_annuity_schedule(
                loan_amount, interest_rate, total_months, start_date
            )

            # Расчёт общей суммы выплат и переплаты
            total_payment = monthly_payment * total_months
            overpayment = total_payment - loan_amount

            # Отображение результатов
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Ежемесячный платёж", f"{monthly_payment:,.2f} руб")
            with col2:
                st.metric("Общая сумма выплат", f"{total_payment:,.2f} руб")
            with col3:
                st.metric("Переплата по кредиту", f"{overpayment:,.2f} руб")
            with col4:
                st.metric("Переплата в %", f"{(overpayment / loan_amount) * 100:.1f}%")

        else:  # Дифференцированный платеж
            schedule_df, first_payment = calculate_differentiated_schedule(
                loan_amount, interest_rate, total_months, start_date
            )

            # Расчёт общей суммы выплат и переплаты
            total_payment = schedule_df["Ежемесячный платёж"].sum()
            overpayment = total_payment - loan_amount
            last_payment = schedule_df["Ежемесячный платёж"].iloc[-1]

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Первый платёж", f"{first_payment:,.2f} руб")
            with col2:
                st.metric("Последний платёж", f"{last_payment:,.2f} руб")
            with col3:
                st.metric("Общая сумма выплат", f"{total_payment:,.2f} руб")
            with col4:
                st.metric("Переплата по кредиту", f"{overpayment:,.2f} руб")
            with col5:
                st.metric("Переплата в %", f"{(overpayment / loan_amount) * 100:.1f}%")

        # Добавляем даты платежей, если указана дата первого платежа
        if use_date and start_date:
            dates = []
            current_date = start_date
            for i in range(len(schedule_df)):
                dates.append(current_date)
                # Переход на следующий месяц
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            schedule_df.insert(1, "Дата платежа", dates)

        # Форматирование денежных значений для отображения
        for col in ["Остаток долга на начало", "Ежемесячный платёж",
                    "Процентная часть", "Долговая часть", "Остаток долга на конец"]:
            if col in schedule_df.columns:
                schedule_df[col] = schedule_df[col].apply(lambda x: f"{x:,.2f} руб")

        # Отображение графика платежей
        st.markdown("---")
        st.header("График платежей")

        # Использование st.expander() для сворачиваемой таблицы
        with st.expander("Показать полный график платежей", expanded=True):
            st.dataframe(schedule_df, use_container_width=True, hide_index=True)

        # Дополнительная статистика
        st.markdown("---")
        st.header("Анализ кредита")

        col1, col2 = st.columns(2)
        with col1:
            # Условный рендеринг: показываем разные сообщения для разных типов платежей
            if payment_type == "Аннуитетный":
                st.info(f"При аннуитетных платежах вы платите ежемесячно одинаковую сумму {monthly_payment:,.2f} руб")
                st.success(
                    f"Переплата составляет {overpayment:,.2f} руб, что на {(overpayment / loan_amount) * 100:.1f}% больше суммы кредита")
            else:
                avg_payment = total_payment / total_months
                st.info(f"При дифференцированных платежах средний платёж составляет {avg_payment:,.2f} руб")
                st.success(
                    f"Переплата составляет {overpayment:,.2f} руб, что на {(overpayment / loan_amount) * 100:.1f}% больше суммы кредита")

        with col2:
            st.metric("Количество платежей", f"{total_months} мес")

        # Сохранение расчёта в историю
        calculation_record = {
            "Дата расчёта": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Сумма": loan_amount,
            "Ставка": interest_rate,
            "Срок (мес)": total_months,
            "Тип": payment_type,
            "Переплата": overpayment
        }
        st.session_state.calculation_history.append(calculation_record)

        # Обработка случая с большим количеством расчётов (сохраняем последние 10)
        if len(st.session_state.calculation_history) > 10:
            st.session_state.calculation_history = st.session_state.calculation_history[-10:]

    except Exception as e:
        st.error(f"Ошибка при расчёте: {str(e)}")
        st.stop()  # Использование st.stop() для прекращения выполнения при ошибке

elif calculate_button and total_months <= 0:
    st.error("Пожалуйста, укажите корректный срок кредита (больше 0)")

# Отображение истории расчётов
if st.session_state.calculation_history:
    st.markdown("---")
    st.header("История расчётов")

    history_df = pd.DataFrame(st.session_state.calculation_history)
    st.dataframe(history_df, use_container_width=True, hide_index=True)

    # Кнопка для очистки истории
    if st.button("Очистить историю"):
        st.session_state.calculation_history = []
        st.rerun()  # Использование st.rerun() для обновления страницы

# Инструкция по запуску
st.markdown("---")
st.caption(
    "Совет: Используйте боковую панель для ввода параметров кредита. Калькулятор поддерживает оба типа платежей и может отображать даты платежей.")