# Affinity

| Задача | Инструмент |
|---|---|
| «Хочу на ноду с label `gpu=true`» | `nodeSelector` |
| «Хочу на SSD, но если нет — на HDD» | `nodeAffinity.preferred` |
| «Только на ноды в зоне `eu-west-1a`» | `nodeAffinity.required` + `topologyKey` |
| «Не размещать два пода `app=web` на одной ноде» | `podAntiAffinity.required` + `topologyKey: hostname` |
| «Стараться не размещать рядом, но можно» | `podAntiAffinity.preferred` |
| «Разные реплики в разных AZ» | `topologySpreadConstraints` (лучше) или `podAntiAffinity.required` + `topologyKey: zone` |
| «Под `app=cache` должен быть на той же ноде, что `app=web`» | `podAffinity.required` + `topologyKey: hostname` |

- текст

| | Jsonnet | Helm | Kustomize |
|---|---|---|---|
| Подход | полноценный язык | текстовые шаблоны (Go) + values | overlay/патчи (YAML) |
| Мощность | высокая (функции, композиция, импорты) | средняя | низкая (патчи) |
| Кривая обучения | **высокая** | средняя | низкая |
| Пакетирование | нет (библиотеки + `jb`) | чарты (OCI, ChartMuseum) | нет |
| Rollback | вручную / GitOps | `helm rollback` | Git revert |
| Экосистема | академическая, Google-adjacent | 20 000+ чартов | встроен в kubectl |
| GitOps | через Tanka/плагины | нативно (ArgoCD/Flux) | нативно |

- **Когда Jsonnet**: нужна сложная генерация, много окружений, DRY, команда готова учить язык, Google-adjacent окружение.

| Шаг | Клиент | Сервер |
|---|---|---|
| До | CLOSED | LISTEN |
| После SYN | SYN_SENT | SYN_RECV |
| После SYN-ACK | SYN_SENT → ESTABLISHED (после ACK) | SYN_RECV |
| После ACK | ESTABLISHED | ESTABLISHED |
  - Видно в `ss -tan` / `netstat -tan`: `SYN-SENT`, `SYN-RECV`, `ESTABLISHED`.
  - **Half-open connection** — состояние `SYN_RECV` на сервере, если клиент не прислал ACK (например, SYN flood).

- Sequence numbers — зачем и почему случайные

| Компонент | Рекомендация |
|---|---|
| **Управление** | Оператор (CloudNativePG, Zalando, Crunchy, Percona) |
| **Хранилище** | Local NVMe (скорость) + durability через репликацию СУБД |
| **reclaimPolicy** | Retain |
| **volumeBindingMode** | WaitForFirstConsumer |
| **Планирование** | podAntiAffinity по hostname + topologySpreadConstraints по zone |
| **Ресурсы** | Guaranteed QoS (requests = limits) |
| **Репликация** | Синхронная кворумная, минимум 3 инстанса |
| **Бэкапы** | WAL-архивация + полные бэкапы + PITR + Velero |
| **NFS для `$PGDATA`** | Не использовать |

- Короткий ответ на собеседовании

| | QoS | PriorityClass |
|---|---|---|
| Как задаётся | автоматически по `requests`/`limits` | вручную в `spec.priorityClassName` |
| Кто использует | kubelet (eviction, OOM score) | scheduler (порядок планирования, preemption) |
| Классы | Guaranteed, Burstable, BestEffort | произвольные (например, `high-priority`, `low-priority`) |
| Влияет на | eviction при давлении на ноду | кого планировать первым, кого вытеснять при нехватке места на ноде |
| Когда срабатывает | когда нода уже под давлением | когда scheduler не может найти место для пода |
  - **PriorityClass** нужен, чтобы критичный под запланировался **первым** и вытеснил менее важные поды (preemption), если места нет.
  - **QoS** нужен, чтобы критичный под **выжил** при eviction на уже работающей ноде.
  - **Обычно используют вместе**: БД → `Guaranteed` + `PriorityClass: high`.
  - **Системные поды** (`kube-system`) имеют высокий PriorityClass (`system-cluster-critical`, `system-node-critical`), чтобы не быть вытесненными.

- Практические рекомендации

| | PriorityClass | QoS |
|---|---|---|
| Как задаётся | **вручную** в `spec.priorityClassName` | **автоматически** по `requests`/`limits` |
| Кто использует | **scheduler** (порядок планирования, preemption) | **kubelet** (eviction при давлении, OOM score) |
| Когда срабатывает | когда под **не может быть запланирован** | когда нода **уже под давлением** ресурсов |
| Что делает | вытесняет низкоприоритетные поды, чтобы освободить место | выселяет поды с низким QoS при нехватке ресурсов на ноде |
| Учитывается ли при выборе жертв preemption | **Да** (только он) | **Нет** (QoS не учитывается в preemption) |
| Для БД | `high` + `Guaranteed` | `Guaranteed` (requests==limits) |
  - **Scheduler учитывает PriorityClass раньше, чем QoS**.
  - Обычно **используют вместе**: БД → PriorityClass `high` + QoS `Guaranteed`.

- Практические рекомендации

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

| | StatefulSet | Deployment |
|---|---|---|
| Имена подов | стабильные (`pg-0`, `pg-1`) | случайные (`pg-7d4b9c8f5-abcde`) |
| DNS | стабильный per-pod через headless Service | общий Service (ClusterIP) |
| Хранилище | свой PVC на под, переживает пересоздание | общий PVC или вообще без |
| Порядок создания/удаления | строгий (OrderedReady) | параллельный |
| Rolling update | по одному, в обратном порядке, ждёт Ready | maxSurge/maxUnavailable, параллельно |
| Идентичность | под = конкретный экземпляр (primary/replica) | поды взаимозаменяемы |
| Для чего | БД, Kafka, Zookeeper, Elasticsearch | stateless-сервисы, web, API |
| Failover/репликация | **не решает** — нужен Оператор | не применимо |

