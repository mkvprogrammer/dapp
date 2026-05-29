// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Импорт интерфейса ERC1155 для взаимодействия со стандартом токенов (переводы, балансы).
import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
// Импорт базового контракта-холдера, который реализует функцию onERC1155Received.
// Это позволяет нашему контракту легально принимать токены ERC1155 через safeTransferFrom.
import "@openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
// Импорт механизма управления доступом на основе ролей (AccessControl) от OpenZeppelin.
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165.sol";  // Для ERC165

// Импорт интерфейсов ваших кастомных контрактов для взаимодействия с реестром проектов и логикой токена.
import "./ProjectRegistry.sol";
import "./UniversityToken.sol";

/**
 * @title AuctionManager
 * @dev Контракт управляет системой аукционов-очередей для записи на занятия/лабораторные работы.
 *      Реализует механику стейкинга токенов, динамических штрафов за отмену и возврат средств при посещении.
 *      Наследует AccessControl для разграничения прав и ERC1155Holder для приема токенов.
 */
contract AuctionManager is AccessControl, ERC1155Holder {
    
    // --- РОЛИ И КОНСТАНТЫ ---

    // Роль организатора (преподавателя/администратора): может создавать аукционы, подтверждать посещение и закрывать дни.
    bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE");
    
    // Роль обычного пользователя (студента): может создавать аукционы (если разрешено бизнес-логикой) и участвовать в них.
    // Примечание: в текущей реализации USER_ROLE используется для проверки прав создания, 
    // но участие в ставках открыто для всех, кто имеет токены.
    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    uint256 private constant BASIS_POINTS = 10000;
    
    // --- ВНЕШНИЕ ЗАВИСИМОСТИ ---

    // Интерфейс контракта токена UniversityToken (ERC1155). Используется для блокировки и возврата средств.
    IERC1155 public tokenContract;
    
    // Интерфейс реестра проектов. Хранит настройки штрафов и процентов возврата для разных типов занятий.
    ProjectRegistry public registry;

    // --- СТРУКТУРЫ ДАННЫХ ---

    /**
     * @dev Структура, описывающая один аукцион (очередь на занятие).
     */
    struct Auction {
        uint256 projectId;        // ID проекта/курса, к которому привязан этот аукцион (соответствует ID токена в ERC1155).
        string resourceName;      // Название ресурса или темы занятия (например, "Лабораторная работа №1").
        uint256 endTime;          // Unix-timestamp окончания фазы торгов (после этого времени новые ставки невозможны, но можно отменяться со штрафом).
        uint256 lessonStartTime;  // Unix-timestamp физического начала занятия. Важно для расчета штрафов за позднюю отмену.
        bool active;              // Флаг активности аукциона. Если false, аукцион закрыт и больше не принимает действий.
        uint256 resourceLimit;

        // Маппинг ставок: адрес студента -> сумма заблокированных токенов.
        mapping(address => uint256) bids;
        // флаг прогульщика, выставляемый учителем
        mapping(address => bool) isAbsent;
        
        // Список адресов всех участников, сделавших хотя бы одну ставку. 
        // Необходим для итерации при массовых операциях (например, закрытие дня), так как маппинги нельзя перебирать напрямую.
        address[] biddersList;
    }

    // --- ХРАНИЛИЩЕ СОСТОЯНИЯ ---

    // Маппинг всех аукционов по их уникальному ID.
    mapping(uint256 => Auction) public auctions;
    
    // Счетчик для генерации уникальных ID новых аукционов.
    uint256 public nextAuctionId;

    // --- СОБЫТИЯ (EVENTS) ---
    // События необходимы для индексации данных фронтендом и отслеживания истории изменений в блокчейне.

    event AuctionCreated(uint256 indexed auctionId, uint256 projectId, uint256 endTime, uint256 lessonStartTime);
    event BidPlaced(uint256 indexed auctionId, address user, uint256 amount);
    event BidCancelled(uint256 indexed auctionId, address user, uint256 penalty);
    event RefundIssued(uint256 indexed auctionId, address user, uint256 refundedAmount);
    event StudentMarkedAbsent(uint256 indexed auctionId, address student);

    // --- КОНСТРУКТОР ---

    /**
     * @dev Конструктор контракта.
     * @param _token Адрес развернутого контракта UniversityToken.
     * @param _registry Адрес развернутого контракта ProjectRegistry.
     * Назначает деплоера контракта администратором и организатором по умолчанию.
     */
    constructor(address _token, address _registry) {
        tokenContract = IERC1155(_token);
        registry = ProjectRegistry(_registry);
        
        // Выдача прав администратора и организатора адресу, который деплоит контракт.
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ORGANIZER_ROLE, msg.sender);
    }

    // --- ФУНКЦИИ УПРАВЛЕНИЯ АУКЦИОНАМИ ---

    /**
     * @dev Создание нового аукциона-очереди.
     * Доступно только пользователям с ролью USER_ROLE или ORGANIZER_ROLE.
     * 
     * @param projectId ID проекта, для которого создается очередь.
     * @param resourceName Текстовое описание занятия.
     * @param durationSeconds Длительность фазы торгов в секундах (относительно текущего времени).
     * @param _lessonStartTime Абсолютное время (Unix timestamp) начала физического занятия.
     * @return id Уникальный идентификатор созданного аукциона.
     */
    function createAuction(
        uint256 projectId, 
        string memory resourceName, 
        uint256 durationSeconds,
        uint256 _lessonStartTime,
        uint256 _resourceLimit // Передаем лимит (например, 10 мест на сдачу)
    ) external returns (uint256) {
        // Проверка прав доступа: только авторизованные пользователи могут создавать очереди.
        require(hasRole(USER_ROLE, msg.sender) || hasRole(ORGANIZER_ROLE, msg.sender), "No rights");
        require(_resourceLimit > 0, "Limit must be > 0");

        uint256 id = nextAuctionId++;
        Auction storage auc = auctions[id];
        
        auc.projectId = projectId;
        auc.resourceName = resourceName;
        // Расчет времени окончания торгов: текущее время блока + длительность.
        auc.endTime = block.timestamp + durationSeconds;
        
        // Логическая проверка: занятие не может начаться раньше, чем закончатся торги.
        // Это гарантирует, что у студентов будет время сделать ставки до начала урока.
        require(_lessonStartTime > auc.endTime, "Lesson must start after auction ends");
        auc.lessonStartTime = _lessonStartTime;
        auc.resourceLimit = _resourceLimit;
        auc.active = true;
        
        emit AuctionCreated(id, projectId, auc.endTime, _lessonStartTime);
        return id;
    }

    // --- ФУНКЦИИ УЧАСТИЯ (СТАВКИ) ---

    /**
     * @dev Placement ставки (стейкинг токенов) для участия в аукционе.
     * Студент блокирует токены на балансе этого контракта в обмен на место в очереди.
     * 
     * @param auctionId ID аукциона.
     * @param amount Количество токенов для ставки.
     */
    function placeBid(uint256 auctionId, uint256 amount) external {
        Auction storage auc = auctions[auctionId];
        
        // Проверки состояния аукциона:
        require(auc.active, "Auction not active"); // Аукцион должен быть активен.
        require(block.timestamp < auc.endTime, "Auction already ended"); // Торги должны быть открыты.
        require(amount > 0, "Amount must be > 0"); // Ставка должна быть положительной.

        // БЕЗОПАСНЫЙ ПЕРЕВОД ТОКЕНОВ:
        // Контракт забирает токены у студента (msg.sender) на свой баланс.
        // ВАЖНО: Студент должен предварительно вызвать approve/setApprovalForAll в контракте токена для этого адреса.
        tokenContract.safeTransferFrom(msg.sender, address(this), auc.projectId, amount, "");

        // Если студент участвует впервые, добавляем его в список для последующей итерации.
        if (auc.bids[msg.sender] == 0) {
            auc.biddersList.push(msg.sender);
        }
        
        // Увеличиваем сумму ставки студента (накопительный эффект, если он делает несколько транзакций).
        auc.bids[msg.sender] += amount;
        
        emit BidPlaced(auctionId, msg.sender, amount);
    }

    // --- ФУНКЦИИ ОТМЕНЫ И ШТРАФОВ ---

    /**
     * @dev Проверяет, входит ли студент в топ гарантированных мест по размеру ставки.
     * Возвращает true, если студент НАХОДИТСЯ в топ-N мест.
     */
    function isStudentInGuaranteedTop(uint256 auctionId, address student) public view returns (bool) {
        Auction storage auc = auctions[auctionId];
        uint256 myBid = auc.bids[student];
        if (myBid == 0) return false;

        uint256 dynamicPosition = 1;
        // Пробегаемся по всем участникам и считаем, у скольких людей ставка выше нашей
        for (uint256 i = 0; i < auc.biddersList.length; i++) {
            address other = auc.biddersList[i];
            if (other != student && auc.bids[other] > myBid) {
                dynamicPosition++;
            }
        }
        // Если позиция в списке меньше или равна лимиту мест — студент в топе
        return dynamicPosition <= auc.resourceLimit;
    }


    /**
    * @dev Удаляет адрес из списка участников аукциона (swap-and-pop, O(1)).
    * Безопасно: если адреса нет в списке — ничего не делает.
    */
    function _removeBidderFromList(Auction storage auc, address bidder) internal {
        address[] storage list = auc.biddersList;
        uint256 len = list.length;
        
        for (uint256 i = 0; i < len; i++) {
            if (list[i] == bidder) {
                if (i != len - 1) {
                    list[i] = list[len - 1];
                }
                list.pop();
                break;
            }
        }
    }


    /**
     * @dev Отмена ставки самим студентом.
     * Логика штрафов зависит от того, на какой стадии находится аукцион относительно начала урока.
     * 
     * @param auctionId ID аукциона.
     */
    function cancelBid(uint256 auctionId) external {
        Auction storage auc = auctions[auctionId];
        //require(auc.active, "Auction not active");
        
        uint256 bidAmount = auc.bids[msg.sender];
        require(bidAmount > 0, "No bid to cancel");
        
        // ЗАЩИТА ОТ ПОЗДНЕЙ ОТМЕНЫ:
        // Если урок уже начался, студент не может отменить ставку самостоятельно.
        // Возврат возможен только через преподавателя (processAttendanceRefund) или после закрытия дня.
        // Используем внутреннюю функцию для получения времени начала урока.
        require(block.timestamp < getLessonStartTime(auc), "Lesson already started, use code confirmation");

        uint256 penaltyPercent = 0;

        // ЛОГИКА РАСЧЕТА ШТРАФА:
        // Если торги завершены, проверяем, где находится студент в очереди
        if (block.timestamp >= auc.endTime) {
            // Если студент НЕ попал в лимит гарантированных мест (в «хвосте» очереди)
            if (!isStudentInGuaranteedTop(auctionId, msg.sender)) {
                penaltyPercent = 0; // Ему отмена БЕСПЛАТНА в любой момент до урока!
            } else {
                // Если он был в ТОПе, но решил сняться — рассчитываем стандартный штраф за срыв
                uint256 timeLeftToLesson = auc.lessonStartTime - block.timestamp;
                (, , , uint16[4] memory penalties, ) = registry.getProjectInfo(auc.projectId);

                if (timeLeftToLesson > 8 hours) penaltyPercent = penalties[0];
                else if (timeLeftToLesson > 2 hours) penaltyPercent = penalties[1];
                else penaltyPercent = penalties[2];
            }
        } 
        // Если block.timestamp < auc.endTime, штраф равен 0 (бесплатная отмена во время активной фазы торгов).

        // Расчет сумм
        uint256 penaltyAmount = (bidAmount * penaltyPercent) / BASIS_POINTS;
        uint256 refundAmount = bidAmount - penaltyAmount;

        // ПАТТЕРН CHECKS-EFFECTS-INTERACTIONS:
        // Сначала обнуляем баланс пользователя внутри контракта, чтобы предотвратить реентерабельность (reentrancy).
        auc.bids[msg.sender] = 0;

        _removeBidderFromList(auc, msg.sender);

        // Внешние взаимодействия (переводы и сжигание) выполняются после обновления состояния.
        if (refundAmount > 0) {
            // Возврат оставшейся части токенов студенту.
            tokenContract.safeTransferFrom(address(this), msg.sender, auc.projectId, refundAmount, "");
        }
        
        if (penaltyAmount > 0) {
            // Сжигание штрафной части токенов.
            // Требует, чтобы у этого контракта были права на сжигание (burn) токенов в контракте UniversityToken.
            UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penaltyAmount);
        }

        emit BidCancelled(auctionId, msg.sender, penaltyAmount);
    }

    // --- ФУНКЦИИ АДМИНИСТРИРОВАНИЯ (ПРЕПОДАВАТЕЛЬ) ---

    /**
     * @dev МЕХАНИЗМ УЧИТЕЛЯ №1: Отметить прогульщика (кто занял место в топе, но не пришел)
     */
    function markAsAbsent(uint256 auctionId, address student) external onlyRole(ORGANIZER_ROLE) {
        Auction storage auc = auctions[auctionId];
        require(auc.active, "Auction not active");
        require(auc.bids[student] > 0, "Student has no bid");
        
        auc.isAbsent[student] = true;
        emit StudentMarkedAbsent(auctionId, student);
    }

    /**
     * @dev МЕХАНИЗМ УЧИТЕЛЯ №2: Успешный прием ответа (Мгновенный возврат во время пары)
     */
    function processAttendanceRefund(uint256 auctionId, address student) external onlyRole(ORGANIZER_ROLE) {
        Auction storage auc = auctions[auctionId];
        require(auc.active, "Auction not active");
        
        uint256 bidAmount = auc.bids[student];
        require(bidAmount > 0, "No bid");

        (, , uint256 refundRate, , ) = registry.getProjectInfo(auc.projectId);
        uint256 refundAmount = (bidAmount * refundRate) / BASIS_POINTS;
        
        auc.bids[student] = 0;
        _removeBidderFromList(auc, student);

        tokenContract.safeTransferFrom(address(this), student, auc.projectId, refundAmount, "");
        
        uint256 penalty = bidAmount - refundAmount;
        if (penalty > 0) {
             UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penalty);
        }

        emit RefundIssued(auctionId, student, refundAmount);
    }

    /**
     * @dev МЕХАНИЗМ УЧИТЕЛЯ №3: Мягкое закрытие урока в конце дня.
     * Возвращает 100% баланса всем, кого учитель не успел принять, и жестко сжигает токены прогульщиков.
     */
    function closeDayAndRefundRemaining(uint256 auctionId) external onlyRole(ORGANIZER_ROLE) {
        Auction storage auc = auctions[auctionId];
        //require(auc.active, "Already closed");
        
        // Закрыть день можно только после фактического начала урока
        require(block.timestamp > auc.lessonStartTime, "Lesson hasn't started yet");

        (, , , uint16[4] memory penalties, ) = registry.getProjectInfo(auc.projectId);
        uint256 maxPenaltyPercent = penalties[3]; // Штраф за полный прогул (например, 50%)

        // Перебираем всю очередь
        for (uint256 i = 0; i < auc.biddersList.length; i++) {
            address student = auc.biddersList[i];
            uint256 remainingBid = auc.bids[student];

            if (remainingBid > 0) {
                auc.bids[student] = 0; // Сбрасываем баланс

                // ЕСЛИ УЧИТЕЛЬ ОТМЕТИЛ СТУДЕНТА КАК ПРОГУЛЬЩИКА:
                if (auc.isAbsent[student] == true) {
                    uint256 penaltyAmount = (remainingBid * maxPenaltyPercent) / BASIS_POINTS;
                    uint256 refundAmount = remainingBid - penaltyAmount;

                    if (refundAmount > 0) {
                        tokenContract.safeTransferFrom(address(this), student, auc.projectId, refundAmount, "");
                    }
                    if (penaltyAmount > 0) {
                        UniversityToken(address(tokenContract)).burnFrom(address(this), auc.projectId, penaltyAmount);
                    }
                    emit BidCancelled(auctionId, student, penaltyAmount);
                } 
                // ЕСЛИ СТУДЕНТ ПРОСТО ОСТАЛСЯ В ОЧЕРЕДИ (Учитель до него не дошел или забыл отметить):
                else {
                    // Возвращаем ВСЕ 100% БЕЗ ШТРАФОВ И БЕЗ СНИЖЕНИЯ КОМИССИИ РЕЕСТРА!
                    tokenContract.safeTransferFrom(address(this), student, auc.projectId, remainingBid, "");
                    emit RefundIssued(auctionId, student, remainingBid);
                }
            }
        }
        
        auc.active = false; // Закрываем этот день навсегда
    }

    // --- VIEW ФУНКЦИИ И УТИЛИТЫ ---

    /**
     * @dev Внутренняя функция-геттер для безопасного доступа к времени начала урока из структуры.
     * Используется для соблюдения принципа инкапсуляции и удобства чтения кода.
     */
    function getLessonStartTime(Auction storage auc) internal view returns (uint256) {
        return auc.lessonStartTime;
    }

    /**
     * @dev Получение лидерборда (списка участников и их ставок).
     * Используется фронтендом для отображения текущей очереди.
     * 
     * @param auctionId ID аукциона.
     * @param limit Ограничение количества возвращаемых записей (для пагинации). Если 0, возвращает всех.
     * @return users Массив адресов участников.
     * @return bids Массив соответствующих им ставок.
     */
    function getLeaderboard(uint256 auctionId, uint256 limit) external view returns (address[] memory users, uint256[] memory bids) {
        Auction storage auc = auctions[auctionId];
        uint256 count = auc.biddersList.length;
        
        // Применяем лимит, если он задан и меньше общего количества участников.
        if (limit > 0 && limit < count) {
            count = limit;
        }
        
        // Инициализация массивов в памяти фиксированного размера.
        users = new address[](count);
        bids = new uint256[](count);
        
        // Копирование данных из Storage в Memory для возврата.
        for (uint256 i = 0; i < count; i++) {
            users[i] = auc.biddersList[i];
            bids[i] = auc.bids[auc.biddersList[i]];
        }
    }

    function supportsInterface(bytes4 interfaceId) public view virtual override(AccessControl, ERC1155Receiver) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

}