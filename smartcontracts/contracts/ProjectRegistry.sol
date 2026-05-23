// SPDX-License-Identifier: MIT
// Указывает лицензию кода. MIT означает, что код открытый и его может использовать любой желающий.

// Реестр предметов/курсов. Хранит настройки (штрафы, лимиты) и управляет правами организаторов.
pragma solidity ^0.8.20;
// Указывает компилятору использовать версию Solidity не ниже 0.8.20 для сборки контракта.

// Импортируем стандартный контракт управления доступом от OpenZeppelin.
// Он даст нам роли, функции их выдачи и модификатор onlyRole.
import "@openzeppelin/contracts/access/AccessControl.sol";

// Объявляем контракт ProjectRegistry, который наследует (is) всю логику AccessControl.
contract ProjectRegistry is AccessControl {
    
    // Создаем уникальный 32-байтовый хэш для роли Организатора с помощью keccak256.
    // Ключевое слово constant экономит газ, так как значение заменяется на этапе компиляции.
    bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE");

    // Объявляем структуру (пользовательский тип данных) для хранения настроек каждого проекта.
    struct ProjectSettings {
        string name;              // Название проекта/курса (хранится динамически)
        uint256 refundRate;       // Процент возврата средств в базисных пунктах (например, 8000 = 80.00%)
        uint8[4] penaltySchedule; // Фиксированный массив из 4 элементов для штрафов в зависимости от времени
        bool isActive;            // Флаг: существует/активен ли данный проект
    }

    // Главное хранилище (storage): связываем уникальный ID проекта (uint256) со структурой его настроек.
    mapping(uint256 => ProjectSettings) public projects;
    
    // Счетчик для генерации уникальных ID. Начинается с 0 и увеличивается при каждом создании проекта.
    uint256 public nextProjectId;

    // События (Events) для уведомления внешних приложений (сайтов, бэкенда) о важных действиях.
    // Ключевое слово indexed позволяет быстро фильтровать историю по projectId.
    event ProjectCreated(uint256 indexed projectId, string name, address organizer);
    event SettingsUpdated(
        uint256 indexed projectId, 
        uint256 refundRate, 
        uint8[4] penaltySchedule, 
        bool isActive
    );

    // Конструктор запускается один раз при деплое контракта.
    constructor() {
        // Назначаем создателя контракта (msg.sender) Главным Админом по умолчанию (Суперадмином).
        // Константа DEFAULT_ADMIN_ROLE пришла из унаследованного AccessControl.
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Создание нового предмета/проекта
     * Только пользователи с ролью ORGANIZER_ROLE могут вызывать эту функцию.
     * external экономит газ на чтение аргументов, так как функция вызывается только извне.
     */
    function createProject(
        string memory name,             // Имя передается в memory, так как это динамический тип данных
        uint256 refundRate, 
        uint8[4] memory penaltySchedule // Фиксированный массив также временно создается в памяти memory
    ) external onlyRole(ORGANIZER_ROLE) returns (uint256) {
        
        // Присваиваем текущее значение счетчика локальной переменной id,
        // а сам счетчик тут же увеличиваем на 1 (пост-инкремент ++).
        uint256 id = nextProjectId++;
        
        // Записываем новую структуру настроек в storage-маппинг по сгенерированному id.
        projects[id] = ProjectSettings({
            name: name,
            refundRate: refundRate,
            penaltySchedule: penaltySchedule,
            isActive: true // Активируем проект, чтобы его можно было использовать
        });
        
        // Публикуем в блокчейн событие о том, что проект успешно создан.
        emit ProjectCreated(id, name, msg.sender);
        
        // Возвращаем ID созданного проекта (полезно для вызовов из других смарт-контрактов).
        return id;
    }

    /**
     * @dev Обновление настроек существующего проекта.
     * Доступно только Организаторам.
     */
    function setProjectSettings(
        uint256 projectId, 
        uint256 refundRate, 
        uint8[4] memory penaltySchedule,
        bool isActive
    ) external onlyRole(ORGANIZER_ROLE) {

        // защита от вызова несуществующего проекта
        require(bytes(projects[projectId].name).length > 0, "Project does not exist");

        // Перезаписываем параметры в постоянной памяти (storage) блокчейна.
        projects[projectId].refundRate = refundRate;
        projects[projectId].penaltySchedule = penaltySchedule;
        projects[projectId].isActive = isActive;

        // Логируем изменение настроек для внешних систем.
        emit SettingsUpdated(projectId, refundRate, penaltySchedule, isActive);
    }

    /**
     * @dev Получение информации о проекте.
     * Функция помечена как view, так как она только читает данные и не тратит газ при вызове пользователем.
     */
    function getProjectInfo(uint256 projectId) 
        external 
        view 
        returns (
            string memory name, 
            uint256 refundRate, 
            uint8[4] memory penaltySchedule, 
            bool isActive
        ) 
    {
        // Проверяем ТОЛЬКО существование проекта (имя не должно быть пустым)
        require(bytes(projects[projectId].name).length > 0, "Project does not exist");
        
        ProjectSettings storage p = projects[projectId];
        
        // Возвращаем все данные, включая текущий статус активности
        return (p.name, p.refundRate, p.penaltySchedule, p.isActive);
    }
}
