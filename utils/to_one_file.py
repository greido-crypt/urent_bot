import os

# Название итогового файла
output_filename = "combined.txt"

# Открываем итоговый файл для записи
with open(output_filename, 'w', encoding='utf-8') as outfile:
    # Проходим по всем файлам в текущем каталоге
    for filename in os.listdir():
        # Проверяем, что файл имеет расширение .txt
        if filename.endswith('.txt') and filename != output_filename:
            with open(filename, 'r', encoding='utf-8') as infile:
                # Записываем содержимое файла в итоговый файл
                outfile.write(infile.read())
print(f"Все файлы объединены в {output_filename}")
