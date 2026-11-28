# 12-factor app

- Что это
  - Методология из **12 принципов** для cloud-native приложений.
  - Сформулирована в 2011 году инженерами **Heroku** (Adam Wiggins).
  - Не фреймворк, не библиотека — набор **практик и соглашений**.
  - Цель: приложение, которое легко **деплоить, масштабировать, переносить** между средами.
  - Хорошо ложится на **Docker, Kubernetes, CI/CD, GitOps**.
  - Официальный сайт: `12factor.net`.
  - Расширения: **Beyond 12-factor** (observability, security, API-first), **15-factor** (добавляет API-first, telemetry, auth), **12-factor для data** (dataops).

- 12 факторов

  - **1. Codebase (кодовая база)**
    - Одна кодовая база в системе контроля версий (Git), **много деплоев** (dev/stage/prod).
    - Не «одна база — один деплой», а «одна база — много окружений».
    - Несколько кодовых баз → это **распределённая система** (микросервисы), а не одно приложение.
    - Антипаттерн: копирование кода для разных окружений, «ветка prod».

  - **2. Dependencies (зависимости)**
    - Явно объявлять и **изолировать** зависимости (`package.json`, `go.mod`, `requirements.txt`, `pom.xml`).
    - Не полагаться на «глобально установленное» в системе.
    - **Vendoring** — фиксировать версии, lock-файлы.
    - Контейнеры решают это «из коробки»: всё внутри образа.
    - Антипаттерн: `pip install` без `requirements.txt`, зависимость от системных библиотек.

  - **3. Config (конфигурация)**
    - Конфигурация — **в переменных окружения**, не в коде.
    - Разные окружения — разные env, **один и тот же образ**.
    - Не хранить креды, URL, флаги в коде или в файлах в репозитории.
    - В K8s: `ConfigMap` (неконфиденциальное) + `Secret` (конфиденциальное).
    - Антипаттерн: `config.prod.yaml` в Git, захардкоженные пароли, `if (env == "prod")` в коде.

  - **4. Backing services (backing-сервисы)**
    - БД, очереди, кэши, SMTP, внешние API — рассматривать как **подключаемые ресурсы**.
    - Менять их **без изменения кода**: через URL/креды в env.
    - Локальная БД и managed RDS — для приложения **одно и то же**, меняется только конфиг.
    - Антипаттерн: захардкоженный `localhost:5432`, код, знающий про конкретный сервис.

  - **5. Build, release, run (сборка, релиз, запуск)**
    - Строгое разделение трёх стадий:
      - **Build** — сборка артефакта (образ, бинарь) из кода.
      - **Release** — build + config = релиз, неизменяемый.
      - **Run** — запуск релиза в среде.
    - **Нельзя менять код на стадии run** — только пересобрать и сделать новый релиз.
    - В K8s: build → образ с digest → deploy → run.
    - Антипаттерн: `git pull` на проде, правка файлов руками, «горячие фиксы» на сервере.

  - **6. Processes (процессы)**
    - Приложение — **один или несколько stateless-процессов**.
    - **Stateless**: нет состояния в памяти/на диске между запросами.
    - Состояние — в **backing services** (БД, Redis, S3).
    - Процессы можно **убить и пересоздать** в любой момент.
    - Горизонтальное масштабирование — простое (больше реплик).
    - Антипаттерн: sticky sessions, локальный кэш в памяти, файлы на диске контейнера.

  - **7. Port binding (привязка к порту)**
    - Приложение **само слушает порт** и **экспортирует себя** как сервис.
    - Не полагаться на внешний веб-сервер (Apache/nginx) для «запуска» приложения.
    - В K8s: контейнер слушает порт → `Service` → `Ingress`.
    - Антипаттерн: приложение отдаёт CGI-скрипты, зависимость от mod_php.

  - **8. Concurrency (параллелизм)**
    - Масштабирование через **процессы** (горизонтально), а не только через потоки в одном процессе.
    - Разные типы нагрузки — разные процессы: web, worker, scheduler.
    - В K8s: разные `Deployment` для web и worker, HPA для автоскейлинга.
    - Антипаттерн: один процесс на всё, монолит, который нельзя масштабировать частично.

  - **9. Disposability (одноразовость)**
    - Процессы **быстро стартуют** и **корректно завершаются** (graceful shutdown).
    - Обрабатывать **SIGTERM**: доработать текущие запросы, закрыть соединения, отпустить ресурсы.
    - Быстрый старт — для автоскейлинга и canary.
    - **Устойчивость к внезапному kill** (SIGKILL) — не терять данные.
    - В K8s: `terminationGracePeriodSeconds`, `preStop` hook, exec-форма `CMD`.
    - Антипаттерн: долгий старт (миграции в entrypoint), игнорирование SIGTERM, потеря данных при kill.

  - **10. Dev/prod parity (паритет сред)**
    - **Dev, staging, prod максимально похожи**: одинаковый стек, версии, backing services.
    - **Минимизировать разрывы**: time gap (деплой раз в неделю vs каждый день), personnel gap (разработчики vs ops), tools gap (SQLite vs PostgreSQL).
    - В K8s: одинаковый образ во всех средах, разные ConfigMap/Secret.
    - Антипаттерн: SQLite в dev, PostgreSQL в prod; разные версии языка.
    - 12-factor: «the twelve-factor app is designed for continuous deployment by keeping the gap between development and production small».

  - **11. Logs (логи)**
    - Логи — **поток событий** в **stdout/stderr**, не файлы.
    - Приложение **не управляет** логами: не ротирует, не архивирует, не пишет в файл.
    - Сборщик (Fluent Bit, Filebeat, Loki promtail) читает stdout и отправляет в централизованное хранилище (ELK, Loki, CloudWatch).
    - В K8s: `kubectl logs`, logging-агент как DaemonSet.
    - Антипаттерн: `log4j` в файл, ротация внутри приложения, `> /var/log/app.log`.

  - **12. Admin processes (административные процессы)**
    - Одноразовые админ-задачи (миграции, бэкапы, консоль) — **как отдельные процессы**, не как часть основного приложения.
    - Тот же код, тот же образ, та же среда.
    - В K8s: `Job`, `CronJob`, `kubectl exec` для отладки, миграции через `initContainer` или отдельный Job.
    - Антипаттерн: миграции в entrypoint (долгий старт, race conditions), админ-скрипты «на сервере».

