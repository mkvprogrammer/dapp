// // SPDX-License-Identifier: MIT
// pragma solidity ^0.8.20;

// // Импортируем интерфейс стандарта ERC1155 для вызова функций безопасного перевода токенов.
// import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
// // Импортируем утилиту-хранитель, которая позволяет данному контракту легально принимать ERC1155 токены.
// // Без этого наследования вызов safeTransferFrom на этот контракт завершится ошибкой.
// import "@openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
// // Импортируем стандартное управление доступом на основе ролей.
// import "@openzeppelin/contracts/access/AccessControl.sol";
// // Импортируем ваши предыдущие контракты для взаимодействия с ними (проверка настроек и сжигание).
// import "./ProjectRegistry.sol";
// import "./UniversityToken.sol";

// // Контракт наследует права доступа и становится легальным приемником ERC1155 токенов.
// contract AuctionManager is AccessControl, ERC1155Holder {
//     // Хэш роли для организаторов, которые имеют право создавать проекты/аукционы и делать возвраты.
//     bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE");
//     bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

//     // Экземпляры внешних контрактов для отправки к ним запросов.
//     IERC1155 public tokenContract;
//     ProjectRegistry public registry;

//     // Структура, описывающая один аукцион.
//     struct Auction {
//         uint256 projectId;        // ID проекта (соответствует ID токена в ERC1155), под который создан аукцион
//         string resourceName;     // Название разыгрываемого ресурса (например, "Место в лаборатории №3")
//         uint256 endTime;          // Метка времени (Unix timestamp) окончания аукциона
//         bool active;              // Статус активности аукциона
//         mapping(address => uint256) bids; // Внутренний маппинг: адрес студента => сумма его заблокированной ставки
//         address[] biddersList;    // Динамический массив адресов участников для возможности перебора (итерации)
//     }

//     // Хранилище (storage): связываем уникальный ID аукциона со структурой его данных.
//     mapping(uint256 => Auction) public auctions;
//     // Счетчик для генерации ID следующего аукциона.
//     uint256 public nextAuctionId;

//     // События для уведомления фронтенда о действиях на аукционе.
//     event AuctionCreated(uint256 indexed auctionId, uint256 projectId, uint256 endTime);
//     event BidPlaced(uint256 indexed auctionId, address user, uint256 amount);
//     event BidCancelled(uint256 indexed auctionId, address user, uint256 penalty);
//     event RefundIssued(uint256 indexed auctionId, address user, uint256 refundedAmount);

//     // Конструктор принимает адреса развернутых в сети токена и реестра.
//     constructor(address _token, address _registry) {
//         tokenContract = IERC1155(_token);
//         registry = ProjectRegistry(_registry);
//         // Деплоер контракта автоматически становится и Главным Админом, и Организатором.
//         _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
//         _grantRole(ORGANIZER_ROLE, msg.sender);
//     }

//     /**
//      * @dev Создание аукциона. Доступно только Организаторам.
//      */
//     function createAuction(
//         uint256 projectId, 
//         string memory resourceName, 
//         uint256 durationSeconds
//     ) external returns (uint256) {
//         // Проверяем: у вызывающего должна быть роль ИЛИ студента, ИЛИ учителя
//         require(
//             hasRole(STUDENT_ROLE, msg.sender) || hasRole(TEACHER_ROLE, msg.sender),
//             "Must be a student or teacher to create an auction"
//         );

//         // Дополнительная безопасность: проверяем через реестр, что проект вообще активен
//         (, , , bool isProjectActive) = registry.getProjectInfo(projectId);
//         require(isProjectActive, "Project is not active");

//         uint256 id = nextAuctionId++;
        
//         // Получаем ссылку на область памяти в storage для инициализации нового аукциона.
//         Auction storage auc = auctions[id];
//         auc.projectId = projectId;
//         auc.resourceName = resourceName;
//         // Время окончания = текущее время блока + длительность в секундах.
//         auc.endTime = block.timestamp + durationSeconds;
//         auc.active = true;
        
//         emit AuctionCreated(id, projectId, auc.endTime);
//         return id;
//     }

