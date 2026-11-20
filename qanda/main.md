# Kubernetes. Что такое StatefulSet?

- Что это
  - Контроллер для stateful-приложений (`apps/v1`, `kind: StatefulSet`).
  - Гарантирует **стабильную идентичность** каждого пода: имя, DNS, хранилище.
  - В отличие от Deployment, поды **не взаимозаменяемы** — `pg-0` ≠ `pg-1`.
  - Управляет подами **по порядку**: создаёт 0 → 1 → 2, удаляет 2 → 1 → 0.
  - **Не решает** failover, репликацию, бэкапы — это задача Оператора (CNPG, Percona, Zalando).
  - **Stable** с Kubernetes v1.9.

- Три гарантии StatefulSet
  - **Стабильное сетевое имя**: `pg-0`, `pg-1`, `pg-2` — не меняются при пересоздании.
  - **Стабильный DNS**: `pg-0.pg.default.svc.cluster.local` через **headless Service**.
  - **Стабильное хранилище**: у каждого пода **свой PVC** (`data-pg-0`, `data-pg-1`), который переживает пересоздание пода и привязан к нему по имени.

- Ключевые поля
  - **`serviceName`** (обязательное) — имя **headless Service** (`clusterIP: None`), который даёт DNS-имена подам. Без него StatefulSet не работает как ожидается.
  - **`replicas`** — количество подов.
  - **`selector`** — по каким labels находить поды (иммутабелен, должен совпадать с `template.metadata.labels`).
  - **`template`** — шаблон пода (как в Deployment).
  - **`volumeClaimTemplates`** — шаблон PVC, из которого создаётся **свой PVC на каждый под** (`data-pg-0`, `data-pg-1`, ...).
  - **`podManagementPolicy`** — `OrderedReady` (по умолчанию) или `Parallel`.
  - **`updateStrategy`** — `RollingUpdate` (по умолчанию) или `OnDelete`.
  - **`revisionHistoryLimit`** — сколько ревизий хранить (default 10).
  - **`persistentVolumeClaimRetentionPolicy`** (K8s 1.27+, stable 1.32) — удалять ли PVC при удалении пода/StatefulSet.

- Порядок создания и удаления (OrderedReady)
  - **Создание**: строго по порядку `0 → 1 → 2`. Под `N+1` создаётся **только когда под `N` стал `Ready`**.
  - **Удаление**: строго в обратном порядке `2 → 1 → 0`.
  - **Rolling update**: обновляет поды в обратном порядке (с наибольшего номера), по одному, ждёт `Ready`.
  - **Зачем**: для кластеров с quorum (Zookeeper, etcd, Kafka) — нельзя поднимать всех одновременно, иначе не будет кворума.
  - **`podManagementPolicy: Parallel`** — создаёт/удаляет все поды одновременно, без ожидания `Ready`. Для приложений, где порядок не важен, но нужна идентичность (например, некоторые кэши).

  - **`clusterIP: None`** — Service не имеет виртуального IP, DNS возвращает **IP подов напрямую**.
  - DNS-имена:
    - `pg-0.pg.default.svc.cluster.local` — конкретный под.
    - `pg.default.svc.cluster.local` — все поды (round-robin на уровне DNS).
  - **Зачем**: StatefulSet использует `serviceName`, чтобы дать каждому поду **уникальное DNS-имя**. Приложение (или Оператор) может обращаться к конкретному поду (`pg-0` — primary, `pg-1` — replica).
  - **Без headless Service** StatefulSet создастся, но DNS-идентичности не будет — pods будут видны только по IP, которые меняются.
  - Для каждого пода создаётся **свой PVC**: `data-pg-0`, `data-pg-1`, `data-pg-2`.
  - PVC **привязан к поду по имени** — при пересоздании пода `pg-0` он монтирует **тот же** `data-pg-0`.
  - **PVC не удаляются** при удалении пода или scale down — данные сохраняются.
  - **При удалении StatefulSet** PVC **тоже остаются** (по умолчанию) — нужно чистить вручную или через `persistentVolumeClaimRetentionPolicy: Delete`.
  - **Resize PVC**: если StorageClass `allowVolumeExpansion: true`, можно увеличить размер PVC, но **не уменьшить**.
  - **`volumeBindingMode: WaitForFirstConsumer`** — обязательно для multi-AZ (EBS, GCE PD, local PV), иначе PV создастся в одной AZ, а под запланируется в другой.