- Плюсы 12-factor
  - **Переносимость**: одинаково работает локально, в облаке, on-prem.
  - **Масштабируемость**: stateless-процессы легко масштабировать.
  - **Быстрый деплой**: build → release → run, immutable артефакты.
  - **Dev/prod parity**: меньше «работает у меня локально».
  - **Наблюдаемость**: логи в stdout, метрики, трейсы.
  - **Устойчивость**: graceful shutdown, disposability.
  - **Совместимость с cloud-native**: Docker, K8s, CI/CD, GitOps.
  - **Командная работа**: единые соглашения, меньше сюрпризов.

- Минусы и ограничения
  - **Не про data**: 12-factor не покрывает stateful-сервисы (БД, Kafka), миграции данных, бэкапы.
  - **Не про безопасность**: нет явных принципов про auth, secrets management, supply chain security.
  - **Не про observability**: только логи в stdout, нет метрик/трейсов (Beyond 12-factor добавляет).
  - **Не про API**: нет про API-first, versioning, contracts.
  - **Stateless — не всегда**: stateful-приложения (БД, игровые серверы) плохо ложатся.
  - **Монолиты тоже могут быть 12-factor**: это не только про микросервисы.
  - **Не догма**: некоторые принципы устарели или требуют адаптации (например, «port binding» в serverless).

- 12-factor и Kubernetes — как ложится

| Фактор | В K8s |
|---|---|
| Codebase | Git + ArgoCD/Flux (GitOps) |
| Dependencies | Docker-образ, lock-файлы |
| Config | ConfigMap, Secret, env |
| Backing services | Service, ExternalName, managed DB |
| Build/release/run | CI build → image digest → deploy |
| Processes | stateless Pods, Deployment |
| Port binding | containerPort + Service + Ingress |
| Concurrency | HPA, несколько Deployment (web/worker) |
| Disposability | terminationGracePeriodSeconds, preStop, exec CMD |
| Dev/prod parity | один образ, разные values/overlays |
| Logs | stdout → Fluent Bit → Loki/ELK |
| Admin processes | Job, CronJob |

