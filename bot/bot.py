import matplotlib.pyplot as plt
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import requests
import asyncio
from bot_config import token, DATA_FILE

FLASK_API_URL = "http://10.58.167.168:5000/latest"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Статус котла"), KeyboardButton("Статистика")], [KeyboardButton("Газ")]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Я бот управления котлом. Выберите опцию:", reply_markup=reply_markup)


async def fetch_latest_data():
    try:
        response = requests.get(FLASK_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return (
                float(data["temp_outside"]),  # подача
                float(data["temp_back"]),  # обратка
                float(data["temp_come"]),  # помещение
                float(data["temp_inside"]),  # улица
                float(data["gas"]),  # газ
                data["timestamp"]
            )
        else:
            print(f"Ошибка запроса: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return None


# Статус котла
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await fetch_latest_data()
    if not data:
        await update.message.reply_text("Ошибка получения данных с сервера!")
        return
    temp1, temp2, temp3, temp4, gas, time_str = data
    save_data(temp1, temp2, temp3, temp4, gas, time_str)
    message = (
        f"🔥 Текущий статус котла:\n"
        f"Подача: {temp1:.2f}°C\n"
        f"Обратка: {temp2:.2f}°C\n"
        f"В помещении: {temp3:.2f}°C\n"
        f"На улице: {temp4:.2f}°C\n"
        f"Газ: {gas:.2f} ppm\n"
        f"🕒 Время: {time_str}"
    )
    await update.message.reply_text(message)


# Сохраняем в файл
def save_data(temp1, temp2, temp3, temp4, gas, time_str):
    with open(DATA_FILE, "a") as f:
        f.write(f"{temp1},{temp2},{temp3},{temp4},{gas},{time_str}\n")


# Построение графика
def generate_graph():
    temp1, temp2, temp3, temp4, gas, times = [], [], [], [], [], []
    with open(DATA_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 6:
                continue
            try:
                temp1.append(float(parts[0]))
                temp2.append(float(parts[1]))
                temp3.append(float(parts[2]))
                temp4.append(float(parts[3]))
                gas.append(float(parts[4]))
                times.append(parts[5])
            except ValueError:
                continue
    if not times:
        return None
    plt.figure(figsize=(12, 6))
    plt.plot(times, temp1, label='Подача', color='red')
    plt.plot(times, temp2, label='Обратка', color='blue')
    plt.plot(times, temp3, label='Помещение', color='green')
    plt.plot(times, temp4, label='Улица', color='purple')
    plt.xlabel('Время')
    plt.ylabel('Значения')
    plt.title('График показаний')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    path = "temperature_graph.jpg"
    plt.savefig(path)
    plt.close()
    return path

def generate_gas_graph():
    gas, times = [], []
    with open(DATA_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 6:
                continue
            try:
                gas.append(float(parts[4]))
                times.append(parts[5])
            except ValueError:
                continue
    if not times:
        return None
    plt.figure(figsize=(10, 4))
    plt.plot(times, gas, label='Газ (ppm)', color='orange')
    plt.xlabel('Время')
    plt.ylabel('Газ, ppm')
    plt.title('График концентрации газа')
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    path = "gas_graph.jpg"
    plt.savefig(path)
    plt.close()
    return path



async def send_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = generate_graph()
    if path:
        with open(path, "rb") as f:
            await update.message.reply_photo(photo=f)
    else:
        await update.message.reply_text("Нет данных для построения графика температуры")


async def send_gas_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = generate_gas_graph()
    if path:
        with open(path, "rb") as f:
            await update.message.reply_photo(photo=f)
    else:
        await update.message.reply_text("Нет данных для построения графика по газу.")


# Обработка кнопок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Статус котла":
        await status(update, context)
    elif text == "Статистика":
        await send_statistics(update, context)
    elif text == "Газ":
        await send_gas_statistics(update, context)


# Запуск
def main():
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
