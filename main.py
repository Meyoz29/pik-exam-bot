"""
 ПИК | Подготовка к ОГЭ и ЕГЭ
Тренажёр с заданиями из банка ФИПИ
Дизайн в стиле онлайн-школы ПИК
"""

import os
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, JSON, BigInteger, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, date, timedelta
import urllib.parse
import json
import random

# ===== БД =====
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./exam_bot.db")
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(256))
    exam = Column(String(16))
    subject = Column(String(64))
    streak = Column(Integer, default=0)
    last_answer_date = Column(Date)
    achievements = Column(JSON, default=[])
    total_solved = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam = Column(String(16), index=True)
    subject = Column(String(64), index=True)
    task_number = Column(Integer, index=True)
    topic = Column(String(128))
    type = Column(String(16))
    question = Column(Text)
    options = Column(JSON)
    correct_answer = Column(String(256))
    explanation = Column(Text)
    difficulty = Column(Integer, default=1)

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    task_number = Column(Integer)
    correct = Column(Boolean)
    user_answer = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)

# ===== БАНК ЗАДАНИЙ (расширенный) =====
# Формат: exam, subject, task_number, topic, type, question, options, correct_answer, explanation

TASKS_DB = [
    # ========== ЕГЭ МАТЕМАТИКА (ПРОФИЛЬ) — 19 заданий ==========
    dict(exam="EGE", subject="Математика (профиль)", task_number=1, topic="Планиметрия", type="short",
         question="В треугольнике ABC угол A равен 60°, угол B равен 70°. Найдите угол C (в градусах).",
         correct_answer="50", explanation="Сумма углов треугольника = 180°. 180 - 60 - 70 = 50°"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=1, topic="Планиметрия", type="short",
         question="В прямоугольном треугольнике катеты равны 3 и 4. Найдите гипотенузу.",
         correct_answer="5", explanation="По теореме Пифагора: c = √(a²+b²) = (9+16) = √25 = 5"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=1, topic="Планиметрия", type="short",
         question="Площадь прямоугольного треугольника равна 24, один катет равен 6. Найдите другой катет.",
         correct_answer="8", explanation="S = (a·b)/2 → 24 = (6·b)/2 → b = 8"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=1, topic="Планиметрия", type="short",
         question="Радиус окружности, вписанной в квадрат со стороной 6, равен?",
         correct_answer="3", explanation="r = a/2 = 6/2 = 3"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=2, topic="Векторы", type="short",
         question="Найдите скалярное произведение векторов (2, 3) и (4, 5).",
         correct_answer="23", explanation="a·b = 2·4 + 3·5 = 8 + 15 = 23"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=2, topic="Векторы", type="short",
         question="Найдите длину вектора (3, 4).",
         correct_answer="5", explanation="|v| = √(3²+4²) = √(9+16) = √25 = 5"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=3, topic="Стереометрия", type="short",
         question="Объём куба равен 27. Найдите площадь его поверхности.",
         correct_answer="54", explanation="Ребро a = ∛27 = 3. S = 6a² = 6·9 = 54"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=3, topic="Стереометрия", type="short",
         question="Объём цилиндра с радиусом 2 и высотой 5 равен? (ответ через π, например 20π)",
         correct_answer="20π", explanation="V = πr²h = π·4·5 = 20π"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=4, topic="Теория вероятностей", type="short",
         question="Бросают две монеты. Найдите вероятность того, что выпадет хотя бы один орёл.",
         correct_answer="0.75", explanation="P = 1 - P(два решки) = 1 - 0.25 = 0.75"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=4, topic="Теория вероятностей", type="short",
         question="В классе 25 учеников, 10 из них — отличники. Наугад выбирают одного. Найдите вероятность, что это отличник.",
         correct_answer="0.4", explanation="P = 10/25 = 0.4"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=5, topic="Уравнения", type="short",
         question="Решите уравнение: 2^x = 32",
         correct_answer="5", explanation="32 = 2⁵, значит x = 5"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=5, topic="Уравнения", type="short",
         question="Решите уравнение: log₃(x) = 2",
         correct_answer="9", explanation="x = 3² = 9"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=6, topic="Производная", type="short",
         question="Найдите производную функции f(x) = 3x²",
         correct_answer="6x", explanation="f'(x) = 2·3x = 6x"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=6, topic="Производная", type="short",
         question="Найдите значение производной функции f(x) = x³ в точке x = 2",
         correct_answer="12", explanation="f'(x) = 3x², f'(2) = 3·4 = 12"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=7, topic="Логарифмы", type="short",
         question="Вычислите: log₂(8)",
         correct_answer="3", explanation="2³ = 8"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=7, topic="Логарифмы", type="short",
         question="Вычислите: log₅(125)",
         correct_answer="3", explanation="5³ = 125"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=8, topic="Тригонометрия", type="short",
         question="Найдите sin(30°)",
         correct_answer="0.5", explanation="sin(30°) = 1/2 = 0.5"),
    dict(exam="EGE", subject="Математика (профиль)", task_number=8, topic="Тригонометрия", type="short",
         question="Найдите cos(60°)",
         correct_answer="0.5", explanation="cos(60°) = 1/2 = 0.5"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=9, topic="Текстовая задача", type="short",
         question="Велосипедист едет со скоростью 15 км/ч. Какое расстояние он проедет за 2 часа?",
         correct_answer="30", explanation="S = v·t = 15·2 = 30 км"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=10, topic="Комбинаторика", type="short",
         question="Сколькими способами можно выбрать 2 человека из 5?",
         correct_answer="10", explanation="C(5,2) = 5!/(2!·3!) = 10"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=11, topic="Функции", type="short",
         question="Найдите область определения функции y = 1/x (ответ: x≠0)",
         correct_answer="x≠0", explanation="Знаменатель не может быть равен 0"),
    
    dict(exam="EGE", subject="Математика (профиль)", task_number=12, topic="Неравенства", type="short",
         question="Решите неравенство: x² - 4 > 0. Запишите ответ в виде интервала, например (-∞,-2)U(2,+)",
         correct_answer="(-∞,-2)U(2,+∞)", explanation="x² > 4 → x < -2 или x > 2"),

    # ========== ЕГЭ РУССКИЙ ЯЗЫК — 27 заданий ==========
    dict(exam="EGE", subject="Русский язык", task_number=1, topic="Информационная обработка текста", type="choice",
         question="Какое утверждение соответствует содержанию текста?",
         options=["Главная мысль выражена в первом абзаце", "Автор критикует современное общество", "Текст носит научный характер", "Все варианты неверны"],
         correct_answer="1", explanation="Главная мысль обычно формулируется в начале текста"),
    dict(exam="EGE", subject="Русский язык", task_number=1, topic="Информационная обработка текста", type="choice",
         question="Определите, какое предложение передаёт главную мысль текста.",
         options=["Первое", "Второе", "Третье", "Последнее"],
         correct_answer="1", explanation="Главная мысль чаще всего в начале"),
    
    dict(exam="EGE", subject="Русский язык", task_number=2, topic="Средства связи предложений", type="choice",
         question="Какое средство связи используется между предложениями?",
         options=["Личное местоимение", "Союз", "Наречие", "Частица"],
         correct_answer="1", explanation="Личные местоимения часто связывают предложения в тексте"),
    
    dict(exam="EGE", subject="Русский язык", task_number=3, topic="Лексическое значение слова", type="choice",
         question="В каком значении употреблено слово «светлый» в предложении «светлая комната»?",
         options=["Прямом", "Переносном", "И том и другом", "Ни в одном"],
         correct_answer="1", explanation="Здесь «светлый» = хорошо освещённый — прямое значение"),
    
    dict(exam="EGE", subject="Русский язык", task_number=4, topic="Орфоэпия", type="choice",
         question="В каком слове ударение падает на второй слог?",
         options=["квартал", "красивее", "звонит", "все варианты"],
         correct_answer="4", explanation="квартАл, красивЕе, звонИт — все на второй слог"),
    dict(exam="EGE", subject="Русский язык", task_number=4, topic="Орфоэпия", type="choice",
         question="Где правильное ударение?",
         options=["тОрты", "тортЫ", "оба неверно"],
         correct_answer="2", explanation="Правильно: тортЫ"),
    
    dict(exam="EGE", subject="Русский язык", task_number=5, topic="Лексические ошибки", type="choice",
         question="В каком предложении есть лексическая ошибка?",
         options=["Он прибыл вовремя", "Он приехал заблаговременно", "Он пришёл заранее", "Все верны"],
         correct_answer="4", explanation="Все предложения корректны"),
    
    dict(exam="EGE", subject="Русский язык", task_number=6, topic="Морфология", type="choice",
         question="Какой частью речи является слово «быстро»?",
         options=["Прилагательное", "Наречие", "Глагол", "Существительное"],
         correct_answer="2", explanation="«Быстро» — наречие"),
    
    dict(exam="EGE", subject="Русский язык", task_number=7, topic="Синтаксис", type="choice",
         question="Какое предложение простое?",
         options=["Он пришёл и сел", "Дождь шёл, и ветер дул", "Мама мыла раму", "Все сложные"],
         correct_answer="3", explanation="«Мама мыла раму» — простое предложение"),
    
    dict(exam="EGE", subject="Русский язык", task_number=8, topic="Пунктуация", type="short",
         question="Сколько запятых в предложении: «Мама мыла раму»?",
         correct_answer="0", explanation="Простое предложение без однородных членов"),
    
    dict(exam="EGE", subject="Русский язык", task_number=9, topic="Орфография", type="choice",
         question="В каком слове пропущена буква «о»?",
         options=["Ш..пот", "Ж..нглёр", "Ц..рк", "Все варианты"],
         correct_answer="4", explanation="Шёпот, жонглёр, цирк"),
    
    dict(exam="EGE", subject="Русский язык", task_number=10, topic="Словообразование", type="choice",
         question="Каким способом образовано слово «подснежник»?",
         options=["Приставочный", "Суффиксальный", "Приставочно-суффиксальный", "Сложение основ"],
         correct_answer="3", explanation="Под- + -снеж- + -ник"),
    
    dict(exam="EGE", subject="Русский язык", task_number=11, topic="Средства выразительности", type="choice",
         question="Что такое метафора?",
         options=["Сравнение с помощью «как»", "Переносное употребление слова", "Преувеличение", "Олицетворение"],
         correct_answer="2", explanation="Метафора — скрытое сравнение"),
    
    dict(exam="EGE", subject="Русский язык", task_number=12, topic="Сочинение", type="choice",
         question="Какой тип речи используется в сочинении-рассуждении?",
         options=["Повествование", "Описание", "Рассуждение", "Диалог"],
         correct_answer="3", explanation="Сочинение-рассуждение использует рассуждение"),

    # ========== ЕГЭ ИНФОРМАТИКА — 27 заданий ==========
    dict(exam="EGE", subject="Информатика", task_number=1, topic="Системы счисления", type="short",
         question="Переведите число 13 в двоичную систему.",
         correct_answer="1101", explanation="13 = 8+4+1 → 1101₂"),
    dict(exam="EGE", subject="Информатика", task_number=1, topic="Системы счисления", type="short",
         question="Переведите число 25 в двоичную систему.",
         correct_answer="11001", explanation="25 = 16+8+1 → 11001₂"),
    dict(exam="EGE", subject="Информатика", task_number=1, topic="Системы счисления", type="short",
         question="Переведите двоичное число 1010 в десятичную систему.",
         correct_answer="10", explanation="1·8 + 0·4 + 1·2 + 0·1 = 10"),
    
    dict(exam="EGE", subject="Информатика", task_number=2, topic="Кодирование информации", type="short",
         question="Сколько бит нужно для кодирования 16 символов?",
         correct_answer="4", explanation="2⁴ = 16 → 4 бита"),
    dict(exam="EGE", subject="Информатика", task_number=2, topic="Кодирование информации", type="short",
         question="Сколько байт занимает текст из 100 символов в кодировке UTF-8 (1 символ = 1 байт)?",
         correct_answer="100", explanation="100 символов × 1 байт = 100 байт"),
    
    dict(exam="EGE", subject="Информатика", task_number=3, topic="Логика", type="choice",
         question="(1 ∨ 0) ∧ (0 ∨ 1) = ?",
         options=["0", "1", "не определено"],
         correct_answer="2", explanation="(1∨0)=1, (0∨1)=1, 1∧1=1"),
    dict(exam="EGE", subject="Информатика", task_number=3, topic="Логика", type="short",
         question="Чему равно ¬(1 ∧ 0)?",
         correct_answer="1", explanation="1∧0=0, ¬0=1"),
    
    dict(exam="EGE", subject="Информатика", task_number=4, topic="Алгоритмы", type="short",
         question="Сумма 1+2+3+4+5 = ?",
         correct_answer="15", explanation="15"),
    dict(exam="EGE", subject="Информатика", task_number=4, topic="Алгоритмы", type="short",
         question="Что выведет цикл: for i in range(1, 6): print(i)? (последнее число)",
         correct_answer="5", explanation="range(1,6) даёт 1,2,3,4,5"),
    
    dict(exam="EGE", subject="Информатика", task_number=5, topic="Программирование", type="short",
         question="Что выведет: print(2**3)?",
         correct_answer="8", explanation="2³ = 8"),
    
    dict(exam="EGE", subject="Информатика", task_number=6, topic="Файловая система", type="short",
         question="Сколько байт в 1 КБ?",
         correct_answer="1024", explanation="1 КБ = 1024 байт"),
    
    dict(exam="EGE", subject="Информатика", task_number=7, topic="Базы данных", type="choice",
         question="Что такое первичный ключ в БД?",
         options=["Поле для сортировки", "Уникальный идентификатор записи", "Поле для поиска", "Связь между таблицами"],
         correct_answer="2", explanation="Первичный ключ уникально идентифицирует запись"),
    
    dict(exam="EGE", subject="Информатика", task_number=8, topic="Моделирование", type="choice",
         question="Что такое модель?",
         options=["Точная копия объекта", "Упрощённое представление объекта", "Программа", "База данных"],
         correct_answer="2", explanation="Модель — упрощённое представление реального объекта"),

    # ========== ЕГЭ ХИМИЯ — 35 заданий ==========
    dict(exam="EGE", subject="Химия", task_number=1, topic="Строение атома", type="choice",
         question="Сколько электронов на внешнем уровне у атома хлора?",
         options=["5", "6", "7", "8"],
         correct_answer="3", explanation="Хлор в VII группе → 7 электронов на внешнем уровне"),
    dict(exam="EGE", subject="Химия", task_number=1, topic="Строение атома", type="short",
         question="Сколько протонов в атоме углерода?",
         correct_answer="6", explanation="Атомный номер углерода = 6"),
    dict(exam="EGE", subject="Химия", task_number=1, topic="Строение атома", type="short",
         question="Сколько нейтронов в атоме ¹⁴C?",
         correct_answer="8", explanation="14 - 6 = 8 нейтронов"),
    
    dict(exam="EGE", subject="Химия", task_number=2, topic="Периодический закон", type="choice",
         question="Какой элемент находится в 3 периоде, VII группе?",
         options=["Фтор", "Хлор", "Бром", "Йод"],
         correct_answer="2", explanation="Хлор — 3 период, VII группа"),
    dict(exam="EGE", subject="Химия", task_number=2, topic="Периодический закон", type="choice",
         question="Какой элемент имеет наибольший атомный радиус?",
         options=["Li", "Na", "K", "Rb"],
         correct_answer="4", explanation="Радиус увеличивается вниз по группе"),
    
    dict(exam="EGE", subject="Химия", task_number=3, topic="Химическая связь", type="choice",
         question="Какой тип связи в молекуле NaCl?",
         options=["Ковалентная полярная", "Ковалентная неполярная", "Ионная", "Металлическая"],
         correct_answer="3", explanation="NaCl — ионное соединение"),
    dict(exam="EGE", subject="Химия", task_number=3, topic="Химическая связь", type="choice",
         question="Какой тип связи в молекуле Cl₂?",
         options=["Ионная", "Ковалентная полярная", "Ковалентная неполярная", "Металлическая"],
         correct_answer="3", explanation="Cl₂ — два одинаковых атома, неполярная связь"),
    
    dict(exam="EGE", subject="Химия", task_number=4, topic="Степень окисления", type="short",
         question="Какая степень окисления у серы в H₂SO?",
         correct_answer="+6", explanation="H(+1)·2 + S + O(-2)·4 = 0 → S = +6"),
    dict(exam="EGE", subject="Химия", task_number=4, topic="Степень окисления", type="short",
         question="Какая степень окисления у азота в HNO₃?",
         correct_answer="+5", explanation="H(+1) + N + O(-2)·3 = 0 → N = +5"),
    
    dict(exam="EGE", subject="Химия", task_number=5, topic="Классы веществ", type="choice",
         question="К какому классу относится NaOH?",
         options=["Кислота", "Основание", "Соль", "Оксид"],
         correct_answer="2", explanation="NaOH — щёлочь, основание"),
    dict(exam="EGE", subject="Химия", task_number=5, topic="Классы веществ", type="choice",
         question="К какому классу относится H₂SO?",
         options=["Кислота", "Основание", "Соль", "Оксид"],
         correct_answer="1", explanation="H₂SO₄ — серная кислота"),
    
    dict(exam="EGE", subject="Химия", task_number=6, topic="Типы реакций", type="choice",
         question="Какой тип реакции: A + B → AB?",
         options=["Разложение", "Соединение", "Замещение", "Обмен"],
         correct_answer="2", explanation="Это реакция соединения"),
    dict(exam="EGE", subject="Химия", task_number=6, topic="Типы реакций", type="choice",
         question="Какой тип реакции: AB → A + B?",
         options=["Разложение", "Соединение", "Замещение", "Обмен"],
         correct_answer="1", explanation="Это реакция разложения"),
    
    dict(exam="EGE", subject="Химия", task_number=7, topic="Расчёты", type="short",
         question="Сколько моль в 18 г воды (H₂O)? M(H₂O) = 18 г/моль",
         correct_answer="1", explanation="n = m/M = 18/18 = 1 моль"),
    dict(exam="EGE", subject="Химия", task_number=7, topic="Расчёты", type="short",
         question="Какой объём занимает 1 моль газа при н.у. (в литрах)?",
         correct_answer="22.4", explanation="1 моль любого газа при н.у. = 22.4 л"),
    
    dict(exam="EGE", subject="Химия", task_number=8, topic="Органическая химия", type="choice",
         question="Какая формула у метана?",
         options=["CH₄", "C₂H₆", "C₃H₈", "CH₁₀"],
         correct_answer="1", explanation="Метан — CH₄"),
    dict(exam="EGE", subject="Химия", task_number=8, topic="Органическая химия", type="choice",
         question="Какой углеводород имеет формулу C₂H₄?",
         options=["Этан", "Этилен", "Ацетилен", "Пропан"],
         correct_answer="2", explanation="C₂H₄ — этилен (этен)"),

    # ========== ЕГЭ БИОЛОГИЯ — 28 заданий ==========
    dict(exam="EGE", subject="Биология", task_number=1, topic="Биология как наука", type="choice",
         question="Какой метод используется для изучения наследственности?",
         options=["Наблюдение", "Эксперимент", "Генеалогический", "Микроскопия"],
         correct_answer="3", explanation="Генеалогический метод изучает наследственность"),
    dict(exam="EGE", subject="Биология", task_number=1, topic="Биология как наука", type="short",
         question="Как называется наука о клетке?",
         correct_answer="цитология", explanation="Цитология — наука о клетке"),
    
    dict(exam="EGE", subject="Биология", task_number=2, topic="Клетка", type="choice",
         question="Какой органоид отвечает за синтез белка?",
         options=["Митохондрия", "Рибосома", "Лизосома", "Аппарат Гольджи"],
         correct_answer="2", explanation="Рибосомы синтезируют белок"),
    dict(exam="EGE", subject="Биология", task_number=2, topic="Клетка", type="choice",
         question="Какой органоид называется «энергетической станцией» клетки?",
         options=["Ядро", "Митохондрия", "Рибосома", "Лизосома"],
         correct_answer="2", explanation="Митохондрии производят энергию (АТФ)"),
    
    dict(exam="EGE", subject="Биология", task_number=3, topic="Организм", type="choice",
         question="Сколько хромосом в соматической клетке человека?",
         options=["23", "46", "48", "22"],
         correct_answer="2", explanation="46 хромосом (23 пары)"),
    dict(exam="EGE", subject="Биология", task_number=3, topic="Организм", type="short",
         question="Сколько хромосом в половой клетке человека?",
         correct_answer="23", explanation="В гаметах — гаплоидный набор, 23 хромосомы"),
    
    dict(exam="EGE", subject="Биология", task_number=4, topic="Размножение", type="choice",
         question="Какой тип деления клеток приводит к образованию гамет?",
         options=["Митоз", "Мейоз", "Амитоз", "Бинарное деление"],
         correct_answer="2", explanation="Мейоз — деление с уменьшением числа хромосом"),
    dict(exam="EGE", subject="Биология", task_number=4, topic="Размножение", type="choice",
         question="Какой тип деления сохраняет число хромосом?",
         options=["Митоз", "Мейоз", "Амитоз", "Бинарное деление"],
         correct_answer="1", explanation="Митоз — деление с сохранением числа хромосом"),
    
    dict(exam="EGE", subject="Биология", task_number=5, topic="Генетика", type="short",
         question="Какой закон Менделя описывает расщепление 3:1?",
         correct_answer="второй", explanation="Второй закон Менделя — закон расщепления"),
    dict(exam="EGE", subject="Биология", task_number=5, topic="Генетика", type="choice",
         question="Что такое генотип?",
         options=["Внешние признаки", "Совокупность генов", "Среда обитания", "Фенотип"],
         correct_answer="2", explanation="Генотип — совокупность всех генов организма"),
    
    dict(exam="EGE", subject="Биология", task_number=6, topic="Эволюция", type="choice",
         question="Кто является автором теории эволюции?",
         options=["Ламарк", "Дарвин", "Мендель", "Пастер"],
         correct_answer="2", explanation="Чарльз Дарвин"),
    dict(exam="EGE", subject="Биология", task_number=6, topic="Эволюция", type="choice",
         question="Что такое естественный отбор?",
         options=["Случайные мутации", "Выживание наиболее приспособленных", "Искусственная селекция", "Генетический дрейф"],
         correct_answer="2", explanation="Естественный отбор — выживание наиболее приспособленных"),
    
    dict(exam="EGE", subject="Биология", task_number=7, topic="Экология", type="choice",
         question="Что такое экосистема?",
         options=["Только живые организмы", "Только среда обитания", "Организмы + среда", "Популяция"],
         correct_answer="3", explanation="Экосистема = организмы + среда обитания"),
    dict(exam="EGE", subject="Биология", task_number=7, topic="Экология", type="choice",
         question="Кто является продуцентом в экосистеме?",
         options=["Хищники", "Растения", "Грибы", "Бактерии"],
         correct_answer="2", explanation="Растения — продуценты, создают органику"),
    
    dict(exam="EGE", subject="Биология", task_number=8, topic="Ботаника", type="choice",
         question="Какой процесс происходит в хлоропластах?",
         options=["Дыхание", "Фотосинтез", "Брожение", "Гниение"],
         correct_answer="2", explanation="Фотосинтез"),
    dict(exam="EGE", subject="Биология", task_number=8, topic="Ботаника", type="short",
         question="Какой пигмент придаёт растениям зелёный цвет?",
         correct_answer="хлорофилл", explanation="Хлорофилл — зелёный пигмент"),
    
    dict(exam="EGE", subject="Биология", task_number=9, topic="Зоология", type="choice",
         question="Сколько камер в сердце млекопитающих?",
         options=["2", "3", "4", "5"],
         correct_answer="3", explanation="4 камеры: 2 предсердия и 2 желудочка"),

    # ========== ОГЭ МАТЕМАТИКА — 20 заданий ==========
    dict(exam="OGE", subject="Математика", task_number=1, topic="Вычисления", type="short",
         question="Найдите значение: 2,5 · 4 − 3",
         correct_answer="7", explanation="10 − 3 = 7"),
    dict(exam="OGE", subject="Математика", task_number=1, topic="Вычисления", type="short",
         question="Найдите значение: 15 − 3 · 4",
         correct_answer="3", explanation="15 − 12 = 3"),
    
    dict(exam="OGE", subject="Математика", task_number=2, topic="Числа", type="short",
         question="Найдите значение: 1/2 + 1/3",
         correct_answer="5/6", explanation="3/6 + 2/6 = 5/6"),
    dict(exam="OGE", subject="Математика", task_number=2, topic="Числа", type="short",
         question="Найдите значение: 3/4 − 1/2",
         correct_answer="1/4", explanation="3/4 − 2/4 = 1/4"),
    
    dict(exam="OGE", subject="Математика", task_number=3, topic="Уравнения", type="short",
         question="Решите: 3x − 9 = 0",
         correct_answer="3", explanation="3x = 9 → x = 3"),
    dict(exam="OGE", subject="Математика", task_number=3, topic="Уравнения", type="short",
         question="Решите: 2x + 6 = 0",
         correct_answer="-3", explanation="2x = -6 → x = -3"),
    
    dict(exam="OGE", subject="Математика", task_number=4, topic="Геометрия", type="short",
         question="Площадь прямоугольника 5×8?",
         correct_answer="40", explanation="S = 5·8 = 40"),
    dict(exam="OGE", subject="Математика", task_number=4, topic="Геометрия", type="short",
         question="Периметр квадрата со стороной 6?",
         correct_answer="24", explanation="P = 4·6 = 24"),
    
    dict(exam="OGE", subject="Математика", task_number=5, topic="Геометрия", type="short",
         question="Сумма углов треугольника?",
         correct_answer="180", explanation="180 градусов"),
    
    dict(exam="OGE", subject="Математика", task_number=6, topic="Вероятность", type="short",
         question="Вероятность выпадения орла при броске монеты?",
         correct_answer="0.5", explanation="P = 1/2 = 0.5"),
    
    dict(exam="OGE", subject="Математика", task_number=7, topic="Статистика", type="short",
         question="Найдите среднее арифметическое чисел: 2, 4, 6",
         correct_answer="4", explanation="(2+4+6)/3 = 4"),
    
    dict(exam="OGE", subject="Математика", task_number=8, topic="Функции", type="short",
         question="Найдите значение функции y = 2x + 1 при x = 3",
         correct_answer="7", explanation="y = 2·3 + 1 = 7"),

    # ========== ОГЭ РУССКИЙ ЯЗЫК — 15 заданий ==========
    dict(exam="OGE", subject="Русский язык", task_number=1, topic="Сжатие текста", type="choice",
         question="Какой приём сжатия текста использован?",
         options=["Исключение", "Обобщение", "Упрощение", "Все варианты"],
         correct_answer="4", explanation="Все три приёма используются при сжатии"),
    
    dict(exam="OGE", subject="Русский язык", task_number=2, topic="Синтаксис", type="choice",
         question="Какое предложение простое?",
         options=["Он пришёл и сел", "Дождь шёл, и ветер дул", "Мама мыла раму", "Все сложные"],
         correct_answer="3", explanation="«Мама мыла раму» — простое"),
    
    dict(exam="OGE", subject="Русский язык", task_number=3, topic="Пунктуация", type="short",
         question="Сколько запятых: «Мама мыла раму»?",
         correct_answer="0", explanation="Простое предложение — без запятых"),
    
    dict(exam="OGE", subject="Русский язык", task_number=4, topic="Синонимы", type="choice",
         question="Синоним к «храбрый»:",
         options=["трусливый", "смелый", "медленный", "тихий"],
         correct_answer="2", explanation="храбрый = смелый"),
    
    dict(exam="OGE", subject="Русский язык", task_number=5, topic="Антонимы", type="choice",
         question="Антоним к слову «высокий»:",
         options=["большой", "низкий", "маленький", "короткий"],
         correct_answer="2", explanation="высокий ↔ низкий"),
    
    dict(exam="OGE", subject="Русский язык", task_number=6, topic="Части речи", type="choice",
         question="«Быстро» — это...",
         options=["прилагательное", "наречие", "глагол", "существительное"],
         correct_answer="2", explanation="Наречие"),
    
    dict(exam="OGE", subject="Русский язык", task_number=7, topic="Орфография", type="choice",
         question="Где ошибка?",
         options=["солнце", "солнцевый", "солнечный"],
         correct_answer="2", explanation="Правильно: солнечный"),
    
    dict(exam="OGE", subject="Русский язык", task_number=8, topic="Морфология", type="choice",
         question="Какой частью речи является слово «красивый»?",
         options=["Существительное", "Прилагательное", "Глагол", "Наречие"],
         correct_answer="2", explanation="Прилагательное"),

    # ========== ОГЭ ИНФОРМАТИКА — 20 заданий ==========
    dict(exam="OGE", subject="Информатика", task_number=1, topic="Единицы измерения", type="short",
         question="Сколько байт в 1 КБ?",
         correct_answer="1024", explanation="1 КБ = 1024 байт"),
    dict(exam="OGE", subject="Информатика", task_number=1, topic="Единицы измерения", type="short",
         question="Сколько бит в 1 байте?",
         correct_answer="8", explanation="1 байт = 8 бит"),
    
    dict(exam="OGE", subject="Информатика", task_number=2, topic="Системы счисления", type="short",
         question="Переведите число 5 в двоичную систему.",
         correct_answer="101", explanation="5 = 4+1 → 101₂"),
    
    dict(exam="OGE", subject="Информатика", task_number=3, topic="Файловая система", type="choice",
         question="Что такое расширение файла?",
         options=["Имя файла", "Тип файла", "Размер файла", "Дата создания"],
         correct_answer="2", explanation="Расширение определяет тип файла"),
    
    dict(exam="OGE", subject="Информатика", task_number=4, topic="Алгоритмы", type="short",
         question="Сколько раз выполнится: for i in range(5)?",
         correct_answer="5", explanation="5 раз (0,1,2,3,4)"),
    
    dict(exam="OGE", subject="Информатика", task_number=5, topic="Логика", type="choice",
         question="Результат 1 AND 0:",
         options=["0", "1", "не определено"],
         correct_answer="1", explanation="1 AND 0 = 0"),
]