- StatefulSet vs Оператор

| | **ResourceQuota** | **LimitRange** |
|---|---|---|
| **Уровень** | Весь namespace (суммарно) | Отдельный под/контейнер |
| **Что ограничивает** | Общее потребление CPU/памяти/диска и количество объектов | Минимальные/максимальные `requests` и `limits` для одного контейнера, а также дефолтные значения |
| **Когда срабатывает** | При создании/обновлении объекта, если суммарное потребление превышает лимит | При создании/обновлении пода/контейнера, если его `requests`/`limits` выходят за рамки min/max или не заданы (тогда подставляются дефолты) |
| **Цель** | Соблюдение бюджета namespace | Защита от «слишком маленьких» или «слишком больших» контейнеров и заполнение пропущенных ресурсов |
| **Взаимодействие** | Часто используется **вместе** с LimitRange, чтобы все поды имели явные `requests`/`limits` и квота могла их учитывать |

- Плюсы
  - **Простота**: один YAML-объект на namespace.
  - **Гибкость**: можно ограничивать как суммарные ресурсы, так и количество объектов по типам.
  - **Мультитенантность**: основа для безопасного shared-кластера.
  - **Интеграция с admission**: работает автоматически, не требует изменений в приложениях.

- Минусы и подводные камни
  - **Не влияет на уже запущенные поды**: если уменьшить квоту, существующие поды не будут выселены, но новые создать не получится.
  - **Требует явных `requests`/`limits`**: если в namespace включена квота на CPU/память, поды без этих полей будут отклонены.
  - **Не заменяет мониторинг**: квота — это жёсткий лимит, а не рекомендация; при неправильных значениях можно заблокировать создание нужных подов.
  - **Конкуренция за ресурсы**: если суммарные квоты всех namespace превышают容量 кластера, при одновременном пике ресурсы могут не достаться всем (работает принцип «первый пришёл — первый получил»).
  - **`count/*` квоты** не учитывают поды, созданные контроллерами (Deployment, StatefulSet), — они считают объекты API, а не фактические поды.

- `scopes` — дополнительные области действия
  - ResourceQuota можно ограничить определёнными **классами приоритета** или **QoS**:
    - `scope: PriorityClass` — квота только для подов с определённым `priorityClassName`.
    - `scope: BestEffort`, `scope: NotBestEffort` — квота для подов с определённым QoS.
  - Позволяет, например, задать отдельный бюджет для критичных (Guaranteed) и для batch (BestEffort) нагрузок.

- Частые вопросы на собеседовании
  - **«Что такое ResourceQuota?»** — Объект, ограничивающий **суммарное** потребление ресурсов (CPU, память, хранилище) и количество объектов в рамках **namespace**.
  - **«Чем отличается от LimitRange?»** — ResourceQuota — **суммарный** лимит на namespace. LimitRange — лимиты на **каждый отдельный** контейнер/под (min/max/default).
  - **«Что происходит при превышении квоты?»** — API-сервер отклоняет запрос с **HTTP 403 Forbidden** и сообщением о нарушенном ограничении.
  - **«Влияет ли изменение квоты на существующие поды?»** — **Нет**, существующие поды продолжают работать. Квота проверяется только при создании/обновлении объектов.
  - **«Почему под не создаётся, хотя квота не превышена?»** — Возможно, в namespace включена квота на CPU/память, а в поде не заданы `requests`/`limits`. Нужно добавить их или настроить LimitRange для дефолтов.
  - **«Можно ли ограничить количество LoadBalancer-сервисов?»** — Да, через `services.loadbalancers` в `spec.hard`.
  - **«Что такое `scopes` в ResourceQuota?»** — Позволяют применять квоту только к подам с определённым PriorityClass или QoS (например, только к BestEffort).

- Короткий ответ на собеседовании
  - ResourceQuota — это объект Kubernetes, который задаёт **жёсткие лимиты на совокупное потребление ресурсов и количество объектов в рамках одного namespace**. Он работает как admission-контроллер: если создание или обновление ресурса превышает квоту, API-сервер отклоняет запрос с ошибкой 403 Forbidden. ResourceQuota ограничивает суммарные `requests`/`limits` CPU и памяти, объём хранилища, количество подов, сервисов, PVC, ConfigMap и т.д. Важно не путать его с **LimitRange**: ResourceQuota управляет бюджетом всего namespace, а LimitRange — ограничениями на каждый отдельный контейнер (min/max/default). Обычно их используют вместе: LimitRange проставляет дефолтные `requests`/`limits` контейнерам, чтобы ResourceQuota мог корректно учитывать их сумму. ResourceQuota не влияет на уже созданные поды, но блокирует создание новых, если они превышают лимит.

- Что запомнить железно
  - **ResourceQuota — это бюджет namespace**, а не отдельного контейнера.
  - **Ограничивает сумму** CPU, памяти, хранилища и **количество** объектов.
  - **При превышении — 403 Forbidden** при создании/обновлении.
  - **Не влияет на уже запущенные поды**.
  - **Требует явных `requests`/`limits`** у подов, если квота на CPU/память включена.
  - **LimitRange дополняет** ResourceQuota: задаёт дефолты и min/max для контейнеров.
  - **Проверка**: `kubectl get resourcequota -n <namespace>`.