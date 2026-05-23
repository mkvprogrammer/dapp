// SPDX-License-Identifier: MIT
// Отвечает за токены (ERC-1155). Каждый `projectId` — это отдельный тип токена.
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract UniversityToken is ERC1155, AccessControl {
    // Используем стандартные роли OpenZeppelin
    // DEFAULT_ADMIN_ROLE = 0x00...00
    // ORGANIZER_ROLE будет использоваться для вызова mint/burn через AccessControl

    constructor() ERC1155("") {
        // создание главного админа (присваивается тому, кто создаёт этот контракт)
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Выпускает токены для конкретного проекта (projectId = id токена ERC1155)
     * Только ADMIN или ORGANIZER (если ему выдали роль) могут вызывать
     */
    function mint(address to, uint256 projectId, uint256 amount, bytes memory data) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _mint(to, projectId, amount, data);
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

    // Стандартные функции ERC1155 (balanceOf, safeTransferFrom и т.д.) уже реализованы в базовом контракте
}