def seed_database():
    Base.metadata.create_all(engine)
    session = Session()
    count = session.query(Task).count()
    if count == 0:
        for t in TASKS_DB:
            session.add(Task(**t))
        session.commit()
        print(f"✅ Загружено {len(TASKS_DB)} заданий в базу")
    else:
        print(f"ℹ️  В базе уже {count} заданий")
    session.close()

# ===== ДОСТИЖЕНИЯ =====
ACHIEVEMENTS = {
    "first_blood": {"name": "Первая кровь", "desc": "Реши первое задание", "icon": "🎯", "need_total": 1},
    "streak_3": {"name": "Разминка", "desc": "3 дня подряд", "icon": "🔥", "need_streak": 3},
    "streak_7": {"name": "Неделя силы", "desc": "7 дней подряд", "icon": "💪", "need_streak": 7},
    "solved_10": {"name": "Десятка", "desc": "Реши 10 заданий", "icon": "🏆", "need_total": 10},
    "solved_50": {"name": "Полсотни", "desc": "Реши 50 заданий", "icon": "🌟", "need_total": 50},
    "solved_100": {"name": "Соточка", "desc": "Реши 100 заданий", "icon": "", "need_total": 100},
    "master": {"name": "Мастер ПИК", "desc": "Реши 200 заданий", "icon": "👑", "need_total": 200},
    "perfect_5": {"name": "Снайпер", "desc": "5 правильных подряд", "icon": "⭐", "need_total": 5},
}

