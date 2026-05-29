// SPDX-License-Identifier: MIT
// Отвечает за токены (ERC-1155). Каждый `projectId` — это отдельный тип токена.
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

// Минимальный интерфейс для чтения владельца проекта из реестра
// Это позволяет избежать циклических зависимостей импортов
interface IProjectRegistry {
    function getProjectOwner(uint256 projectId) external view returns (address);
}

contract UniversityToken is ERC1155, AccessControl {
    // Используем стандартные роли OpenZeppelin
    // ORGANIZER_ROLE будет использоваться для вызова mint/burn через AccessControl
    bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE");

    // Адрес контракта реестра проектов (устанавливается при деплое)
    address public registry;

    constructor(address _registry) ERC1155("") {
        // создание главного админа (присваивается тому, кто создаёт этот контракт)
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        registry = _registry;
    }

    /**
     * @dev Выпускает токены для конкретного проекта (projectId = id токена ERC1155)
     * 
     * Правила доступа:
     * 1. Если вызывающий имеет DEFAULT_ADMIN_ROLE -> доступ разрешён (глобальный админ).
     * 2. Если вызывающий имеет ORGANIZER_ROLE -> проверяем, что он владелец проекта.
     * 3. Иначе -> транзакция отклоняется (revert).
     */
    function mint(address to, uint256 projectId, uint256 amount, bytes memory data) external {
        if (hasRole(DEFAULT_ADMIN_ROLE, msg.sender)) {
            // Глобальный админ может делать что угодно
            _mint(to, projectId, amount, data);
        } else {
            // Для организатора:
            // 1. Проверяем наличие роли
            _checkRole(ORGANIZER_ROLE, msg.sender);
            
            // 2. Проверяем владение проектом (защита от межпроектных атак)
            // Если проект не существует, getProjectOwner должен вернуть 0x0, и проверка упадет
            address projectOwner = IProjectRegistry(registry).getProjectOwner(projectId);
            require(projectOwner == msg.sender, "UniversityToken: Caller is not project owner");
            
            _mint(to, projectId, amount, data);
        }
    }

    /**
     * @dev Любой пользователь может сжечь СВОИ токены
     */
    function burn(uint256 projectId, uint256 amount) external {
        _burn(msg.sender, projectId, amount);
    }
    
    /**
     * @dev Админ может сжечь токены у любого пользователя (для штрафов через контракт аукциона)
     */
    function burnFrom(address account, uint256 projectId, uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _burn(account, projectId, amount);
    }

    // Стандартная функция для поддержки интерфейсов (нужна для ERC165)
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC1155, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    // Стандартные функции ERC1155 (balanceOf, safeTransferFrom и т.д.) уже реализованы в базовом контракте
}