% ===================================================
% Лабораторная работа №2. Проект №13 "Вывод статистики"
% Система учёта нарушений ПДД.
% Предикат show_statistics/0 выводит статистику по всем автомобилям:
% общее количество нарушений и среднее количество нарушений на автомобиль.
% Загрузка:  ?- [violations].
% ===================================================

% ---------------- ФАКТЫ ----------------
% violation_type(Код, Описание, Штраф_руб).
violation_type(speeding,   'Превышение скорости',                   500).
violation_type(red_light,  'Проезд на красный свет',               1000).
violation_type(parking,    'Нарушение правил парковки',            1500).
violation_type(no_belt,    'Непристёгнутый ремень безопасности',   1000).
violation_type(phone,      'Разговор по телефону за рулём',        1500).

% car(Госномер, Владелец).
car('А123ВС116', 'Иванов').
car('В456ОР116', 'Петрова').
car('Е789КХ716', 'Сидоров').
car('М321ТТ116', 'Кузнецова').
car('О555ОО16',  'Смирнов').

% violation(Госномер, Код_нарушения, date(Год, Месяц, День)).
violation('А123ВС116', speeding,  date(2025, 1, 14)).
violation('А123ВС116', red_light, date(2025, 2, 3)).
violation('А123ВС116', speeding,  date(2025, 3, 21)).
violation('В456ОР116', parking,   date(2025, 1, 30)).
violation('Е789КХ716', no_belt,   date(2025, 2, 11)).
violation('Е789КХ716', phone,     date(2025, 2, 27)).
violation('Е789КХ716', speeding,  date(2025, 4, 5)).
violation('Е789КХ716', parking,   date(2025, 4, 19)).
violation('М321ТТ116', red_light, date(2025, 3, 8)).
% У автомобиля 'О555ОО16' нарушений нет.

% ---------------- ПРАВИЛА ----------------
% car_violation_count(+Car, -Count): количество нарушений автомобиля Car.
car_violation_count(Car, Count) :-
    car(Car, _),
    aggregate_all(count, violation(Car, _, _), Count).

% total_violations(-Total): общее количество зафиксированных нарушений.
total_violations(Total) :-
    aggregate_all(count, violation(_, _, _), Total).

% cars_count(-N): количество автомобилей в базе.
cars_count(N) :-
    aggregate_all(count, car(_, _), N).

% average_violations(-Avg): среднее количество нарушений на один автомобиль.
% Учитываются все автомобили базы, включая автомобили без нарушений.
average_violations(Avg) :-
    total_violations(Total),
    cars_count(N),
    N > 0,
    Avg is Total / N.

% show_statistics: вывод статистики по всем автомобилям.
show_statistics :-
    format('=== Статистика нарушений ===~n'),
    forall(car(Car, Owner),
           ( car_violation_count(Car, Count),
             format('~w (~w): ~d~n', [Car, Owner, Count])
           )),
    total_violations(Total),
    cars_count(N),
    average_violations(Avg),
    format('Всего автомобилей: ~d~n', [N]),
    format('Общее количество нарушений: ~d~n', [Total]),
    format('Среднее количество нарушений на автомобиль: ~2f~n', [Avg]).

% Примеры запросов:
% ?- show_statistics.
% ?- total_violations(T).
% ?- average_violations(A).
% ?- car_violation_count('А123ВС116', N).