# ===== HTML С ДИЗАЙНОМ ПИК =====
HTML_CONTENT = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>ПИК | Подготовка к ОГЭ и ЕГЭ</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 50%,#3b82f6 100%);color:#fff;min-height:100vh;overflow-x:hidden}
#app{max-width:480px;margin:0 auto;min-height:100vh;padding:20px}
.screen{display:none;animation:fadeIn .3s ease}
.screen.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* ШАПКА ПИК */
.pik-header{text-align:center;margin-bottom:24px;padding:20px 0}
.pik-logo{font-size:64px;margin-bottom:8px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.3))}
.pik-title{font-size:42px;font-weight:900;letter-spacing:-2px;background:linear-gradient(135deg,#60a5fa 0%,#ffffff 50%,#60a5fa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 30px rgba(96,165,250,.5)}
.pik-subtitle{font-size:14px;color:#93c5fd;letter-spacing:4px;margin-top:4px;font-weight:600}
.pik-divider{width:60px;height:3px;background:linear-gradient(90deg,#3b82f6,#60a5fa);margin:12px auto;border-radius:2px}

/* КАРТОЧКИ */
.card{background:rgba(255,255,255,.08);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:24px;margin-bottom:16px;box-shadow:0 8px 32px rgba(0,0,0,.2)}
.card h2{font-size:20px;font-weight:700;margin-bottom:16px;color:#e0f2fe}

/* КНОПКИ */
.btn{border:none;border-radius:14px;padding:16px 24px;font-size:16px;font-weight:700;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;gap:10px;width:100%;margin:8px 0;background:linear-gradient(135deg,#3b82f6 0%,#1d4ed8 100%);color:#fff;box-shadow:0 4px 15px rgba(59,130,246,.4);text-transform:uppercase;letter-spacing:1px}
.btn:active{transform:scale(.97)}
.btn.oge{background:linear-gradient(135deg,#06b6d4 0%,#0891b2 100%);box-shadow:0 4px 15px rgba(6,182,212,.4)}
.btn.small{padding:12px;font-size:14px}

/* МЕНЮ */
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding:12px 16px;background:rgba(255,255,255,.08);border-radius:16px;border:1px solid rgba(255,255,255,.1)}
.streak-badge{display:flex;align-items:center;gap:6px;font-weight:700;font-size:15px}
.streak-badge .fire{font-size:20px}
.user-subject{font-size:16px;font-weight:700;color:#e0f2fe}

.menu-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:20px}
.menu-card{background:linear-gradient(135deg,rgba(59,130,246,.2) 0%,rgba(30,58,138,.3) 100%);backdrop-filter:blur(20px);border:1px solid rgba(96,165,250,.2);border-radius:18px;padding:22px 14px;cursor:pointer;transition:all .2s;text-align:center;color:#fff}
.menu-card:active{transform:scale(.95);border-color:#60a5fa}
.menu-icon{font-size:42px;margin-bottom:10px}
.menu-title{font-size:16px;font-weight:700;margin-bottom:4px}
.menu-desc{font-size:12px;opacity:.7}

/* ЗАДАНИЯ */
.tasks-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.task-num-btn{background:linear-gradient(135deg,rgba(59,130,246,.3) 0%,rgba(30,58,138,.4) 100%);border:1px solid rgba(96,165,250,.3);border-radius:14px;padding:16px 8px;font-size:15px;font-weight:700;cursor:pointer;color:#fff;transition:all .2s}
.task-num-btn:active{transform:scale(.93);background:linear-gradient(135deg,#3b82f6 0%,#1d4ed8 100%)}
.task-num-btn.has-tasks{background:linear-gradient(135deg,#3b82f6 0%,#1d4ed8 100%);border-color:#60a5fa;box-shadow:0 4px 12px rgba(59,130,246,.4)}

/* КАРТОЧКА ЗАДАНИЯ */
.task-card{background:#fff;border-radius:20px;padding:24px;color:#1e293b;box-shadow:0 12px 40px rgba(0,0,0,.3)}
.task-topic{color:#3b82f6;font-size:13px;font-weight:800;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px}
.task-question{font-size:18px;line-height:1.5;margin-bottom:20px;color:#0f172a;font-weight:500}
.option-btn{background:#f1f5f9;border:2px solid #e2e8f0;border-radius:14px;padding:14px 16px;text-align:left;font-size:15px;cursor:pointer;transition:all .2s;color:#1e293b;width:100%;margin:6px 0;font-weight:500}
.option-btn:active{transform:scale(.98)}
.option-btn.selected{background:linear-gradient(135deg,#3b82f6 0%,#1d4ed8 100%);color:#fff;border-color:#3b82f6}
.task-input{width:100%;padding:14px 16px;border:2px solid #e2e8f0;border-radius:14px;font-size:16px;outline:none;transition:border-color .2s}
.task-input:focus{border-color:#3b82f6}

/* РЕЗУЛЬТАТ */
.result-icon{font-size:100px;text-align:center;margin:30px 0;animation:scaleIn .5s ease}
@keyframes scaleIn{from{transform:scale(0)}to{transform:scale(1)}}
.result-details{background:rgba(255,255,255,.1);border-radius:16px;padding:20px;margin:20px 0;line-height:1.6;border:1px solid rgba(255,255,255,.1)}
.result-details strong{display:block;margin-bottom:8px;color:#e0f2fe}

/* СТАТИСТИКА */
.stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.stat-card{background:linear-gradient(135deg,rgba(59,130,246,.2) 0%,rgba(30,58,138,.3) 100%);border:1px solid rgba(96,165,250,.2);border-radius:16px;padding:20px;text-align:center}
.stat-value{font-size:32px;font-weight:900;margin-bottom:4px;background:linear-gradient(135deg,#60a5fa,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-label{font-size:13px;opacity:.8;color:#93c5fd}

/* ДОСТИЖЕНИЯ */
.achievements-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.achievement-card{background:linear-gradient(135deg,rgba(59,130,246,.2) 0%,rgba(30,58,138,.3) 100%);border:1px solid rgba(96,165,250,.2);border-radius:16px;padding:18px;text-align:center;transition:all .2s}
.achievement-card.unlocked{border-color:#60a5fa;box-shadow:0 4px 20px rgba(96,165,250,.3)}
.achievement-icon{font-size:40px;margin-bottom:8px}
.achievement-name{font-size:14px;font-weight:700;margin-bottom:4px;color:#e0f2fe}
.achievement-desc{font-size:12px;opacity:.7;color:#93c5fd}
.achievement-card.locked{opacity:.4;filter:grayscale(1)}
.new-badge{background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#000;border-radius:8px;padding:2px 8px;font-size:11px;font-weight:800;margin-left:6px}

.back-btn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:12px;padding:12px 20px;font-size:15px;cursor:pointer;color:#e0f2fe;margin-bottom:16px;font-weight:600;transition:all .2s}
.back-btn:active{background:rgba(255,255,255,.2)}

.hidden{display:none!important}
</style>
</head>
<body>
<div id="app">
<div id="loading" class="screen active"><div style="text-align:center;margin-top:100px;font-size:24px">⏳ Загрузка...</div></div>

<div id="setup-screen" class="screen">
<div class="pik-header">
<div class="pik-logo">🦅</div>
<div class="pik-title">ПИК</div>
<div class="pik-divider"></div>
<div class="pik-subtitle">ОГЭ • ЕГЭ</div>
</div>
<div class="card">
<h2> Выбери экзамен</h2>
<button class="btn" onclick="selectExam('EGE')">🎓 ЕГЭ</button>
<button class="btn oge" onclick="selectExam('OGE')">📘 ОГЭ</button>
</div>
<div id="subject-select" class="card hidden">
<h2>📚 Выбери предмет</h2>
<div id="subject-buttons"></div>
</div>
</div>

<div id="main-screen" class="screen">
<div class="pik-header" style="margin-bottom:16px;padding:10px 0">
<div class="pik-title" style="font-size:32px">ПИК</div>
<div class="pik-subtitle">ОГЭ • ЕГЭ</div>
</div>
<div class="header">
<div class="streak-badge"><span class="fire">🔥</span><span id="streak-count">0</span> дн.</div>
<div class="user-subject" id="user-subject">—</div>
</div>
<div class="menu-grid">
<button class="menu-card" onclick="showTaskNumbers()"><div class="menu-icon">📝</div><div class="menu-title">Задания</div><div class="menu-desc">По номерам</div></button>
<button class="menu-card" onclick="showStats()"><div class="menu-icon">📊</div><div class="menu-title">Статистика</div><div class="menu-desc">Прогресс</div></button>
<button class="menu-card" onclick="showAchievements()"><div class="menu-icon">🏆</div><div class="menu-title">Достижения</div><div class="menu-desc">Ачивки</div></button>
<button class="menu-card" onclick="changeSubject()"><div class="menu-icon">⚙️</div><div class="menu-title">Настройки</div><div class="menu-desc">Сменить</div></button>
</div>
</div>

<div id="tasks-screen" class="screen">
<button class="back-btn" onclick="showScreen('main-screen')">← Назад</button>
<h2 style="margin-bottom:16px"> Выбери номер задания</h2>
<div id="task-numbers" class="tasks-grid"></div>
</div>

<div id="training-screen" class="screen">
<button class="back-btn" onclick="showScreen('tasks-screen')">← К заданиям</button>
<div class="task-card">
<div class="task-topic" id="task-topic">Тема</div>
<div class="task-question" id="task-question">Вопрос</div>
<div id="task-options"></div>
<input type="text" id="task-input" class="task-input hidden" placeholder="Введи ответ...">
</div>
<button class="btn" onclick="submitAnswer()" style="margin-top:16px">Проверить</button>
</div>

<div id="result-screen" class="screen">
<div id="result-icon" class="result-icon">✅</div>
<h2 id="result-title" style="text-align:center;margin-bottom:16px">Верно!</h2>
<div id="result-details" class="result-details"></div>
<button class="btn" onclick="nextTask()">Следующее задание →</button>
</div>

<div id="stats-screen" class="screen">
<button class="back-btn" onclick="showScreen('main-screen')">← Назад</button>
<div class="pik-header" style="margin-bottom:16px">
<div class="pik-title" style="font-size:28px">📊 Статистика</div>
</div>
<div class="stats-grid">
<div class="stat-card"><div class="stat-value" id="stat-total">0</div><div class="stat-label">Решено</div></div>
<div class="stat-card"><div class="stat-value" id="stat-correct">0</div><div class="stat-label">Правильных</div></div>
<div class="stat-card"><div class="stat-value" id="stat-pct">0%</div><div class="stat-label">Точность</div></div>
<div class="stat-card"><div class="stat-value" id="stat-streak">0</div><div class="stat-label">🔥 Streak</div></div>
</div>
</div>

<div id="achievements-screen" class="screen">
<button class="back-btn" onclick="showScreen('main-screen')">← Назад</button>
<div class="pik-header" style="margin-bottom:16px">
<div class="pik-title" style="font-size:28px">🏆 Достижения</div>
</div>
<div id="achievements-list" class="achievements-grid"></div>
</div>
</div>

<script>
const tg=window.Telegram.WebApp;tg.expand();tg.ready();
let state={userId:null,exam:null,subject:null,tasks:[],currentTaskIdx:0,correctCount:0,selectedAnswer:null,taskNumber:null};
const SUBJECTS={EGE:['Математика (профиль)','Русский язык','Информатика','Химия','Биология'],OGE:['Математика','Русский язык','Информатика']};

function getInitData(){return encodeURIComponent(tg.initData)}

async function api(endpoint,options={}){
  const sep=endpoint.includes('?')?'&':'?';
  const url=endpoint+sep+'init_data='+getInitData();
  const r=await fetch(url,{...options,headers:{'Content-Type':'application/json','ngrok-skip-browser-warning':'true',...(options.headers||{})}});
  if(!r.ok){const t=await r.text();throw new Error('API '+r.status+': '+t)}
  return r.json();
}

function showScreen(id){document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));document.getElementById(id).classList.add('active')}

async function init(){
  try{
    const u=await api('/api/user');
    state.userId=u.id;
    if(u.exam&&u.subject){state.exam=u.exam;state.subject=u.subject;document.getElementById('user-subject').textContent=u.subject;document.getElementById('streak-count').textContent=u.streak;showScreen('main-screen')}
    else showScreen('setup-screen');
  }catch(e){console.error(e);showScreen('setup-screen')}
}

function selectExam(exam){
  state.exam=exam;
  const c=document.getElementById('subject-buttons');c.innerHTML='';
  SUBJECTS[exam].forEach(s=>{const b=document.createElement('button');b.className='btn'+(exam==='OGE'?' oge':'');b.textContent=s;b.onclick=()=>selectSubject(s);c.appendChild(b)});
  document.getElementById('subject-select').classList.remove('hidden');
}

async function selectSubject(subject){
  state.subject=subject;
  try{
    await api('/api/set_profile',{method:'POST',body:JSON.stringify({exam:state.exam,subject})});
    document.getElementById('user-subject').textContent=subject;
    showScreen('main-screen');
  }catch(e){tg.showAlert('Ошибка: '+e.message)}
}

async function showTaskNumbers(){
  try{
    const data=await api('/api/task_numbers');
    const container=document.getElementById('task-numbers');container.innerHTML='';
    if(!data.length){tg.showAlert('Нет заданий');return}
    data.forEach(num=>{
      const btn=document.createElement('button');
      btn.className='task-num-btn has-tasks';btn.textContent=num;
      btn.onclick=()=>startTraining(num);container.appendChild(btn);
    });
    showScreen('tasks-screen');
  }catch(e){tg.showAlert('Ошибка: '+e.message)}
}

async function startTraining(taskNumber){
  try{
    const tasks=await api('/api/tasks?task_number='+taskNumber+'&limit=5');
    if(!tasks.length){tg.showAlert('Нет заданий этого типа');return}
    state.tasks=tasks;state.currentTaskIdx=0;state.correctCount=0;state.taskNumber=taskNumber;
    showScreen('training-screen');showTask();
  }catch(e){tg.showAlert('Ошибка: '+e.message)}
}

function showTask(){
  const t=state.tasks[state.currentTaskIdx];state.selectedAnswer=null;
  document.getElementById('task-topic').textContent='ЗАДАНИЕ '+state.taskNumber+' • '+t.topic.toUpperCase();
  document.getElementById('task-question').textContent=t.question;
  const oc=document.getElementById('task-options'),inp=document.getElementById('task-input');oc.innerHTML='';
  if(t.type==='choice'&&t.options){
    inp.classList.add('hidden');oc.classList.remove('hidden');
    t.options.forEach((o,i)=>{const b=document.createElement('button');b.className='option-btn';b.textContent=(i+1)+'. '+o;b.onclick=()=>{state.selectedAnswer=''+(i+1);document.querySelectorAll('.option-btn').forEach(x=>x.classList.remove('selected'));b.classList.add('selected')};oc.appendChild(b)});
  }else{oc.classList.add('hidden');inp.classList.remove('hidden');inp.value='';inp.focus()}
}

async function submitAnswer(){
  const t=state.tasks[state.currentTaskIdx];let ua;
  if(t.type==='choice'){if(!state.selectedAnswer){tg.showAlert('Выбери вариант');return}ua=state.selectedAnswer}
  else{ua=document.getElementById('task-input').value.trim();if(!ua){tg.showAlert('Введи ответ');return}}
  try{
    const r=await api('/api/check',{method:'POST',body:JSON.stringify({task_id:t.id,user_answer:ua})});
    if(r.correct){state.correctCount++;tg.HapticFeedback.notificationOccurred('success')}else tg.HapticFeedback.notificationOccurred('error');
    document.getElementById('result-icon').textContent=r.correct?'✅':'❌';
    document.getElementById('result-title').textContent=r.correct?'Верно!':'Неверно';
    let d='';if(!r.correct)d+='<strong>Правильный ответ: '+r.right_answer+'</strong>';
    d+='<strong>Тема: '+r.topic+'</strong>';if(r.explanation)d+='<p>'+r.explanation+'</p>';
    d+='<p>🔥 Streak: '+r.streak+' дн.</p>';
    if(r.new_achievements&&r.new_achievements.length>0){d+='<p style="margin-top:12px"><strong>🏆 Новые достижения:</strong></p>';r.new_achievements.forEach(a=>{d+='<p>'+a.icon+' '+a.name+'</p>'})}
    document.getElementById('result-details').innerHTML=d;showScreen('result-screen');
  }catch(e){tg.showAlert('Ошибка: '+e.message)}
}

function nextTask(){state.currentTaskIdx++;if(state.currentTaskIdx>=state.tasks.length){tg.showAlert('Серия окончена! Правильных: '+state.correctCount+'/'+state.tasks.length);showScreen('tasks-screen')}else{showScreen('training-screen');showTask()}}

async function showStats(){
  try{const s=await api('/api/stats');document.getElementById('stat-total').textContent=s.total;document.getElementById('stat-correct').textContent=s.correct;document.getElementById('stat-pct').textContent=s.pct+'%';document.getElementById('stat-streak').textContent=s.streak;showScreen('stats-screen')}catch(e){tg.showAlert('Ошибка: '+e.message)}
}

async function showAchievements(){
  try{
    const data=await api('/api/achievements');
    const container=document.getElementById('achievements-list');container.innerHTML='';
    data.forEach(a=>{
      const card=document.createElement('div');
      card.className='achievement-card'+(a.unlocked?' unlocked':' locked');
      card.innerHTML='<div class="achievement-icon">'+a.icon+'</div><div class="achievement-name">'+a.name+(a.new?' <span class="new-badge">NEW</span>':'')+'</div><div class="achievement-desc">'+a.desc+'</div>';
      container.appendChild(card);
    });
    showScreen('achievements-screen');
  }catch(e){tg.showAlert('Ошибка: '+e.message)}
}

function changeSubject(){showScreen('setup-screen');document.getElementById('subject-select').classList.add('hidden')}

init();
</script>
</body>
</html>'''

# ===== СЕРВЕР =====
seed_database()

app = FastAPI(title="ПИК | Тренажёр ОГЭ и ЕГЭ")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_user_id_from_init(init_data: str) -> int:
    try:
        params = urllib.parse.parse_qs(init_data)
        user_json = params.get("user", [None])[0]
        if not user_json:
            raise HTTPException(401, "Нет данных пользователя")
        user = json.loads(user_json)
        return user["id"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, f"Ошибка initData: {str(e)}")

@app.get("/api/user")
async def get_user(init_data: str = Query(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    u = s.query(User).get(uid)
    if not u:
        u = User(id=uid, achievements=[], total_solved=0, correct_count=0)
        s.add(u); s.commit(); s.refresh(u)
    result = {"id": u.id, "exam": u.exam, "subject": u.subject, "streak": u.streak or 0, "total_solved": u.total_solved or 0, "achievements": u.achievements or []}
    s.close()
    return result

@app.post("/api/set_profile")
async def set_profile(init_data: str = Query(...), data: dict = Body(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    u = s.query(User).get(uid) or User(id=uid, achievements=[], total_solved=0, correct_count=0)
    u.exam = data["exam"]; u.subject = data["subject"]
    s.add(u); s.commit(); s.close()
    return {"ok": True}

@app.get("/api/task_numbers")
async def get_task_numbers(init_data: str = Query(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    u = s.query(User).get(uid)
    if not u or not u.exam or not u.subject:
        s.close(); return []
    numbers = [r[0] for r in s.query(Task.task_number).filter(Task.exam == u.exam, Task.subject == u.subject).distinct().order_by(Task.task_number).all()]
    s.close()
    return numbers

@app.get("/api/tasks")
async def get_tasks(task_number: int = None, limit: int = 5, init_data: str = Query(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    u = s.query(User).get(uid)
    if not u or not u.exam:
        s.close(); return []
    q = s.query(Task).filter(Task.exam == u.exam, Task.subject == u.subject)
    if task_number:
        q = q.filter(Task.task_number == task_number)
    rows = q.all()
    if not rows:
        s.close(); return []
    random.shuffle(rows)
    chosen = rows[:limit]
    s.close()
    return [{"id": t.id, "topic": t.topic, "question": t.question, "options": t.options, "type": t.type, "task_number": t.task_number} for t in chosen]

class CheckReq(BaseModel):
    task_id: int
    user_answer: str

@app.post("/api/check")
async def check_answer(init_data: str = Query(...), req: CheckReq = Body(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    t = s.query(Task).get(req.task_id)
    if not t:
        s.close(); raise HTTPException(404, "Задание не найдено")
    u_ans = req.user_answer.lower().replace("ё", "е").strip()
    c_ans = t.correct_answer.lower().replace("ё", "е").strip()
    ok = u_ans == c_ans
    s.add(Attempt(user_id=uid, task_id=t.id, task_number=t.task_number, correct=ok, user_answer=req.user_answer))
    user = s.query(User).get(uid)
    today = date.today()
    if user.last_answer_date != today:
        if user.last_answer_date == today - timedelta(days=1):
            user.streak = (user.streak or 0) + 1
        else:
            user.streak = 1
        user.last_answer_date = today
    user.total_solved = (user.total_solved or 0) + 1
    if ok:
        user.correct_count = (user.correct_count or 0) + 1
    user_achievements = user.achievements or []
    new_achievements = []
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id not in user_achievements:
            earned = False
            if "need_total" in ach_data and user.total_solved >= ach_data["need_total"]:
                earned = True
            if "need_streak" in ach_data and user.streak >= ach_data["need_streak"]:
                earned = True
            if earned:
                user_achievements.append(ach_id)
                new_achievements.append({"id": ach_id, "name": ach_data["name"], "icon": ach_data["icon"]})
    user.achievements = user_achievements
    s.commit()
    result = {"correct": ok, "right_answer": t.correct_answer, "topic": t.topic, "explanation": t.explanation, "streak": user.streak, "new_achievements": new_achievements}
    s.close()
    return result

@app.get("/api/stats")
async def get_stats(init_data: str = Query(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    total = s.query(Attempt).filter(Attempt.user_id == uid).count()
    correct = s.query(Attempt).filter(Attempt.user_id == uid, Attempt.correct == True).count()
    u = s.query(User).get(uid)
    s.close()
    return {"total": total, "correct": correct, "pct": round(correct / total * 100) if total else 0, "streak": u.streak if u else 0, "total_solved": u.total_solved if u else 0}

@app.get("/api/achievements")
async def get_achievements(init_data: str = Query(...)):
    uid = get_user_id_from_init(init_data)
    s = Session()
    u = s.query(User).get(uid)
    user_achievements = u.achievements or [] if u else []
    s.close()
    result = []
    for ach_id, ach_data in ACHIEVEMENTS.items():
        unlocked = ach_id in user_achievements
        result.append({"id": ach_id, "name": ach_data["name"], "desc": ach_data["desc"], "icon": ach_data["icon"], "unlocked": unlocked, "new": False})
    return result

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_CONTENT

# Для Railway.app — порт из переменной окружения
PORT = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