//     /**
//      * @dev Участие в аукционе (блокировка/стейкинг токенов студента на балансе этого менеджера)
//      */
//     function placeBid(uint256 auctionId, uint256 amount) external {
//         Auction storage auc = auctions[auctionId];
//         // Проверяем базовые условия: активен ли аукцион, не вышло ли время и валидна ли сумма.
//         require(auc.active, "Auction not active");
//         require(block.timestamp < auc.endTime, "Auction ended");
//         require(amount > 0, "Amount must be > 0");

//         // ПЕРЕВОД ТОКЕНОВ: контракт принудительно забирает токены у студента (msg.sender) на свой адрес.
//         // ВНИМАНИЕ: Студент перед вызовом этой функции обязан вызвать setApprovalForAll на контракте токена
//         // и одобрить действия этого контракта AuctionManager, иначе транзакция упадет.
//         tokenContract.safeTransferFrom(msg.sender, address(this), auc.projectId, amount, "");

//         // Если это самая первая ставка данного студента на этом аукционе, 
//         // добавляем его адрес в массив итерации.
//         if (auc.bids[msg.sender] == 0) {
//             auc.biddersList.push(msg.sender);
//         }
//         // Увеличиваем виртуальный баланс ставки студента в маппинге аукциона.
//         auc.bids[msg.sender] += amount;
        
//         emit BidPlaced(auctionId, msg.sender, amount);
//     }

//     /**
//      * @dev Отмена ставки самим пользователем (со штрафом за отказ)
//      */
//     function cancelBid(uint256 auctionId) external {
//         Auction storage auc = auctions[auctionId];
//         require(auc.active, "Auction not active");
        
//         uint256 bidAmount = auc.bids[msg.sender];
//         require(bidAmount > 0, "No bid to cancel");

//         // Вычисляем, сколько времени осталось до запланированного конца аукциона.
//         // Примечание: если block.timestamp >= auc.endTime, эта строка вызовет ошибку 
//         // из-за переполнения uint256 (в Solidity 0.8.+ встроенная защита от отрицательных чисел).
//         uint256 timeLeft = auc.endTime - block.timestamp;
        
//         // Кросс-контрактный вызов: запрашиваем массив штрафов из контракта реестра ProjectRegistry.
//         // Запятые пропускают ненужные нам возвращаемые параметры (name и refundRate).
//         (, , uint8[4] memory penalties) = registry.getProjectInfo(auc.projectId);
        
//         // Динамический расчет процента штрафа в зависимости от оставшегося времени.
//         uint256 penaltyPercent;
//         if (timeLeft < 2 hours) penaltyPercent = penalties[3];  // Отмена менее чем за 2 часа
//         else if (timeLeft < 8 hours) penaltyPercent = penalties[2];  // Отмена в диапазоне от 1 до 3 суток
//         else if (timeLeft < 24 hours) penaltyPercent = penalties[1];  // Отмена в диапазоне от 1 до 24 часов
//         else if (timeLeft < 48 hours) penaltyPercent = penalties[0];  // Меньше часа до конца — самый жесткий штраф

//         // Считаем сумму штрафа и сумму, которую нужно вернуть студенту.
//         uint256 penaltyAmount = (bidAmount * penaltyPercent) / 100;
//         uint256 refundAmount = bidAmount - penaltyAmount;

//         // Если после штрафа что-то осталось, отправляем эти токены обратно студенту.
//         if (refundAmount > 0) {
//             tokenContract.safeTransferFrom(address(this), msg.sender, auc.projectId, refundAmount, "");
//         }
        
//         // СЖИГАНИЕ ШТРАФА: Т.к. токены штрафа сейчас физически находятся на балансе этого контракта,
//         // мы вызываем burnFrom на контракте UniversityToken, указывая адрес этого контракта (address(this)).
//         // ВНИМАНИЕ: Чтобы этот вызов сработал, при деплое токена этому контракту нужно выдать роль DEFAULT_ADMIN_ROLE в токене.
//         UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penaltyAmount);

//         // Обнуляем ставку студента, чтобы он не мог вызвать отмену повторно.
//         auc.bids[msg.sender] = 0;
//         emit BidCancelled(auctionId, msg.sender, penaltyAmount);
//     }