- 12-factor vs другие методологии
  - **Beyond 12-factor** — добавляет **API-first**, **telemetry** (метрики, трейсы), **authentication/authorization**.
  - **15-factor app** — расширение: API-first, telemetry, auth.
  - **12-factor для data** — dataops, версионирование данных, воспроизводимость.
  - **Cloud Native** (CNCF) — шире: контейнеры, оркестрация, service mesh, observability.
  - **12-factor** — про **приложение**, cloud-native — про **всю экосистему**.

- Типичные вопросы на собеседовании
  - **«Что такое 12-factor app?»** — Методология из 12 принципов для cloud-native приложений: codebase, dependencies, config, backing services, build/release/run, processes, port binding, concurrency, disposability, dev/prod parity, logs, admin processes.
  - **«Какой фактор нарушается, если приложение пишет логи в файл?»** — Фактор 11 (Logs): логи должны быть потоком в stdout/stderr, приложение не управляет ими.
  - **«Почему конфигурация в env, а не в коде?»** — Фактор 3 (Config): один образ — разные окружения, без пересборки; секреты не в Git.
  - **«Почему приложение должно быть stateless?»** — Фактор 6 (Processes): stateless-процессы можно убить и пересоздать, легко масштабировать; состояние — в backing services.
  - **«Что такое graceful shutdown и зачем?»** — Фактор 9 (Disposability): обработка SIGTERM, доработать запросы, закрыть соединения. В K8s — `terminationGracePeriodSeconds`, `preStop`.
  - **«Почему dev и prod должны быть похожи?»** — Фактор 10 (Dev/prod parity): меньше «работает у меня локально», одинаковый стек и версии.
  - **«Как 12-factor relates to Docker/K8s?»** — Docker решает dependencies/port binding, K8s — config (ConfigMap/Secret), processes (stateless Pods), concurrency (HPA), disposability (graceful shutdown), logs (stdout → сборщик).
  - **«Чего не хватает в 12-factor?»** — Security, observability (метрики, трейсы), API-first, data management — Beyond 12-factor / 15-factor.
  - **«Может ли монолит быть 12-factor?»** — Да, 12-factor не про микросервисы, а про практики.
  - **«Почему миграции не в entrypoint?»** — Фактор 12 (Admin processes): миграции — отдельный процесс (Job), иначе долгий старт, race conditions при нескольких репликах.

- Короткий ответ на собеседовании
  - 12-factor app — это методология из 12 принципов для cloud-native приложений, сформулированная в Heroku в 2011 году. Принципы: одна кодовая база — много деплоев (codebase); явные изолированные зависимости (dependencies); конфигурация в env, а не в коде (config); backing services как подключаемые ресурсы (backing services); строгое разделение build/release/run (build, release, run); stateless-процессы (processes); приложение само слушает порт (port binding); масштабирование через процессы (concurrency); быстро стартует и корректно завершается по SIGTERM (disposability); dev/stage/prod максимально похожи (dev/prod parity); логи — поток в stdout/stderr (logs); админ-задачи — отдельные процессы (admin processes). Хорошо ложится на Docker/K8s: ConfigMap/Secret для config, stateless Pods для processes, HPA для concurrency, terminationGracePeriodSeconds для disposability, Fluent Bit для logs, Job для admin processes. Ограничения: не про security, observability (метрики/трейсы), API-first, data management — это Beyond 12-factor / 15-factor. 12-factor не про микросервисы — монолит тоже может быть 12-factor.

- Что запомнить железно
  - **12 принципов**, Heroku, 2011, cloud-native.
  - **Codebase** — одна база, много деплоев.
  - **Dependencies** — явные, изолированные, lock-файлы.
  - **Config** — в env, не в коде.
  - **Backing services** — подключаемые ресурсы (БД, очереди, API).
  - **Build/release/run** — строгое разделение, immutable релизы.
  - **Processes** — stateless, состояние в backing services.
  - **Port binding** — приложение само слушает порт.
  - **Concurrency** — масштабирование через процессы.
  - **Disposability** — быстрый старт, graceful shutdown по SIGTERM.
  - **Dev/prod parity** — одинаковый стек, версии, backing services.
  - **Logs** — поток в stdout/stderr, не файлы.
  - **Admin processes** — отдельные процессы (Job, CronJob), не entrypoint.
  - **В K8s**: ConfigMap/Secret, stateless Pods, HPA, terminationGracePeriodSeconds, Fluent Bit, Job.
  - **Ограничения**: не про security, observability, API-first, data.
  - **Beyond 12-factor / 15-factor** — добавляют API-first, telemetry, auth.