import numpy as np
import sqlite3

class Casino:
    def __init__(self, initial_balance, bet_size, games_count, db_name='roulette_results.db'):
        self.initial_balance = initial_balance
        self.bet_size = bet_size
        self.games_count = games_count
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # Создаем таблицу. 
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roulette_simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                initial_balance INTEGER,
                bet_size INTEGER,
                games_count INTEGER,            
                label TEXT,
                win_prob REAL,
                coef REAL,
                wins INTEGER,
                losses INTEGER,
                balance_new REAL
            )
        ''')
        self.conn.commit()
    
    def simulate(self, win_prob, label, coef):
        # 1. Генерируем массив чистых исходов (1 или -1) в зависимоти от игры и вероятности
        results_raw = np.random.choice([1, -1], size=self.games_count, p=[win_prob, 1 - win_prob])
        
        # 2. Ищем победы в массие (число 1), заменяем на (ставка * на win coef.) Если нет, минус ставка. 
        money_flow = np.where(results_raw == 1, self.bet_size * coef, -self.bet_size)
        
        # 3. Строим пошаговую историю баланса с помощью кумулятивной суммы
        balance_history = self.initial_balance + np.cumsum(money_flow)
        
        # 4. Проверяем, наступило ли банкротство (баланс <= 0)
        # С помошью векторной фильтрации. Котроая вернет массив [False, False, ..., True] 
        is_bankrupt = balance_history <= 0
        
        if np.any(is_bankrupt): # Если в массиве векторной фильрации есть одно True то...
            # Находим индекс первой игры, где баланс упал до нуля или ниже (первый true в массиве)
            first_bankrupt_index = np.argmax(is_bankrupt)
            
            # Обрезаем массивы до этого шага включительно
            games_played = int(first_bankrupt_index + 1)
            results_raw = results_raw[:games_played]
            balance_new = 0.0  # Игрок всё проиграл
        else:
            # Если банкротства не было, игрок доиграл всю сессию
            games_played = self.games_count
            balance_new = float(balance_history[-1])

        # 5. Пересчитываем wins и losses на основе реально сыгранных раундов
        wins = int(np.sum(results_raw == 1))
        losses = int(np.sum(results_raw == -1))
        
        # 6. Записываем в базу данных. 
        self.cursor.execute(
            '''INSERT INTO roulette_simulations 
               (initial_balance, bet_size, games_count, label, win_prob, coef, wins, losses, balance_new) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (self.initial_balance, self.bet_size, games_played, label, win_prob, coef, wins, losses, balance_new)
        )
        self.conn.commit()
       
    # Хранилище: вероятностей (prob), названия игры (label), коэффицент победы (coef)
    def all_eu(self):
        bets = [
            (18/37, "18 чисел", 1),
            (12/37, "12 чисел", 2),
            (6/37, "6 чисел", 5),
            (4/37, "4 чисел", 8),
            (3/37, "3 чисел", 11),
            (2/37, "2 чисел", 17),
            (1/37, "1 чисел", 35)
        ]
        for prob, label, coef in bets:
            self.simulate(prob, label, coef)

    def close_connection(self):
        self.conn.close()

# --- ЗАПУСК СИМУЛЯЦИИ ---
if __name__ == '__main__':
    for i in range(1000):
        # Стартуем с балансом 1000, ставка 10, планируем 100 игр. (тест ставки 50, 100)
        casino = Casino(initial_balance=1000, bet_size=100, games_count=100)
    
        # Проводим все тесты
        casino.all_eu()
    
        # Закрываем сессию базы данных
        casino.close_connection()
    