//     /**
//      * @dev Пустая функция-заглушка для MVP (изначальная задумка автора для пакетного возврата).
//      */
//     function claimRefund(uint256 auctionId, bytes32 /*codeHash*/) external onlyRole(ORGANIZER_ROLE) {
//         // Код закомментирован автором архитектуры, так как пакетный возврат сложен 
//         // и заменен точечной функцией ниже.
//     }
    
//     /**
//      * @dev Точечный частичный возврат средств студенту (вызывается бэкендом вуза после подтверждения посещения занятия)
//      */
//     function processAttendanceRefund(uint256 auctionId, address student) external onlyRole(ORGANIZER_ROLE) {
//         Auction storage auc = auctions[auctionId];
//         // Проверяем: аукцион должен быть либо закрыт принудительно, либо его время вышло.
//         require(!auc.active || block.timestamp >= auc.endTime, "Auction still active");
        
//         uint256 bidAmount = auc.bids[student];
//         require(bidAmount > 0, "No bid");

//         // Запрашиваем базовый процент возврата из реестра (пропуская имя и штрафы).
//         (, uint256 refundRate, ) = registry.getProjectInfo(auc.projectId);
        
//         // Расчет суммы возврата. refundRate измеряется в базисных пунктах (например, 8000 = 80.00%).
//         // Поэтому делим на 10000, а не на 100. Это обеспечивает высокую точность до сотых долей процента.
//         uint256 refundAmount = (bidAmount * refundRate) / 10000;
        
//         // Возвращаем легитимную часть токенов обратно студенту.
//         tokenContract.safeTransferFrom(address(this), student, auc.projectId, refundAmount, "");
        
//         // Если возврат не 100% (например, 80%), оставшиеся 20% токенов удерживаются в качестве
//         // комиссии/удержания системы и безвозвратно сжигаются через контракт токена.
//         uint256 penalty = bidAmount - refundAmount;
//         if (penalty > 0) {
//              UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penalty);
//         }

//         // Обнуляем запись о ставке данного студента, фиксируя завершение расчетов по нему.
//         auc.bids[student] = 0;
//         emit RefundIssued(auctionId, student, refundAmount);
//     }

//     /**
//      * @dev Получение лидерборда (списка участников и их ставок) для отображения на сайте.
//      * Функция view — бесплатна для вызова пользователями.
//      */
//     function getLeaderboard(
//         uint256 auctionId, 
//         uint256 limit) external view returns (address[] memory users, uint256[] memory bids) {
        
//         Auction storage auc = auctions[auctionId];
//         uint256 count = auc.biddersList.length;
        
//         // Если передан лимит отображения (например, топ-10 мест),
//         // уменьшаем размер возвращаемого массива до лимита.
//         if (limit > 0 && limit < count) count = limit;
        
//         // Инициализируем фиксированные массивы в оперативной памяти (memory).
//         // В Solidity динамическое выделение памяти для массивов требует четкого указания размера new type[](size).
//         users = new address;
//         bids = new uint256;
        
//         // Циклом переносим данные из постоянной памяти (storage) во временную (memory) для отправки на фронтенд.
//         for (uint256 i = 0; i < count; i++) {
//             users[i] = auc.biddersList[i];  // Записываем адрес студента
//             bids[i] = auc.bids[auc.biddersList[i]];  // Записываем его текущую ставку
//         }
//         // Автоматически возвращает заполненные массивы users и bids.
//     }
// }



// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "@openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./ProjectRegistry.sol";
import "./UniversityToken.sol";