- Пример StatefulSet
  ```yaml
  apiVersion: apps/v1
  kind: StatefulSet
  metadata:
    name: pg
  spec:
    serviceName: pg
    replicas: 3
    selector:
      matchLabels:
        app: postgres
    template:
      metadata:
        labels:
          app: postgres
      spec:
        containers:
        - name: postgres
          image: postgres:16
          ports:
          - containerPort: 5432
          volumeMounts:
          - name: data
            mountPath: /var/lib/postgresql/data
    volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast
        resources:
          requests:
            storage: 100Gi
  ```

- StatefulSet vs Deployment
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
  - **StatefulSet** даёт: имена, DNS, PVC, порядок.
  - **StatefulSet не даёт**: автоматический failover, репликацию, бэкапы, PITR, выбор primary, обновления версий БД.
  - **Оператор** (CNPG, Percona, Zalando, Crunchy) **оборачивает** StatefulSet (или управляет подами напрямую, как CNPG) и добавляет логику эксплуатации.
  - **Правило**: для БД в проде — **Оператор**, а не «голый» StatefulSet.
  - **CNPG** вообще **не использует StatefulSet** — управляет подами и PVC напрямую через свой контроллер + instance manager в поде.

- `podManagementPolicy`
  - **`OrderedReady`** (default) — строгий порядок: создаёт `0 → 1 → 2`, ждёт `Ready` перед следующим. Удаляет `2 → 1 → 0`.
  - **`Parallel`** — все поды создаются/удаляются одновременно, без ожидания `Ready`. Быстрее, но нет гарантий порядка.
  - **Когда `Parallel`**: приложения, где порядок не важен, но нужна идентичность (например, кэши, некоторые worker'ы).
  - **Когда `OrderedReady`**: quorum-based (Zookeeper, etcd, Kafka), БД с primary/replica.

- `updateStrategy`
  - **`RollingUpdate`** (default) — обновляет поды по одному, в обратном порядке (`2 → 1 → 0`), ждёт `Ready` перед следующим.
  - **`OnDelete`** — не обновляет автоматически; новый под создаётся только когда старый **удалён вручную**. Для ручного контроля (например, БД, где обновление требует orchestration).
  - **`partition`** (в RollingUpdate) — обновлять только поды с номером `>= partition` (canary-подход).

- `persistentVolumeClaimRetentionPolicy` (K8s 1.27+ beta, stable 1.32)
  ```yaml
  persistentVolumeClaimRetentionPolicy:
    whenDeleted: Retain   # при удалении StatefulSet
    whenScaled: Retain    # при scale down
  ```
  - **`Retain`** (default) — PVC остаются (данные сохраняются).
  - **`Delete`** — PVC удаляются вместе с подом/StatefulSet.
  - **Осторожно с `Delete`**: данные теряются. Для прода с БД — `Retain`.

- Типичные проблемы и подводные камни
  - **Забыли `serviceName` / headless Service** → нет стабильного DNS, Оператор не может найти поды по имени.
  - **`podManagementPolicy: OrderedReady` + под не становится `Ready`** → весь StatefulSet застревает (например, `pg-1` не поднялся → `pg-2` не создаётся).
  - **Readiness probe критична**: без неё StatefulSet считает под готовым сразу после запуска и идёт дальше — можно получить неготовый кластер.
  - **PVC не удаляются при удалении StatefulSet** → «висящие» PVC, занимают место. Чистить вручную или `persistentVolumeClaimRetentionPolicy`.
  - **PVC не удаляются при scale down** → scale down с 5 до 3 оставляет `data-pg-3`, `data-pg-4`. При scale up обратно — они переиспользуются.
  - **Resize PVC только вверх** — уменьшить нельзя.
  - **`volumeBindingMode: Immediate` + multi-AZ** → PV в одной AZ, под в другой → Pending. Нужен `WaitForFirstConsumer`.
  - **StatefulSet не делает failover** — при падении `pg-0` (primary) никто не назначит нового primary. Нужен Оператор.
  - **`OrderedReady` + rolling update** → обновление идёт с последнего пода, но если `pg-2` не поднялся, `pg-1` и `pg-0` не обновятся.
  - **`selector` иммутабелен** — нельзя поменять после создания.
  - **`commonLabels` в Kustomize** может сломать `selector` — использовать `labels`.

- Частые вопросы на собеседовании
  - **«Что такое StatefulSet?»** — Контроллер для stateful-приложений, даёт стабильные имена, DNS и PVC на каждый под, упорядоченный жизненный цикл.
  - **«StatefulSet vs Deployment?»** — StatefulSet: стабильные имена/DNS/PVC, порядок, поды не взаимозаменяемы. Deployment: случайные имена, общий Service, поды взаимозаменяемы, для stateless.
  - **«Зачем headless Service?»** — Даёт стабильные DNS-имена подам (`pg-0.pg.default.svc.cluster.local`), чтобы можно было обращаться к конкретному экземпляру. Без него StatefulSet не даёт сетевой идентичности.
  - **«Что такое `volumeClaimTemplates`?»** — Шаблон PVC, из которого создаётся **свой PVC на каждый под** (`data-pg-0`, `data-pg-1`). PVC привязан к поду по имени, переживает пересоздание.
  - **«Что происходит с PVC при удалении StatefulSet?»** — По умолчанию **остаются** (Retain). Удаляются только при `persistentVolumeClaimRetentionPolicy: Delete`.
  - **«`OrderedReady` vs `Parallel`?»** — OrderedReady: строгий порядок (0→1→2), ждёт Ready. Parallel: все сразу, для приложений без порядка.
  - **«Делает ли StatefulSet failover?»** — **Нет**. StatefulSet только даёт идентичность. Failover, репликацию, бэкапы делает Оператор (CNPG, Percona, Zalando).
  - **«Можно ли использовать StatefulSet для БД в проде?»** — Технически да, но нужен Оператор сверху. «Голый» StatefulSet не решает failover и бэкапы.
  - **«Что такое `persistentVolumeClaimRetentionPolicy`?»** — Управляет удалением PVC при удалении StatefulSet или scale down. `Retain` (default) или `Delete`.
  - **«Почему StatefulSet обновляет поды в обратном порядке?»** — Чтобы не потерять quorum и primary: сначала обновляются реплики, потом (если нужно) primary через orchestration Оператора.
  - **«CNPG использует StatefulSet?»** — **Нет**, CNPG управляет подами и PVC напрямую через свой контроллер + instance manager. StatefulSet не даёт нужного контроля для failover по LSN.

- Короткий ответ на собеседовании
  - StatefulSet — это контроллер Kubernetes для stateful-приложений. Он даёт три гарантии: стабильные имена подов (`pg-0`, `pg-1`), стабильный DNS через headless Service (`pg-0.pg.default.svc.cluster.local`) и стабильное хранилище — свой PVC на каждый под через `volumeClaimTemplates`, который переживает пересоздание пода. Поды управляются в строгом порядке (`OrderedReady`: 0→1→2, ждёт Ready), обновляются по одному в обратном порядке. В отличие от Deployment, поды не взаимозаменяемы — `pg-0` и `pg-1` имеют разную идентичность. StatefulSet **не решает** failover, репликацию, бэкапы, PITR — для этого нужен **Оператор** (CNPG, Percona, Zalando, Crunchy), который оборачивает StatefulSet (или управляет подами напрямую, как CNPG). `podManagementPolicy: Parallel` — для приложений без порядка. `persistentVolumeClaimRetentionPolicy` управляет удалением PVC при удалении StatefulSet или scale down. Типичные ловушки: забыли headless Service, `OrderedReady` + под не Ready → весь StatefulSet застревает, PVC остаются после удаления, `volumeBindingMode: Immediate` + multi-AZ → Pending, resize PVC только вверх.

- Что запомнить железно
  - **StatefulSet = стабильные имена + DNS + PVC на под + порядок**.
  - **Headless Service (`clusterIP: None`) обязателен** для DNS-идентичности.
  - **`volumeClaimTemplates`** → свой PVC на каждый под (`data-pg-0`).
  - **PVC переживают пересоздание пода**, по умолчанию **не удаляются** с StatefulSet.
  - **`OrderedReady`** (default): 0→1→2, ждёт Ready. **`Parallel`** — все сразу.
  - **Rolling update** — по одному, в обратном порядке.
  - **StatefulSet не делает failover** — для этого Оператор.
  - **`persistentVolumeClaimRetentionPolicy`** (1.27+): `Retain` (default) или `Delete`.
  - **Readiness probe критична** — без неё StatefulSet идёт дальше с неготовым подом.
  - **`volumeBindingMode: WaitForFirstConsumer`** — для multi-AZ.
  - **Resize PVC только вверх**, при `allowVolumeExpansion: true`.
  - **CNPG не использует StatefulSet** — управляет подами напрямую.