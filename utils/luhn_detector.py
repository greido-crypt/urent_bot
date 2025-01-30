def luhn_algorithm(card_number):
    # Преобразуем строку в список цифр
    digits = [int(x) for x in card_number if x.isdigit()]

    # Удваиваем значения каждой второй цифры, начиная с конца
    for i in range(len(digits) - 2, -1, -2):
        digits[i] = digits[i] * 2
        if digits[i] > 9:
            digits[i] -= 9

    # Суммируем все цифры
    total = sum(digits)

    # Если сумма делится на 10 без остатка, номер карты валиден
    return total % 10 == 0


def validate_credit_card(card_number: str):
    # Удаляем пробелы и тире, оставляем только цифры
    card_number = ''.join(c for c in card_number if c.isdigit())

    # Проверяем длину номера карты
    if len(card_number) < 13 or len(card_number) > 19:
        return False

    # Проверяем номер карты с помощью алгоритма Луна
    return luhn_algorithm(card_number)