contract AuctionManager is AccessControl, ERC1155Holder {
    bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE");
    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");
    
    IERC1155 public tokenContract;
    ProjectRegistry public registry;

    struct Auction {
        uint256 projectId;
        string resourceName;
        uint256 endTime;         // Время, когда аукцион закрывается и очередь зафиксирована
        uint256 lessonStartTime; // Новое поле: Время, когда ФИЗИЧЕСКИ начинается занятие/прием работ
        bool active;
        mapping(address => uint256) bids;
        address[] biddersList;
    }

    mapping(uint256 => Auction) public auctions;
    uint256 public nextAuctionId;

    event AuctionCreated(uint256 indexed auctionId, uint256 projectId, uint256 endTime, uint256 lessonStartTime);
    event BidPlaced(uint256 indexed auctionId, address user, uint256 amount);
    event BidCancelled(uint256 indexed auctionId, address user, uint256 penalty);
    event RefundIssued(uint256 indexed auctionId, address user, uint256 refundedAmount);

    constructor(address _token, address _registry) {
        tokenContract = IERC1155(_token);
        registry = ProjectRegistry(_registry);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ORGANIZER_ROLE, msg.sender);
    }

    /**
     * @dev Создание аукциона-очереди. Могут вызывать ORGANIZER и USER.
     * Параметр durationSeconds задает время торгов, а lessonStartTime — время самого занятия.
     */
    function createAuction(
        uint256 projectId, 
        string memory resourceName, 
        uint256 durationSeconds,
        uint256 _lessonStartTime // Передаем Unix-время начала урока (например, 23.05.2026 в 14:00)
    ) external returns (uint256) {
        require(hasRole(USER_ROLE, msg.sender) || hasRole(ORGANIZER_ROLE, msg.sender), "No rights");
        
        uint256 id = nextAuctionId++;
        Auction storage auc = auctions[id];
        auc.projectId = projectId;
        auc.resourceName = resourceName;
        auc.endTime = block.timestamp + durationSeconds;
        
        // Проверка: урок не должен начинаться раньше, чем закончатся торги в аукционе
        require(_lessonStartTime > auc.endTime, "Lesson must start after auction ends");
        auc.lessonStartTime = _lessonStartTime;
        auc.active = true;
        
        emit AuctionCreated(id, projectId, auc.endTime, _lessonStartTime);
        return id;
    }

    /**
     * @dev Стейкинг токенов для участия в очереди
     */
    function placeBid(uint256 auctionId, uint256 amount) external {
        Auction storage auc = auctions[auctionId];
        require(auc.active, "Auction not active");
        require(block.timestamp < auc.endTime, "Auction already ended");
        require(amount > 0, "Amount must be > 0");

        tokenContract.safeTransferFrom(msg.sender, address(this), auc.projectId, amount, "");

        if (auc.bids[msg.sender] == 0) {
            auc.biddersList.push(msg.sender);
        }
        auc.bids[msg.sender] += amount;
        
        emit BidPlaced(auctionId, msg.sender, amount);
    }

    /**
     * @dev Самовольная отмена ставки студентом.
     * Работает как во время аукциона, так и ПОСЛЕ его завершения вплоть до начала урока.
     */
    function cancelBid(uint256 auctionId) external {
        Auction storage auc = auctions[auctionId];
        require(auc.active, "Auction not active");
        
        uint256 bidAmount = auc.bids[msg.sender];
        require(bidAmount > 0, "No bid to cancel");
        
        // Защита: после начала урока отменяться самостоятельно НЕЛЬЗЯ. 
        // Если урок начался — вернуть токены теперь можно только через код преподавателя.
        require(block.timestamp < auc.bodyLessonStartTime(), "Lesson already started, use code confirmation");

        uint256 penaltyPercent = 0;

        // Если аукцион уже закончился, но урок еще не начался — рассчитываем штрафы за срыв очереди
        if (block.timestamp >= auc.endTime) {
            // Вычисляем, сколько времени осталось ДО НАЧАЛА УРОКА
            uint256 timeLeftToLesson = auc.lessonStartTime - block.timestamp;
            
            // Получаем массив штрафов из реестра проектов
            // Будем интерпретировать их под вашу логику: например, [>8h, 8-2h, <2h, прогул]
            (, , uint8[4] memory penalties) = registry.getProjectInfo(auc.projectId);

            if (timeLeftToLesson > 8 hours) {
                penaltyPercent = penalties[0]; // Отписался заранее (например, 5% штрафа)
            } else if (timeLeftToLesson > 2 hours) {
                penaltyPercent = penalties[1]; // Отписался за пару часов, очередь пострадала (например, 20%)
            } else {
                penaltyPercent = penalties[2]; // Отписался прямо перед уроком, подставил всех (например, 50%)
            }
        } 
        // Если block.timestamp < auc.endTime, то penaltyPercent остается равен 0 (бесплатная отмена во время торгов)

        uint256 penaltyAmount = (bidAmount * penaltyPercent) / 100;
        uint256 refundAmount = bidAmount - penaltyAmount;

        // Обнуляем баланс ДО внешних вызовов (Защита от Reentrancy!)
        auc.bids[msg.sender] = 0;

        if (refundAmount > 0) {
            tokenContract.safeTransferFrom(address(this), msg.sender, auc.projectId, refundAmount, "");
        }
        if (penaltyAmount > 0) {
            UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penaltyAmount);
        }

        emit BidCancelled(auctionId, msg.sender, penaltyAmount);
    }

    /**
     * @dev МГНОВЕННЫЙ ВОЗВРАТ ПРИ ПРИСУТСТВИИ (Вызывается бэкендом/учителем в течении дня)
     */
    function processAttendanceRefund(uint256 auctionId, address student) external onlyRole(ORGANIZER_ROLE) {
        Auction storage auc = auctions[auctionId];
        require(auc.active, "Auction not active");
        
        uint256 bidAmount = auc.bids[student];
        require(bidAmount > 0, "No bid");

        // Запрашиваем стандартный процент успешного возврата курса (например, 10000 = 100% возврат)
        (, uint256 refundRate, ) = registry.getProjectInfo(auc.projectId);
        uint256 refundAmount = (bidAmount * refundRate) / 10000;
        
        auc.bids[student] = 0; // Обнуляем

        // Возвращаем студенту его токены прямо во время пары
        tokenContract.safeTransferFrom(address(this), student, auc.projectId, refundAmount, "");
        
        uint256 penalty = bidAmount - refundAmount;
        if (penalty > 0) {
             UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penalty);
        }

        emit RefundIssued(auctionId, student, refundAmount);
    }

    /**
     * @dev ЗАКРЫТИЕ ДНЯ (Штраф для тех, кто не пришел)
     * Вызывается в конце дня (или на следующий день). Сжигает ставки всех, кто остался в маппинге.
     */
    function closeDayAndClearAbsentee(uint256 auctionId) external onlyRole(ORGANIZER_ROLE) {
        Auction storage auc = auctions[auctionId];
        require(auc.active, "Already closed");
        
        // Проверяем, что день урока действительно завершился.
        // Чтобы избежать проблем с задержками учителя, даем студентам время до конца суток (24:00) текущего дня.
        // Занятие началось в какой-то Unix-момент. Окончание дня — это примерно +12 часов от начала, либо жесткий лимит.
        // Для MVP зафиксируем: закрыть день можно только спустя 10 часов после планируемого начала урока.
        require(block.timestamp > auc.lessonStartTime + 10 hours, "Too early to slash, wait for day end");

        (, , uint8[4] memory penalties) = registry.getProjectInfo(auc.projectId);
        uint256 maxPenaltyPercent = penalties[3]; // Самый жесткий штраф за полный прогул (например, 100%)

        // Перебираем всех участников аукциона
        for (uint256 i = 0; i < auc.biddersList.length; i++) {
            address student = auc.biddersList[i];
            uint256 remainingBid = auc.bids[student];

            // Если у студента осталась ставка — значит он не отменился сам и не ввёл код у учителя
            if (remainingBid > 0) {
                auc.bids[student] = 0; // Обнуляем запись

                uint256 penaltyAmount = (remainingBid * maxPenaltyPercent) / 100;
                uint256 refundAmount = remainingBid - penaltyAmount;

                if (refundAmount > 0) {
                    tokenContract.safeTransferFrom(address(this), student, auc.projectId, refundAmount, "");
                }
                if (penaltyAmount > 0) {
                    UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penaltyAmount);
                }
                emit BidCancelled(auctionId, student, penaltyAmount);
            }
        }
        
        auc.active = false; // Закрываем аукцион навсегда
    }

    // Вспомогательная функция для получения времени начала урока (нужна для логики require)
    function bodyLessonStartTime(Auction storage auc) internal view returns (uint256) {
        return auc.lessonStartTime;
    }

    function getLeaderboard(uint256 auctionId, uint256 limit) external view returns (address[] memory users, uint256[] memory bids) {
        Auction storage auc = auctions[auctionId];
        uint256 count = auc.biddersList.length;
        if (limit > 0 && limit < count) count = limit;
        users = new address[](count);
        bids = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            users[i] = auc.biddersList[i];
            bids[i] = auc.bids[auc.biddersList[i]];
        }
    }
}
